# Official sources used

Verified 2026-09-30.

## Hermes Agent

- Plugin development: https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
- Middleware: https://hermes-agent.nousresearch.com/docs/developer-guide/middleware
- Event hooks: https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks
- Plugin user guide: https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins
- Model/configuration and auxiliary tasks: https://hermes-agent.nousresearch.com/docs/user-guide/configuration
- Model providers/custom endpoints: https://hermes-agent.nousresearch.com/docs/integrations/providers
- Installation/runtime: https://hermes-agent.nousresearch.com/docs/getting-started/installation
- Updating/current runtime notes: https://hermes-agent.nousresearch.com/docs/getting-started/updating

## Data Privacy Stack Presidio

- Analyzer: https://presidio.dataprivacystack.org/analyzer/
- Analyzer configuration: https://presidio.dataprivacystack.org/analyzer/analyzer_engine_provider/
- NLP model customization: https://presidio.dataprivacystack.org/analyzer/customizing_nlp_models/
- Anonymizer: https://presidio.dataprivacystack.org/anonymizer/
- Custom anonymization: https://presidio.dataprivacystack.org/tutorial/11_custom_anonymization/
- LangExtract / local Ollama PII detection: https://presidio.dataprivacystack.org/samples/python/langextract/
- LiteLLM + Presidio masking: https://presidio.dataprivacystack.org/samples/docker/litellm/
- Samples: https://presidio.dataprivacystack.org/samples/
- Presidio Analyzer PyPI metadata (2.2.364): https://pypi.org/project/presidio-analyzer/
- Presidio Anonymizer PyPI metadata (2.2.364): https://pypi.org/project/presidio-anonymizer/

## Design choices that are ours, not upstream guarantees

The following are implementation decisions in this repository, not claims that Hermes or Presidio natively provide them:

- HMAC-derived stable typed aliases.
- Fernet-encrypted alias values.
- Exact-name tool rehydration allowlist.
- Blocking common non-text provider payloads.
- Removing a narrow set of high-confidence secrets before aliasing.
- Enabling `ORGANIZATION` in the included NLP configuration.
- Recommending a dedicated sensitive profile and an external fail-closed egress boundary.
