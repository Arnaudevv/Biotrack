# BioTrack Communication Protocol

**Protocol version:** 1.0
**Application version:** 2.0.0

## 1. Introduction

This document specifies the communication protocol used between the BioTrack **client** (terminal application) and the BioTrack **server** (business logic and persistence).

The protocol is a **REST-inspired subset of HTTP/1.1 carried directly over TCP sockets**:

- Messages are text-based, with lines terminated by CRLF (`\r\n`).
- Resources are identified by URL paths (nouns); HTTP methods express the operation (verbs).
- Message bodies are JSON documents encoded in UTF-8.
- Each request is stateless: it carries everything the server needs to process it.

A third party must be able to write a compatible client using only this document.

### Conventions

- `<value>` denotes a placeholder.
- `{name}` in a path denotes a path parameter.
- "MUST", "MUST NOT" and "MAY" are used in their usual normative sense.

---

## 2. Transport

| Aspect | Specification |
|---|---|
| Transport protocol | TCP (blocking sockets) |
| Default address | `127.0.0.1:8000` (configurable on both sides) |
| Connection model | One request and one response per connection |
| Connection closing | The server closes the connection after sending the response (`Connection: close`) |
| Concurrency | The server handles **one client at a time**. Other connections wait in the operating system queue |
| Text encoding | UTF-8 for bodies; ASCII for the start line and headers |

### Limits

| Limit | Value | Violation |
|---|---|---|
| Maximum size of start line + headers | 8 KB (8192 bytes) | `413` |
| Maximum body size | 1 MB (1 048 576 bytes) | `413` |
| Server read timeout | 5 seconds without receiving data | `408` |
| Client connection/read timeout | 10 seconds | client error (see section 7.4) |

---

## 3. Request format

```
<METHOD> <path>[?<query>] HTTP/1.1\r\n
Host: <host>:<port>\r\n
Content-Type: application/json\r\n
Content-Length: <n>\r\n
Connection: close\r\n
\r\n
<body: exactly n bytes>
```

### 3.1 Request line

`<METHOD> <target> <version>` with **exactly three tokens separated by one space**.

- **Method:** one of `GET`, `POST`, `PUT`, `PATCH`, `DELETE`.
- **Target:** an absolute path starting with `/`, optionally followed by `?` and a query string.
- **Version:** MUST be `HTTP/1.1`.

### 3.2 Headers

Each header has the form `Name: value\r\n`. Header names are **case-insensitive**. The header block ends with an empty line (`\r\n\r\n` marks the end of the headers).

| Header | Required | Description |
|---|---|---|
| `Host` | Yes | Server address and port |
| `Content-Length` | Yes (value `0` when there is no body) | Size of the body **in bytes** (not characters) |
| `Content-Type` | When there is a body | MUST be `application/json` |
| `Connection` | Yes | MUST be `close` |

- The server SHOULD treat a missing `Content-Length` as `0`.
- `Transfer-Encoding` (for example `chunked`) is **not supported**. A request containing it is rejected with `400`.
- Unknown headers are ignored.

### 3.3 Query string

Format: `key=value` pairs separated by `&`. Keys and values are percent-encoded (`%XX`); a space MAY be sent as `%20` or `+`. When a key is repeated, the last value wins.

### 3.4 Path parameters

Path segments that carry user data (such as codes) MUST be percent-encoded by the client and are decoded by the server before use.

### 3.5 Body

A JSON **object**. Requests that do not define a body (`GET`, `DELETE`) send `Content-Length: 0`.

---

## 4. Response format

```
HTTP/1.1 <status> <reason>\r\n
Content-Type: application/json; charset=utf-8\r\n
Content-Length: <n>\r\n
Connection: close\r\n
\r\n
<body: exactly n bytes>
```

- The status line contains the numeric status code and its reason phrase.
- `Content-Length` is always present. For `204 No Content` it is `0` and there is no body.
- On success the body is a JSON object or a JSON array. On failure it is an error object (section 7).
- The client MAY read until the server closes the connection or until `Content-Length` bytes have been received; both give the same result.

### Status codes used

| Code | Reason | Meaning |
|---|---|---|
| 200 | OK | Successful read or update |
| 201 | Created | Resource or relation created |
| 204 | No Content | Successful deletion, no body |
| 400 | Bad Request | Malformed request or invalid query parameter |
| 404 | Not Found | Resource or route does not exist |
| 405 | Method Not Allowed | The route exists but not for that method |
| 408 | Request Timeout | The request was not received in time |
| 409 | Conflict | Duplicate, or the operation violates data integrity |
| 413 | Payload Too Large | Headers or body exceed the limits |
| 422 | Unprocessable Entity | Well-formed request with invalid data |
| 500 | Internal Server Error | Unexpected server failure |

