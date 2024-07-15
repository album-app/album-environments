import os
from enum import Enum


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

    # need self-hosted installation for windows due to unzip issues
    micromamba_url_windows = "https://gitlab.com/album-app/plugins/album-package/-/raw/micromamba_installer/win-64_micromamba-1.5.6-0.zip?ref_type=heads&inline=false"  # noqa: E501
    micromamba_base_prefix = (
        "micromamba"  # base folder prefix where micromamba is installed into
    )

    # micromamba
    micromamba_path = os.getenv("ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH")

    # mamba, feature for debugging only
    mamba_path = os.getenv("ENVIRONMENT_DEBUGGING_MAMBA_PATH")

    # conda, feature for debugging only
    conda_path = os.getenv("ENVIRONMENT_DEBUGGING_CONDA_PATH")

    # conda-lock
    conda_lock_path = os.getenv("ENVIRONMENT_CONDA_LOCK_PATH")

    # environment base path
    environment_install_path = os.getenv("ENVIRONMENT_INSTALLATION_PATH")
