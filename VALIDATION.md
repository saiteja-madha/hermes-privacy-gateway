# Validation record

Build date: 2026-09-30

Performed in the artifact build environment:

- `python -m py_compile __init__.py privacy.py vault.py scripts/*.py` — passed.
- YAML parse check for `plugin.yaml`, `nlp.yaml`, and `examples/hermes-config.yaml` — passed.
- `pytest -q` — 12 tests passed in Hermes's managed Python 3.14 environment.
- Presidio smoke test — passed with `en_core_web_lg` 3.8.0: synthetic name/email were aliased and restored.
- `hermes plugins doctor . --ci` — passed: manifest parsing, import, and registration; 2 hooks registered.
- Live Discord test — passed: synthetic PII was answered and rehydrated correctly.

Not performed in the artifact build environment:

- Live cloud-provider/Gmail end-to-end testing.
- Provider-side request capture proving the cloud provider received aliases rather than raw synthetic PII.

Run the commands in `docs/TESTING.md` inside the target Hermes installation before using this with sensitive data.
