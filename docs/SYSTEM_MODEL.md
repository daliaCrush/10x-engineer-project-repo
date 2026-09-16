# PromptLab System Model

## Purpose and scope

PromptLab is a FastAPI backend for storing and organizing AI prompt templates. It currently supports prompts, optional prompt collections, filtering, searching, and in-memory CRUD operations.

This document describes the application’s current behavior before the Module 1 bug fixes. Required behavior that has not yet been implemented is identified separately so it is not confused with working behavior.

## Application startup

The application starts in `backend/main.py`.

When the file is executed directly, it starts Uvicorn with:

* Application: `app.api.app`
* Host: `0.0.0.0`
* Port: `8000`
* Automatic reload: enabled

`backend/app/api.py` creates the FastAPI application using version `0.1.0` from `backend/app/__init__.py`.

The application installs `CORSMiddleware` with all origins, methods, and headers allowed. This is a permissive development configuration.

## Major components

| Component                   | Responsibility                                                                                             |
| --------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `backend/main.py`           | Starts the Uvicorn development server.                                                                     |
| `backend/app/api.py`        | Creates the FastAPI application and defines every HTTP endpoint.                                           |
| `backend/app/models.py`     | Defines request, stored-resource, and response models with Pydantic. It also generates IDs and timestamps. |
| `backend/app/storage.py`    | Stores prompts and collections in memory and provides CRUD methods.                                        |
| `backend/app/utils.py`      | Provides prompt sorting, filtering, searching, content validation, and variable extraction utilities.      |
| `backend/tests/conftest.py` | Provides test fixtures and resets shared storage between tests.                                            |
| `backend/tests/test_api.py` | Exercises the API through FastAPI’s `TestClient`.                                                          |

## API routes

### Health route

| Method | Path      | Function         | Request               | Storage or utility calls | Response                   | Current errors          |
| ------ | --------- | ---------------- | --------------------- | ------------------------ | -------------------------- | ----------------------- |
| GET    | `/health` | `health_check()` | No body or parameters | None                     | `HealthResponse`; HTTP 200 | No explicit error cases |

`health_check()` returns a status of `healthy` and the application version.

### Prompt routes

| Method | Path                   | Function          | Request                                                  | Storage and utility calls                                                                                                                      | Success response              | Current errors                                                                                                                                                                               |
| ------ | ---------------------- | ----------------- | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GET    | `/prompts`             | `list_prompts()`  | Optional `collection_id` and `search` query parameters   | `storage.get_all_prompts()`, optionally `filter_prompts_by_collection()` and `search_prompts()`, followed by `sort_prompts_by_date()`          | `PromptList`; HTTP 200        | No explicit errors. An unknown collection ID produces an empty list.                                                                                                                         |
| GET    | `/prompts/{prompt_id}` | `get_prompt()`    | String `prompt_id` path parameter                        | `storage.get_prompt()`                                                                                                                         | `Prompt`; HTTP 200 when found | A missing prompt causes an unhandled `AttributeError` when the function accesses `prompt.id`. A running server would ordinarily return HTTP 500; the test client can re-raise the exception. |
| POST   | `/prompts`             | `create_prompt()` | `PromptCreate` JSON body                                 | If `collection_id` is truthy, `storage.get_collection()` validates it. The endpoint constructs a `Prompt` and calls `storage.create_prompt()`. | Created `Prompt`; HTTP 201    | HTTP 400 when the referenced collection does not exist; HTTP 422 when Pydantic request validation fails.                                                                                     |
| PUT    | `/prompts/{prompt_id}` | `update_prompt()` | String `prompt_id` and complete `PromptUpdate` JSON body | `storage.get_prompt()`, optional `storage.get_collection()`, construction of a replacement `Prompt`, and `storage.update_prompt()`             | Updated `Prompt`; HTTP 200    | HTTP 404 when the prompt does not exist; HTTP 400 when a referenced collection does not exist; HTTP 422 when request validation fails.                                                       |
| DELETE | `/prompts/{prompt_id}` | `delete_prompt()` | String `prompt_id` path parameter                        | `storage.delete_prompt()`                                                                                                                      | No body; HTTP 204             | HTTP 404 when the prompt does not exist.                                                                                                                                                     |

The application does not currently expose `PATCH /prompts/{prompt_id}`.

### Collection routes

