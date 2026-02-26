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

## Version Mapping

Package versions follow sqlc releases — e.g., package version `1.30.0` ships sqlc `v1.30.0`. Packaging-only fixes use PEP 440 post releases: `1.30.0.post1`, `1.30.0.post2`, etc.
