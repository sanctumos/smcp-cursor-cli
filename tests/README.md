# Test suite

- **Unit** (`tests/unit/`): Plugin functions and `main()` with mocks and temp dirs. Fast.
- **Integration** (`tests/integration/`): CLI invoked as subprocess (`python -m plugins.cursor_cli`) with real session dir and fake agent script.
- **E2E** (`tests/e2e/`): Full flow: start → status (until completed) → output using a fake agent.

## Run all tests

```bash
# From repo root
pip install -r requirements-test.txt
python -m pytest tests/ -v
```

## Coverage (≥80% required)

```bash
python -m pytest tests/ --cov=plugins.cursor_cli --cov-report=term-missing --cov-fail-under=80
```

HTML report:

```bash
python -m pytest tests/ --cov=plugins.cursor_cli --cov-report=html
# open htmlcov/index.html
```

## Run by category

```bash
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/e2e/ -v
```
