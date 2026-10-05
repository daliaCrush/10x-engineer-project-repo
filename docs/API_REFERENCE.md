# PromptLab API Reference

PromptLab is a FastAPI application for managing prompts and prompt collections.

- **Local base URL:** `http://localhost:8000`
- **Authentication:** None. The current API has no authentication or authorization.
- **Storage:** Process-local and in memory. All prompts and collections are lost when the server restarts.
- **Identifiers:** Generated resource identifiers are UUID strings.
- **Datetimes:** Datetime fields are serialized as JSON strings.
- **Interactive documentation:** `/docs` and `/redoc`

## GET /health

Returns the current API health status and application version.

### Parameters

- Path parameters: None
- Query parameters: None
- Request body: None

### Request

```bash
curl http://localhost:8000/health
```

### Success response

Status: `200 OK`

```json
{
  "status": "healthy",
  "version": "<application-version>"
}
```

### Errors

No application-defined errors.

## GET /prompts

Lists prompts and optionally filters them by collection or searches their content. Results are sorted by `created_at`, newest first.

### Parameters

- Path parameters: None
- Query parameters:
  - `collection_id` (optional string): Returns prompts whose `collection_id` exactly matches the supplied value. The API does not check whether that collection exists; an unknown value produces an empty result when no prompts match.
  - `search` (optional string): Searches prompt content.
- Request body: None

### Request

```bash
curl "http://localhost:8000/prompts?collection_id=4b197cf8-62b5-4600-a60f-8f2e2cb29ec5&search=summary"
```

### Success response

Status: `200 OK`

```json
{
  "prompts": [
    {
      "title": "Article summary",
      "content": "Summarize the following article: {article}",
      "description": "Produces a concise article summary.",
      "collection_id": "4b197cf8-62b5-4600-a60f-8f2e2cb29ec5",
      "id": "f9a946ea-f9e8-4405-a5f6-2c6ffc6ef230",
      "created_at": "2026-10-05T20:00:00",
      "updated_at": "2026-10-05T20:00:00"
    }
  ],
  "total": 1
}
```

### Errors

No application-defined errors. In particular, an unknown `collection_id` does not produce `400` or `404`.

## GET /prompts/{prompt_id}

Returns one prompt by its identifier.

### Parameters

- Path parameters:
  - `prompt_id` (string, required): Identifier of the prompt.
- Query parameters: None
- Request body: None

### Request

```bash
curl http://localhost:8000/prompts/f9a946ea-f9e8-4405-a5f6-2c6ffc6ef230
```

### Success response

Status: `200 OK`

```json
{
  "title": "Article summary",
  "content": "Summarize the following article: {article}",
  "description": "Produces a concise article summary.",
  "collection_id": null,
  "id": "f9a946ea-f9e8-4405-a5f6-2c6ffc6ef230",
  "created_at": "2026-10-05T20:00:00",
  "updated_at": "2026-10-05T20:00:00"
}
```

### Errors

- `404 Not Found`: The prompt does not exist.

```json
{
  "detail": "Prompt not found"
}
```

## POST /prompts

Creates a prompt.

### Parameters

- Path parameters: None
- Query parameters: None
- Request body:
  - `title` (string, required): Length from 1 through 200 characters.
  - `content` (string, required): Minimum length of 1 character.
  - `description` (string or null, optional): Maximum length of 500 characters. Defaults to null.
  - `collection_id` (string or null, optional): Must identify an existing collection when non-null. Defaults to null.

### Request

```bash
curl -X POST http://localhost:8000/prompts -H "Content-Type: application/json" -d '{"title":"Article summary","content":"Summarize the following article: {article}","description":"Produces a concise article summary.","collection_id":null}'
```

### Success response

Status: `201 Created`

```json
{
  "title": "Article summary",
  "content": "Summarize the following article: {article}",
  "description": "Produces a concise article summary.",
  "collection_id": null,
  "id": "f9a946ea-f9e8-4405-a5f6-2c6ffc6ef230",
  "created_at": "2026-10-05T20:00:00",
  "updated_at": "2026-10-05T20:00:00"
}
```

### Errors

- `400 Bad Request`: A non-null `collection_id` does not identify an existing collection.
- `422 Unprocessable Entity`: The request body does not satisfy the model constraints.

## PUT /prompts/{prompt_id}

Replaces the editable values of an existing prompt. It preserves `id` and `created_at` and refreshes `updated_at`.

`title` and `content` are required. `description` and `collection_id` are optional in the request model, but omission sets them to null rather than preserving their previous values.

### Parameters

- Path parameters:
  - `prompt_id` (string, required): Identifier of the prompt to replace.
- Query parameters: None
- Request body:
  - `title` (string, required): Length from 1 through 200 characters.
  - `content` (string, required): Minimum length of 1 character.
  - `description` (string or null, optional): Maximum length of 500 characters. Omission sets it to null.
  - `collection_id` (string or null, optional): Must identify an existing collection when non-null. Omission sets it to null.

### Request

```bash
curl -X PUT http://localhost:8000/prompts/f9a946ea-f9e8-4405-a5f6-2c6ffc6ef230 -H "Content-Type: application/json" -d '{"title":"Updated summary","content":"Summarize this text in three bullets.","description":null,"collection_id":null}'
```

### Success response

Status: `200 OK`

```json
{
  "title": "Updated summary",
  "content": "Summarize this text in three bullets.",
  "description": null,
  "collection_id": null,
  "id": "f9a946ea-f9e8-4405-a5f6-2c6ffc6ef230",
  "created_at": "2026-10-05T20:00:00",
  "updated_at": "2026-10-05T20:10:00"
}
```

### Errors

