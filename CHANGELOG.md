# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

We use the following:

- `Added` for new features.
- `Changed` for changes in existing functionality.
- `Deprecated` for soon-to-be removed features.
- `Removed` for now removed features.
- `Fixed` for any bug fixes.
- `Security` in case of vulnerabilities.

## [unreleased]

### Changed

- CI: the jobs create their environment with `zstandard` from conda-forge. `zstandard`, which conda-lock needs, has no
  wheels for Python 3.15 on PyPI yet, and the runners have no compiler to build it, so pip failed on 3.15.
  PyYAML, which has no 3.15 wheels either, is built without libyaml (`PYYAML_FORCE_LIBYAML=0`): on Windows its
  build failed without a compiler instead of falling back to pure Python.
- pre-commit is no longer installed with album-environments, only its developers need it: it is in the dependency
  group `dev` (`pip install --group dev`, pip >= 25.1)

### Fixed

- the automatic micromamba download on Linux ARM64 and POWER: `uname -m` reports `aarch64` and `ppc64le` there, but
  only `arm64` and `power` were recognized, so album stopped with "There is no micromamba version for your processor
  architecture."
- parallel solution runs no longer wait for each other on micromamba's shared process registry
  `~/.cache/mamba/proc` ("Cannot lock ... Waiting for other mamba process to finish") and no longer fail
  occasionally while reading it: every `micromamba run` gets a private, temporary registry (album#227).
  Set `ENVIRONMENT_MICROMAMBA_RUN_PRIVATE_PROC_DIR=0` to use the shared registry again.
- creating an environment logs the hint how to activate it ("To activate this environment, use: micromamba
  activate ...") at DEBUG instead of INFO: album runs solutions in their environments itself, so a user who follows
  the hint does something they do not need to (album#151). All other output stays at INFO. `subcommand.run()` has
  a new keyword argument `debug_from` for this.

## [0.3.2]

### Changed

- pyproject.toml over setup.cfg

## [0.3.1]

### Fixed

- os.system.stdout undefined

## [0.2.2]

### Added

- reconstruct changelog
- changelog to the repository

[unreleased]: https://gitlab.com/album-app/album-environments/-/compare/v0.3.2...HEAD
[0.3.2]: https://gitlab.com/album-app/album-environments/-/compare/v0.3.1...v0.3.2
[0.3.1]: https://gitlab.com/album-app/album-environments/-/compare/v0.3.0...v0.3.1
[0.3.0]: https://gitlab.com/album-app/album-environments/-/compare/v0.2.2...v0.3.0
[0.2.2]: https://gitlab.com/album-app/album-environments/-/compare/v0.2.1...v0.2.2
[0.2.1]: https://gitlab.com/album-app/album-environments/-/compare/v0.2.0...v0.2.1
[0.2.0]: https://gitlab.com/album-app/album-environments/-/compare/v0.1.0...v0.2.0
[0.1.0]: https://gitlab.com/album-app/album-environments/-/tags/v0.1.0