---

## 5. Data serialization

All request and response bodies are JSON. Field names use `snake_case`.

| Type | JSON representation | Example |
|---|---|---|
| string | JSON string | `"Ana"` |
| integer | JSON number | `1` |
| boolean | `true` / `false` | `true` |
| date | String `YYYY-MM-DD` | `"1990-05-01"` |
| datetime | String ISO 8601 `YYYY-MM-DDTHH:MM:SS` | `"2026-10-14T10:30:00"` |
| decimal | **String** (preserves precision) | `"12.3400"` |
| enumeration | String with one of the allowed values | `"pending"` |
| absent optional value | `null` | `null` |

Rules:

- **Decimals** are always sent as strings. The server also accepts a JSON number in requests and converts it.
- **Enumerations** are case-sensitive and lowercase.
- **Unknown fields** in a request body are ignored.
- **Relations** are expressed by business codes (`patient_code`, `staff_code`, ...) or by `id` where the resource has no code (projects).
- **Binary data:** the protocol file of a protocol (`protocol_file`) is **not transmitted** in this version (see section 9).

### Enumerations

| Name | Allowed values |
|---|---|
| `sample_status` | `pending`, `in_process`, `analyzed`, `rejected`, `archived` |
| `staff_role` | `researcher`, `analyst`, `technician`, `manager`, `administrator` |
| `quality_result` | `approved`, `rejected`, `pending_review` |
| `project_role` | `principal_investigator`, `co_investigator`, `analyst`, `technician`, `assistant` |

---

## 6. Supported operations

### 6.0 Summary

Identifiers in paths: `{code}` is the unique business code of the resource; `{id}` is the numeric identifier (projects only).

| Resource | Operation | Method and path | Success |
|---|---|---|---|
| Health | Ping | `GET /ping` | 200 |
| Patients | List | `GET /patients` | 200 |
| | Create | `POST /patients` | 201 |
| | Read | `GET /patients/{code}` | 200 |
| | Update | `PATCH /patients/{code}` | 200 |
| | Delete | `DELETE /patients/{code}` | 204 |
| | List samples | `GET /patients/{code}/samples` | 200 |
| Samples | List | `GET /samples` | 200 |
| | Create | `POST /samples` | 201 |
| | Read | `GET /samples/{code}` | 200 |
| | Read with relations | `GET /samples/{code}/full` | 200 |
| | Update | `PATCH /samples/{code}` | 200 |
| | Delete | `DELETE /samples/{code}` | 204 |
| | Read quality control | `GET /samples/{code}/quality-control` | 200 |
| | Set quality control | `PUT /samples/{code}/quality-control` | 200 |
| | Apply protocol | `POST /samples/{code}/protocols` | 201 |
| Staff | List | `GET /staff` | 200 |
| | Create | `POST /staff` | 201 |
| | Read | `GET /staff/{code}` | 200 |
| | Update | `PATCH /staff/{code}` | 200 |
| | Delete | `DELETE /staff/{code}` | 204 |
| | List assignments | `GET /staff/{code}/assignments` | 200 |
| Projects | List | `GET /projects` | 200 |
| | Create | `POST /projects` | 201 |
| | Read with team and samples | `GET /projects/{id}` | 200 |
| | Update | `PATCH /projects/{id}` | 200 |
| | Delete | `DELETE /projects/{id}` | 204 |
| | Link sample | `POST /projects/{id}/samples` | 201 |
| | Add team member | `POST /projects/{id}/team` | 201 |
| Protocols | List / search | `GET /protocols` | 200 |
| | Create | `POST /protocols` | 201 |
| | Read | `GET /protocols/{code}` | 200 |
| | Update | `PATCH /protocols/{code}` | 200 |
| | Delete | `DELETE /protocols/{code}` | 204 |
| | List samples | `GET /protocols/{code}/samples` | 200 |
| Administration | List containers | `GET /containers` | 200 |
| | Create container | `POST /containers` | 201 |
| | List sample types | `GET /sample-types` | 200 |
| | Create sample type | `POST /sample-types` | 201 |

Semantics of the methods:

