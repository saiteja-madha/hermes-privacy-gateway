# Gmail deployment notes

This plugin is Gmail-agnostic: it intercepts Hermes model/tool boundaries rather than importing a specific Gmail SDK. That avoids guessing which Gmail connector, MCP server, or Google Workspace integration you use.

## Reading mail

Typical conceptual flow:

```text
Gmail tool returns raw message text
        |
        v
Hermes post-tool observers (raw may be visible to trusted enabled plugins)
        |
        v
privacy-gateway transform_tool_result
        |
        v
Presidio + stable aliases
        |
        v
model conversation receives aliases
```

The cloud model should receive the transformed tool result, not the plaintext, when the hook runs successfully.

## Sending/replying

The model may produce a tool call using aliases:

```text
recipient = [EMAIL_ADDRESS_...]
body = "Hi [PERSON_...] ..."
```

To let a Gmail-send/reply tool receive real values, add **that exact tool name** to `rehydrate_tool_allowlist`.

Do not guess the name from this document. Inspect your live Hermes tool registry/integration and identify the exact Gmail write tool(s) you trust.

Example shape only:

```yaml
plugins:
  entries:
    privacy-gateway:
      settings:
        rehydrate_tool_allowlist:
          - YOUR_EXACT_GMAIL_SEND_TOOL_NAME
          - YOUR_EXACT_GMAIL_REPLY_TOOL_NAME
```

Those placeholders are intentionally not real tool names.

## Read-only first rollout

Recommended rollout order:

1. Connect Gmail read-only if your integration supports a read-only scope/mode.
2. Keep `rehydrate_tool_allowlist: []`.
3. Test summaries/searches against a private mail corpus.
4. Inspect model/provider logs through the local egress proxy to confirm only aliases leave the VPS.
5. Only then enable write scopes/tools.
6. Allowlist the minimum exact Gmail write tool names.
7. Keep human approval for sends/replies until you are confident in both content and recipient reconstruction.

## Calendar/Drive/Contacts

If your Google integration exposes those tools in the same profile, their text results are also transformed because `transform_tool_result` applies to every tool result string.

That can be desirable for privacy, but it also means aliases can appear in model-generated calls to those tools. Decide individually which exact local/trusted tools need rehydration and add only those names.
