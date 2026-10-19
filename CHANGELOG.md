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

## [0.3.4]

### Changed

- Python 3.14 is listed among the supported Python versions; the CI tests it
- CI: the jobs create their environment with `zstandard` from conda-forge. `zstandard`, which conda-lock needs, has no
  wheels for Python 3.15 on PyPI yet, and the runners have no compiler to build it, so pip failed on 3.15.
  PyYAML, which has no 3.15 wheels either, is built without libyaml (`PYYAML_FORCE_LIBYAML=0`): on Windows its
  build failed without a compiler instead of falling back to pure Python.
- pre-commit is no longer installed with album-environments, only its developers need it: it is in the dependency
  group `dev` (`pip install --group dev`, pip >= 25.1)
- the operating system is checked the same way everywhere, with `sys.platform` (`sys.platform == "win32"` for
  Windows), instead of `platform.system()` in some places and `sys.platform` in others (album#241). Nothing changes
  for users.

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
- a progress bar of a solution, such as one of tqdm, became a log line for every update (album#217). A line the
  process redraws with a lone `\r` is now logged as a progress update: at most ten times per second (as often as
  tqdm redraws its bar), a blank one not at all, and with the attribute `album_progress` on its log record, so that
  album redraws it in place on a terminal and logs it once per 30 seconds elsewhere. If the output ends in a
  redrawn line, such as one printed with `end="\r"`, its last update is logged as a line.
- output of a process that is not valid in the file system encoding no longer stops the run with a
  `UnicodeDecodeError`: the invalid bytes are logged as `�`
- on Windows, what a solution prints reached the log only when Python's output buffer was full or the solution ended,
  e.g. every print inside a tqdm loop came after the loop (album#217). The solution's Python now runs with `-u`
  there as well, as on Linux and macOS.

## [0.3.3]

### Changed

- when no micromamba is installed, album-environments downloads micromamba 2.5.0 instead of 1.5.6
- CI: the micromamba download installs CA certificates and retries; testing against the dev version of
  album-solution-api; coverage calculation

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

[unreleased]: https://gitlab.com/album-app/album-environments/-/compare/v0.3.4...HEAD
[0.3.4]: https://gitlab.com/album-app/album-environments/-/compare/v0.3.3...v0.3.4
[0.3.3]: https://gitlab.com/album-app/album-environments/-/compare/v0.3.2...v0.3.3
[0.3.2]: https://gitlab.com/album-app/album-environments/-/compare/v0.3.1...v0.3.2
[0.3.1]: https://gitlab.com/album-app/album-environments/-/compare/v0.3.0...v0.3.1
[0.3.0]: https://gitlab.com/album-app/album-environments/-/compare/v0.2.2...v0.3.0
[0.2.2]: https://gitlab.com/album-app/album-environments/-/compare/v0.2.1...v0.2.2
[0.2.1]: https://gitlab.com/album-app/album-environments/-/compare/v0.2.0...v0.2.1
[0.2.0]: https://gitlab.com/album-app/album-environments/-/compare/v0.1.0...v0.2.0
[0.1.0]: https://gitlab.com/album-app/album-environments/-/tags/v0.1.0
