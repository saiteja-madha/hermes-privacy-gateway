# Architecture

## Main model request

Hermes officially supports `llm_request` middleware that can replace the effective provider request before provider execution.

```text
raw local user/session state
          |
          v
Hermes builds provider request
          |
          v
privacy-gateway llm_request
          |
   Presidio + alias vault
          |
          v
sanitized provider request
          |
          v
primary model
```

The plugin sanitizes common provider text roots when present:

- `messages`
- `input`
- `instructions`
- `prompt`

Those roots contain both model-visible text and provider protocol metadata.
The traversal sanitizes known text fields (`content`, `text`, `input_text`,
`output_text`, prompts/instructions) and arbitrary strings inside tool
arguments/outputs. It preserves structural fields such as `id`, `call_id`,
`type`, `role`, `name`, and unknown scalar metadata exactly. This is required
for Responses-style APIs, whose item IDs accept only a restricted character
set and must never be replaced with bracketed PII aliases.

If a provider request exposes none of the recognized top-level roots, the
plugin replaces it with a blocked request instead of guessing which unknown
strings are content versus protocol identifiers.

If normal sanitization fails inside the callback, those roots are replaced with a block marker. This is best-effort fail-closed behavior **inside the callback only**; Hermes's middleware framework itself is documented as fail-open, so the external egress layer remains required for a hard security boundary.

## Tool results

Hermes documents this order for tools:

1. tool request middleware
2. approvals/guardrails and tool execution
3. post-tool observer hooks
4. `transform_tool_result`
5. append result into conversation context

The plugin uses `transform_tool_result` so the model receives pseudonymized tool output.

Important consequence: another trusted/untrusted plugin subscribed to earlier raw tool observers can see raw tool data before this transform. This is why the recommended sensitive profile has a minimal enabled-plugin set.

## Tool arguments

Cloud models operate on aliases. Some tools eventually need real values, for example an email-send tool needing an actual recipient.

The plugin uses Hermes `tool_request` middleware, which is documented to rewrite arguments before downstream policy/approval/execution.

Rehydration is limited to exact tool names listed in `rehydrate_tool_allowlist`.

```text
cloud model emits alias argument
            |
            v
      tool_request
            |
   tool allowlisted? ----- no ---> alias stays unresolved
            |
           yes
            |
            v
      local alias vault
            |
            v
     real argument value
            |
            v
 approvals / execution
```

Because Hermes evaluates rewritten arguments downstream, human/tool policy sees the real rehydrated value for allowlisted tools.

## Final model output

Hermes documents `transform_llm_output` as running before `post_llm_call` and final delivery. The plugin rehydrates known aliases there so the user sees natural text.

```text
cloud response with aliases
           |
           v
 transform_llm_output
           |
           v
 local rehydration
           |
           v
 Telegram / CLI / other surface
```

If rehydration fails, the plugin leaves aliases in place rather than guessing.

## Alias vault

Hermes documents `plugins.plugin_storage.plugin_db()` as the sanctioned profile-scoped persistent SQLite storage for native plugins.

The vault stores:

```text
alias
entity kind
keyed lookup digest
encrypted plaintext
```

It does not store plaintext entity values directly in the table.

Two independent subkeys are derived from the 32-byte master key using HKDF-SHA256:

- HMAC lookup/alias key
- Fernet encryption key

The alias uses the first 128 bits of an HMAC-SHA256 digest, rendered as typed uppercase hex:

```text
[PERSON_A59B4E9F19D7C7FC552326D2F026BD14]
```

This is designed for stable pseudonymization, not anonymity against a party that also obtains the local key/vault.

## Local LangExtract path

Optional:

```text
text
 |
 +--> standard Presidio recognizers / spaCy
 |
 +--> BasicLangExtractRecognizer --> local Ollama model
 |
 v
merged Presidio detections
```

Presidio currently marks LangExtract PII detection experimental. Treat it as an additional detector, not as the only control.

## Hard egress boundary

Recommended:

```text
Hermes process/container
       |
       | only allowed model egress
       v
localhost privacy proxy
       |
       | second PII masking layer
       v
cloud provider
```

The Hermes process/container should not have an alternate route to the cloud model API. The exact firewall/container rules depend on your deployment and are intentionally not invented in this repository.
