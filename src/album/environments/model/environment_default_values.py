import os
from enum import Enum


class EnvironmentDefaultValues(Enum):
    # micromamba
    micromamba_url_linux_X86_64 = "https://micro.mamba.pm/api/micromamba/linux-64/2.5.0"
    micromamba_url_linux_X86_64_hash = (
        "cec496f2299f9ceb5f5e23fc2ccf081fffda0c4bc87a6fdab575bf1e04f103b6"
    )

    micromamba_url_linux_ARM64 = (
        "https://micro.mamba.pm/api/micromamba/linux-aarch64/2.5.0"
    )
    micromamba_url_linux_ARM64_hash = (
        "6ec1517c8c89c875a8fa93f9c66abd4fe3dd147341376bdc37b57c526bc13e44"
    )

    micromamba_url_linux_POWER = (
        "https://micro.mamba.pm/api/micromamba/linux-ppc64le/2.5.0"
    )
    micromamba_url_linux_POWER_hash = (
        "337d86dbaad0e3ef220a2e943106180fddf6a887bb854dc53efd640a948a92c0"
    )

    micromamba_url_osx_X86_64 = "https://micro.mamba.pm/api/micromamba/osx-64/2.5.0"
    micromamba_url_osx_X86_64_hash = (
        "2d6ab968ba08c003e43642f55afded1f0fc4247387f04e340cdc6a0129d9c550"
    )

    micromamba_url_osx_ARM64 = "https://micro.mamba.pm/api/micromamba/osx-arm64/2.5.0"
    micromamba_url_osx_ARM64_hash = (
        "74d1f250b1505cd4d78728bd8b0b7f0ffbaa660b18042f15f7b610c16102d201"
    )

    # Self-hosted zip for Windows — Python's tarfile r:bz2 may fail on minimal
    # Windows Python installations missing libbz2.  The CI also uses 7-Zip rather
    # than Python for bz2 extraction.  Keep the zip workaround until tar.bz2
    # extraction is verified across all Windows targets.
    micromamba_url_windows = "https://gitlab.com/album-app/plugins/album-package/-/raw/micromamba_installer/win-64_micromamba-2.5.0-0.zip?ref_type=heads&inline=false"  # noqa: E501
    micromamba_url_windows_hash = (
        "f63a1a0eb7ac9849eab8169301c45afc7b4b4cf394d80f07d29d01be3ec00138"
    )

    micromamba_base_prefix = (
        "micromamba"  # base folder prefix where micromamba is installed into
    )

    # Name of the environment variable that controls whether every "micromamba run" of a solution gets a private,
    # temporary process registry instead of the shared ~/.cache/mamba/proc (default: yes). Parallel runs otherwise
    # wait for each other's lock on that registry. Set the variable to 0/false/no/off for the shared registry.
    micromamba_run_private_proc_dir_env_name = (
        "ENVIRONMENT_MICROMAMBA_RUN_PRIVATE_PROC_DIR"
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
