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

- pre-commit is no longer installed with album-environments, only its developers need it: it is in the dependency
  group `dev` (`pip install --group dev`, pip >= 25.1)

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
