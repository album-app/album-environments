from pathlib import Path
from typing import Union

from album.runner import album_logging

from album.environments.api.model.environment import IEnvironment

module_logger = album_logging.get_active_logger


class Environment(IEnvironment):
    def __init__(
        self,
        yaml_file: Union[Path, None],
        environment_name: str,
        environment_path: str = None,
    ):
        """Initialize the environment object.

        Args:
            yaml_file:
                The YAML file specifying the environment dependencies
            environment_name:
                name prefix for all files to cache.
                Used when "name" is not available during yaml-file download for example.
        """
        self._name = environment_name
        self._yaml_file = yaml_file
        self._path = environment_path

    def name(self):
        return self._name

    def yaml_file(self):
        return self._yaml_file

    def path(self):
        return self._path

    def set_path(self, path):
        self._path = path
