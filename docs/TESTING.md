# Testing

## 1. Static syntax check

```bash
python -m py_compile __init__.py privacy.py vault.py scripts/*.py
```

## 2. Unit tests

Install the repository's development dependency and run:

```bash
pytest
```

The tests cover:

- stable aliases for normalized values
- entity-type separation
- encrypted-at-rest vault records
- wrong-key refusal
- alias rehydration
- recursive string transformation helpers
- common non-text payload detection
- narrow structured-secret removal

## 3. Presidio smoke test

Requires the plugin dependencies plus `en_core_web_lg`:

```bash
export HERMES_PRIVACY_GATEWAY_KEY="$(python scripts/generate_key.py)"
python scripts/smoke_test.py
```

Check that raw name/email disappear from the sanitized line and are restored locally on the final line.

## 4. Hermes Plugin Doctor

From the plugin root:

```bash
hermes plugins doctor . --ci
```

Hermes documents this as the authoritative development validation path for native plugin discovery/manifest/import/registration.

## 5. End-to-end model test

Before Gmail, use synthetic PII:

```text
My name is Jane Example. Email me at jane.example@example.com.
```

Capture the request at the **local proxy**, not at the cloud provider, and verify that the outbound model request contains aliases rather than the original values.

Then ask the model to repeat the values. Confirm the user-facing response is locally rehydrated.

## 6. Tool-result test

Use a trusted local tool that returns synthetic PII. Confirm:

1. The raw tool works locally.
2. `transform_tool_result` produces aliases for model context.
3. A non-allowlisted tool receives aliases, not plaintext.
4. An explicitly allowlisted test tool receives rehydrated plaintext.

## 7. Failure tests

Test intentionally broken configurations:

- unset vault key
- wrong vault key after aliases exist
- missing spaCy model
- stopped Ollama while LangExtract is enabled
- invalid LangExtract config
- proxy down

Required desired result for cloud egress: **no raw fallback path**. The external network/proxy layer should make a failed privacy path become a failed request.

## Package-build validation note

The ZIP was assembled in an environment without direct package-index network resolution, so Presidio could not be installed into that build environment for runtime integration execution. Python source compilation succeeded, and the repo includes the tests/doctor/smoke commands to run in the target Hermes installation.
