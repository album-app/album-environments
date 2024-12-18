from pathlib import Path

from album.environments.controller.conda_manager import CondaManager


class MambaManager(CondaManager):
    """Class for handling conda environments via mamba."""

    def __init__(self, mamba_executable: str, base_env_path: Path):
        super().__init__(mamba_executable, base_env_path, "mamba")