| Method | Path                           | Function              | Request                               | Storage calls                                                     | Success response               | Current errors                                                                                         |
| ------ | ------------------------------ | --------------------- | ------------------------------------- | ----------------------------------------------------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------ |
| GET    | `/collections`                 | `list_collections()`  | No body or parameters                 | `storage.get_all_collections()`                                   | `CollectionList`; HTTP 200     | No explicit errors                                                                                     |
| GET    | `/collections/{collection_id}` | `get_collection()`    | String `collection_id` path parameter | `storage.get_collection()`                                        | `Collection`; HTTP 200         | HTTP 404 when the collection does not exist                                                            |
| POST   | `/collections`                 | `create_collection()` | `CollectionCreate` JSON body          | Constructs a `Collection` and calls `storage.create_collection()` | Created `Collection`; HTTP 201 | HTTP 422 when Pydantic request validation fails                                                        |
| DELETE | `/collections/{collection_id}` | `delete_collection()` | String `collection_id` path parameter | `storage.delete_collection()`                                     | No body; HTTP 204              | HTTP 404 when the collection does not exist. Prompts assigned to a deleted collection are not updated. |

There are no collection update or partial-update routes.

## Request-to-response flow

### General request flow

1. Uvicorn receives the HTTP request and passes it to the FastAPI application.
2. `CORSMiddleware` processes applicable cross-origin request and response headers.
3. FastAPI matches the HTTP method and path to an endpoint in `backend/app/api.py`.
4. FastAPI extracts path and query parameters and uses the Pydantic model declared by the endpoint to validate a request body when one is present.
5. The endpoint performs any additional collection-reference validation.
6. The endpoint calls utility functions or the global storage instance as required.
7. The storage layer reads or changes its in-memory dictionaries and returns a model, list, Boolean result, or `None`.
8. The endpoint returns its result or raises `HTTPException`.
9. FastAPI validates and serializes successful data through the declared response model. Delete operations return HTTP 204 with no response body.

Invalid Pydantic request bodies are rejected with HTTP 422 before the endpoint’s main logic executes.

### Creating a prompt

For `POST /prompts`:

1. FastAPI validates the JSON body as `PromptCreate`.
2. If `collection_id` is truthy, `create_prompt()` checks it with `storage.get_collection()`.
3. An unknown collection causes HTTP 400.
4. The endpoint constructs a `Prompt` from the validated request.
5. `Prompt` default factories generate a UUID string, `created_at`, and `updated_at`.
6. `storage.create_prompt()` inserts the object into `_prompts`, keyed by its ID.
7. FastAPI serializes the object as `Prompt` and returns HTTP 201.

### Listing prompts

For `GET /prompts`:

1. `list_prompts()` retrieves every prompt through `storage.get_all_prompts()`.
2. If `collection_id` was provided, `filter_prompts_by_collection()` retains prompts whose `collection_id` exactly matches it.
3. The endpoint does not verify that the requested collection exists. A nonexistent ID therefore produces an empty result.
4. If `search` was provided, `search_prompts()` performs a case-insensitive substring search against each prompt’s title and optional description.
5. `sort_prompts_by_date()` is called with `descending=True`.
6. The current utility ignores that argument and sorts by `created_at` in ascending order.
7. The endpoint returns `PromptList`, containing the resulting list and its length as `total`.

Filtering occurs before searching, and sorting occurs after both operations.

### Retrieving one prompt

For `GET /prompts/{prompt_id}`:

1. `get_prompt()` calls `storage.get_prompt(prompt_id)`.
2. The storage method performs a dictionary lookup and returns a `Prompt` or `None`.
3. When a prompt exists, the endpoint returns it.
4. When it does not exist, the endpoint accesses `.id` on `None`.
5. This raises an unhandled `AttributeError` instead of the required HTTP 404 response.

### Replacing a prompt

For `PUT /prompts/{prompt_id}`:

1. FastAPI requires a complete `PromptUpdate` body.
2. `update_prompt()` retrieves the existing prompt.
3. A missing prompt produces HTTP 404.
4. If the submitted `collection_id` is truthy, the endpoint verifies that the collection exists.
5. An unknown collection produces HTTP 400.
6. The endpoint creates a replacement `Prompt`, preserving the existing ID and `created_at`.
7. The current implementation also preserves the old `updated_at`, which is a bug.
8. `storage.update_prompt()` replaces the dictionary entry.
9. FastAPI returns the updated prompt with HTTP 200.