- `GET` reads and never modifies data.
- `POST` creates a resource or creates a relation between two resources.
- `PUT` replaces a resource entirely (idempotent).
- `PATCH` modifies **only the fields present** in the body.
- `DELETE` removes a resource.

In the tables below, **Required** means the field MUST be present on creation; optional fields use the default shown or `null`. Resource representations returned by the server (marked "Response") always contain all their fields.

---

### 6.1 Health

#### `GET /ping`
Checks that the server is reachable.

- **Response 200:** `{"message": "pong"}`

---

### 6.2 Patients

**Patient representation (Response)**

| Field | Type | Description |
|---|---|---|
| `id` | integer | Internal identifier |
| `code` | string | Unique code (e.g. `PAT-001`) |
| `name` | string | First name |
| `lastname` | string | Last name |
| `birth_date` | date | Date of birth |
| `active` | boolean | Whether the patient is active |
| `test` | string | Clinical note / test |
| `registration_date` | datetime | Set by the server on creation |

#### `GET /patients`
Lists patients.

| Query parameter | Values | Effect |
|---|---|---|
| `active` | `true` / `false` | Only active / inactive patients. Any other value gives `400` |

- **Response 200:** array of patients (empty array if none).

#### `POST /patients`

| Field | Type | Required | Default |
|---|---|---|---|
| `code` | string | Yes | |
| `name` | string | Yes | |
| `lastname` | string | Yes | |
| `birth_date` | date | Yes | |
| `test` | string | No | `"Routine checkup"` |
| `active` | boolean | No | `true` |

- **Response 201:** the created patient.
- **Errors:** `409` if `code` already exists; `422` if validation fails.

#### `GET /patients/{code}`
- **Response 200:** the patient. **Errors:** `404`.

#### `PATCH /patients/{code}`
Optional fields: `name`, `lastname`, `birth_date`, `test`, `active`. The `code` cannot be changed.

- **Response 200:** the updated patient. **Errors:** `404`, `422`.

#### `DELETE /patients/{code}`
- **Response 204.** **Errors:** `404`; `409` if the patient still has samples.

#### `GET /patients/{code}/samples`
- **Response 200:** array of samples (see 6.3). **Errors:** `404` if the patient does not exist.

---

### 6.3 Samples

**Sample representation (Response)**

| Field | Type | Description |
|---|---|---|
| `id` | integer | Internal identifier |
| `code` | string | Unique code |
| `volume` | decimal | Volume, greater than 0 |
| `extraction_date` | date | Extraction date |
| `status` | `sample_status` | Current status |
| `patient_code` | string | Code of the owning patient |
| `sample_type` | string | Name of the sample type |
| `container_code` | string | Code of the container |

**Full sample representation** (`/full`): all fields above plus

| Field | Type | Description |
|---|---|---|
| `patient` | object | `{code, name, lastname}` |
| `quality_control` | object or `null` | See 6.3.1 |
| `protocols` | array | `[{code, name}]` |
| `temperature_logs` | array | `[{id, reading_date, temperature}]` (`temperature` is a decimal) |
| `projects` | array | `[{id, project_name, assignment_date}]` |

#### `GET /samples`

| Query parameter | Values | Effect |
|---|---|---|
| `status` | a `sample_status` | Samples with that status |
| `from`, `to` | dates | Samples whose `extraction_date` is within the range (inclusive). Both are required together; `from` MUST NOT be later than `to` |

Combining `status` with a date range is not supported. Invalid values, a single date, or an unsupported combination give `400`.

- **Response 200:** array of samples.

#### `POST /samples`

| Field | Type | Required | Default |
|---|---|---|---|
| `code` | string | Yes | |
| `volume` | decimal | Yes | |
| `extraction_date` | date | Yes | |
| `patient_code` | string | Yes | |
| `sample_type` | string | Yes | |
| `container_code` | string | Yes | |
| `status` | `sample_status` | No | `"pending"` |

- **Response 201:** the created sample.
- **Errors:** `409` if `code` exists; `422` if validation fails, `volume` is not greater than 0, or the referenced patient, sample type or container does not exist.

#### `GET /samples/{code}`
- **Response 200:** the sample. **Errors:** `404`.

#### `GET /samples/{code}/full`
- **Response 200:** the full sample representation. **Errors:** `404`.

#### `PATCH /samples/{code}`
Optional fields: `volume`, `extraction_date`, `status`, `sample_type`, `container_code`. The `code` and the patient cannot be changed.

