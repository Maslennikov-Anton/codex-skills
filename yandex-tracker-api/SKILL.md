---
name: yandex-tracker-api
description: >
  Work with the Yandex Tracker API end to end: validate access, choose the
  correct auth headers, inspect queues and fields, read and update issues,
  search issues, add comments, upload attachments, execute transitions, and
  troubleshoot common API errors. Use when a user needs help integrating with,
  debugging, or operating Yandex Tracker via HTTP requests, curl, or scripts.
---

# Yandex Tracker API

Use this skill when the task involves the HTTP API of Yandex Tracker.

## What this skill covers

- Access setup and auth verification.
- Correct request shape for Yandex 360 and Yandex Cloud organizations.
- Common issue workflows: get, search, create, update, comment, attach files, transition status.
- Queue and field discovery before writes.
- Error handling for `401`, `403`, `404`, `409`, `412`, `422`, `423`, `428`, `429`.
- Reusable local helper script for authenticated `curl` requests.

## Workflow

1. Read the user's goal and identify the exact operation and target object.
2. If credentials or org identifiers are missing, ask only for what is required:
   - auth type: OAuth or IAM;
   - org header: `X-Org-ID` or `X-Cloud-Org-ID`;
   - org id;
   - token source or env var names.
3. Verify access first with `GET /v3/myself`.
4. Before creating or updating issues, inspect queue requirements:
   - read [references/common-operations.md](references/common-operations.md) for the relevant endpoints;
   - if queue-specific fields matter, read [references/discovery-and-troubleshooting.md](references/discovery-and-troubleshooting.md) and check queue fields.
5. Prefer the local helper `scripts/tracker_api.sh` for repeatable calls.
6. When editing issues, change only the fields requested by the user.
7. For large searches, use the search modes documented in [references/common-operations.md](references/common-operations.md).
8. If the API returns an error, map it through [references/discovery-and-troubleshooting.md](references/discovery-and-troubleshooting.md) and state the likely root cause concretely.

## Minimal request contract

- Base URL: `https://api.tracker.yandex.net/v3`
- Auth header:
  - `Authorization: OAuth <token>` for OAuth 2.0
  - `Authorization: Bearer <token>` for IAM tokens
- Organization header:
  - `X-Org-ID: <id>` for Yandex 360
  - `X-Cloud-Org-ID: <id>` for Yandex Cloud Organization

Read [references/auth-and-request-format.md](references/auth-and-request-format.md) when you need auth, headers, pagination, or PATCH semantics.

## Helper script

Use `scripts/tracker_api.sh` when you need to run authenticated requests from the terminal.

Required env vars:

- `TRACKER_TOKEN`
- `TRACKER_ORG_ID`

Optional env vars:

- `TRACKER_BASE_URL` default: `https://api.tracker.yandex.net/v3`
- `TRACKER_AUTH_SCHEME` default: `OAuth`
- `TRACKER_ORG_HEADER` default: `X-Org-ID`
- `TRACKER_ACCEPT_LANGUAGE` optional, for example `en`

Examples:

```bash
scripts/tracker_api.sh GET /myself
scripts/tracker_api.sh GET /issues/TEST-1 '?expand=attachments'
scripts/tracker_api.sh POST /issues/_search '' '{"filter":{"queue":"TEST","assignee":"me"}}'
scripts/tracker_api.sh PATCH /issues/TEST-1 '' '{"summary":"New title"}'
scripts/tracker_api.sh POST /issues/TEST-1/comments '' '{"text":"Done","markupType":"md"}'
scripts/tracker_api.sh FILE /issues/TEST-1/attachments/ /tmp/image.png
```

## Which reference to open

- Broad coverage map by API area:
  [references/api-coverage-map.md](references/api-coverage-map.md)
- Endpoint matrix with methods, paths, and quick examples:
  [references/endpoint-matrix.md](references/endpoint-matrix.md)
- Auth, headers, pagination, request body rules:
  [references/auth-and-request-format.md](references/auth-and-request-format.md)
- Common endpoints and ready-to-adapt examples:
  [references/common-operations.md](references/common-operations.md)
- Queue discovery, custom fields, troubleshooting:
  [references/discovery-and-troubleshooting.md](references/discovery-and-troubleshooting.md)

## Operating rules

- Validate access before deeper debugging.
- Do not expose tokens in responses.
- Prefer queue keys and issue keys when they are stable and human-readable.
- For transitions, fetch available transitions first, then execute one by id.
- For file upload, use multipart form data, not JSON.
- Mention when an inference is based on docs rather than on a live API response.
