from pathlib import Path
from typing import List

from album.runner.album_logging import get_active_logger

from album.environments.api.controller.conda_lock_manager import ICondaLockManager
from album.environments.api.controller.package_manager import IPackageManager
from album.environments.utils import subcommand
from album.environments.utils.file_operations import force_remove


class CondaLockManager(ICondaLockManager):
    def __init__(self, conda_lock_executable: str, package_manager: IPackageManager):
        self._conda_lock_executable = conda_lock_executable
        self._package_manager = package_manager

    def create_conda_lock_file(
        self, solution_yml: Path, conda_lock_executable: Path
    ) -> Path:
        if conda_lock_executable is None:
            raise RuntimeError(
                "No conda-lock executable found! Cannot lock environments!"
            )
        solution_lock_path = solution_yml.parent.joinpath("solution.conda-lock.yml")
        if solution_lock_path.exists():
            force_remove(solution_lock_path)
        conda_lock_args = [
            str(conda_lock_executable),
            "--file",
            str(solution_yml),
            "-p",
            "linux-64",
            "-p",
            "osx-64",
            "-p",
            "win-64",
            "-p",
            "osx-arm64",  # For Apple Silicon, e.g. M1/M2
            "-p",
            "linux-aarch64",  # aka arm64, use for Docker on Apple Silicon
            "-p",
            "linux-ppc64le",
        ]
        conda_lock_args.extend(self._append_package_manager_choice_args())
        conda_lock_args.extend(["--lockfile", str(solution_lock_path)])
        subcommand.run(conda_lock_args)
        return solution_lock_path

    def create_environment_from_lockfile(
        self, conda_lock_file: Path, environment_path: Path
    ) -> None:
        environment_path = Path(environment_path)
        if self._package_manager.environment_exists(environment_path):
            get_active_logger().debug(
                "Environment already exists, removing it first..."
            )
            self._package_manager.remove_environment(environment_path)

        env_prefix = environment_path
        force_remove(
            env_prefix
        )  # Force remove is needed since the env location need to be created to create the link to it but
        # for micromamba the env location has to be created by micromamba itself or an error is raised

        if not (
            str(conda_lock_file).endswith(".yml")
            or str(conda_lock_file).endswith(".yaml")
        ):
            raise NameError("Conda lock file needs to be a yml or yaml file!")

        install_args = self._get_env_create_args(env_prefix, conda_lock_file)

        try:
            subcommand.run(install_args, log_output=True)
        except RuntimeError as e:
            # cleanup after failed installation
            if self._package_manager.environment_exists(env_prefix):
                get_active_logger().debug("Cleanup failed environment creation...")
                self._package_manager.remove_environment(env_prefix)
            raise RuntimeError("Command failed due to: %s" % e) from e

    def _get_env_create_args(self, env_prefix: Path, lock_file: Path) -> List[str]:
        """Return the arguments for the conda-lock install subprocess using the installed package manager."""
        args = [str(self._conda_lock_executable), "install", "-p", str(env_prefix)]
        args.extend(self._append_package_manager_choice_args())
        args.append(str(lock_file))
        return args

    def _append_package_manager_choice_args(self) -> List[str]:
        if self._package_manager.get_package_manager_name() == "micromamba":
            return self._get_install_args_micromamba()
        elif self._package_manager.get_package_manager_name() == "mamba":
            return self._get_install_args_mamba()
        else:
            return self._get_install_args_conda()

    def _get_install_args_micromamba(self) -> List[str]:
        """Return the arguments for the conda-lock install subprocess using the micromamba."""
        return [
            "--conda",
            str(self._package_manager.get_install_environment_executable()),
        ]

    def _get_install_args_conda(self) -> List[str]:
        """Return the arguments for the conda-lock install subprocess using conda."""
        return [
            "--no-mamba",
            "--no-micromamba",
        ]  # , "--conda", self.get_install_environment_executable() this is not pased since the conda executable is
        # mots of the times just the str conda which is not a supported arguement of conda-lock

    def _get_install_args_mamba(self) -> List[str]:
        """Return the arguments for the conda-lock install subprocess using mamba."""
        return [
            "--no-micromamba",
            "--conda",
            str(self._package_manager.get_install_environment_executable()),
        ]

    def conda_lock_executable(self) -> str:
        if self._conda_lock_executable is None:
            raise RuntimeError("No conda-lock executable found!")
        return self._conda_lock_executable
