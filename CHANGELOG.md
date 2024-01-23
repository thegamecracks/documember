# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.5] - 2023-01-22

### Changed

- Prefix class attributes with a period like regular annotations

### Fixed

- Method descriptors not being treated as methods

## [0.1.4] - 2023-01-22

### Added

- Allow showing docstrings for module-level functions
- New help text describing the default behaviour of documember and options
  to customize it
- Support for detecting inherited docstrings

## [0.1.3] - 2023-01-22

### Changed

- Start pinning the `pip install` link to the current release
- Correct an example in the readme

## [0.1.2] - 2023-01-22

### Added

- Various examples of invoking documember in readme

### Changed

- BREAKING: Rename `--show-docstring` and `--show-full-docstring` options
  to `--show-docstrings` and `--show-full-docstrings` respectively

### Fixed

- Regression in v0.1.1 causing `--ignore-all` to not ignore `__all__`

## [0.1.1] - 2023-01-22

### Added

- Indicate which modules define an `__all__` member

## [0.1.0] - 2023-01-22

### Added

- Initial source code
- Build configuration to allow installing via `pip`

[Unreleased]: https://github.com/thegamecracks/documember/compare/v0.1.5...main
[0.1.5]: https://github.com/thegamecracks/documember/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/thegamecracks/documember/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/thegamecracks/documember/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/thegamecracks/documember/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/thegamecracks/documember/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/thegamecracks/documember/commits/v0.1.0