`PromptUpdate` inherits `PromptBase`, so `title` and `content` are required. It supports full replacement but cannot provide true partial-update behavior.

### Deleting a prompt

For `DELETE /prompts/{prompt_id}`:

1. `delete_prompt()` calls `storage.delete_prompt()`.
2. Storage removes the dictionary entry and returns `True` when the ID exists.
3. The endpoint returns HTTP 204.
4. If the ID is absent, storage returns `False` and the endpoint raises HTTP 404.

### Deleting a collection

For `DELETE /collections/{collection_id}`:

1. `delete_collection()` calls `storage.delete_collection()`.
2. Storage removes the collection when it exists.
3. A missing collection produces HTTP 404.
4. The endpoint returns HTTP 204 after a successful deletion.
5. No code finds or updates prompts that reference the deleted collection.
6. Those prompts remain in `_prompts` with a `collection_id` that no longer resolves to a collection.

## Data models

### Prompt models

`PromptBase` defines:

* `title`: required string, 1–200 characters
* `content`: required nonempty string
* `description`: optional string, maximum 500 characters
* `collection_id`: optional string

`PromptCreate` inherits all fields from `PromptBase`.

`PromptUpdate` also inherits all fields from `PromptBase`. It therefore requires `title` and `content` and represents a complete update rather than a partial update.

`Prompt` adds:

* `id`: UUID string generated by `generate_id()`
* `created_at`: generated by `get_current_time()`
* `updated_at`: generated by `get_current_time()`

`get_current_time()` uses `datetime.utcnow()` and returns a naive UTC `datetime`.

### Collection models

`CollectionBase` defines:

* `name`: required string, 1–100 characters
* `description`: optional string, maximum 500 characters

`CollectionCreate` inherits the collection input fields.

`Collection` adds:

* `id`: generated UUID string
* `created_at`: generated timestamp

### List and health models

* `PromptList` contains `prompts: List[Prompt]` and `total: int`.
* `CollectionList` contains `collections: List[Collection]` and `total: int`.
* `HealthResponse` contains `status: str` and `version: str`.

## Prompt and collection relationship

The relationship is represented only by the optional `Prompt.collection_id` string.

A collection can be referenced by many prompts, while each prompt can reference at most one collection. A prompt can also exist without a collection.

This resembles an optional many-to-one relationship, but the storage layer does not enforce it like a relational database would:

* There is no foreign-key constraint.
* Prompt creation and full update perform collection checks in the API layer.
* Direct storage calls can insert a prompt containing any collection ID.
* Listing by an unknown collection ID returns an empty list.
* Deleting a collection does not delete its prompts or set their `collection_id` fields to `None`.

The current behavior can therefore create orphaned prompt references.

## In-memory storage

`backend/app/storage.py` creates one global `Storage` instance named `storage`.

The instance contains:

* `_prompts: Dict[str, Prompt]`
* `_collections: Dict[str, Collection]`

Objects are keyed by their generated string IDs.

The storage methods provide:

* Prompt creation, retrieval, listing, replacement, and deletion
* Collection creation, retrieval, listing, and deletion
* Prompt lookup by collection
* A `clear()` operation used to empty both dictionaries

The layer returns stored Pydantic objects directly. It does not copy them, persist them to disk, enforce relationships, provide transactions, or protect concurrent changes.

Because storage is process memory:

* All data disappears when the application restarts.
* Multiple server processes would not share the same data.
* IDs and timestamps are created by the models before objects enter storage.
* Test isolation depends on clearing the global storage instance between tests.

## Utility behavior

`backend/app/utils.py` contains five utilities:

| Function                         | Current behavior                                                               | API usage                     |
| -------------------------------- | ------------------------------------------------------------------------------ | ----------------------------- |
| `sort_prompts_by_date()`         | Sorts by `created_at` in ascending order and ignores its `descending` argument | Used by `list_prompts()`      |
| `filter_prompts_by_collection()` | Keeps prompts with an exactly matching `collection_id`                         | Used by `list_prompts()`      |
| `search_prompts()`               | Performs case-insensitive substring matching against title and description     | Used by `list_prompts()`      |
| `validate_prompt_content()`      | Rejects empty, whitespace-only, or fewer-than-ten-character content            | Not called by the current API |
| `extract_variables()`            | Extracts word-character names contained in `{{variable}}` patterns             | Not called by the current API |

