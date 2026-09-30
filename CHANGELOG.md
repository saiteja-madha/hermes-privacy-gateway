# Changelog

## 0.1.0 - 2026-09-30

- Initial reference implementation.
- Hermes `llm_request` text pseudonymization.
- Hermes `transform_tool_result` sanitization.
- Hermes `tool_request` exact-name allowlisted rehydration.
- Hermes `transform_llm_output` local final-response rehydration.
- Profile-scoped encrypted stable alias vault.
- Optional Presidio LangExtract/Ollama recognizer.
- Default non-text provider-content block.
- Installation, Gmail, architecture, testing, and security documentation.

# Unreleased

- Replace the incompatible Presidio Anonymizer dependency with deterministic,
  overlap-aware local span replacement compatible with Hermes's
  `cryptography==50.0.1` runtime pin.
- Remove the obsolete anonymizer dependency from installation documentation.
- Add coverage for overlapping detections and document the managed spaCy model
  installation path.
