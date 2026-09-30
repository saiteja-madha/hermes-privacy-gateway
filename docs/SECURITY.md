# Security model

## Read this before using the plugin with private mail

This plugin reduces exposure; it does not prove that PII can never leave the machine.

Two upstream facts drive the security design:

1. **Hermes middleware failures are fail-open.** Hermes logs a middleware failure and continues the underlying operation.
2. **Presidio does not guarantee complete sensitive-data detection.** Its FAQ explicitly cautions that automated PII detection cannot guarantee all sensitive information will be found.

Therefore the plugin is one layer in a defense-in-depth design, not the sole enforcement boundary.

## Recommended controls

### 1. Use a dedicated privacy-sensitive Hermes profile

Keep the enabled plugin set minimal and reviewed. Hermes observer hooks can intentionally receive raw user messages, raw conversation history, raw request-message fields, and raw tool data on some hook surfaces.

A redaction plugin cannot prevent another in-process plugin from reading data that Hermes intentionally supplies to that plugin.

### 2. Keep auxiliary model traffic local

Hermes documents auxiliary LLM calls as separate from the primary tool-calling loop. Compression can see the full transcript; other auxiliary tasks can see sensitive content too.

Configure all applicable auxiliary slots in the sensitive profile to use local inference.

### 3. Put a fail-closed privacy proxy between Hermes and cloud models

Presidio publishes an official sample integrating Presidio masking with LiteLLM Proxy. Use a local proxy as a second detector/masker.

Desired property:

```text
Hermes -> privacy proxy -> cloud
```

Undesired property:

```text
Hermes -----------------> cloud
```

Use network/container policy so the direct path does not exist. If the proxy fails, the provider request should fail instead of falling back to direct provider access.

This repository does not provide firewall rules because they depend on Docker/Podman/systemd/firewall/VPS topology.

### 4. Keep provider credentials out of Hermes when possible

For the strongest topology, store the real cloud-provider credential only in the local proxy. Hermes receives only a local proxy credential/address.

### 5. Treat the alias vault as sensitive

The database values are encrypted, but the master key can decrypt them. Protect:

- the active Hermes profile directory
- `HERMES_PRIVACY_GATEWAY_KEY`
- backups
- process environment access

If both encrypted database and key are stolen, aliases are reversible.

### 6. Do not alias authentication secrets

This plugin removes narrow high-confidence examples such as PEM private keys and `Authorization: Bearer/Basic ...` headers instead of storing them as reversible aliases.

That list is not exhaustive. Add local deterministic rules/Presidio recognizers for your own credential formats.

### 7. Keep tool rehydration narrow

`rehydrate_tool_allowlist` is empty by default. Add only exact trusted tool names.

Do not casually allowlist:

- web search
- arbitrary browser navigation
- generic HTTP clients
- webhook tools
- shell commands that upload data
- unreviewed MCP tools

unless sending real plaintext to that destination is explicitly intended.

### 8. Non-text data is blocked by default

PII can exist in screenshots, PDFs, images, audio, and attachments. Text Presidio analysis does not sanitize those bytes.

The plugin defaults `block_non_text_content: true`. If you disable it, build a separate local media/OCR redaction pipeline first.

## Data that remains local but may be plaintext

This plugin modifies provider/tool boundaries; it does not rewrite Hermes's local storage model.

Depending on your Hermes configuration, local state can include:

- original user messages
- raw tool inputs/results before transformation
- rehydrated final assistant responses
- local session/history data
- encrypted alias-vault records

Secure the VPS/profile accordingly.

## Stable-alias privacy tradeoff

Stable aliases deliberately leak equality:

```text
[PERSON_X] appears today
[PERSON_X] appears tomorrow
```

The model can infer it is the same pseudonymous entity. That improves reasoning and continuity but is weaker than one-time random redaction.

## Threats not solved here

- A compromised/root VPS.
- Malicious code in another in-process Hermes plugin.
- PII that Presidio/local recognizers fail to detect.
- Sensitive facts that are identifying without matching a configured PII entity.
- Side channels such as timing/token lengths.
- PII in unprocessed binary/media content.
- Provider-side information you intentionally choose not to redact.

## Recommended acceptance test before Gmail

Build a private test corpus covering your actual mail patterns:

- names and nicknames
- email addresses
- phone numbers
- mailing addresses
- customer/vendor/company names
- bank/account identifiers
- invoice/order identifiers
- signatures
- quoted mail threads
- URLs with identifying query parameters
- internal project names
- credentials/tokens that must be removed rather than aliased

Measure **false negatives first**. A privacy gateway should be tuned to minimize misses even if that causes some inconvenience from false positives.
