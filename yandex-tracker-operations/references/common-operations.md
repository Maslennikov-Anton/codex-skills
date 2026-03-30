# Common Operations

Primary source pages:

- https://yandex.ru/support/tracker/ru/get-user-info
- https://yandex.ru/support/tracker/ru/get-user
- https://yandex.ru/support/tracker/ru/get-users
- https://yandex.ru/support/tracker/ru/concepts/issues/get-issue
- https://yandex.ru/support/tracker/ru/concepts/issues/create-issue
- https://yandex.ru/support/tracker/ru/concepts/issues/search-issues
- https://yandex.ru/support/tracker/ru/concepts/issues/add-comment
- https://yandex.ru/support/tracker/ru/concepts/issues/post-attachment
- https://yandex.ru/support/tracker/ru/concepts/issues/get-transitions
- https://yandex.ru/support/tracker/ru/concepts/issues/new-transition
- https://yandex.ru/support/tracker/ru/concepts/issues/get-links
- https://yandex.ru/support/tracker/ru/concepts/queues/get-queue
- https://yandex.ru/support/tracker/ru/concepts/queues/get-fields
- https://yandex.ru/support/tracker/ru/concepts/queues/get-local-fields

## Access smoke test

```bash
scripts/tracker_api.sh GET /myself
```

## User operations

Get current user:

```bash
scripts/tracker_api.sh GET /myself
```

Get one user:

```bash
scripts/tracker_api.sh GET /users/username '?expand=groups'
```

If a login contains only digits, use `login:<value>` in the path:

```bash
scripts/tracker_api.sh GET /users/login:12345
```

List users in the org:

```bash
scripts/tracker_api.sh GET /users '?expand=groups&perPage=100&page=1'
```

## Queue discovery

Get queue details with all expansions:

```bash
scripts/tracker_api.sh GET /queues/TEST '?expand=all'
```

Get required queue fields:

```bash
scripts/tracker_api.sh GET /queues/TEST/fields
```

Get local queue fields:

```bash
scripts/tracker_api.sh GET /queues/TEST/localFields
```

Use queue discovery before creating issues if field requirements are unclear.

## Read an issue

```bash
scripts/tracker_api.sh GET /issues/TEST-1
scripts/tracker_api.sh GET /issues/TEST-1 '?expand=attachments,comments,links'
```

## Search issues

Search by structured filter:

```bash
scripts/tracker_api.sh POST /issues/_search '' '{
  "filter": {
    "queue": "TEST",
    "assignee": "me"
  }
}'
```

Search with pagination:

```bash
scripts/tracker_api.sh POST /issues/_search '?perPage=100&page=1' '{
  "filter": {
    "queue": "TEST"
  }
}'
```

Search with free-form query:

```bash
scripts/tracker_api.sh POST /issues/_search '' '{
  "query": "Queue: TEST Status: Open Assignee: me"
}'
```

If results can exceed 10,000, use the scroll mode from the search docs rather than plain page numbers.

## Create an issue

Minimal example:

```bash
scripts/tracker_api.sh POST /issues/ '' '{
  "queue": "TEST",
  "summary": "API-created issue",
  "type": "task"
}'
```

Expanded example:

```bash
scripts/tracker_api.sh POST /issues/ '' '{
  "queue": "TEST",
  "summary": "Bug from API",
  "description": "Steps to reproduce:\\n1. Open page\\n2. Observe error",
  "type": "bug",
  "assignee": "userlogin",
  "tags": ["api", "incident"]
}'
```

## Update an issue

Simple partial update:

```bash
scripts/tracker_api.sh PATCH /issues/TEST-1 '' '{
  "summary": "Updated summary",
  "description": "Updated description"
}'
```

Array updates:

```bash
scripts/tracker_api.sh PATCH /issues/TEST-1 '' '{
  "followers": {
    "add": ["user1"],
    "remove": ["user2"]
  }
}'
```

Clear a field:

```bash
scripts/tracker_api.sh PATCH /issues/TEST-1 '' '{
  "deadline": null
}'
```

## Add a comment

Plain text or YFM:

```bash
scripts/tracker_api.sh POST /issues/TEST-1/comments '' '{
  "text": "Done. See verification steps below.",
  "markupType": "md"
}'
```

Comment with summons:

```bash
scripts/tracker_api.sh POST /issues/TEST-1/comments '' '{
  "text": "Please review",
  "summonees": ["userlogin"],
  "markupType": "md"
}'
```

## Attach a file

```bash
scripts/tracker_api.sh FILE /issues/TEST-1/attachments/ /tmp/image.png
```

For attachments, the API expects multipart form data and the docs state a limit of 1024 MB per file.

## Links

Read issue links:

```bash
scripts/tracker_api.sh GET /issues/TEST-1/links
```

Create a link:

```bash
scripts/tracker_api.sh POST /issues/TEST-1/links '' '{
  "relationship": "is dependent by",
  "issue": "TEST-2"
}'
```

Adjust relationship values to those supported by the target Tracker setup.

## Transitions

Fetch allowed transitions first:

```bash
scripts/tracker_api.sh GET /issues/TEST-1/transitions
```

Execute a transition:

```bash
scripts/tracker_api.sh POST /issues/TEST-1/transitions/resolve/_execute '' '{
  "comment": "Resolved from API"
}'
```

Some transitions may require extra fields in the JSON body.
