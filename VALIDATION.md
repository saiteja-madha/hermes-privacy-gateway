# Validation record

Build date: 2026-09-30

Performed in the artifact build environment:

- `python -m py_compile __init__.py privacy.py vault.py scripts/*.py` — passed.
- YAML parse check for `plugin.yaml`, `nlp.yaml`, and `examples/hermes-config.yaml` — passed.
- `pytest -q -rs` — 6 alias-vault tests passed; the Presidio-dependent helper test module was skipped because `presidio_analyzer` was not installed in the build environment.

Not performed in the artifact build environment:

- Full Presidio runtime smoke test (requires Presidio dependencies and `en_core_web_lg`).
- `hermes plugins doctor . --ci` (Hermes CLI was not installed in the build environment).
- Live cloud-provider/Gmail end-to-end testing.

Run the commands in `docs/TESTING.md` inside the target Hermes installation before using this with sensitive data.
