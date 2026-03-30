# API Coverage Map

This file expands the skill from a task-focused subset to a broader map of Yandex Tracker API areas.

Important: this is a practical coverage map built from official docs pages and endpoint patterns, not a byte-for-byte mirror of the full site tree. For rare operations, confirm the exact request body on the linked doc page before implementation.

Primary official docs used while building this map:

- https://yandex.ru/support/tracker/ru/api-ref/access
- https://yandex.ru/support/tracker/ru/common-format
- https://yandex.ru/support/tracker/ru/error-codes
- https://yandex.ru/support/tracker/en/concepts/issues/get-issue
- https://yandex.ru/support/tracker/en/concepts/issues/create-issue
- https://yandex.ru/support/tracker/en/concepts/issues/patch-issue
- https://yandex.ru/support/tracker/en/concepts/issues/search-issues
- https://yandex.ru/support/tracker/en/concepts/issues/count-issues
- https://yandex.ru/support/tracker/en/concepts/issues/get-links
- https://yandex.ru/support/tracker/en/concepts/issues/link-issue
- https://yandex.ru/support/tracker/en/concepts/issues/new-transition
- https://yandex.ru/support/tracker/en/concepts/queues/get-queues
- https://yandex.ru/support/tracker/en/concepts/queues/get-queue
- https://yandex.ru/support/tracker/en/concepts/queues/create-queue
- https://yandex.ru/support/tracker/en/concepts/queues/get-fields
- https://yandex.ru/support/tracker/en/concepts/queues/get-local-fields
- https://yandex.ru/support/tracker/en/concepts/queues/create-local-field
- https://yandex.ru/support/tracker/en/concepts/queues/manage-access
- https://yandex.ru/support/tracker/en/concepts/queues/get-trigger
- https://yandex.ru/support/tracker/en/concepts/queues/create-trigger
- https://yandex.ru/support/tracker/en/concepts/issues/get-global-fields
- https://yandex.ru/support/tracker/en/concepts/issues/get-issue-fields
- https://yandex.ru/support/tracker/en/concepts/issues/create-field
- https://yandex.ru/support/tracker/en/concepts/issues/create-issue-field-category
- https://yandex.ru/support/tracker/en/concepts/issues/get-priorities
- https://yandex.ru/support/tracker/en/concepts/create-status
- https://yandex.ru/support/tracker/en/concepts/queues/create-version
- https://yandex.ru/support/tracker/en/get-components
- https://yandex.ru/support/tracker/en/get-boards
- https://yandex.ru/support/tracker/en/get-board
- https://yandex.ru/support/tracker/en/post-board
- https://yandex.ru/support/tracker/en/get-columns
- https://yandex.ru/support/tracker/en/get-column
- https://yandex.ru/support/tracker/en/post-column
- https://yandex.ru/support/tracker/en/concepts/bulkchange/bulk-transition
- https://yandex.ru/support/tracker/en/concepts/bulkchange/bulk-move-info
- https://yandex.ru/support/tracker/en/concepts/entities/about-entities
- https://yandex.ru/support/tracker/en/concepts/entities/create-entity
- https://yandex.ru/support/tracker/en/concepts/entities/get-entity
- https://yandex.ru/support/tracker/en/concepts/entities/update-entity
- https://yandex.ru/support/tracker/en/concepts/entities/delete-entity
- https://yandex.ru/support/tracker/en/concepts/entities/bulkchange-entities
- https://yandex.ru/support/tracker/en/concepts/dashboards/create-dashboard

## 1. Access and common transport

Core concerns:

- auth: OAuth or IAM token;
- organization header: `X-Org-ID` or `X-Cloud-Org-ID`;
- common request body rules;
- pagination and error handling.

Core endpoints:

- `GET /v3/myself`

Reference:

- [auth-and-request-format.md](auth-and-request-format.md)

## 2. Users

Used for assignee resolution, follower lookup, org inspection, and permission debugging.

Common endpoints:

- current user;
- specific user by login or id;
- list users.

Typical paths:

- `GET /v3/myself`
- `GET /v3/users/<login_or_id>`
- `GET /v3/users`

## 3. Issues

This is the main working surface for most integrations.

Operations:

- read issue;
- create issue;
- patch issue fields;
- count issues;
- search issues with filters or query language;
- expand comments, transitions, links, attachments;
- comment on issue;
- attach files;
- list or create links;
- list or execute transitions.

