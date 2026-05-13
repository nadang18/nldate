# nldate

A small Python package for parsing common natural-language date expressions into
`datetime.date` objects.

## Usage

```python
from datetime import date

from nldate import parse

parse("5 days before December 1st, 2025")
parse("next Tuesday", today=date(2025, 11, 5))
parse("1 year and 2 months after yesterday", today=date(2025, 11, 5))
```

## Development

This project is managed with `uv`.

```bash
uv sync
uv run pytest
uv run mypy src tests
uv run ruff check .
```
