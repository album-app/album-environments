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


class PackageManagerHandler:
    """Detects the package manager to use."""

    def __init__(
        self,
        base_env_path: Path,
        installation_path: Path,
        micromamba_path: Optional[str] = None,
        conda_path: Optional[str] = None,
        mamba_path: Optional[str] = None,
        conda_lock_path: Optional[str] = None,
    ):
        """Initialize the package manager detector."""
        self._conda_executable = None
        self._mamba_executable = None
        self._micromamba_executable = None
        self._conda_lock_executable = None

        _def_pktm_path = None

        # explicitly defined valid package manager
        if micromamba_path is not None and Path(micromamba_path).is_file():
            self._micromamba_executable = micromamba_path
            get_active_logger().debug(
                "Using micromamba executable: %s", self._micromamba_executable
            )
        elif mamba_path is not None and Path(mamba_path).is_file():
            self._mamba_executable = mamba_path
            get_active_logger().warn(
                "Using unsupported mamba executable: %s", self._mamba_executable
            )
        elif conda_path is not None and Path(conda_path).is_file():
            self._conda_executable = conda_path
            get_active_logger().warn(
                "Using unsupported conda executable: %s", self._conda_executable
            )
        else:
            # expected mamba executable
            _micromamba_exe = Path(
                self.get_mamba_exe(
                    installation_path.joinpath(
                        EnvironmentDefaultValues.micromamba_base_prefix.value
                    )
                )
            )
            if not _micromamba_exe.is_file():
                # download and install micromamba
                get_active_logger().debug(
                    "No package manager explicitly specified. Installing micromamba..."
                )
                _def_pktm_path = self.install_default_package_manager(installation_path)
                self._micromamba_executable = self.get_mamba_exe(_def_pktm_path)
            else:
                self._micromamba_executable = str(_micromamba_exe)

        self._package_manager = self.create_package_manager(base_env_path)

        # check for conda-lock
        if conda_lock_path is not None and Path(conda_lock_path).is_file():
            get_active_logger().info("Using conda-lock executable: %s", conda_lock_path)
            self._conda_lock_executable = conda_lock_path
        elif self.search_lock_manager(msg=False):
            self._conda_lock_executable = self.search_lock_manager()
        else:
            if _def_pktm_path is not None:
                # install conda-lock in base environment of downloaded package manager
                self.install_conda_lock(self.get_package_manager())
                self._conda_lock_executable = self.get_conda_lock_exe(_def_pktm_path)
            else:
                get_active_logger().debug(
                    "No conda-lock executable found! Cannot lock environments during deployment! "
                    "Set explicitly in the environment variable ENVIRONMENT_CONDA_LOCK_PATH."
                )
                self._conda_lock_executable = None

        self._conda_lock_manager = CondaLockManager(
            self._conda_lock_executable, self._package_manager
        )

    def install_default_package_manager(self, install_path: Path) -> Path:
        """Install the default package manager."""
        return self.install_micro_mamba(
            str(install_path), EnvironmentDefaultValues.micromamba_base_prefix.value
        )

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
    def _download_mamba_linux(mamba_installer_path: Path) -> Path:
        """Download micromamba for linux depending on the processor architecture."""
        if PackageManagerHandler.check_architecture().__eq__("x86_64"):
            return Path(
                pooch.retrieve(
                    url=EnvironmentDefaultValues.micromamba_url_linux_X86_64.value,
                    known_hash=EnvironmentDefaultValues.micromamba_url_linux_X86_64_hash.value,
                    fname=EnvironmentDefaultValues.micromamba_base_prefix.value,
                    path=mamba_installer_path,
                    progressbar=False,
                )
            )
        elif PackageManagerHandler.check_architecture().lower().__eq__("arm64"):
            return Path(
                pooch.retrieve(
                    url=EnvironmentDefaultValues.micromamba_url_linux_ARM64.value,
                    known_hash=EnvironmentDefaultValues.micromamba_url_linux_ARM64_hash.value,
                    fname=EnvironmentDefaultValues.micromamba_base_prefix.value,
                    path=mamba_installer_path,
                    progressbar=False,
                )
            )
        elif PackageManagerHandler.check_architecture().lower().__eq__("power"):
            return Path(
                pooch.retrieve(
                    url=EnvironmentDefaultValues.micromamba_url_linux_POWER.value,
                    known_hash=EnvironmentDefaultValues.micromamba_url_linux_POWER_hash.value,
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
    def _unpack_mamba_win(mamba_installer: Path, mamba_base_path: Path) -> None:
        """Unpack the Windows version of the micromamba archive."""
        with zipfile.ZipFile(mamba_installer) as zipf:
            zipf.extractall(mamba_base_path)

    @staticmethod
    def _unpack_mamba_unix(mamba_installer: Path, mamba_base_path: Path) -> None:
        """Unpack the micromamba archives for linux and macOS."""
        with tarfile.open(mamba_installer, "r") as tar:
            tar.extractall(mamba_base_path)

    @staticmethod
    def _set_mamba_env_vars(mamba_base_path: Path) -> None:
        """Set the micromamba environment variables."""
        os.environ["MAMBA_ROOT_PREFIX"] = str(mamba_base_path)
        os.environ["MAMBA_EXE"] = PackageManagerHandler.get_mamba_exe(mamba_base_path)

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
            return str(Path(mamba_base_path).joinpath("bin", "micromamba").resolve())

    @staticmethod
    def get_conda_lock_exe(mamba_root_prefix: Path) -> str:
        """Return the path to the micromamba executable."""
        if platform.system() == "Windows":
            return str(
                Path(mamba_root_prefix).joinpath("Scripts", "conda-lock.exe").resolve()
            )
        else:
            return str(Path(mamba_root_prefix).joinpath("bin", "conda-lock").resolve())

    @staticmethod
    def install_micro_mamba(install_base_path: str, mamba_base_prefix: str) -> Path:
        """Install micromamba."""
        install_base_path_ = Path(install_base_path)
        if not install_base_path_.exists():
            install_base_path_.mkdir()

        mamba_base_path_ = install_base_path_.joinpath(mamba_base_prefix)
        if not mamba_base_path_.exists():
            mamba_base_path_.mkdir()

        installer = PackageManagerHandler._download_mamba(mamba_base_path_)
        if platform.system() == "Windows":
            PackageManagerHandler._unpack_mamba_win(installer, mamba_base_path_)
        else:
            PackageManagerHandler._unpack_mamba_unix(installer, mamba_base_path_)
        PackageManagerHandler._set_mamba_env_vars(mamba_base_path_)

        return mamba_base_path_

    @staticmethod
    def search_lock_manager(msg: bool = True) -> Optional[str]:
        """Search for the conda-lock executable."""
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
        if self._micromamba_executable:
            return MicromambaManager(
                self._micromamba_executable, base_env_path=base_env_path
            )
        elif self._mamba_executable:
            return MambaManager(self._mamba_executable, base_env_path=base_env_path)
        else:
            if self._conda_executable is None:
                raise RuntimeError("No package manager found!")
            return CondaManager(self._conda_executable, base_env_path=base_env_path)

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
    micromamba_path_or_cmd = EnvironmentDefaultValues.micromamba_path.value
    mamba_path_or_cmd = EnvironmentDefaultValues.mamba_path.value
    conda_path_or_cmd = EnvironmentDefaultValues.conda_path.value
    conda_lock_path_or_cmd = EnvironmentDefaultValues.conda_lock_path.value

    package_manager_handler = PackageManagerHandler(
        base_env_path=env_base_path,
        installation_path=installation_base_path,
        micromamba_path=micromamba_path_or_cmd,
        mamba_path=mamba_path_or_cmd,
        conda_path=conda_path_or_cmd,
        conda_lock_path=conda_lock_path_or_cmd,
    )
    package_manager = package_manager_handler.get_package_manager()
    conda_lock_manager = package_manager_handler.get_conda_lock_manager()
    return EnvironmentAPI(package_manager, conda_lock_manager)
