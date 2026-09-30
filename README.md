# Hermes Privacy Gateway

A Hermes Agent plugin that pseudonymizes detected text PII locally before the primary model provider sees it, keeps stable reversible aliases in a profile-scoped encrypted vault, sanitizes tool results before they are appended to the model conversation, and rehydrates aliases locally for final user-facing text and explicitly allowlisted tools.

> **Security status:** reference implementation, not an audited DLP product. Do not treat the plugin alone as a hard confidentiality boundary. See [docs/SECURITY.md](docs/SECURITY.md).

## What it is for

Example input stored/received locally:

```text
From: john.smith@example.com
John Smith asked Susan Lee at Contoso to review account 384983.
```

Example model-facing representation:

```text
From: [EMAIL_ADDRESS_...]
[PERSON_...] asked [PERSON_...] at [ORGANIZATION_...] to review [US_BANK_NUMBER_...].
```

The alias vault retains the local mapping, so a final model answer such as:

```text
Tell [PERSON_...] that the review is complete.
```

can be rehydrated locally before delivery to the user.

## Design goals

- Keep raw text PII out of the **main cloud model request** when Presidio detects it.
- Preserve entity relationships using stable aliases instead of replacing everything with `[REDACTED]`.
- Encrypt alias-to-plaintext values in Hermes profile-scoped plugin storage.
- Strip a small set of high-confidence secrets rather than creating reversible aliases for them.
- Sanitize every string tool result before Hermes appends it back into the model conversation.
- Rehydrate tool arguments only for an explicit exact-name allowlist.
- Block common non-text model inputs by default, because this plugin only redacts text.
- Support Presidio's optional local LangExtract/Ollama recognizer.

## Non-goals / important limitations

- **No PII detector guarantees zero misses.** Presidio's own documentation says automated detection cannot guarantee all sensitive information will be found.
- Hermes middleware is documented as **fail-open** if middleware itself fails. This plugin catches its own normal errors and substitutes block markers, but a hard boundary requires a separate egress proxy/network rule.
- Other enabled Hermes plugins/hooks can receive raw local data through documented observer hooks. Use a dedicated/trusted profile for sensitive mail.
- Hermes auxiliary LLM calls are separate from the primary tool loop. Route all sensitive-profile auxiliary model slots to local inference.
- This version pseudonymizes text. It does not redact pixels, audio, arbitrary binary attachments, or OCR image content. Non-text model payloads are blocked by default.
- Stable aliases reveal equality/correlation: the cloud can tell that the same alias appeared again even though it does not know the plaintext.
- `John Smith` and `John` are not automatically entity-resolved into one person. The vault is stable for exact normalized values, not semantic identity resolution.

## Repository layout

```text
privacy-gateway/
├── __init__.py               # Hermes middleware/hook registration
├── plugin.yaml               # Hermes plugin manifest
├── pyproject.toml            # Python dependency declaration
├── privacy.py                # Presidio detection/pseudonymization
├── vault.py                  # encrypted alias vault
├── nlp.yaml                  # local spaCy NLP configuration
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CONFIGURATION.md
│   ├── GMAIL.md
│   ├── INSTALL.md
│   ├── SECURITY.md
│   ├── TESTING.md
│   └── SOURCES.md
├── examples/
│   ├── hermes-config.yaml
│   └── profile-env.example
├── scripts/
│   ├── generate_key.py
│   └── smoke_test.py
└── tests/
```

## Quick start

Read [docs/INSTALL.md](docs/INSTALL.md) before enabling it. The minimal sequence is:

```bash
mkdir -p ~/.hermes/plugins/privacy-gateway
cp -R /path/to/hermes-privacy-gateway/. ~/.hermes/plugins/privacy-gateway/

cd ~/.hermes/plugins/privacy-gateway
hermes plugins doctor . --ci
hermes plugins enable privacy-gateway
```

Generate the vault key locally:

```bash
python scripts/generate_key.py
```

Store the generated value as `HERMES_PRIVACY_GATEWAY_KEY` in the active Hermes profile's secret environment.

Presidio's spaCy-backed NLP engine requires its configured model to be installed. This repo uses `en_core_web_lg`; see [docs/INSTALL.md](docs/INSTALL.md).

## Recommended privacy deployment

```text
Telegram / Gmail / local files
            |
            v
          Hermes
            |
     privacy-gateway
            |
        aliases only
            |
            v
  local fail-closed LLM proxy
            |
            v
       cloud model
```

The proxy is not bundled here. Presidio publishes an official LiteLLM + Presidio masking integration, linked in [docs/SECURITY.md](docs/SECURITY.md). The strongest setup also prevents the Hermes process/container from connecting directly to the cloud provider, so the only allowed egress path is through the local privacy proxy.

## Local LLM-assisted detection

Presidio 2.2.364 includes the experimental `BasicLangExtractRecognizer` and documents local Ollama support. Enable it with:

```yaml
plugins:
  entries:
    privacy-gateway:
      settings:
        enable_langextract: true
```

With an empty `langextract_config_path`, Presidio uses its own documented defaults. To choose another Ollama model or endpoint, create a Presidio LangExtract config and set its path. See [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## Validation performed for this package

- Python source syntax compilation.
- Unit tests for the encrypted alias vault and helper functions are included.
- The full Presidio runtime smoke test and `hermes plugins doctor` should be run in the target Hermes installation after dependencies are admitted.
- The implementation and docs were checked against official Hermes Agent and Data Privacy Stack Presidio documentation on **2026-09-30**. See [docs/SOURCES.md](docs/SOURCES.md).
- The plugin uses Presidio Analyzer for detection and a small local span-replacement routine for aliases. Presidio Anonymizer is intentionally not a dependency because its current release requires `cryptography<49`, while Hermes's managed runtime pins `cryptography==50.0.1`.
