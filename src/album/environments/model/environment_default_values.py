import os
from enum import Enum


class EnvironmentDefaultValues(Enum):
    # micromamba
    micromamba_url_linux_X86_64 = "https://micro.mamba.pm/api/micromamba/linux-64/1.5.6"
    micromamba_url_linux_X86_64_hash = (
        "efe462c7ffcae8b338c7dd7b168ce8d48cfc60b48ab991d02a035c3b8d73633c"
    )

    micromamba_url_linux_ARM64 = (
        "https://micro.mamba.pm/api/micromamba/linux-aarch64/1.5.6"
    )
    micromamba_url_linux_ARM64_hash = (
        "37b17006eff1dd6ff797ec59ec19b1f9e50f518dbbfe684f15b2fd5d3d1f529a"
    )

    micromamba_url_linux_POWER = (
        "https://micro.mamba.pm/api/micromamba/linux-ppc64le/1.5.6"
    )
    micromamba_url_linux_POWER_hash = (
        "4cffe81de8bc5281984d8085de5481a88f73ecbd1d9cb77c1149408e5bdbb5ef"
    )

    micromamba_url_osx_X86_64 = "https://micro.mamba.pm/api/micromamba/osx-64/1.5.6"
    micromamba_url_osx_X86_64_hash = (
        "17636ef379560a43fd49524e1c802238ce69f88d39e43285b23a7920bcb404a1"
    )

    micromamba_url_osx_ARM64 = "https://micro.mamba.pm/api/micromamba/osx-arm64/1.5.6"
    micromamba_url_osx_ARM64_hash = (
        "b22ad01c4fe0cc24c72c642068363faea0d5c868f403f6568fcf41bfe4c3052c"
    )

    # need self-hosted installation for windows due to unzip issues
    micromamba_url_windows = "https://gitlab.com/album-app/plugins/album-package/-/raw/micromamba_installer/win-64_micromamba-1.5.6-0.zip?ref_type=heads&inline=false"  # noqa: E501
    micromamba_url_windows_hash = (
        "75f4483892beca793316989422f8f4fbd528803cf603c651264f27abfcea43d3"
    )

    micromamba_base_prefix = (
        "micromamba"  # base folder prefix where micromamba is installed into
    )

    # ### Debugging Options ###
    # micromamba
    micromamba_path = os.getenv("ENVIRONMENT_DEBUGGING_MICROMAMBA_PATH")

    # mamba, feature for debugging only
    mamba_path = os.getenv("ENVIRONMENT_DEBUGGING_MAMBA_PATH")

    # conda, feature for debugging only
    conda_path = os.getenv("ENVIRONMENT_DEBUGGING_CONDA_PATH")

    # conda-lock
    conda_lock_path = os.getenv("ENVIRONMENT_CONDA_LOCK_PATH")

    # default python version
    default_solution_python_version = "3.10"
