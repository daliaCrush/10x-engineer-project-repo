# PromptLab System Model

## Purpose and Scope

PromptLab is a FastAPI backend for storing, organizing, searching, and managing reusable AI prompts.

The completed Module 1 backend supports:

- Prompt creation, retrieval, listing, replacement, partial updates, and deletion
- Collection creation, retrieval, listing, and deletion
- Optional relationships between prompts and collections
- Filtering prompts by collection
- Case-insensitive prompt search
- Prompt sorting by creation time
- In-memory storage
- Request validation with Pydantic
- Automated API and utility tests

This document describes the verified system after the Module 1 bug fixes and PATCH implementation.

## Application Startup

The application starts in `backend/main.py`.

When executed directly, it starts Uvicorn with:

- Application: `app.api.app`
- Host: `0.0.0.0`
- Port: `8000`
- Automatic reload: enabled

`backend/app/api.py` creates the FastAPI application using the application version exported by `backend/app/__init__.py`.

The application installs `CORSMiddleware` with all origins, methods, and headers allowed. This is a permissive development configuration and would require tighter restrictions before production use.

## Major Components

| Component | Responsibility |
|---|---|
| `backend/main.py` | Starts the Uvicorn development server. |
| `backend/app/api.py` | Creates the FastAPI application and defines its HTTP endpoints. |
| `backend/app/models.py` | Defines request, stored-resource, and response models using Pydantic. |
| `backend/app/storage.py` | Stores prompts and collections in memory and provides CRUD methods. |
| `backend/app/utils.py` | Provides prompt sorting, filtering, searching, validation, and template-variable extraction. |
| `backend/tests/conftest.py` | Provides test fixtures and resets shared storage between tests. |
| `backend/tests/test_api.py` | Exercises the API and sorting utility through 24 automated tests. |

## General Request Flow

1. Uvicorn receives an HTTP request.
2. `CORSMiddleware` processes applicable cross-origin headers.
3. FastAPI matches the HTTP method and path to a route in `backend/app/api.py`.
4. FastAPI extracts path and query parameters.
5. If the request contains JSON, Pydantic validates it against the declared request model.
6. The route performs any additional resource or collection-reference validation.
7. The route calls utility functions or the global storage instance.
8. The storage layer reads or modifies its in-memory dictionaries.
9. The route returns a result or raises `HTTPException`.
10. FastAPI validates and serializes successful responses through the declared response model.

Invalid Pydantic request bodies return HTTP `422` before the route’s main logic executes.

## API Routes

### Health

| Method | Path | Function | Response | Errors |
|---|---|---|---|---|
| `GET` | `/health` | `health_check()` | `HealthResponse`; HTTP `200` | No explicit error cases |

The response contains:

- `status`: `healthy`
- `version`: current application version

### Prompts

| Method | Path | Function | Request | Success | Errors |
|---|---|---|---|---|---|
| `GET` | `/prompts` | `list_prompts()` | Optional `collection_id` and `search` query parameters | `PromptList`; HTTP `200` | No explicit errors |
| `GET` | `/prompts/{prompt_id}` | `get_prompt()` | Prompt ID path parameter | `Prompt`; HTTP `200` | HTTP `404` when missing |
| `POST` | `/prompts` | `create_prompt()` | `PromptCreate` body | Created `Prompt`; HTTP `201` | HTTP `400` for an invalid collection; HTTP `422` for invalid data |
| `PUT` | `/prompts/{prompt_id}` | `update_prompt()` | Prompt ID and complete `PromptUpdate` body | Updated `Prompt`; HTTP `200` | HTTP `404`, `400`, or `422` |
| `PATCH` | `/prompts/{prompt_id}` | `patch_prompt()` | Prompt ID and partial `PromptPatch` body | Updated `Prompt`; HTTP `200` | HTTP `404`, `400`, or `422` |
| `DELETE` | `/prompts/{prompt_id}` | `delete_prompt()` | Prompt ID path parameter | No body; HTTP `204` | HTTP `404` when missing |

### Collections

