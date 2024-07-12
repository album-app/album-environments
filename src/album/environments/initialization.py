"""Initializes the environmentAPI object."""
import os
import platform
import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path
from typing import Optional

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
from album.environments.utils.url_operations import download_resource


class PackageManagerDetector:
    """Detects the package manager to use."""

    def __init__(
        self,
        base_env_path: Path,
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

        # explicitly defined valid package manager
        if micromamba_path is not None and Path(micromamba_path).is_file():
            self._micromamba_executable = micromamba_path
            get_active_logger().debug(
                "Using micromamba executable: %s", self._micromamba_executable
            )
        elif conda_path is not None:
            self._conda_executable = conda_path

            # check if mamba is available and favor it over conda
            if mamba_path is not None:
                self._mamba_executable = mamba_path
                get_active_logger().debug(
                    "Using mamba executable: %s", self._mamba_executable
                )
            else:
                get_active_logger().debug(
                    "Using conda executable: %s", self._conda_executable
                )
        elif mamba_path is not None:
            self._mamba_executable = mamba_path
            get_active_logger().debug(
                "Using mamba executable: %s", self._mamba_executable
            )
        elif not self.search_package_manager():
            # download and install micromamba
            get_active_logger().debug(
                "No package manager found! Trying to install micromamba..."
            )
            self.install_default_package_manager()
            # todo: install conda-lock

        self._package_manager = self.create_package_manager(base_env_path)

        # check for conda-lock
        if conda_lock_path is None:
            self._conda_lock_executable = self.search_lock_manager()
        else:
            self._conda_lock_executable = conda_lock_path

        if self._conda_lock_executable is not None:
            self._conda_lock_manager = CondaLockManager(
                self._conda_lock_executable, self._package_manager
            )

    def install_default_package_manager(self) -> None:
        """Install the default package manager."""
        base_cache_path = str(
            os.getenv(
                "ALBUM_BASE_CACHE_PATH", EnvironmentDefaultValues.base_cache_path.value
            )
        )
        self.install_mamba(
            base_cache_path, EnvironmentDefaultValues.micromamba_base_path.value
        )

    @staticmethod
    def check_architecture() -> str:
        """Check the processor architecture of the system."""
        check = subprocess.run(["uname", "-m"], capture_output=True)
        return check.stdout.decode().rstrip()

    @staticmethod
    def _download_mamba(mamba_base_path: Path) -> Path:
        """Download micromamba."""
        if platform.system() == "Windows":
            return PackageManagerDetector._download_mamba_win(
                mamba_base_path.joinpath("micromamba.zip")
            )
        elif platform.system() == "Darwin":
            return PackageManagerDetector._download_mamba_macos(
                mamba_base_path.joinpath("micromamba.tar")
            )
        elif platform.system() == "Linux":
            return PackageManagerDetector._download_mamba_linux(
                mamba_base_path.joinpath("micromamba.tar")
            )
        else:
            raise NotImplementedError(
                "Your operating system is currently not supported."
            )

    @staticmethod
    def _download_mamba_win(mamba_installer_path: Path) -> Path:
        """Download micromamba for windows."""
        return download_resource(
            EnvironmentDefaultValues.micromamba_url_windows.value, mamba_installer_path
        )

    @staticmethod
    def _download_mamba_macos(mamba_installer_path: Path) -> Path:
        """Download micromamba for macOS depending on the processor architecture."""
        if PackageManagerDetector.check_architecture().__eq__("x86_64"):
            return download_resource(
                EnvironmentDefaultValues.micromamba_url_osx_X86_64.value,
                mamba_installer_path,
            )
        elif PackageManagerDetector.check_architecture().lower().__eq__("arm64"):
            return download_resource(
                EnvironmentDefaultValues.micromamba_url_osx_ARM64.value,
                mamba_installer_path,
            )
        else:
            raise NotImplementedError(
                "There is no micromamba version for your processor architecture."
            )

    @staticmethod
    def _download_mamba_linux(mamba_installer_path: Path) -> Path:
        """Download micromamba for linux depending on the processor architecture."""
        if PackageManagerDetector.check_architecture().__eq__("x86_64"):
            return download_resource(
                EnvironmentDefaultValues.micromamba_url_linux_X86_64.value,
                mamba_installer_path,
            )
        elif PackageManagerDetector.check_architecture().lower().__eq__("arm64"):
            return download_resource(
                EnvironmentDefaultValues.micromamba_url_linux_ARM64.value,
                mamba_installer_path,
            )
        elif PackageManagerDetector.check_architecture().lower().__eq__("power"):
            return download_resource(
                EnvironmentDefaultValues.micromamba_url_linux_POWER.value,
                mamba_installer_path,
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
        os.environ["MAMBA_EXE"] = PackageManagerDetector.get_mamba_exe(mamba_base_path)

    @staticmethod
    def get_mamba_exe(mamba_base_path: Path) -> str:
        """Return the path to the micromamba executable."""
        if platform.system() == "Windows":
            return str(
                Path(mamba_base_path).joinpath("Library", "bin", "micromamba.exe")
            )
        else:
            return str(Path(mamba_base_path).joinpath("bin", "micromamba"))

    @staticmethod
    def install_mamba(album_base_path: str, mamba_base_path: str) -> None:
        """Install micormamba."""
        album_base_path_ = Path(album_base_path)
        mamba_base_path_ = Path(mamba_base_path)
        if not album_base_path_.exists():
            album_base_path_.mkdir()
        if not mamba_base_path_.exists():
            mamba_base_path_.mkdir()

        installer = PackageManagerDetector._download_mamba(mamba_base_path_)
        if platform.system() == "Windows":
            PackageManagerDetector._unpack_mamba_win(installer, mamba_base_path_)
        else:
            PackageManagerDetector._unpack_mamba_unix(installer, mamba_base_path_)
        PackageManagerDetector._set_mamba_env_vars(mamba_base_path_)

    @staticmethod
    def search_lock_manager() -> Optional[str]:
        """Search for the conda-lock executable."""
        conda_lock_executable = shutil.which("conda-lock")
        if conda_lock_executable:
            get_active_logger().debug(
                "Using conda-lock executable: %s", conda_lock_executable
            )
        else:
            get_active_logger().debug(
                "No conda-lock executable found! Cannot lock environments during deployment!"
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
    env_base_path: Path,
) -> IEnvironmentAPI:
    """Initialize the environment API.

    Only method that should be called from the album core.
    """
    micromamba_path = EnvironmentDefaultValues.micromamba_path.value
    mamba_path = EnvironmentDefaultValues.mamba_path.value
    conda_path = EnvironmentDefaultValues.conda_path.value
    conda_lock_path = EnvironmentDefaultValues.conda_lock_path.value

    package_manager_detector = PackageManagerDetector(
        env_base_path, micromamba_path, mamba_path, conda_path, conda_lock_path
    )
    package_manager = package_manager_detector.get_package_manager()
    conda_lock_manager = package_manager_detector.get_conda_lock_manager()
    return EnvironmentAPI(package_manager, conda_lock_manager)
