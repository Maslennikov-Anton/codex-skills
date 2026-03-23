# Auth And Request Format

Primary source pages:

- https://yandex.ru/support/tracker/ru/api-ref/access
- https://yandex.ru/support/tracker/ru/common-format
- https://yandex.ru/support/tracker/ru/error-codes

## Access modes

- OAuth 2.0 works for both Yandex 360 and Yandex Cloud organizations.
- IAM token auth is available only for Yandex Cloud organizations.
- Tracker API requests run with the permissions of the user or service account behind the token.

## Required headers

```text
Authorization: OAuth <token>
X-Org-ID: <org-id>
```

or

```text
Authorization: Bearer <iam-token>
X-Cloud-Org-ID: <org-id>
```

Common host:

```text
Host: api.tracker.yandex.net
```

Optional localization header:

```text
Accept-Language: en
```

## First verification request

Use this before all other operations:

```bash
curl -X GET 'https://api.tracker.yandex.net/v3/myself' \
  -H 'Authorization: OAuth <token>' \
  -H 'X-Org-ID: <org-id>'
```

Expected result: `200 OK`. If access is not configured, the docs say this request returns `401 Unauthorized`.

## Generic request shape

```text
<METHOD> https://api.tracker.yandex.net/v3/<resource>/<id>?<query>
```

Supported methods:

- `GET` for reads
- `POST` for creates and search operations
- `PATCH` for partial updates
- `DELETE` for removals

## PATCH semantics

`PATCH` changes only explicitly passed fields.

Useful patterns:

- Set a scalar field:
  ```json
  {"summary":"New summary"}
  ```
- Clear a field:
  ```json
  {"followers":null}
  ```
- Add to an array:
  ```json
  {"followers":{"add":["user1","user2"]}}
  ```
- Remove from an array:
  ```json
  {"followers":{"remove":["user1"]}}
  ```
- Replace an array fully:
  ```json
  {"tags":{"set":["backend","urgent"]}}
  ```

## Text format

- Description and comment text can use Yandex Flavored Markdown.
- Newlines should be encoded as `\n` inside JSON strings.
- Escape `"`, `\`, and `/` where required by JSON.

## Pagination

For list responses, default page size is 50.

Common parameters:

- `perPage`
- `page`

Common response headers:

- `X-Total-Pages`
- `X-Total-Count`

For issue search there are multiple modes:

- regular pagination for smaller filtered results;
- relative pagination for queue-based traversal;
- scroll for results above 10,000.

## Time zone behavior

The API exchanges dates and times in UTC+00:00. If the user expects local time, call that out explicitly.

## Error codes

- `400`: invalid request parameter value
- `401`: auth missing, invalid, expired, or service account not enabled for Tracker
- `403`: token is valid but the account lacks Tracker permissions
- `404`: wrong resource id, wrong key, or no access to the object
- `409` / `412`: edit conflict, usually version mismatch or stale object state
- `422`: JSON validation error
- `423`: object edit blocked, including version ceiling cases
- `428`: required precondition missing
- `429`: rate limit exceeded

When debugging, separate these cases:

- auth problem;
- permission problem;
- data shape problem;
- concurrency/version problem;
- rate limiting.
