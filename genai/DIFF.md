---
lab3_genai_diff:
  instrumentation: "opentelemetry-instrumentation-genai-openai 1.2b0 (with opentelemetry-util-genai 1.2b0), on opentelemetry-sdk 1.45.0 and openai 3.19.2"
  spec_ref: "semantic-conventions@v1.41.1"
  attributes:
    - {name: gen_ai.operation.name, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.provider.name, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.request.model, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.request.temperature, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.request.max_tokens, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.id, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.model, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.finish_reasons, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.usage.input_tokens, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.usage.output_tokens, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.system, emitted: false, in_spec: true, stability: deprecated}
    - {name: gen_ai.openai.response.system_fingerprint, emitted: false, in_spec: true, stability: deprecated}
    - {name: gen_ai.request.top_p, emitted: false, in_spec: true, stability: development}
    - {name: gen_ai.conversation.id, emitted: false, in_spec: true, stability: development}
---
<!-- ai-generated: 85% - Claude Code ran the call in containers, looked the attributes up in the spec and drafted the prose, reviewed by me -->

# What the library emits, against the spec

## The call

One chat completion through the `openai` Python client, instrumented with `OpenAIInstrumentor` from
`opentelemetry.instrumentation.genai.openai`, against a local model: Ollama (`ollama/ollama:0.12.3`) serving
`qwen3:1.7b` through its OpenAI-compatible endpoint, both in Docker containers, on 10 October 2026. The spans were
written by `FileSpanExporter` of `opentelemetry-exporter-otlp-json-file` 0.66b0 to `genai/spans.json`: one span,
`chat qwen3:1.7b`, kind CLIENT, scope `opentelemetry.instrumentation.genai.openai` 1.2b0. Message content was not
captured (the library's default), so no prompt or answer text is in the file.

The comparison is against the attribute registry of `semantic-conventions` v1.41.1 (`model/gen-ai/registry.yaml`
and `model/gen-ai/deprecated/registry-deprecated.yaml`), which defines 60 `gen_ai.*` attributes.

## What agrees

All ten `gen_ai.*` keys the library emitted are defined in the ref, under the same names and with the types the
registry gives them: the operation (`chat`), the provider, the requested model and the two sampling parameters
that were sent (`temperature`, `max_tokens`), the response's id, model and finish reasons (an array, as the spec
says), and the input and output token counts. The span's name follows the spec's `{gen_ai.operation.name}
{gen_ai.request.model}` pattern, its kind is CLIENT, and `server.address` and `server.port` are set as the spec
recommends. Every required and conditionally required attribute that applies to a plain chat call is present.

The library also follows the renames the ref records: it emits `gen_ai.provider.name`, not the deprecated
`gen_ai.system` it replaced, and the system fingerprint as `openai.response.system_fingerprint`, not the deprecated
`gen_ai.openai.response.system_fingerprint`. Attributes the request did not carry (`gen_ai.request.top_p`) are
left out rather than filled with defaults, and `gen_ai.conversation.id`, which the client cannot know, is absent.

## What does not, or not quite

- `gen_ai.provider.name` is `openai`, but the model was served by Ollama. The spec allows this - the provider is
  named after the API the client speaks, as the instrumentation best knows it - but it is not who answered. Only
  `server.address` (`ollama`) and the model name tell the calls apart.
- Every one of these attributes is at stability `development`. Nothing in the GenAI conventions is stable yet, and
  two names the library would have emitted a few releases ago are already deprecated renames.

## What it means for a dashboard

A dashboard built on these spans can count calls, tokens and finish reasons per requested model today, and
`gen_ai.usage.*` is enough for a token-cost panel. But it should not group by `gen_ai.provider.name` to tell
OpenAI from a self-hosted model, because every OpenAI-compatible endpoint reports `openai`; group by
`server.address` instead. And because the whole namespace is `development`, a panel's queries are tied to the
instrumentation's version: an upgrade can rename an attribute, as `gen_ai.system` was renamed, and silently turn a
panel into "No data". Pin the instrumentation version and re-check the panels when it changes.