Typical paths:

- `GET /v3/issues/<issue>`
- `POST /v3/issues/`
- `PATCH /v3/issues/<issue>`
- `POST /v3/issues/_search`
- `POST /v3/issues/_count`
- `POST /v3/issues/<issue>/comments`
- `POST /v3/issues/<issue>/attachments/`
- `GET /v3/issues/<issue>/links`
- `POST /v3/issues/<issue>/links`
- `GET /v3/issues/<issue>/transitions`
- `POST /v3/issues/<issue>/transitions/<transition>/_execute`

## 4. Queues

Used to discover queue metadata and administer queue behavior.

Operations:

- list queues;
- get one queue;
- create queue;
- inspect required fields;
- inspect local fields;
- create local field;
- manage queue permissions;
- inspect or create queue triggers.

Typical paths:

- `GET /v3/queues/`
- `GET /v3/queues/<queue>`
- `POST /v3/queues/`
- `GET /v3/queues/<queue>/fields`
- `GET /v3/queues/<queue>/localFields`
- `GET /v3/queues/<queue>/localFields/<field>`
- `POST /v3/queues/<queue>/localFields`
- `PATCH /v3/queues/<queue>/permissions`
- `GET /v3/queues/<queue>/triggers/<trigger>`
- `POST /v3/queues/<queue>/triggers`

## 5. Fields and field categories

Use when the integration needs schema discovery or admin-level schema changes.

Operations:

- list global fields;
- get one field;
- create field;
- list or create field categories.

Typical paths:

- `GET /v3/fields`
- `GET /v3/fields/<field_id>`
- `POST /v3/fields`
- `GET /v3/fields/categories`
- `POST /v3/fields/categories`

## 6. Metadata dictionaries

These endpoints help convert human labels into stable ids or keys for writes.

Likely areas:

- priorities;
- statuses;
- versions;
- issue types;
- resolutions;
- components.

Confirmed examples from docs:

- `GET /v3/priorities`
- `POST /v3/statuses/`
- `POST /v3/versions/`
- `GET /v3/components`

Practical rule:

- if the payload expects a key like `bug`, `normal`, `wontFix`, or queue version id, resolve it from metadata endpoints first instead of guessing.

## 7. Boards and columns

Used for kanban/scrum board management and board-aware automations.

Operations:

- list boards;
- get board;
- create board;
- list columns of a board;
- get one column;
- create column.

Typical paths:

- `GET /v3/boards`
- `GET /v3/boards/<board>`
- `POST /v3/boards/`
- `GET /v3/boards/<board>/columns`
- `GET /v3/boards/<board>/columns/<column>`
- `POST /v3/boards/<board>/columns/`

## 8. Dashboards

Less common for issue automations, but part of the API surface.

Confirmed example:

- `POST /v3/dashboards/`

Use this area when the user automates reporting or personal/team workspace setup.

## 9. Bulk operations

Use for high-volume updates where one-by-one issue edits are too slow or too fragile.

Confirmed examples:

- `POST /v3/bulkchange/_transition`
- `GET /v3/bulkchange/<id>`
- `GET /v3/bulkchange/<id>/issues`

Bulk operations normally return an operation id that must be polled.

## 10. Entities API

Modern API area for goals, projects, and portfolios.

Operations:

- create entity;
- get entity;
- update entity;
- delete entity;
- bulk update entities.

Typical paths:

- `POST /v3/entities/<entity_type>`
- `GET /v3/entities/<entity_type>/<entity_id>`
- `PATCH /v3/entities/<entity_type>/<entity_id>`
- `DELETE /v3/entities/<entity_type>/<entity_id>`
- `POST /v3/entities/<entity_type>/bulkchange/_update`

Entity types:

- `goal`
- `project`
- `portfolio`

## 11. Coverage guidance for future expansion

When the user asks for a rare or admin-only operation:

1. Open [endpoint-matrix.md](endpoint-matrix.md) to find the nearest category.
2. If the exact method is not already listed, search the official docs by path fragment and endpoint family.
3. Reuse `scripts/tracker_api.sh` for direct probing if credentials are available.
4. State clearly whether the answer is based on:
   - a confirmed documentation page;
   - an inferred endpoint pattern in the same family.
