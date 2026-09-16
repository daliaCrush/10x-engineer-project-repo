"""FastAPI routes for PromptLab."""

from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.models import (
    Collection,
    CollectionCreate,
    CollectionList,
    HealthResponse,
    Prompt,
    PromptCreate,
    PromptList,
    PromptPatch,
    PromptUpdate,
    get_current_time,
)
from app.storage import storage
from app.utils import (
    filter_prompts_by_collection,
    search_prompts,
    sort_prompts_by_date,
)


app = FastAPI(
    title="PromptLab API",
    description="AI Prompt Engineering Platform",
    version=__version__,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Health Check ==============


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return the API health status.

    Returns:
        The current API health status and application version.
    """
    return HealthResponse(status="healthy", version=__version__)


# ============== Prompt Endpoints ==============


@app.get("/prompts", response_model=PromptList)
def list_prompts(
    collection_id: Optional[str] = None,
    search: Optional[str] = None,
) -> PromptList:
    """List prompts, optionally filtering or searching them.

    Args:
        collection_id: Optional collection identifier used to filter prompts.
        search: Optional text used to search prompt content.

    Returns:
        A list of matching prompts sorted newest first.
    """
    prompts = storage.get_all_prompts()

    if collection_id:
        prompts = filter_prompts_by_collection(prompts, collection_id)

    if search:
        prompts = search_prompts(prompts, search)

    prompts = sort_prompts_by_date(prompts, descending=True)

    return PromptList(prompts=prompts, total=len(prompts))


@app.get("/prompts/{prompt_id}", response_model=Prompt)
def get_prompt(prompt_id: str) -> Prompt:
    """Retrieve a prompt by its identifier.

    Args:
        prompt_id: Identifier of the prompt to retrieve.

    Returns:
        The matching prompt.

    Raises:
        HTTPException: If no prompt exists with the supplied identifier.
    """
    prompt = storage.get_prompt(prompt_id)

    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return prompt


@app.post("/prompts", response_model=Prompt, status_code=201)
def create_prompt(prompt_data: PromptCreate) -> Prompt:
    """Create a prompt.

    Args:
        prompt_data: Values for the new prompt.

    Returns:
        The newly created prompt.

    Raises:
        HTTPException: If the referenced collection does not exist.
    """
    if prompt_data.collection_id is not None:
        collection = storage.get_collection(prompt_data.collection_id)
        if collection is None:
            raise HTTPException(
                status_code=400,
                detail="Collection not found",
            )

    prompt = Prompt(**prompt_data.model_dump())
    return storage.create_prompt(prompt)


@app.put("/prompts/{prompt_id}", response_model=Prompt)
def update_prompt(
    prompt_id: str,
    prompt_data: PromptUpdate,
) -> Prompt:
    """Replace an existing prompt with new field values.

    Args:
        prompt_id: Identifier of the prompt to update.
        prompt_data: Complete replacement values for the prompt.

    Returns:
        The updated prompt.

    Raises:
        HTTPException: If the prompt or referenced collection does not exist.
    """
    existing = storage.get_prompt(prompt_id)

    if existing is None:
        raise HTTPException(status_code=404, detail="Prompt not found")

    if prompt_data.collection_id is not None:
        collection = storage.get_collection(prompt_data.collection_id)
        if collection is None:
            raise HTTPException(
                status_code=400,
                detail="Collection not found",
            )

    updated_prompt = Prompt(
        id=existing.id,
        title=prompt_data.title,
        content=prompt_data.content,
        description=prompt_data.description,
        collection_id=prompt_data.collection_id,
        created_at=existing.created_at,
        updated_at=get_current_time(),
    )

    stored_prompt = storage.update_prompt(prompt_id, updated_prompt)

    if stored_prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return stored_prompt


@app.patch("/prompts/{prompt_id}", response_model=Prompt)
def patch_prompt(
    prompt_id: str,
    patch_data: PromptPatch,
) -> Prompt:
    """Partially update an existing prompt.

    Args:
        prompt_id: Identifier of the prompt to update.
        patch_data: Prompt fields explicitly supplied for updating.

    Returns:
        The updated prompt.

    Raises:
        HTTPException: If the prompt or referenced collection does not exist.
    """
    existing = storage.get_prompt(prompt_id)

    if existing is None:
        raise HTTPException(status_code=404, detail="Prompt not found")

    patch_values = patch_data.model_dump(exclude_unset=True)

    if (
        "collection_id" in patch_values
        and patch_values["collection_id"] is not None
    ):
        collection = storage.get_collection(
            patch_values["collection_id"]
        )
        if collection is None:
            raise HTTPException(
                status_code=400,
                detail="Collection not found",
            )

    updated_data = existing.model_dump()
    updated_data.update(patch_values)
    updated_data["updated_at"] = get_current_time()

    updated_prompt = Prompt(**updated_data)
    stored_prompt = storage.update_prompt(prompt_id, updated_prompt)

    if stored_prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return stored_prompt


@app.delete("/prompts/{prompt_id}", status_code=204)
def delete_prompt(prompt_id: str) -> None:
    """Delete a prompt by its identifier.

    Args:
        prompt_id: Identifier of the prompt to delete.

    Raises:
        HTTPException: If the prompt does not exist.
    """
    if not storage.delete_prompt(prompt_id):
        raise HTTPException(status_code=404, detail="Prompt not found")

    return None


# ============== Collection Endpoints ==============


@app.get("/collections", response_model=CollectionList)
def list_collections() -> CollectionList:
    """List all collections.

    Returns:
        All stored collections and their total count.
    """
    collections = storage.get_all_collections()
    return CollectionList(
        collections=collections,
        total=len(collections),
    )


@app.get("/collections/{collection_id}", response_model=Collection)
def get_collection(collection_id: str) -> Collection:
    """Retrieve a collection by its identifier.

    Args:
        collection_id: Identifier of the collection to retrieve.

    Returns:
        The matching collection.

    Raises:
        HTTPException: If the collection does not exist.
    """
    collection = storage.get_collection(collection_id)

    if collection is None:
        raise HTTPException(
            status_code=404,
            detail="Collection not found",
        )

    return collection


@app.post("/collections", response_model=Collection, status_code=201)
def create_collection(
    collection_data: CollectionCreate,
) -> Collection:
    """Create a collection.

    Args:
        collection_data: Values for the new collection.

    Returns:
        The newly created collection.
    """
    collection = Collection(**collection_data.model_dump())
    return storage.create_collection(collection)


@app.delete("/collections/{collection_id}", status_code=204)
def delete_collection(collection_id: str) -> None:
    """Delete a collection and detach its associated prompts.

    Args:
        collection_id: Identifier of the collection to delete.

    Raises:
        HTTPException: If the collection does not exist.
    """
    collection = storage.get_collection(collection_id)

    if collection is None:
        raise HTTPException(
            status_code=404,
            detail="Collection not found",
        )

    prompts = storage.get_prompts_by_collection(collection_id)

    for prompt in prompts:
        prompt_data = prompt.model_dump()
        prompt_data["collection_id"] = None
        prompt_data["updated_at"] = get_current_time()

        updated_prompt = Prompt(**prompt_data)
        storage.update_prompt(prompt.id, updated_prompt)

    storage.delete_collection(collection_id)
    return None