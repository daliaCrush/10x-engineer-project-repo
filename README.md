# PromptLab

**Your AI Prompt Engineering Platform**

PromptLab is an internal tool for AI engineers to store, organize, search, and manage reusable prompts. It is designed as a professional workspace—similar to a “Postman for Prompts.”

The broader PromptLab vision includes:

- Storing prompt templates with variables such as `{{input}}` and `{{context}}`
- Organizing prompts into collections
- Searching prompt titles, content, and descriptions
- Tracking prompt versions
- Testing prompts with sample inputs
- Supporting collaborative prompt-engineering workflows

## Module 1 Backend

The current implementation provides a FastAPI backend with in-memory storage for prompts and collections.

Module 1 includes:

- Prompt creation, retrieval, listing, replacement, partial updates, and deletion
- Collection creation, retrieval, listing, and deletion
- Prompt filtering by collection
- Case-insensitive prompt search
- Newest-first prompt sorting
- Validation of collection references
- Safe collection deletion that detaches associated prompts
- Automated API and utility tests

The storage layer is currently in memory. Data is cleared whenever the application restarts.

## Prerequisites

Install the following tools before running the project:

- Python 3.10 or newer
- Git
- Node.js 18 or newer for later frontend modules

## Clone the Repository

```bash
git clone https://github.com/daliaCrush/10x-engineer-project-repo.git
cd 10x-engineer-project-repo
```

## Backend Setup

### Windows PowerShell

From the repository root:

```powershell
cd backend
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If the virtual environment already exists, activate it with:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
```

### macOS or Linux

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run the Backend

With the virtual environment activated and the terminal inside `backend`:

```bash
python main.py
```

The API is available at:

- API: [http://localhost:8000](http://localhost:8000)
- Interactive API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Alternative API documentation: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

Stop the development server with `Ctrl + C`.

## Run the Tests

With the terminal inside `backend`:

```bash
python -m pytest tests -v
```

The completed Module 1 test suite contains 24 tests covering:

- Health checks
- Prompt CRUD behavior
- Full prompt replacement with `PUT`
- Partial prompt updates with `PATCH`
- Missing-resource responses
- Invalid collection references
- Prompt sorting in both directions
- Collection deletion and prompt detachment
- Explicitly clearing nullable fields
- Validation of required prompt fields

Current verified result:

```text
24 passed
```

The test run may display deprecation warnings from Python, Pydantic, or Starlette dependencies. These warnings do not represent test failures.

## API Endpoints

| Method | Endpoint | Description | Success |
|---|---|---|---:|
| `GET` | `/health` | Check API health | `200` |
| `GET` | `/prompts` | List prompts | `200` |
| `GET` | `/prompts/{prompt_id}` | Retrieve one prompt | `200` |
| `POST` | `/prompts` | Create a prompt | `201` |
| `PUT` | `/prompts/{prompt_id}` | Replace a prompt | `200` |
| `PATCH` | `/prompts/{prompt_id}` | Partially update a prompt | `200` |
| `DELETE` | `/prompts/{prompt_id}` | Delete a prompt | `204` |
| `GET` | `/collections` | List collections | `200` |
| `GET` | `/collections/{collection_id}` | Retrieve one collection | `200` |
| `POST` | `/collections` | Create a collection | `201` |
| `DELETE` | `/collections/{collection_id}` | Delete a collection | `204` |

## List, Filter, and Search Prompts

List all prompts:

```http
GET /prompts
```

Filter prompts by collection:

```http
GET /prompts?collection_id={collection_id}
```

Search prompt titles, content, and descriptions:

```http
GET /prompts?search=review
```

Filters and search can be combined:

```http
GET /prompts?collection_id={collection_id}&search=review
```

Prompt results are returned newest first.

## Update Behavior

### Full replacement with PUT

`PUT /prompts/{prompt_id}` requires the complete editable prompt representation.

Example:

```json
{
  "title": "Updated prompt",
  "content": "Updated prompt content",
  "description": "Updated description",
  "collection_id": null
}
```

A successful update:

- Preserves `id`
- Preserves `created_at`
- Updates `updated_at`
- Validates a non-null `collection_id`

### Partial update with PATCH

`PATCH /prompts/{prompt_id}` changes only fields explicitly included in the request.

Example:

```json
{
  "title": "New title"
}
```

Omitted fields remain unchanged.

The nullable fields `description` and `collection_id` can be cleared explicitly:

```json
{
  "description": null,
  "collection_id": null
}
```

The required fields `title` and `content` cannot be explicitly set to `null`. Invalid requests return HTTP `422`.

## Collection Deletion Behavior

Deleting a collection does not delete its prompts.

When `DELETE /collections/{collection_id}` succeeds:

1. Prompts assigned to the collection remain stored.
2. Their `collection_id` values are changed to `null`.
3. Their `updated_at` timestamps are refreshed.
4. The collection is deleted.

This prevents prompts from retaining invalid collection references.

## Error Responses

The backend returns:

| Situation | Status |
|---|---:|
| Prompt not found | `404` |
| Collection not found | `404` |
| Nonexistent collection supplied for a prompt | `400` |
| Invalid request data | `422` |

Errors use FastAPI’s standard JSON structure:

```json
{
  "detail": "Prompt not found"
}
```

## Project Structure

```text
10x-engineer-project-repo/
├── README.md
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api.py
│   │   ├── models.py
│   │   ├── storage.py
│   │   └── utils.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   └── test_api.py
│   ├── main.py
│   └── requirements.txt
├── docs/
│   ├── SYSTEM_MODEL.md
│   └── prompt-log.md
├── frontend/
├── specs/
└── .gitignore
```

## Backend Components

- `backend/main.py` starts the FastAPI application.
- `backend/app/api.py` defines HTTP routes and request handling.
- `backend/app/models.py` defines Pydantic request and response models.
- `backend/app/storage.py` provides in-memory prompt and collection storage.
- `backend/app/utils.py` provides filtering, searching, and sorting functions.
- `backend/tests/conftest.py` provides isolated test fixtures.
- `backend/tests/test_api.py` verifies endpoint and utility behavior.

## Documentation

- `docs/SYSTEM_MODEL.md` documents the backend architecture and data flow.
- `docs/prompt-log.md` records the AI-assisted development iterations.
- `docs/ai-verification-note.md` records an AI-generated error and how it was identified and corrected.

## Technology Stack

- **Backend:** Python, FastAPI
- **Validation:** Pydantic
- **Server:** Uvicorn
- **Testing:** pytest, FastAPI TestClient, HTTPX
- **Storage:** In-memory Python dictionaries
- **Frontend:** React and Vite planned for a later module
- **DevOps:** Docker and GitHub Actions planned for a later module

## Development Roadmap

### Week 1: Backend Foundation

- Understand the existing codebase
- Fix the four known backend bugs
- Implement partial prompt updates
- Expand automated test coverage

### Week 2: Documentation and Specifications

- Document the system architecture
- Create feature specifications
- Establish coding standards

### Week 3: Production Readiness

- Expand test coverage
- Implement features using test-driven development
- Add CI/CD and Docker support

### Week 4: Frontend

- Build the React frontend
- Connect it to the backend
- Refine the user experience