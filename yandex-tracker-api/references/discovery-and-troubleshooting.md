# Discovery And Troubleshooting

Primary source pages:

- https://yandex.ru/support/tracker/ru/concepts/queues/get-queue
- https://yandex.ru/support/tracker/ru/concepts/queues/get-fields
- https://yandex.ru/support/tracker/ru/concepts/queues/get-local-fields
- https://yandex.ru/support/tracker/ru/error-codes

## Discovery sequence before writes

Use this sequence when the user wants to create or edit issues but field requirements are unclear:

1. Verify access with `/myself`.
2. Inspect the queue:
   - `GET /queues/<queue>?expand=all`
3. Inspect required fields:
   - `GET /queues/<queue>/fields`
4. Inspect local custom fields:
   - `GET /queues/<queue>/localFields`
5. If updating an existing issue, fetch the issue first and inspect current field shapes.

This avoids trial-and-error on required fields and field value formats.

## Practical debugging map

### 401 Unauthorized

Likely causes:

- wrong token;
- expired IAM token;
- wrong auth scheme;
- wrong org header type;
- service account not enabled for Tracker in Yandex Cloud.

Check:

- `Authorization` prefix is `OAuth` or `Bearer` as appropriate;
- correct org header is used;
- `/myself` fails the same way.

### 403 Forbidden

Likely causes:

- account lacks Tracker rights;
- queue or issue permissions do not allow the action.

Check:

- whether the same action is allowed in the Tracker UI;
- whether the user can edit the target queue or issue manually.

### 404 Not Found

Likely causes:

- wrong issue key or queue key;
- wrong identifier type;
- object exists but is inaccessible to the caller.

Check:

- key case sensitivity for queues;
- raw object fetch without expansions;
- whether the user can open the same object in UI.

### 409 or 412 Conflict

Likely causes:

- stale edit against a newer object version;
- concurrent update.

Approach:

1. Re-read the issue.
2. Rebuild the PATCH body from fresh state.
3. Retry only if the business intent is still valid.

### 422 Validation error

Likely causes:

- malformed JSON;
- wrong field key;
- value type mismatch;
- unsupported enum/key.

Approach:

- compare the payload against queue field metadata;
- reduce the payload to the smallest failing body;
- confirm whether the field expects a scalar, object, or array.

### 423 Locked

Likely causes:

- edit blocked by version ceiling or object state.

Call this out explicitly. This is not a normal auth error.

### 428 Precondition required

Likely causes:

- missing required execution precondition for the endpoint or object state.

Re-check the endpoint-specific docs and object state.

### 429 Too Many Requests

Approach:

- retry with backoff;
- reduce concurrency;
- avoid unnecessary polling.

## Field-shape heuristics

When a field format is unclear:

- fetch an existing issue where the field is already populated;
- inspect queue field metadata;
- prefer passing canonical keys or ids rather than localized display names.

## Time and locale gotchas

- API timestamps are in UTC+00:00.
- Localized display names can vary by `Accept-Language`.
- For automations and stable integrations, keys and ids are safer than display labels.
