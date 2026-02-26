# sqlc-py

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![main](https://github.com/Flamefork/sqlc-py/actions/workflows/main.yml/badge.svg)](https://github.com/Flamefork/sqlc-py/actions/workflows/main.yml)
[![PyPI - Version](https://img.shields.io/pypi/v/sqlc)](https://pypi.org/project/sqlc/)


[sqlc](https://github.com/sqlc-dev/sqlc) binary packaged for Python. Provides the `sqlc` command-line tool as a pip-installable package, built from the official Go source using [go-to-wheel](https://github.com/nicois/go-to-wheel).

## Installation

```bash
pip install sqlc
```

## Usage

After installation, the `sqlc` command is available directly:

```bash
sqlc generate
sqlc vet
sqlc compile
```

From Python code, use `get_binary_path()` to locate the bundled binary:

```python
import subprocess
from sqlc import get_binary_path

result = subprocess.run([get_binary_path(), "generate"], check=True)
```

See the [sqlc documentation](https://docs.sqlc.dev/) for full usage details.

## How it works

`build_wheel.py` compiles the Go binary and builds platform-specific wheels, using [go-to-wheel](https://github.com/nicois/go-to-wheel) for wheel construction and platform mappings. CI builds wheels per-platform in a matrix, then publishes all wheels in a separate job.

### Why not plain go-to-wheel?

go-to-wheel cross-compiles Go binaries from a single CI host with `CGO_ENABLED=0`. This project uses per-platform matrix builds with `CGO_ENABLED=1` instead, because sqlc depends on [wasilibs/go-pgquery](https://github.com/wasilibs/go-pgquery) — a library that, without CGO, falls back to [wazero](https://github.com/aspect-build/wazero) and doesn't cache compiled WASM binaries, adding ~500ms to every `sqlc` invocation.

## Version Mapping

Package versions follow sqlc releases — e.g., package version `1.30.0` ships sqlc `v1.30.0`. Packaging-only fixes use PEP 440 post releases: `1.30.0.post1`, `1.30.0.post2`, etc.