| Method | Path | Function | Request | Success | Errors |
|---|---|---|---|---|---|
| `GET` | `/collections` | `list_collections()` | No parameters | `CollectionList`; HTTP `200` | No explicit errors |
| `GET` | `/collections/{collection_id}` | `get_collection()` | Collection ID path parameter | `Collection`; HTTP `200` | HTTP `404` when missing |
| `POST` | `/collections` | `create_collection()` | `CollectionCreate` body | Created `Collection`; HTTP `201` | HTTP `422` for invalid data |
| `DELETE` | `/collections/{collection_id}` | `delete_collection()` | Collection ID path parameter | No body; HTTP `204` | HTTP `404` when missing |

The backend does not currently expose collection update routes.

## Prompt Operations

### Create a Prompt

For `POST /prompts`:

1. FastAPI validates the body as `PromptCreate`.
2. If `collection_id` is non-null, the route verifies that the collection exists.
3. An unknown collection produces HTTP `400`.
4. The route constructs a `Prompt`.
5. Default factories generate its ID and timestamps.
6. `storage.create_prompt()` inserts the prompt into `_prompts`.
7. FastAPI returns the created prompt with HTTP `201`.

### List Prompts

For `GET /prompts`:

1. `storage.get_all_prompts()` retrieves every stored prompt.
2. If `collection_id` was provided, `filter_prompts_by_collection()` retains exact matches.
3. If `search` was provided, `search_prompts()` performs a case-insensitive substring search.
4. `sort_prompts_by_date()` sorts the resulting prompts newest first.
5. The route returns a `PromptList` with the prompts and their count.

Filtering occurs before searching, and sorting occurs after both operations.

An unknown collection ID used as a filter produces an empty list rather than HTTP `404`.

### Retrieve One Prompt

For `GET /prompts/{prompt_id}`:

1. `get_prompt()` calls `storage.get_prompt(prompt_id)`.
2. Storage returns a `Prompt` or `None`.
3. A stored prompt is returned with HTTP `200`.
4. A missing prompt causes the route to raise HTTP `404`.

This behavior fixes the original unhandled `AttributeError`.

### Replace a Prompt

For `PUT /prompts/{prompt_id}`:

1. FastAPI requires a complete `PromptUpdate` body.
2. The route retrieves the existing prompt.
3. A missing prompt produces HTTP `404`.
4. A non-null `collection_id` is validated.
5. An unknown collection produces HTTP `400`.
6. The route constructs a replacement `Prompt`.
7. The existing `id` and `created_at` are preserved.
8. `updated_at` is set using `get_current_time()`.
9. `storage.update_prompt()` replaces the stored prompt.
10. The updated prompt is returned with HTTP `200`.

`PUT` represents a full replacement because `PromptUpdate` requires `title` and `content`.

### Partially Update a Prompt

For `PATCH /prompts/{prompt_id}`:

1. FastAPI validates the body as `PromptPatch`.
2. The route retrieves the existing prompt.
3. A missing prompt produces HTTP `404`.
4. `model_dump(exclude_unset=True)` extracts only explicitly supplied fields.
5. A supplied, non-null `collection_id` is validated.
6. An unknown collection produces HTTP `400`.
7. Existing prompt data is merged with the supplied patch fields.
8. `updated_at` is refreshed.
9. A new validated `Prompt` is constructed.
10. Storage replaces the existing prompt.
11. The updated prompt is returned with HTTP `200`.

PATCH distinguishes omitted fields from explicit `null` values:

- Omitted fields remain unchanged.
- `description: null` clears the description.
- `collection_id: null` detaches the prompt from its collection.
- `title: null` is rejected with HTTP `422`.
- `content: null` is rejected with HTTP `422`.

### Delete a Prompt

For `DELETE /prompts/{prompt_id}`:

1. The route calls `storage.delete_prompt()`.
2. Storage deletes the prompt and returns `True` when it exists.
3. The route returns HTTP `204`.
4. If the prompt is missing, storage returns `False` and the route raises HTTP `404`.

## Collection Operations

### Create a Collection

For `POST /collections`:

1. FastAPI validates the body as `CollectionCreate`.
2. The route constructs a `Collection`.
3. Default factories generate its ID and creation timestamp.
4. Storage adds it to `_collections`.
5. The route returns HTTP `201`.

### Delete a Collection

For `DELETE /collections/{collection_id}`:

1. The route verifies that the collection exists.
2. A missing collection produces HTTP `404`.
3. `storage.get_prompts_by_collection()` finds associated prompts.
4. Each associated prompt is reconstructed with:
   - `collection_id` set to `None`
   - `updated_at` set to the current time
