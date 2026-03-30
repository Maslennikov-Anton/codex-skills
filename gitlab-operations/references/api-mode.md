# API Mode With `glab api`

Primary official docs:

- https://docs.gitlab.com/cli/api/

## When to use it

Use `glab api` when a high-level `glab` subcommand is missing or too restrictive.

It supports:

- GitLab REST API v4 endpoints
- GitLab GraphQL through the special `graphql` endpoint

## Basic REST

Get releases of the current repo:

```bash
glab api projects/:fullpath/releases
```

Get issues for a specific project path:

```bash
glab api projects/gitlab-com%2Fwww-gitlab-com/issues
```

Paginate over issues:

```bash
glab api issues --paginate
glab api issues --paginate --output ndjson
```

Filter with `jq`:

```bash
glab api issues --paginate --output ndjson | jq 'select(.state == "opened")'
```

## Sending fields

The docs describe two parameter flags:

- `--raw-field key=value`: always sends strings
- `--field key=value`: infers booleans, nulls, integers, placeholders, and `@file` values

Examples:

```bash
glab api projects/:id/issues --method POST \
  --field title='Bug from CLI' \
  --field description='Created via glab api'
```

Read body from file or stdin:

```bash
glab api projects/:id/releases --method POST --input body.json
cat body.json | glab api projects/:id/releases --method POST --input -
```

## GraphQL

Simple query:

```bash
glab api graphql -f query='
  query {
    currentUser {
      username
    }
  }
'
```

Paginated GraphQL:

```bash
glab api graphql --paginate -f query='
  query($endCursor: String) {
    project(fullPath: "gitlab-org/graphql-sandbox") {
      issues(first: 2, after: $endCursor) {
        edges {
          node {
            title
          }
        }
        pageInfo {
          endCursor
          hasNextPage
        }
      }
    }
  }'
```

The docs note that paginated GraphQL queries must:

- accept `$endCursor: String`;
- request `pageInfo { hasNextPage endCursor }`.

## Placeholder values

In repo context, `glab api` can resolve these placeholders:

- `:branch`
- `:fullpath`
- `:group`
- `:id`
- `:namespace`
- `:repo`
- `:user`
- `:username`

Use them to avoid hardcoding project ids and namespaces in local scripts.
