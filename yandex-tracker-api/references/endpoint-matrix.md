# Endpoint Matrix

This matrix is a quick lookup table for the most useful and most visible endpoint families in Yandex Tracker API.

Legend:

- Status `confirmed`: explicitly confirmed from an official documentation page inspected while building this skill.
- Status `family`: included because it belongs to a documented endpoint family and is a common companion method, but verify the exact body or query parameters on the linked page when implementing.

## Access and users

| Area | Method | Path | Status | Purpose | Example |
|---|---|---|---|---|---|
| Access | GET | `/v3/myself` | confirmed | Verify auth and org header | `scripts/tracker_api.sh GET /myself` |
| Users | GET | `/v3/users/<login_or_id>` | confirmed | Get one user | `scripts/tracker_api.sh GET /users/userlogin` |
| Users | GET | `/v3/users` | confirmed | List org users | `scripts/tracker_api.sh GET /users '?perPage=100&page=1'` |

## Issues

| Area | Method | Path | Status | Purpose | Example |
|---|---|---|---|---|---|
| Issues | GET | `/v3/issues/<issue>` | confirmed | Read issue | `scripts/tracker_api.sh GET /issues/TEST-1` |
| Issues | POST | `/v3/issues/` | confirmed | Create issue | `scripts/tracker_api.sh POST /issues/ '' '{"queue":"TEST","summary":"API issue","type":"task"}'` |
| Issues | PATCH | `/v3/issues/<issue>` | confirmed | Update issue fields | `scripts/tracker_api.sh PATCH /issues/TEST-1 '' '{"summary":"Updated"}'` |
| Issues | POST | `/v3/issues/_search` | confirmed | Search issues | `scripts/tracker_api.sh POST /issues/_search '' '{"filter":{"queue":"TEST"}}'` |
| Issues | POST | `/v3/issues/_count` | confirmed | Count issues | `scripts/tracker_api.sh POST /issues/_count '' '{"filter":{"queue":"TEST"}}'` |
| Comments | POST | `/v3/issues/<issue>/comments` | confirmed | Add comment | `scripts/tracker_api.sh POST /issues/TEST-1/comments '' '{"text":"Done","markupType":"md"}'` |
| Attachments | POST | `/v3/issues/<issue>/attachments/` | confirmed | Upload attachment | `scripts/tracker_api.sh FILE /issues/TEST-1/attachments/ /tmp/file.txt` |
| Links | GET | `/v3/issues/<issue>/links` | confirmed | List links | `scripts/tracker_api.sh GET /issues/TEST-1/links` |
| Links | POST | `/v3/issues/<issue>/links` | confirmed | Create link | `scripts/tracker_api.sh POST /issues/TEST-1/links '' '{"relationship":"is dependent by","issue":"TEST-2"}'` |
| Transitions | GET | `/v3/issues/<issue>/transitions` | family | List available transitions | `scripts/tracker_api.sh GET /issues/TEST-1/transitions` |
| Transitions | POST | `/v3/issues/<issue>/transitions/<transition>/_execute` | confirmed | Execute transition | `scripts/tracker_api.sh POST /issues/TEST-1/transitions/resolve/_execute '' '{"comment":"Resolved"}'` |

## Queues

