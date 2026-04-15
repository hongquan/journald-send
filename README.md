# 📜 journald-send

![made-in-vietnam](https://madewithlove.vercel.app/vn?heart=true&colorA=%23ffcd00&colorB=%23da251d)
[![journald-send](https://badge.fury.io/py/journald-send.svg)](https://pypi.org/project/journald-send/)
[![ReadTheDocs](https://readthedocs.org/projects/journald-send/badge/?version=latest)](https://journald-send.readthedocs.io?badge=latest)
[![Common Changelog](https://common-changelog.org/badge.svg)](https://common-changelog.org)

A thin Python library to write messages to [journald] (Linux system logging) using its native protocol.

## 💡 Features

- Simple functions to log messages directly to [journald] using its [native protocol].
- Best for structured logging.
- Pure-Rust (not depending on [libc], although PyO3 may include it when linking with CPython).
- Not depend on C-based `libsystemd` (as `journald-send` focuses on writing to journald, not reading nor interacting with [systemd]).

## 🤔 Motivation

Previously, I used [systemd-python], but this library was slow to release, and its support for Python 3.14, especially in free-threaded mode, was unknown.
So I developed `journald-send` to support Python 3.14 and free-threaded mode.

It is implemented using pure-Rust [rustix] and [memfd] crates, which provide an elegant, Rust-ergonomic API compared to *libc*.

## 📦 Installation

Install via pip:

```sh
pip install journald-send
```

Or using uv:

```sh
uv add journald-send
```

## 🐍 Usage

Import and use the send function:

```python
import journald_send
journald_send.send('Hello, journald!')
```

Or use the `JournalHandler` for Python logging framework integration:

```python
import logging
from journald_send.log_handler import JournalHandler

log = logging.getLogger('my-app')
log.addHandler(JournalHandler(SYSLOG_IDENTIFIER='my-app'))
log.warning('Something happened')
```

## 📁 Examples

See examples in the *examples* folder.

## 📖 Documentation

Full documentation is available at [Read the Docs](https://journald-send.readthedocs.io).

## 🤝 Contributing

Contributions welcome; open an issue or PR.

## 🔧 Development

### Prerequisites

- Python >= 3.12
- Rust toolchain
- [uv] package manager

### Setup

```sh
uv sync --all-groups
```

### Build

```sh
uv run maturin develop
```

### Run Tests

```sh
uv run pytest
```

### Build Documentation

```sh
just docs
```

## 🙏 Acknowledgement

This project learned from [tracing-journald] library for how to talk with [journald] at low level.

[journald]: https://wiki.archlinux.org/title/Systemd/Journal
[libc]: https://crates.io/crates/libc
[memfd]: https://crates.io/crates/memfd
[native protocol]: https://systemd.io/JOURNAL_NATIVE_PROTOCOL/
[rustix]: https://crates.io/crates/rustix
[systemd]: https://systemd.io/
[systemd-python]: https://pypi.org/project/systemd-python/
[tracing-journald]: https://crates.io/crates/tracing-journald
[uv]: https://pypi.org/project/uv/
