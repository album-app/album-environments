import os
from enum import Enum
from pathlib import Path


class EnvironmentDefaultValues(Enum):
    # micromamba
    micromamba_url_linux_X86_64 = "https://micro.mamba.pm/api/micromamba/linux-64/1.5.6"
    micromamba_url_linux_ARM64 = (
        "https://micro.mamba.pm/api/micromamba/linux-aarch64/1.5.6"
    )
    micromamba_url_linux_POWER = (
        "https://micro.mamba.pm/api/micromamba/linux-ppc64le/1.5.6"
    )

    micromamba_url_osx_X86_64 = "https://micro.mamba.pm/api/micromamba/osx-64/1.5.6"
    micromamba_url_osx_ARM64 = "https://micro.mamba.pm/api/micromamba/osx-arm64/1.5.6"

    micromamba_url_windows = "https://gitlab.com/album-app/plugins/album-package/-/raw/micromamba_installer/win-64_micromamba-1.5.6-0.zip?ref_type=heads&inline=false"  # noqa: E501
    micromamba_base_path = (
        "micromamba"  # base folder prefix where micromamba is installed into
    )
    base_cache_path = os.getenv("ALBUM_BASE_CACHE_PATH", Path.home().joinpath(".album"))

    # micromamba
    micromamba_default_command = "micromamba"
    micromamba_path = os.getenv("ALBUM_MICROMAMBA_PATH", micromamba_default_command)

    # mamba
    mamba_default_command = "mamba"
    mamba_path = os.getenv("ALBUM_MAMBA_PATH")

    # conda
    conda_default_command = "conda"  # default conda executable
    conda_path = os.getenv("ALBUM_CONDA_PATH")

    # conda-lock
    conda_lock_default_command = "conda-lock"  # default conda-lock executable
    conda_lock_path = os.getenv("ALBUM_CONDA_LOCK_PATH")
