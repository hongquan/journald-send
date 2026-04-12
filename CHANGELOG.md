# Changelog

All notable changes to this project will be documented in this file.

This file follows the "common changelog" format: https://common-changelog.org/#2-format


## [0.2.0] - 2026-04-12

### Added

- Add `JournalHandler` for `logging`.


## [0.1.0] - 2026-04-12

### Added

- Initial release: Rust-based journald sender with Python bindings via PyO3.
- journald_send.send() function, Priority IntEnum, and module-level priority constants.
- Examples demonstrating Priority usage and custom fields.
- Instructions to build the native extension into the project's virtualenv via `maturin develop` and run tests with `pytest`.

[0.2.0]: https://github.com/hongquan/journald-send/releases/tag/v0.2.0
[0.1.0]: https://github.com/hongquan/journald-send/releases/tag/v0.1.0