- **Response 200:** the updated sample. **Errors:** `404`, `422`.

#### `DELETE /samples/{code}`
- **Response 204.** **Errors:** `404`.

#### 6.3.1 Quality control

**Quality control representation (Response)**

| Field | Type | Description |
|---|---|---|
| `sample_code` | string | Code of the sample |
| `purity` | decimal or `null` | Between 0 and 100 |
| `concentration` | decimal or `null` | Greater than or equal to 0 |
| `result` | `quality_result` | Result |

A sample has at most one quality control.

##### `GET /samples/{code}/quality-control`
- **Response 200:** the quality control. **Errors:** `404` if the sample does not exist or has no quality control.

##### `PUT /samples/{code}/quality-control`
Creates the quality control or replaces the existing one.

| Field | Type | Required |
|---|---|---|
| `result` | `quality_result` | Yes |
| `purity` | decimal | No (`null`) |
| `concentration` | decimal | No (`null`) |

- **Response 200:** the stored quality control. **Errors:** `404` (sample), `422`.

#### 6.3.2 Applying protocols

##### `POST /samples/{code}/protocols`

| Field | Type | Required |
|---|---|---|
| `protocol_code` | string | Yes |

- **Response 201:** `{"sample_code": "<code>", "protocol_code": "<code>"}`
- **Errors:** `404` (sample or protocol), `409` if already applied.

---

### 6.4 Staff

**Staff representation (Response)**

| Field | Type | Description |
|---|---|---|
| `id` | integer | Internal identifier |
| `code` | string | Unique code |
| `name` | string | First name |
| `lastname` | string | Last name |
| `role` | `staff_role` | Role in the organization |
| `active` | boolean | Whether the person is active |

#### `GET /staff`
- **Response 200:** array of staff members.

#### `POST /staff`

| Field | Type | Required | Default |
|---|---|---|---|
| `code` | string | Yes | |
| `name` | string | Yes | |
| `lastname` | string | Yes | |
| `role` | `staff_role` | Yes | |
| `active` | boolean | No | `true` |

- **Response 201.** **Errors:** `409`, `422`.

#### `GET /staff/{code}`
- **Response 200.** **Errors:** `404`.

#### `PATCH /staff/{code}`
Optional fields: `name`, `lastname`, `role`, `active`.

- **Response 200.** **Errors:** `404`, `422`.

#### `DELETE /staff/{code}`
- **Response 204.** **Errors:** `404`; `409` if the person is still referenced (e.g. assigned to a project).

#### `GET /staff/{code}/assignments`
- **Response 200:** array of `{project_id, project_name, role}` where `role` is a `project_role`.
- **Errors:** `404`.

---

### 6.5 Projects

**Project representation (Response)**

| Field | Type | Description |
|---|---|---|
| `id` | integer | Identifier used in paths |
| `project_name` | string | Unique name |
| `start_date` | date | Start date |
| `description` | string or `null` | Description |

**Project detail** (`GET /projects/{id}`): all fields above plus

| Field | Type | Description |
|---|---|---|
| `team` | array | `[{staff_code, name, lastname, role}]` where `role` is a `project_role` |
| `samples` | array | `[{code, assignment_date}]` |

#### `GET /projects`
- **Response 200:** array of projects.

#### `POST /projects`

| Field | Type | Required |
|---|---|---|
| `project_name` | string | Yes |
| `start_date` | date | Yes |
| `description` | string | No |

- **Response 201.** **Errors:** `409` if the name exists; `422`.

#### `GET /projects/{id}`
- **Response 200:** project detail. **Errors:** `404`. A non-numeric `{id}` gives `400`.

#### `PATCH /projects/{id}`
Optional fields: `project_name`, `start_date`, `description`.

- **Response 200.** **Errors:** `404`, `409`, `422`.

#### `DELETE /projects/{id}`
- **Response 204.** **Errors:** `404`.

#### `POST /projects/{id}/samples`
Links a sample to the project.

| Field | Type | Required |
|---|---|---|
| `sample_code` | string | Yes |

- **Response 201:** `{"project_id": <id>, "sample_code": "<code>", "assignment_date": "<datetime>"}`
- **Errors:** `404` (project or sample); `409` if already linked.

#### `POST /projects/{id}/team`
Adds a staff member to the project team.

| Field | Type | Required |
|---|---|---|
| `staff_code` | string | Yes |
| `role` | `project_role` | Yes |

