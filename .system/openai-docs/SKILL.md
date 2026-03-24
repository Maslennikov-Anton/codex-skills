---
name: "openai-docs"
description: "Use when the user asks how to build with OpenAI products or APIs and needs up-to-date official documentation with citations, help choosing the latest model for a use case, or explicit GPT-5.4 upgrade and prompt-upgrade guidance; prioritize OpenAI docs MCP tools, use bundled references only as helper context, and restrict any fallback browsing to official OpenAI domains."
---


# OpenAI Docs

Provide authoritative, current guidance from official OpenAI documentation. If OpenAI docs MCP tools are available in the environment, use them first. If they are not available, or they return no meaningful results, use targeted web search restricted to official OpenAI domains. This skill may also load targeted files from `references/` for model-selection and GPT-5.4-specific requests, but current OpenAI docs remain authoritative.

## Quick start

- If OpenAI docs MCP tools are available, use `mcp__openaiDeveloperDocs__search_openai_docs` to find the most relevant doc pages.
- If OpenAI docs MCP tools are available, use `mcp__openaiDeveloperDocs__fetch_openai_doc` to pull exact sections and quote/paraphrase accurately.
- Use `mcp__openaiDeveloperDocs__list_openai_docs` only when you need to browse or discover pages without a clear query.
- If MCP tools are unavailable, use targeted web search restricted to `developers.openai.com` and `platform.openai.com`.
- Load only the relevant file from `references/` when the question is about model selection or a GPT-5.4 upgrade.

## OpenAI product snapshots

1. Apps SDK: Build ChatGPT apps by providing a web component UI and an MCP server that exposes your app's tools to ChatGPT.
2. Responses API: A unified endpoint designed for stateful, multimodal, tool-using interactions in agentic workflows.
3. Chat Completions API: Generate a model response from a list of messages comprising a conversation.
4. Codex: OpenAI's coding agent for software development that can write, understand, review, and debug code.
5. gpt-oss: Open-weight OpenAI reasoning models (gpt-oss-120b and gpt-oss-20b) released under the Apache 2.0 license.
6. Realtime API: Build low-latency, multimodal experiences including natural speech-to-speech conversations.
7. Agents SDK: A toolkit for building agentic apps where a model can use tools and context, hand off to other agents, stream partial results, and keep a full trace.

## Tool availability

Choose the first branch that applies:

1. If OpenAI docs MCP tools are available, use them first.
2. If MCP tools are unavailable in the current environment, go straight to restricted web search on official OpenAI domains.
3. If MCP tools should exist but appear broken, use restricted web search for the current answer and only then consider repairing the MCP setup.

If the explicit task is to install or repair the MCP server itself:

1. Run `codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp`.
2. If it fails due to permissions or sandboxing, retry with escalated permissions and a short justification.
3. Only if that still fails, ask the user to run the install command.
4. Ask the user to restart Codex.

## Workflow

1. Clarify the product scope and whether the request is general docs lookup, model selection, a GPT-5.4 upgrade, or a GPT-5.4 prompt upgrade.
2. If it is a model-selection request, load `references/latest-model.md`.
3. If it is an explicit GPT-5.4 upgrade request, load `references/upgrading-to-gpt-5p4.md`.
4. If the upgrade may require prompt changes, or the workflow is research-heavy, tool-heavy, coding-oriented, multi-agent, or long-running, also load `references/gpt-5p4-prompting-guide.md`.
5. Retrieve current docs from the best available source:
   - MCP fetch when MCP tools are available;
   - otherwise restricted web search and direct page fetch on official OpenAI domains.
6. Read only the exact section needed.
7. For GPT-5.4 upgrade reviews, always make the per-usage-site output explicit: target model, starting reasoning recommendation, `phase` assessment when relevant, prompt blocks, and compatibility status.
8. Answer with concise guidance and cite the doc source, using the reference files only as helper context.

## Reference map

Read only what you need:

- `references/latest-model.md` -> model-selection and "best/latest/current model" questions; verify every recommendation against current OpenAI docs before answering.
- `references/upgrading-to-gpt-5p4.md` -> only for explicit GPT-5.4 upgrade and upgrade-planning requests; verify the checklist and compatibility guidance against current OpenAI docs before answering.
- `references/gpt-5p4-prompting-guide.md` -> prompt rewrites and prompt-behavior upgrades for GPT-5.4; verify prompting guidance against current OpenAI docs before answering.

## Quality rules

- Treat OpenAI docs as the source of truth; avoid speculation.
- Keep quotes short and within policy limits; prefer paraphrase with citations.
- If multiple pages differ, call out the difference and cite both.
- Reference files are convenience guides only; for volatile guidance such as recommended models, upgrade instructions, or prompting advice, current OpenAI docs always win.
- If docs do not cover the user’s need, say so and offer next steps.

## Tooling notes

- Prefer MCP doc tools when they are actually available in the environment.
- Do not block on MCP setup for an ordinary docs question if official web sources are available.
- When using web search, restrict to official OpenAI domains (`developers.openai.com`, `platform.openai.com`) and cite sources.
- Treat bundled `references/` files as convenience context only; re-verify volatile guidance against live official docs before answering.
