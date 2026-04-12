# 📜 journald-send

![made-in-vietnam](https://madewithlove.vercel.app/vn?heart=true&colorA=%23ffcd00&colorB=%23da251d)
[![journald-send](https://badge.fury.io/py/journald-send.svg)](https://pypi.org/project/journald-send/)
[![ReadTheDocs](https://readthedocs.org/projects/journald-send/badge/?version=latest)](https://journald-send.readthedocs.io?badge=latest)
[![Common Changelog](https://common-changelog.org/badge.svg)](https://common-changelog.org)


A lightweight Python library to send messages to [journald] (Linux system logging) using its native protocol.

## 💡 Features

- Simple function to log messages directly to [journald] using its native protocol.
- Best for structured logging.
- Pure-Rust (not depending on [libc], although PyO3 may include it when linking with CPython).
- Not depend on C-based `libsystemd` (``journald-send`` only writes to journald, does not read or interact with [systemd]).

## 🤔 Motivation

Previously, I use [systemd-python], but this library is slow to make release, and its support of Python 3.14, especially free-threaded mode, is unknown.
So I make `journald-send` to support Python 3.14 and free-threaded mode.
It is implemented with pure-Rust [rustix] and [memfd] crates, which provides elegant, Rust ergonomic API comparing to libc.

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
journald_send.send("Hello, journald!")
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

## 🙏 Credits

This project learned from [tracing-journald] crate for how to talk with [journald] at low level.


[journald]: https://wiki.archlinux.org/title/Systemd/Journal
[systemd]: https://systemd.io/
[systemd-python]: https://pypi.org/project/systemd-python/
[uv]: https://pypi.org/project/uv/
[libc]: https://crates.io/crates/libc
[rustix]: https://crates.io/crates/rustix
[memfd]: https://crates.io/crates/memfd
[tracing-journald]: https://crates.io/crates/tracing-journald