- **Response 201:** `{"project_id": <id>, "staff_code": "<code>", "role": "<role>"}`
- **Errors:** `404` (project or staff); `409` if already in the team; `422` for an invalid role.

---

### 6.6 Protocols

**Protocol representation (Response)**

| Field | Type | Description |
|---|---|---|
| `id` | integer | Internal identifier |
| `code` | string | Unique code |
| `name` | string | Name |
| `description` | string or `null` | Description |
| `file_name` | string or `null` | Name of the associated file |
| `creation_date` | date | Creation date |
| `last_review_date` | date or `null` | Date of the last review |
| `reviewed_by` | string or `null` | Code of the reviewing staff member |

The binary content of the file is never included.

#### `GET /protocols`

| Query parameter | Values | Effect |
|---|---|---|
| `keyword` | text | Protocols whose name contains the text (case-insensitive) |

- **Response 200:** array of protocols.

#### `POST /protocols`

| Field | Type | Required |
|---|---|---|
| `code` | string | Yes |
| `name` | string | Yes |
| `description` | string | No |
| `last_review_date` | date | No |
| `reviewed_by` | string (staff code) | No |

- **Response 201.** **Errors:** `409`; `422` (including a `reviewed_by` that does not exist).

#### `GET /protocols/{code}`
- **Response 200.** **Errors:** `404`.

#### `PATCH /protocols/{code}`
Optional fields: `name`, `description`, `last_review_date`, `reviewed_by`.

- **Response 200.** **Errors:** `404`, `422`.

#### `DELETE /protocols/{code}`
- **Response 204.** **Errors:** `404`.

#### `GET /protocols/{code}/samples`
- **Response 200:** array of samples (see 6.3). **Errors:** `404`.

---

### 6.7 Administration

#### Containers

**Representation:** `{id: integer, code: string, type_name: string}`

- `GET /containers` → **200**, array.
- `POST /containers` → **201**. Required: `code`, `type_name`. Errors: `409`, `422`.

#### Sample types

**Representation:** `{id: integer, type_name: string}`

- `GET /sample-types` → **200**, array.
- `POST /sample-types` → **201**. Required: `type_name`. Errors: `409`, `422`.

---

## 7. Error handling

### 7.1 Error format

Every response with a status code of 400 or higher has the **same body**:

```json
{
  "status": 422,
  "title": "Validation error",
  "detail": "birth_date must be a date in YYYY-MM-DD format"
}
```

| Field | Type | Description |
|---|---|---|
| `status` | integer | Same value as the status line |
| `title` | string | Short, fixed description of the error class |
| `detail` | string | Human-readable explanation of this specific error |

Titles: `400` Bad request · `404` Not found · `405` Method not allowed · `408` Request timeout · `409` Conflict · `413` Payload too large · `422` Validation error · `500` Internal server error.

### 7.2 When each status is returned

| Code | Situation |
|---|---|
| **400** | Malformed request line or headers; unsupported HTTP version or method token; `Transfer-Encoding` present; invalid or negative `Content-Length`; body shorter than `Content-Length`; body is not valid JSON; `Content-Type` other than `application/json` when a body is present; invalid query parameter; non-numeric `{id}` |
| **404** | The route does not exist, or the referenced resource does not exist |
| **405** | The route exists but the method is not supported on it |
| **408** | The server received no data for 5 seconds before the request was complete |
| **409** | Creating a duplicate; deleting a resource that is still referenced; linking something already linked |
| **413** | Headers larger than 8 KB or `Content-Length` larger than 1 MB |
| **422** | The body is valid JSON but not an object; required field missing or empty; wrong field type; invalid date, decimal or enumeration value; violated rule (e.g. `volume` not greater than 0, `purity` outside 0–100); a referenced entity in the body does not exist |
| **500** | Unexpected server failure |

**Precedence:** the server validates the message format first (`400`, `408`, `413`), then the route (`404`, `405`), then the data (`422`), then the business rules (`404`, `409`).

### 7.3 Server guarantees

- The server **always answers** with a well-formed response in the format above, even for garbage input.
- A bad request **never stops the server**: after any error the server returns to accepting connections.
- Database changes made while processing a request are **committed only if the request succeeds**; on any error they are rolled back.
- A `500` response never exposes internal details (stack traces, SQL, paths). Those are written only to the server log.

### 7.4 Client behavior

