"""Initializes the environmentAPI object."""
import os
import platform
import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path
from typing import Optional

import pooch
from album.runner.album_logging import get_active_logger

from album.environments.api.controller.conda_lock_manager import ICondaLockManager
from album.environments.api.controller.package_manager import IPackageManager
from album.environments.api.environment_api import IEnvironmentAPI
from album.environments.controller.conda_lock_manager import CondaLockManager
from album.environments.controller.conda_manager import CondaManager
from album.environments.controller.mamba_manager import MambaManager
from album.environments.controller.micromamba_manager import MicromambaManager
from album.environments.environment_api import EnvironmentAPI
from album.environments.model.environment_default_values import EnvironmentDefaultValues
from album.environments.utils.subcommand import SubProcessError


class PackageManagerHandler:
    """Detects the package manager to use."""

    def __init__(
        self,
        base_env_path: str,
        installation_path: str,
        micromamba_path: Optional[str] = None,
        conda_path: Optional[str] = None,
        mamba_path: Optional[str] = None,
        conda_lock_path: Optional[str] = None,
    ):
        """Initialize the package manager detector."""
        _base_env_path = Path(base_env_path)
        _base_env_path.mkdir(parents=True, exist_ok=True)

        _installation_path = Path(installation_path)
        _installation_path.mkdir(parents=True, exist_ok=True)

        self._conda_executable: Optional[str] = None
        self._mamba_executable: Optional[str] = None
        self._micromamba_executable: Optional[str] = None
        self._conda_lock_executable: Optional[str] = None

        explicitly_set = self._get_package_manager_executable_from_env(
            micromamba_path=micromamba_path,
            conda_path=conda_path,
            mamba_path=mamba_path,
        )
        _def_pktm_path = None
        if not explicitly_set:
            _def_pktm_path = self.set_package_manager_executable(
                _installation_path, _base_env_path
            )

        self._package_manager = self.create_package_manager(_base_env_path)

        self.set_conda_lock(_installation_path, conda_lock_path, _def_pktm_path)

        # allow error
        self._conda_lock_manager = CondaLockManager(
            self._conda_lock_executable, self._package_manager
        )

    def _get_package_manager_executable_from_env(
        self,
        conda_path: Optional[str],
        mamba_path: Optional[str],
        micromamba_path: Optional[str],
    ) -> bool:
        if micromamba_path is not None and Path(micromamba_path).is_file():
            self._micromamba_executable = micromamba_path
            get_active_logger().debug(
                "Using micromamba executable: %s", self._micromamba_executable
            )
            return True
        elif mamba_path is not None and Path(mamba_path).is_file():
            self._mamba_executable = mamba_path
            get_active_logger().warning(
                "Using unsupported mamba executable: %s", self._mamba_executable
            )
            return True
        elif conda_path is not None and Path(conda_path).is_file():
            self._conda_executable = conda_path
            get_active_logger().warning(
                "Using unsupported conda executable: %s", self._conda_executable
            )
            return True
        return False

    def set_package_manager_executable(
        self, installation_path: Path, base_env_path: Path
    ) -> Optional[Path]:
        """Set the package manager executable using defined environment variables or download if not present."""
        _def_pktm_path = None

        # default installation path
        _install_path = installation_path.joinpath(
            EnvironmentDefaultValues.micromamba_base_prefix.value
        )

        # expected default mamba executable
        _micromamba_exe = Path(self.get_mamba_exe(_install_path))
        get_active_logger().debug("Expected micromamba executable: %s", _micromamba_exe)

        if not _micromamba_exe.is_file():
            # download and install micromamba
            get_active_logger().debug(
                "No package manager explicitly specified. Installing default package manager..."
            )
            _def_pktm_path = self.install_default_package_manager(
                _install_path,
            )
            self._micromamba_executable = self.get_mamba_exe(_def_pktm_path)
        else:
            self._micromamba_executable = str(_micromamba_exe)

        # ensure environment variables are correctly set within this python call
        PackageManagerHandler.set_default_package_manager_env_vars(
            _install_path, base_env_path
        )

        return _def_pktm_path

    def set_conda_lock(
        self,
        installation_path: Path,
        conda_lock_path: Optional[str],
        _def_pktm_path: Optional[Path],
    ) -> None:
        """Set the conda lock executable based on environment variables or install in base package manager."""
        # check for conda-lock explicitly given
        if conda_lock_path is not None and Path(conda_lock_path).is_file():
            get_active_logger().info("Using conda-lock executable: %s", conda_lock_path)
            self._conda_lock_executable = conda_lock_path
            return

        # check if conda-lock is available in the base environment of the given package manager
        expected_conda_lock_path = self.get_conda_lock_exe(
            self._package_manager.get_base_environment_path()
        )

        # check if conda-lock is available in the base environment of the given package manager
        if Path(expected_conda_lock_path).is_file():
            self._conda_lock_executable = expected_conda_lock_path
            return

        else:
            # search for conda-lock as it comes with the dependencies of this repository
            _conda_lock_executable = self.search_lock_manager()

            if _conda_lock_executable is not None:
                self._conda_lock_executable = _conda_lock_executable
                return

            # try to install conda-lock in the base environment of the package manager
            if _def_pktm_path is not None:
                try:
                    self._create_base_environment()
                    self.install_conda_lock(self.get_package_manager())
                    self._conda_lock_executable = self.get_conda_lock_exe(
                        _def_pktm_path
                    )
                except SubProcessError as se:
                    get_active_logger().debug(
                        "Error when installing conda-lock in the base environment %s of the package manager %s."
                        "Continuing without conda-lock. Error message: %s"
                        % (
                            str(installation_path),
                            self.get_package_manager().get_package_manager_name(),
                            str(se),
                        )
                    )
                return

            if self._conda_lock_executable is None:
                get_active_logger().debug(
                    "No conda-lock executable found! Cannot lock environments during deployment! "
                    "Set explicitly in the environment variable ENVIRONMENT_CONDA_LOCK_PATH or install in the"
                    " base environment %s of the package manager %s."
                    % (
                        self.get_package_manager().get_base_environment_path(),
                        self.get_package_manager().get_package_manager_name(),
                    )
                )

    def _create_base_environment(self) -> None:
        self.get_package_manager().create_environment(
            str(self.get_package_manager().get_base_environment_path().resolve()),
            EnvironmentDefaultValues.default_solution_python_version.value,
        )

    def install_default_package_manager(self, install_path: Path) -> Path:
        """Install the default package manager."""
        return self.install_micro_mamba(install_path)

    def install_conda_lock(self, package_manager: IPackageManager) -> None:
        """Install conda-lock."""
        package_manager.base_install("conda-lock")

    @staticmethod
    def check_architecture() -> str:
        """Check the processor architecture of the system."""
        check = subprocess.run(["uname", "-m"], capture_output=True)
        return check.stdout.decode().rstrip()

    @staticmethod
    def _download_mamba(mamba_base_path: Path) -> Path:
        """Download micromamba."""
        if platform.system() == "Windows":
            return PackageManagerHandler._download_mamba_win(
                mamba_base_path.joinpath("micromamba.zip")
            )
        elif platform.system() == "Darwin":
            return PackageManagerHandler._download_mamba_macos(
                mamba_base_path.joinpath("micromamba.tar")
            )
        elif platform.system() == "Linux":
            return PackageManagerHandler._download_mamba_linux(
                mamba_base_path.joinpath("micromamba.tar")
            )
        else:
            raise NotImplementedError(
                "Your operating system is currently not supported."
            )

    @staticmethod
    def _download_mamba_win(mamba_installer_path: Path) -> Path:
        """Download micromamba for windows."""
        return Path(
            pooch.retrieve(
                url=EnvironmentDefaultValues.micromamba_url_windows.value,
                known_hash=EnvironmentDefaultValues.micromamba_url_windows_hash.value,
                fname=EnvironmentDefaultValues.micromamba_base_prefix.value,
                path=mamba_installer_path,
                progressbar=False,
            )
        )

    @staticmethod
    def _download_mamba_macos(mamba_installer_path: Path) -> Path:
        """Download micromamba for macOS depending on the processor architecture."""
        if PackageManagerHandler.check_architecture().__eq__("x86_64"):
            return Path(
                pooch.retrieve(
                    url=EnvironmentDefaultValues.micromamba_url_osx_X86_64.value,
                    known_hash=EnvironmentDefaultValues.micromamba_url_osx_X86_64_hash.value,
                    fname=EnvironmentDefaultValues.micromamba_base_prefix.value,
                    path=mamba_installer_path,
                    progressbar=False,
                )
            )

        elif PackageManagerHandler.check_architecture().lower().__eq__("arm64"):
            return Path(
                pooch.retrieve(
                    url=EnvironmentDefaultValues.micromamba_url_osx_ARM64.value,
                    known_hash=EnvironmentDefaultValues.micromamba_url_osx_ARM64_hash.value,
                    fname=EnvironmentDefaultValues.micromamba_base_prefix.value,
                    path=mamba_installer_path,
                    progressbar=False,
                )
            )

        else:
            raise NotImplementedError(
                "There is no micromamba version for your processor architecture."
            )

    @staticmethod
    def _download_mamba_linux(mamba_download_file: Path) -> Path:
        """Download micromamba for linux depending on the processor architecture."""
        if PackageManagerHandler.check_architecture().__eq__("x86_64"):
            return Path(
                pooch.retrieve(
                    url=EnvironmentDefaultValues.micromamba_url_linux_X86_64.value,
                    known_hash=EnvironmentDefaultValues.micromamba_url_linux_X86_64_hash.value,
                    fname=mamba_download_file.name,
                    path=mamba_download_file.parent,
                    progressbar=False,
                )
            )
        elif PackageManagerHandler.check_architecture().lower().__eq__("arm64"):
            return Path(
                pooch.retrieve(
                    url=EnvironmentDefaultValues.micromamba_url_linux_ARM64.value,
                    known_hash=EnvironmentDefaultValues.micromamba_url_linux_ARM64_hash.value,
                    fname=mamba_download_file.name,
                    path=mamba_download_file.parent,
                    progressbar=False,
                )
            )
        elif PackageManagerHandler.check_architecture().lower().__eq__("power"):
            return Path(
                pooch.retrieve(
                    url=EnvironmentDefaultValues.micromamba_url_linux_POWER.value,
                    known_hash=EnvironmentDefaultValues.micromamba_url_linux_POWER_hash.value,
                    fname=mamba_download_file.name,
                    path=mamba_download_file.parent,
                    progressbar=False,
                )
            )
        else:
            raise NotImplementedError(
                "There is no micromamba version for your processor architecture."
            )

    @staticmethod
    def _unpack_mamba_win(mamba_installer: Path, mamba_base_path: Path) -> None:
        """Unpack the Windows version of the micromamba archive."""
        with zipfile.ZipFile(mamba_installer) as zipf:
            get_active_logger().debug(
                f"Extracting {str(mamba_installer)} to {str(mamba_base_path)}"
            )
            zipf.extractall(mamba_base_path)

    @staticmethod
    def _unpack_mamba_unix(mamba_installer: Path, mamba_base_path: Path) -> None:
        """Unpack the micromamba archives for linux and macOS."""
        with tarfile.open(mamba_installer, "r") as tar:
            get_active_logger().debug(
                f"Extracting {str(mamba_installer)} to {str(mamba_base_path)}"
            )
            tar.extractall(mamba_base_path)

    @staticmethod
    def _set_mamba_env_vars(mamba_install_path: Path, env_root: Path) -> None:
        """Set the micromamba environment variables."""
        os.environ["MAMBA_ROOT_PREFIX"] = str(env_root)
        os.environ["MAMBA_EXE"] = PackageManagerHandler.get_mamba_exe(
            mamba_install_path
        )

    @staticmethod
    def set_default_package_manager_env_vars(
        install_path: Path, env_root: Path
    ) -> None:
        """Set the default package manager environment variables."""
        PackageManagerHandler._set_mamba_env_vars(install_path, env_root)

    @staticmethod
    def get_mamba_exe(mamba_base_path: Path) -> str:
        """Return the path to the micromamba executable."""
        if platform.system() == "Windows":
            return str(
                Path(mamba_base_path)
                .joinpath("Library", "bin", "micromamba.exe")
                .resolve()
            )
        else:
            get_active_logger().debug("Mamba base path: %s", mamba_base_path)
            return str(Path(mamba_base_path).joinpath("bin", "micromamba").resolve())

    @staticmethod
    def get_conda_lock_exe(default_prefix: Path) -> str:
        """Return the path to the micromamba executable."""
        if platform.system() == "Windows":
            return str(
                Path(default_prefix).joinpath("Scripts", "conda-lock.exe").resolve()
            )
        else:
            return str(Path(default_prefix).joinpath("bin", "conda-lock").resolve())

    @staticmethod
    def install_micro_mamba(install_base_path: Path) -> Path:
        """Install micromamba."""
        get_active_logger().debug(
            "Installing micromamba in: %s", str(install_base_path)
        )

        install_base_path_ = install_base_path
        if not install_base_path_.exists():
            install_base_path_.mkdir()

        installer = PackageManagerHandler._download_mamba(install_base_path_)
        if platform.system() == "Windows":
            PackageManagerHandler._unpack_mamba_win(installer, install_base_path_)
        else:
            PackageManagerHandler._unpack_mamba_unix(installer, install_base_path_)

        return install_base_path_

    @staticmethod
    def search_lock_manager(msg: bool = True) -> Optional[str]:
        """Search for the conda-lock executable."""
        get_active_logger().debug("Searching for conda-lock")

        conda_lock_executable = shutil.which("conda-lock")
        if conda_lock_executable:
            if msg:
                get_active_logger().debug(
                    "Using conda-lock executable: %s", conda_lock_executable
                )
        else:
            if msg:
                get_active_logger().debug(
                    "No conda-lock executable found! Cannot lock environments during deployment! "
                    "Set explicitly in the environment variable ENVIRONMENT_CONDA_LOCK_PATH."
                )
        return conda_lock_executable

    def search_package_manager(self) -> bool:
        """Search for the package manager."""
        # search for micromamba
        self._micromamba_executable = shutil.which("micromamba")
        if self._micromamba_executable is not None:
            get_active_logger().debug(
                "Using micromamba executable: %s", self._micromamba_executable
            )
            return True
        else:
            # search for conda
            self._conda_executable = shutil.which("conda")
            if self._conda_executable is not None:
                # additionally search for mamba
                self._mamba_executable = shutil.which("mamba")
                if self._mamba_executable is not None:
                    get_active_logger().debug(
                        "Using mamba executable: %s", self._mamba_executable
                    )
                else:
                    get_active_logger().debug(
                        "Using conda executable: %s", self._conda_executable
                    )
                return True
            else:
                return False

    def create_package_manager(self, base_env_path: Path) -> IPackageManager:
        """Create the package manager objet."""
        get_active_logger().debug(
            "Creating package manager with base environment: %s", str(base_env_path)
        )

        # create base environment path if not exists
        if not base_env_path.exists():
            base_env_path.mkdir()

        # init package manager
        if self._micromamba_executable:
            return MicromambaManager(
                self._micromamba_executable, base_env_path=base_env_path
            )
        elif self._mamba_executable:
            return MambaManager(self._mamba_executable, base_env_path=base_env_path)
        elif self._conda_executable:
            return CondaManager(self._conda_executable, base_env_path=base_env_path)
        else:
            raise RuntimeError("No package manager found!")

    def get_conda_lock_manager(self) -> ICondaLockManager:
        """Get the conda lock manager."""
        return self._conda_lock_manager

    def get_package_manager(self) -> IPackageManager:
        """Get the package manager."""
        return self._package_manager


def init_environment_handler(
    env_base_path: Path, installation_base_path: Path
) -> IEnvironmentAPI:
    """Initialize the environment API.

    env_base_path: Path
        The path where the environments are stored.
    installation_base_path: Path
        The path where the installation files are stored.

    Only method that should be called from outside.
    """
    micromamba_exe = EnvironmentDefaultValues.micromamba_path.value
    mamba_exe = EnvironmentDefaultValues.mamba_path.value
    conda_exe = EnvironmentDefaultValues.conda_path.value
    conda_lock_exe = EnvironmentDefaultValues.conda_lock_path.value

    package_manager_handler = PackageManagerHandler(
        base_env_path=str(env_base_path),
        installation_path=str(installation_base_path),
        micromamba_path=micromamba_exe,
        mamba_path=mamba_exe,
        conda_path=conda_exe,
        conda_lock_path=conda_lock_exe,
    )
    package_manager = package_manager_handler.get_package_manager()
    conda_lock_manager = package_manager_handler.get_conda_lock_manager()
    return EnvironmentAPI(package_manager, conda_lock_manager)