5. Storage replaces each updated prompt.
6. Storage deletes the collection.
7. The route returns HTTP `204`.

Prompts are preserved when their collection is deleted. Clearing their references prevents orphaned collection IDs.

## Data Models

### PromptBase

`PromptBase` defines:

- `title`: required string, 1–200 characters
- `content`: required nonempty string
- `description`: optional string, maximum 500 characters
- `collection_id`: optional string

### PromptCreate

`PromptCreate` inherits all fields from `PromptBase` and is used by `POST /prompts`.

### PromptUpdate

`PromptUpdate` inherits all fields from `PromptBase` and is used by `PUT /prompts/{prompt_id}`.

Because `title` and `content` remain required, it represents a complete update rather than a partial update.

### PromptPatch

`PromptPatch` defines every editable prompt field as optional so clients can send only the fields they want to change.

It uses a Pydantic field validator to reject explicitly supplied null values for:

- `title`
- `content`

The default values allow those fields to be omitted. The endpoint uses `exclude_unset=True` to distinguish omission from explicit null.

### Prompt

`Prompt` extends `PromptBase` with:

- `id`: UUID string generated by `generate_id()`
- `created_at`: timestamp generated by `get_current_time()`
- `updated_at`: timestamp generated by `get_current_time()`

`get_current_time()` currently uses `datetime.utcnow()` and produces a naive UTC `datetime`.

### Collection Models

`CollectionBase` defines:

- `name`: required string, 1–100 characters
- `description`: optional string, maximum 500 characters

`CollectionCreate` inherits the collection input fields.

`Collection` adds:

- `id`: UUID string generated by `generate_id()`
- `created_at`: timestamp generated by `get_current_time()`

### Response Models

- `PromptList` contains `prompts: List[Prompt]` and `total: int`.
- `CollectionList` contains `collections: List[Collection]` and `total: int`.
- `HealthResponse` contains `status: str` and `version: str`.

## Prompt and Collection Relationship

The relationship is represented by `Prompt.collection_id`.

A collection can be referenced by many prompts, while each prompt can reference at most one collection. A prompt may also exist without a collection.

This resembles an optional many-to-one relationship:

- One collection can contain many prompts.
- One prompt can belong to zero or one collection.

The storage layer does not enforce the relationship like a relational database:

- There is no foreign-key constraint.
- Prompt creation, PUT, and PATCH validate collection references in the API layer.
- Direct storage calls can bypass API validation.
- Filtering with an unknown collection ID returns an empty list.
- Collection deletion detaches associated prompts before deleting the collection.

## In-Memory Storage

`backend/app/storage.py` creates one global `Storage` instance named `storage`.

It contains:

- `_prompts: Dict[str, Prompt]`
- `_collections: Dict[str, Collection]`

Objects are keyed by their generated string IDs.

The storage layer provides:

- Prompt creation
- Prompt retrieval
- Prompt listing
- Prompt replacement
- Prompt deletion
- Collection creation
- Collection retrieval
- Collection listing
- Collection deletion
- Prompt lookup by collection
- A `clear()` operation for resetting both dictionaries

The storage layer returns stored Pydantic objects directly. It does not:

- Persist data to disk
- Copy returned resources
- Enforce relationships
- Provide transactions
- Protect concurrent updates
- Share data between multiple application processes

Consequences of in-memory storage include:

- All data disappears when the process restarts.
- Multiple server processes would have separate data.
- Models generate IDs and timestamps before storage.
- Test isolation depends on clearing the global storage instance between tests.

## Utility Behavior

`backend/app/utils.py` contains five utilities:

| Function | Behavior | API usage |
|---|---|---|
| `sort_prompts_by_date()` | Sorts by `created_at` and honors its `descending` argument | Used by `list_prompts()` |
| `filter_prompts_by_collection()` | Keeps prompts whose `collection_id` exactly matches | Used by `list_prompts()` |
| `search_prompts()` | Searches title, content, and description using case-insensitive substring matching | Used by `list_prompts()` |
| `validate_prompt_content()` | Requires at least ten non-whitespace characters | Not currently called by the API |
| `extract_variables()` | Extracts word-character names inside `{{variable}}` patterns | Not currently called by the API |

The API’s Pydantic model requires prompt content to contain at least one character. The stricter `validate_prompt_content()` helper is not currently part of the request flow.