- The client converts every response with status ≥ 400 into an error carrying the `status` and the `detail`.
- If the server cannot be reached (connection refused, timeout, connection closed before a complete response), the client reports a connection error with status `0` and the message *"Cannot reach the server"*. This is a client-side condition and is not sent on the wire.
- A request MAY be retried after a timeout only if it is idempotent (`GET`, `PUT`, `DELETE`). `POST` and `PATCH` MUST NOT be retried automatically.

---

## 8. Complete examples

Messages are shown exactly as sent on the wire. Each line ends with `\r\n`, and an empty line separates headers from body. `Content-Length` values are real byte counts.

### 8.1 Create a patient (201)

Request:

```
POST /patients HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json
Content-Length: 75
Connection: close

{"code":"PAT-001","name":"Ana","lastname":"Ruiz","birth_date":"1990-05-01"}
```

Response:

```
HTTP/1.1 201 Created
Content-Type: application/json; charset=utf-8
Content-Length: 163
Connection: close

{"id":1,"code":"PAT-001","name":"Ana","lastname":"Ruiz","birth_date":"1990-05-01","active":true,"test":"Routine checkup","registration_date":"2026-10-14T10:30:00"}
```

### 8.2 List with a query parameter (200)

Request:

```
GET /patients?active=true HTTP/1.1
Host: 127.0.0.1:8000
Content-Length: 0
Connection: close

```

Response:

```
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 165
Connection: close

[{"id":1,"code":"PAT-001","name":"Ana","lastname":"Ruiz","birth_date":"1990-05-01","active":true,"test":"Routine checkup","registration_date":"2026-10-14T10:30:00"}]
```

### 8.3 Resource not found (404)

Request:

```
GET /patients/PAT-999 HTTP/1.1
Host: 127.0.0.1:8000
Content-Length: 0
Connection: close

```

Response:

```
HTTP/1.1 404 Not Found
Content-Type: application/json; charset=utf-8
Content-Length: 73
Connection: close

{"status":404,"title":"Not found","detail":"Patient 'PAT-999' not found"}
```

### 8.4 Duplicate resource (409)

Request: the same body as example 8.1.

Response:

```
HTTP/1.1 409 Conflict
Content-Type: application/json; charset=utf-8
Content-Length: 77
Connection: close

{"status":409,"title":"Conflict","detail":"Patient 'PAT-001' already exists"}
```

### 8.5 Invalid JSON (400)

Request:

```
POST /patients HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json
Content-Length: 19
Connection: close

{"code": "PAT-002",
```

Response:

```
HTTP/1.1 400 Bad Request
Content-Type: application/json; charset=utf-8
Content-Length: 78
Connection: close

{"status":400,"title":"Bad request","detail":"Request body is not valid JSON"}
```

### 8.6 Invalid data (422)

Request:

```
POST /patients HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json
Content-Length: 77
Connection: close

{"code":"PAT-002","name":"Luis","lastname":"Soler","birth_date":"01/05/1990"}
```

Response:

```
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json; charset=utf-8
Content-Length: 99
Connection: close

{"status":422,"title":"Validation error","detail":"birth_date must be a date in YYYY-MM-DD format"}
```

### 8.7 Delete (204)

Request:

```
DELETE /patients/PAT-001 HTTP/1.1
Host: 127.0.0.1:8000
Content-Length: 0
Connection: close

```

Response:

```
HTTP/1.1 204 No Content
Content-Length: 0
Connection: close

```

### 8.8 Create a relation (201)

Request:

```
POST /projects/3/team HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json
Content-Length: 41
Connection: close

{"staff_code":"STF-010","role":"analyst"}
```

Response:

```
HTTP/1.1 201 Created
Content-Type: application/json; charset=utf-8
Content-Length: 56
Connection: close

{"project_id":3,"staff_code":"STF-010","role":"analyst"}
```

---

## 9. Known limitations

These are deliberate decisions for version 2.0.0:

- **No authentication or authorization.** Any client that can reach the server can use every operation. Not suitable for real clinical data as is.
- **No encryption (HTTPS/TLS).** Traffic travels in clear text.
- **One client at a time.** Concurrent clients wait in the operating system queue.
- **One request per connection.** No persistent connections (keep-alive) and no `Transfer-Encoding: chunked`.
- **Binary protocol files are not transmitted.** `protocol_file` is neither sent nor accepted; only its metadata (`file_name`) is exposed.
- **No pagination.** List endpoints return the whole collection.
- **Only HTTP/1.1 semantics are implemented**, not HTTP/2 or HTTP/3.

## 10. Revision history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-10-14 | First version |