| Area | Method | Path | Status | Purpose | Example |
|---|---|---|---|---|---|
| Queues | GET | `/v3/queues/` | confirmed | List queues | `scripts/tracker_api.sh GET /queues/` |
| Queues | GET | `/v3/queues/<queue>` | confirmed | Get queue details | `scripts/tracker_api.sh GET /queues/TEST '?expand=all'` |
| Queues | POST | `/v3/queues/` | confirmed | Create queue | `scripts/tracker_api.sh POST /queues/ '' '{"key":"TEST2","name":"Test 2","lead":"userlogin","defaultType":"task","defaultPriority":"normal"}'` |
| Queue fields | GET | `/v3/queues/<queue>/fields` | confirmed | Get required fields | `scripts/tracker_api.sh GET /queues/TEST/fields` |
| Queue fields | GET | `/v3/queues/<queue>/localFields` | confirmed | Get local fields | `scripts/tracker_api.sh GET /queues/TEST/localFields` |
| Queue fields | GET | `/v3/queues/<queue>/localFields/<field>` | confirmed | Get local field details | `scripts/tracker_api.sh GET /queues/TEST/localFields/myfield` |
| Queue fields | POST | `/v3/queues/<queue>/localFields` | confirmed | Create local field | `scripts/tracker_api.sh POST /queues/TEST/localFields '' '{"id":"myfield","name":{"ru":"Поле","en":"Field"},"category":"0000000000000003********","type":"ru.yandex.startrek.core.fields.StringFieldType"}'` |
| Queue permissions | PATCH | `/v3/queues/<queue>/permissions` | confirmed | Update queue access rules | `scripts/tracker_api.sh PATCH /queues/TEST/permissions '' '{"read":{"roles":{"add":["follower"]}}}'` |
| Triggers | GET | `/v3/queues/<queue>/triggers/<trigger>` | confirmed | Get trigger | `scripts/tracker_api.sh GET /queues/TEST/triggers/16` |
| Triggers | POST | `/v3/queues/<queue>/triggers` | confirmed | Create trigger | `scripts/tracker_api.sh POST /queues/TEST/triggers '' '{"name":"Auto close","actions":[],"conditions":[]}'` |

## Fields and categories

| Area | Method | Path | Status | Purpose | Example |
|---|---|---|---|---|---|
| Fields | GET | `/v3/fields` | confirmed | List global fields | `scripts/tracker_api.sh GET /fields` |
| Fields | GET | `/v3/fields/<field_id>` | confirmed | Get field details | `scripts/tracker_api.sh GET /fields/priority` |
| Fields | POST | `/v3/fields` | confirmed | Create global field | `scripts/tracker_api.sh POST /fields '' '{"id":"myglobalfield","name":{"ru":"Глобальное поле","en":"Global field"},"category":"0000000000000001********","type":"ru.yandex.startrek.core.fields.StringFieldType"}'` |
| Field categories | GET | `/v3/fields/categories` | family | List categories | `scripts/tracker_api.sh GET /fields/categories` |
| Field categories | POST | `/v3/fields/categories` | confirmed | Create category | `scripts/tracker_api.sh POST /fields/categories '' '{"name":{"ru":"Категория","en":"Category"},"description":"API-created","order":400}'` |

## Metadata dictionaries

| Area | Method | Path | Status | Purpose | Example |
|---|---|---|---|---|---|
| Priorities | GET | `/v3/priorities` | confirmed | List priorities | `scripts/tracker_api.sh GET /priorities '?localized=false'` |
| Statuses | GET | `/v3/statuses` | family | List statuses | `scripts/tracker_api.sh GET /statuses` |
| Statuses | POST | `/v3/statuses/` | confirmed | Create status | `scripts/tracker_api.sh POST /statuses/ '' '{"key":"myStatus","name":{"ru":"Мой статус","en":"My status"},"type":"paused"}'` |
| Versions | GET | `/v3/versions` | family | List versions | `scripts/tracker_api.sh GET /versions` |
| Versions | POST | `/v3/versions/` | confirmed | Create queue version | `scripts/tracker_api.sh POST /versions/ '' '{"queue":"TEST","name":"1.0"}'` |
| Components | GET | `/v3/components` | confirmed | List components | `scripts/tracker_api.sh GET /components` |
| Issue types | GET | `/v3/issuetypes` | family | List issue types | `scripts/tracker_api.sh GET /issuetypes` |
| Resolutions | GET | `/v3/resolutions` | family | List resolutions | `scripts/tracker_api.sh GET /resolutions` |

## Boards and columns