- `404 Not Found`: The prompt does not exist.
- `400 Bad Request`: A non-null `collection_id` does not identify an existing collection.
- `422 Unprocessable Entity`: The request body does not satisfy the model constraints.

## PATCH /prompts/{prompt_id}

Partially updates a prompt and refreshes `updated_at`. The implementation uses `model_dump(exclude_unset=True)`, so omitted fields remain unchanged.

An explicit null clears `description` or `collection_id`. Explicit null is rejected for `title` and `content`. An empty JSON object changes no editable fields but still refreshes `updated_at`.

### Parameters

- Path parameters:
  - `prompt_id` (string, required): Identifier of the prompt to update.
- Query parameters: None
- Request body: Any subset of these fields:
  - `title` (string): Length from 1 through 200 characters; cannot be null when supplied.
  - `content` (string): Minimum length of 1 character; cannot be null when supplied.
  - `description` (string or null): Maximum length of 500 characters. Null clears the field.
  - `collection_id` (string or null): A non-null value must identify an existing collection. Null clears the field.

### Request

```bash
curl -X PATCH http://localhost:8000/prompts/f9a946ea-f9e8-4405-a5f6-2c6ffc6ef230 -H "Content-Type: application/json" -d '{"title":"Concise article summary","collection_id":null}'
```

### Success response

Status: `200 OK`

```json
{
  "title": "Concise article summary",
  "content": "Summarize the following article: {article}",
  "description": "Produces a concise article summary.",
  "collection_id": null,
  "id": "f9a946ea-f9e8-4405-a5f6-2c6ffc6ef230",
  "created_at": "2026-10-05T20:00:00",
  "updated_at": "2026-10-05T20:15:00"
}
```

### Errors

- `404 Not Found`: The prompt does not exist.
- `400 Bad Request`: A supplied non-null `collection_id` does not identify an existing collection.
- `422 Unprocessable Entity`: A supplied value violates the patch model, including explicit null for `title` or `content`.

## DELETE /prompts/{prompt_id}

Deletes a prompt.

### Parameters

- Path parameters:
  - `prompt_id` (string, required): Identifier of the prompt to delete.
- Query parameters: None
- Request body: None

### Request

```bash
curl -X DELETE -i http://localhost:8000/prompts/f9a946ea-f9e8-4405-a5f6-2c6ffc6ef230
```

### Success response

Status: `204 No Content`. The response has no body.

### Errors

- `404 Not Found`: The prompt does not exist.

```json
{
  "detail": "Prompt not found"
}
```

## GET /collections

Lists every stored collection.

### Parameters

- Path parameters: None
- Query parameters: None
- Request body: None

### Request

```bash
curl http://localhost:8000/collections
```

### Success response

Status: `200 OK`

```json
{
  "collections": [
    {
      "name": "Writing",
      "description": "Prompts for writing tasks.",
      "id": "4b197cf8-62b5-4600-a60f-8f2e2cb29ec5",
      "created_at": "2026-10-05T19:50:00"
    }
  ],
  "total": 1
}
```

### Errors

No application-defined errors.

## GET /collections/{collection_id}

Returns one collection by its identifier.

### Parameters

- Path parameters:
  - `collection_id` (string, required): Identifier of the collection.
- Query parameters: None
- Request body: None

### Request

```bash
curl http://localhost:8000/collections/4b197cf8-62b5-4600-a60f-8f2e2cb29ec5
```

### Success response

Status: `200 OK`

```json
{
  "name": "Writing",
  "description": "Prompts for writing tasks.",
  "id": "4b197cf8-62b5-4600-a60f-8f2e2cb29ec5",
  "created_at": "2026-10-05T19:50:00"
}
```

### Errors

- `404 Not Found`: The collection does not exist.

```json
{
  "detail": "Collection not found"
}
```

## POST /collections

Creates a collection.

### Parameters

- Path parameters: None
- Query parameters: None
- Request body:
  - `name` (string, required): Length from 1 through 100 characters.
  - `description` (string or null, optional): Maximum length of 500 characters. Defaults to null.

### Request

```bash
curl -X POST http://localhost:8000/collections -H "Content-Type: application/json" -d '{"name":"Writing","description":"Prompts for writing tasks."}'
```

### Success response

Status: `201 Created`

```json
{
  "name": "Writing",
  "description": "Prompts for writing tasks.",
  "id": "4b197cf8-62b5-4600-a60f-8f2e2cb29ec5",
  "created_at": "2026-10-05T19:50:00"
}
```

### Errors

- `422 Unprocessable Entity`: The request body does not satisfy the model constraints.

## DELETE /collections/{collection_id}

Deletes a collection. Before deletion, the API keeps associated prompts, sets their `collection_id` to null, and refreshes their `updated_at` values.

### Parameters

- Path parameters:
  - `collection_id` (string, required): Identifier of the collection to delete.
- Query parameters: None
- Request body: None

### Request

```bash
curl -X DELETE -i http://localhost:8000/collections/4b197cf8-62b5-4600-a60f-8f2e2cb29ec5
```

### Success response

Status: `204 No Content`. The response has no body.

### Errors

- `404 Not Found`: The collection does not exist.

```json
{
  "detail": "Collection not found"
}
```

## Error responses

Application-defined errors use FastAPI's `detail` field:

```json
{
  "detail": "Prompt not found"
}
```

```json
{
  "detail": "Collection not found"
}
```

FastAPI returns `422 Unprocessable Entity` when request validation fails. The exact message depends on the invalid field. A representative response is:

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "title"],
      "msg": "String should have at least 1 character",
      "input": "",
      "ctx": {
        "min_length": 1
      }
    }
  ]
}
```