Although `validate_prompt_content()` requires ten non-whitespace characters, the Pydantic model currently requires only one character. Because the API does not call the utility, one-character content is currently accepted.

## External dependencies

The direct dependencies are declared in `backend/requirements.txt`.

| Dependency |   Version | Role                                                                                                                                                                    |
| ---------- | --------: | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FastAPI    | `0.109.0` | Defines the API application, routes, middleware integration, request handling, response models, `HTTPException`, and `TestClient` interface.                            |
| Uvicorn    |  `0.27.0` | Runs the FastAPI application as an ASGI server from `backend/main.py`.                                                                                                  |
| Pydantic   |   `2.5.3` | Defines and validates request, resource, and response models. It also serializes model data through `model_dump()`.                                                     |
| pytest     |   `7.4.4` | Discovers and executes the backend test suite and fixtures.                                                                                                             |
| pytest-cov |   `4.1.0` | Adds pytest coverage-reporting support when tests are run with coverage options.                                                                                        |
| httpx      |  `0.26.0` | Provides the HTTP client used underneath Starlette/FastAPI `TestClient` during API tests. `test_api.py` does not import it directly, but test requests pass through it. |

The backend also uses Python standard-library modules including `datetime`, `typing`, `uuid`, and `re`. These are not external packages and do not appear in `requirements.txt`.

## Context strategy

I used file-level context throughout the exploration rather than sending the unrestricted repository to the AI.

| Exploration stage                      | Context approach                                                                                                        | Reason                                                                                                                                                                                                                                                                                                                                                   |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Iteration 1: architecture discovery    | A selected file-level batch containing `README.md` and the complete backend source, dependency, startup, and test files | The backend is small and tightly coupled, so reading all relevant backend files was necessary to understand routes, models, storage, utilities, dependencies, and tests together. Generated directories, future frontend/spec directories, documentation, and configuration files were excluded because they could not explain current backend behavior. |
| Iteration 2: function-level correction | Narrowed file-level context containing the application modules, tests, and dependency file                              | The first response found the broad structure but omitted exact parameters, calls, errors, and test weaknesses. Restricting the context to directly coupled implementation and test files made a route-by-route comparison possible.                                                                                                                      |
| Iteration 3: evidence verification     | A tightly bounded file-level set containing startup, API, models, storage, utilities, tests, and dependencies           | The final pass was intended to distinguish current implementation behavior from required behavior. The README was excluded because source code and observed test behavior were the authoritative evidence for this stage.                                                                                                                                |

Whole-repository context was unnecessary because the repository contains directories for later modules and generated environment files unrelated to the current backend. The selected backend files are small enough to inspect together, while repeated narrowing made it easier to verify individual claims directly against functions and tests.

This strategy matches the progression recorded in `docs/prompt-log.md`: broad backend discovery, focused function-level analysis, and a final evidence-checking pass.

## Verified defects and missing behavior

The current source contains four required defects and one missing endpoint:

1. `get_prompt()` fails with an unhandled exception when the prompt does not exist instead of raising HTTP 404.
2. `update_prompt()` preserves the previous `updated_at` timestamp instead of generating a new one.
3. `sort_prompts_by_date()` ignores `descending=True`, producing oldest-first results.
4. `delete_collection()` leaves prompts referencing the deleted collection.
5. `PATCH /prompts/{prompt_id}` is absent, and the existing `PromptUpdate` model requires fields that must be optional for a true partial update.

These statements describe the current implementation. The document must be reviewed and updated after the Module 1 fixes so the submitted system model matches the final code.

## Verification basis

This model was verified against:

* Route decorators and endpoint functions in `backend/app/api.py`
* Model definitions and default factories in `backend/app/models.py`
* Dictionary operations in `backend/app/storage.py`
* Utility implementations in `backend/app/utils.py`
* Server startup in `backend/main.py`
* Versions in `backend/app/__init__.py`
* Direct dependencies in `backend/requirements.txt`
* Fixtures and behavior in `backend/tests/conftest.py`
* Existing tests and baseline pytest behavior in `backend/tests/test_api.py`

The baseline test run produced 10 passing tests and 3 failing tests. AI-generated observations were treated as hypotheses and corrected whenever they conflicted with source code or observed test behavior.
