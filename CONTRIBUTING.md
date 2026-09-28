# Contributing to SekiBanki

Thanks for helping make agent runs easier to understand.

## Before opening a pull request

1. Keep the public API small and framework-agnostic.
2. Add a focused test for every behavior change.
3. Run `python -m unittest discover -s tests -v`.
4. Keep trace JSON portable and backwards-readable when possible.

## Development setup

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

Please include a short explanation of the user problem your change solves and a small usage example when adding a public API.
