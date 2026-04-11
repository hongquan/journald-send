# journald-send

A lightweight Python library to send messages to [journald] using its native protocol.

## Features

- No dependencies on [systemd] or libsystemd.
- Simple function to log messages directly to [journald].

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

See more in the documentation.

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
