from album.environments.controller.conda_manager import CondaManager


class MambaManager(CondaManager):
    """Class for handling conda environments via mamba."""

    def __init__(self, mamba_executable, base_env_path):
        super().__init__(mamba_executable, "mamba", base_env_path)

