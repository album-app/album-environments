import platform
import shutil

from album.environments.controller.conda_manager import CondaManager
from album.environments.controller.environment_handler import EnvironmentHandler
from album.environments.controller.mamba_manager import MambaManager
from album.environments.controller.micromamba_manager import MicromambaManager


def init_environment_handler(env_base_path, default_micromamba_path, default_conda_path, default_conda_executable):
    if EnvironmentHandler.get_installed_package_manager(default_micromamba_path, default_conda_path) == "micromamba":
        _package_manager = MicromambaManager(default_micromamba_path, env_base_path)
        _env_install_manager = _package_manager
    else:
        conda_executable = default_conda_path
        if conda_executable is not default_conda_executable:
            conda_executable = EnvironmentHandler.build_conda_executable(conda_executable)
        else:
            if platform.system() == "Windows":
                conda_executable = shutil.which(conda_executable)
        _package_manager = CondaManager(conda_executable, env_base_path)
        mamba_executable = shutil.which("mamba")
        if mamba_executable:
            _env_install_manager = MambaManager(
                conda_executable, mamba_executable, env_base_path
            )
        else:
            _env_install_manager = _package_manager
    return EnvironmentHandler(_package_manager, _env_install_manager)