## External Dependencies

Direct dependencies are declared in `backend/requirements.txt`.

| Dependency | Version | Role |
|---|---:|---|
| FastAPI | `0.109.0` | API application, routing, middleware, validation integration, responses, and errors |
| Uvicorn | `0.27.0` | ASGI development server |
| Pydantic | `2.5.3` | Request, resource, and response validation and serialization |
| pytest | `7.4.4` | Test discovery and execution |
| pytest-cov | `4.1.0` | Optional test coverage reporting |
| HTTPX | `0.26.0` | HTTP client used underneath FastAPI/Starlette `TestClient` |

The backend also uses Python standard-library modules including:

- `datetime`
- `re`
- `typing`
- `uuid`

## Testing Model

`backend/tests/conftest.py` supplies:

- A FastAPI `TestClient`
- Sample prompt data
- Sample collection data
- Automatic storage cleanup between tests

Automatic cleanup prevents one test’s in-memory records from leaking into another test.

`backend/tests/test_api.py` contains 24 collected tests covering:

- Health status
- Prompt creation and listing
- Successful and missing prompt retrieval
- Prompt deletion
- Full prompt replacement
- Timestamp updates
- Invalid collection references
- Newest-first endpoint sorting
- Both utility sorting directions
- Partial prompt updates
- Omitted-field preservation
- Explicitly clearing nullable fields
- Rejection of null title and content
- Collection creation and listing
- Missing collections
- Collection deletion and prompt detachment

The verified final result is:

```text
24 passed
```

The test run also emits dependency and standard-library deprecation warnings. These warnings do not represent failed tests.

## Resolved Module 1 Defects

| Requirement | Original behavior | Final behavior | Verification |
|---|---|---|---|
| Missing prompt retrieval | Accessed `.id` on `None`, causing an unhandled exception | Returns HTTP `404` | `test_get_prompt_not_found` |
| PUT timestamp | Preserved the previous `updated_at` | Generates a new timestamp | `test_update_prompt` |
| Prompt sorting | Ignored `descending` and returned oldest first | Honors both sort directions; endpoint returns newest first | Sorting endpoint and utility tests |
| Collection deletion | Left prompts with invalid collection references | Clears `collection_id` and refreshes `updated_at` | `test_delete_collection_with_prompts` |
| Partial updates | PATCH route was absent | PATCH updates only explicitly supplied fields | PATCH test group |

## Current Limitations

The Module 1 backend remains a development system:

- Storage is not persistent.
- There is no authentication or authorization.
- CORS is unrestricted.
- There is no concurrency control.
- There are no database transactions.
- Collection update routes are not implemented.
- Prompt tags and version history are not implemented.
- Prompt template execution is not implemented.
- `datetime.utcnow()` and class-based Pydantic configuration produce deprecation warnings.
- The stricter content-validation helper is not connected to API requests.

These limitations are outside the completed Module 1 bug-fix scope.

## AI-Assisted Context Strategy

The codebase was explored through progressively narrower file-level context rather than unrestricted repository context.

| Iteration | Context | Purpose |
|---|---|---|
| Iteration 1 | README plus backend source, startup, dependency, and test files | Build the initial architecture model |
| Iteration 2 | Directly coupled API, model, storage, utility, and test files | Produce route- and function-level analysis |
| Iteration 3 | Source code and observed test behavior | Correct unsupported assumptions and verify required behavior |
| Implementation | Only files required for each backend change | Limit edits and make each change independently testable |

Generated environments, caches, local configuration, frontend code, and future-module directories were excluded because they were not authoritative sources for the current backend.

AI suggestions were treated as proposals rather than accepted automatically. They were compared with:

- Existing source code
- Pydantic version behavior
- Route semantics
- Git diffs
- Focused tests
- The complete test suite

The detailed iterations are recorded in `docs/prompt-log.md`.

## Verification Basis

This system model was verified against:

- `backend/main.py`
- `backend/app/__init__.py`
- `backend/app/api.py`
- `backend/app/models.py`
- `backend/app/storage.py`
- `backend/app/utils.py`
- `backend/requirements.txt`
- `backend/tests/conftest.py`
- `backend/tests/test_api.py`
- The final pytest run

Final verification:

```text
24 tests collected
24 tests passed
0 tests failed
```