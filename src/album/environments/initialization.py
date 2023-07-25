import os
import platform
import shutil
from pathlib import Path

from album.environments.controller.conda_manager import CondaManager
from album.environments.controller.environment_handler import EnvironmentHandler
from album.environments.controller.mamba_manager import MambaManager
from album.environments.controller.micromamba_manager import MicromambaManager


def init_environment_handler(env_base_path):
    micromamba = shutil.which("micromamba")
    conda = shutil.which("conda")
    return init_environment_handler_from_paths(env_base_path, micromamba, conda, default_conda_executable=conda)


def init_micromamba_environment_handler(env_base_path):
    micromamba_path = get_micromamba_path(env_base_path)
    return init_environment_handler_from_paths(env_base_path, micromamba_path, None, default_conda_executable=None)


def init_conda_environment_handler(env_base_path):
    conda_default_executable, conda_path = get_conda_path()
    return init_environment_handler_from_paths(env_base_path, None, conda_path, default_conda_executable=conda_default_executable)


def init_mamba_environment_handler(env_base_path):
    conda_default_executable, conda_path = get_conda_path()
    return init_environment_handler_from_paths(env_base_path, None, conda_path, default_conda_executable=conda_default_executable)


def init_environment_handler_with_default_album_paths(app_data_dir):
    conda_default_executable, conda_path = get_conda_path()
    micromamba_path = get_micromamba_path(app_data_dir)
    return init_environment_handler_from_paths(app_data_dir, micromamba_path, conda_path, conda_default_executable)


def get_micromamba_path(app_data_dir):
    # These default executable cannot be used for environment activation!
    if platform.system() == "Windows":
        micromamba_app_path = str(
            Path(str(app_data_dir)).joinpath(
                "micromamba", "Library", "bin", "micromamba.exe"
            )
        )
    else:
        micromamba_app_path = str(
            Path(str(app_data_dir)).joinpath("micromamba", "bin", "micromamba")
        )
    if not Path(micromamba_app_path).exists():
        micromamba_path = shutil.which("micromamba")
    else:
        micromamba_path = micromamba_app_path
    micromamba_path = os.getenv("ALBUM_CONDA_PATH", micromamba_path)
    if micromamba_path is None:
        raise RuntimeError("Cannot find micromamba executable in %s" % micromamba_app_path)
    return micromamba_path


def get_conda_path():
    conda_default_executable = "conda"  # default conda executable
    conda_path = os.getenv(
        "ALBUM_CONDA_PATH", conda_default_executable
    )  # default conda path, either env. var or conda
    return conda_default_executable, conda_path


def init_environment_handler_from_paths(env_base_path, default_micromamba_path, default_conda_path, default_conda_executable):
    if EnvironmentHandler.check_for_executable(default_micromamba_path):
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