# 📜 journald-send

A lightweight Python library to send messages to [journald] (Linux system logging) using its native protocol.

## Features

- Simple function to log messages directly to [journald] using its native protocol
- Best for structured logging
- Pure-Rust (not depending on [libc], although PyO3 may include it when linking with CPython)
- No dependencies on [systemd] or C-based `libsystemd` (only writes to journald, does not read or interact with systemd)

## Installation

Install via pip:

```
pip install journald-send
```

Or using uv:

```
uv add journald-send
```

## Usage

Import and use the send function:

```python
import journald_send
journald_send.send("Hello, journald!")
```

## Examples

See examples in the [examples folder](examples/).

## Contributing

Contributions welcome; open an issue or PR.

## Development

### Prerequisites

- Python >= 3.12
- Rust toolchain
- [uv] package manager

### Setup

```bash
uv sync --all-groups
```

### Build

```bash
uv run maturin develop
```

### Run Tests

```bash
uv run pytest
```

### Build Documentation

```bash
just docs
```

[journald]: https://www.freedesktop.org/wiki/Software/systemd/journal-files/
[systemd]: https://systemd.io/
[uv]: https://github.com/astral-sh/uv
[libc]: https://docs.rs/libc

## Credits

This project learned from and was inspired by the [tracing-journald] crate.

[tracing-journald]: https://docs.rs/tracing-journald
