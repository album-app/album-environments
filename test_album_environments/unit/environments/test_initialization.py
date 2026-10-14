import unittest
from pathlib import Path
from unittest.mock import patch

from album.environments.initialization import PackageManagerHandler
from album.environments.model.environment_default_values import EnvironmentDefaultValues


class TestDownloadMambaLinux(unittest.TestCase):
    """The micromamba download for the processor architecture reported by "uname -m"."""

    def download_url(self, architecture: str) -> str:
        with patch.object(PackageManagerHandler, "check_architecture", return_value=architecture), patch(
            "album.environments.initialization.pooch.retrieve", return_value="micromamba.tar"
        ) as retrieve:
            PackageManagerHandler._download_mamba_linux(Path("micromamba.tar"))
        return retrieve.call_args.kwargs["url"]

    def test_x86_64(self):
        self.assertEqual(EnvironmentDefaultValues.micromamba_url_linux_X86_64.value, self.download_url("x86_64"))

    def test_arm64(self):
        for architecture in ["aarch64", "arm64"]:
            with self.subTest(architecture=architecture):
                self.assertEqual(
                    EnvironmentDefaultValues.micromamba_url_linux_ARM64.value, self.download_url(architecture)
                )

    def test_power(self):
        for architecture in ["ppc64le", "power"]:
            with self.subTest(architecture=architecture):
                self.assertEqual(
                    EnvironmentDefaultValues.micromamba_url_linux_POWER.value, self.download_url(architecture)
                )

    def test_unknown_architecture(self):
        with self.assertRaises(NotImplementedError):
            self.download_url("riscv64")


if __name__ == "__main__":
    unittest.main()