| Area | Method | Path | Status | Purpose | Example |
|---|---|---|---|---|---|
| Boards | GET | `/v3/boards` | confirmed | List boards | `scripts/tracker_api.sh GET /boards` |
| Boards | GET | `/v3/boards/<board>` | confirmed | Get board | `scripts/tracker_api.sh GET /boards/73` |
| Boards | POST | `/v3/boards/` | confirmed | Create board | `scripts/tracker_api.sh POST /boards/ '' '{"name":"Testing","defaultQueue":{"key":"TEST"}}'` |
| Columns | GET | `/v3/boards/<board>/columns` | confirmed | List board columns | `scripts/tracker_api.sh GET /boards/73/columns` |
| Columns | GET | `/v3/boards/<board>/columns/<column>` | confirmed | Get one column | `scripts/tracker_api.sh GET /boards/73/columns/1` |
| Columns | POST | `/v3/boards/<board>/columns/` | confirmed | Create column | `scripts/tracker_api.sh POST /boards/73/columns/ '' '{"name":"Approve","statuses":["needInfo"]}'` |

## Dashboards

| Area | Method | Path | Status | Purpose | Example |
|---|---|---|---|---|---|
| Dashboards | GET | `/v3/dashboards` | family | List dashboards | `scripts/tracker_api.sh GET /dashboards` |
| Dashboards | GET | `/v3/dashboards/<dashboard>` | family | Get dashboard | `scripts/tracker_api.sh GET /dashboards/10` |
| Dashboards | POST | `/v3/dashboards/` | confirmed | Create dashboard | `scripts/tracker_api.sh POST /dashboards/ '' '{"name":"New Dashboard","layout":"one-column"}'` |

## Bulk operations

| Area | Method | Path | Status | Purpose | Example |
|---|---|---|---|---|---|
| Bulk change | POST | `/v3/bulkchange/_transition` | confirmed | Bulk status transition | `scripts/tracker_api.sh POST /bulkchange/_transition '' '{"transition":"start_progress","issues":["TEST-1","TEST-2"]}'` |
| Bulk change | GET | `/v3/bulkchange/<id>` | confirmed | Poll operation status | `scripts/tracker_api.sh GET /bulkchange/593cd211ef7e8a33********` |
| Bulk change | GET | `/v3/bulkchange/<id>/issues` | confirmed | Get failed issue list | `scripts/tracker_api.sh GET /bulkchange/593cd211ef7e8a33********/issues` |

## Entities API

| Area | Method | Path | Status | Purpose | Example |
|---|---|---|---|---|---|
| Entities | POST | `/v3/entities/<entity_type>` | confirmed | Create project, goal, or portfolio | `scripts/tracker_api.sh POST /entities/project '' '{"fields":{"summary":"Test Project","teamAccess":true}}'` |
| Entities | GET | `/v3/entities/<entity_type>/<entity_id>` | confirmed | Get entity | `scripts/tracker_api.sh GET /entities/project/655f328da834c763******** '?fields=summary,teamAccess'` |
| Entities | PATCH | `/v3/entities/<entity_type>/<entity_id>` | confirmed | Update entity | `scripts/tracker_api.sh PATCH /entities/project/655f328da834c763******** '' '{"fields":{"summary":"Renamed project"},"comment":"Updated from API"}'` |
| Entities | DELETE | `/v3/entities/<entity_type>/<entity_id>` | confirmed | Delete entity | `scripts/tracker_api.sh DELETE /entities/project/655f328da834c763******** '?withBoard=true'` |
| Entities bulk | POST | `/v3/entities/<entity_type>/bulkchange/_update` | confirmed | Bulk update entities | `scripts/tracker_api.sh POST /entities/project/bulkchange/_update '' '{"metaEntities":["id1","id2"],"values":{"fields":{"entityStatus":"blocked"},"comment":"Bulk update"}}'` |

## Practical selection rules

- For ordinary task automation, start with: `myself`, `queues`, `issues`, `comments`, `attachments`, `transitions`.
- For admin/schema work, add: `fields`, `localFields`, `permissions`, `statuses`, `versions`, `boards`, `dashboards`.
- For product planning work in modern Tracker setups, add: `entities/*`.
- If a path in this matrix is marked `family`, verify the exact method-specific doc page before shipping automation code.
