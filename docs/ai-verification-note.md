# AI Verification Note

## Purpose

This note documents an AI-generated implementation error encountered during PromptLab Module 1, how I verified that it was incorrect, and how I corrected it before accepting the code.

AI output was treated as a proposal requiring verification rather than as an authoritative implementation.

## AI-Assisted Task

I asked Continue to help implement the required `PATCH /prompts/{prompt_id}` endpoint.

The endpoint needed to support true partial-update semantics:

- Omitted fields must remain unchanged.
- `description` and `collection_id` must be clearable with explicit JSON `null`.
- `title` and `content` may be omitted but must reject explicit `null`.
- `updated_at` must change after a successful PATCH.
- A missing prompt must return HTTP 404.
- A nonexistent non-null collection must return HTTP 400.

The project uses Pydantic 2.5.3.

## Incorrect AI Proposal

The first proposal defined every PATCH field as optional and applied updates using checks such as:

```python
if patch_data.title is not None:
    existing.title = patch_data.title

if patch_data.collection_id is not None:
    existing.collection_id = patch_data.collection_id
```

It also proposed a test that sent:

```json
{
  "collection_id": null
}
```

to a prompt that had never been assigned to a collection.

## Why the Proposal Was Incorrect

### Omitted and explicitly null fields were treated identically

With optional fields defaulting to `None`, both of these requests produce a `None` attribute value on the validated request model:

```json
{}
```

```json
{
  "collection_id": null
}
```

Checking only:

```python
patch_data.collection_id is not None
```

cannot determine whether the client omitted the field or explicitly requested that its value be cleared.

The proposed endpoint would therefore ignore `collection_id: null` instead of clearing the collection relationship.

### The proposed test was a false positive

The proposed collection-clearing test created a prompt whose `collection_id` was already `None`.

It then patched the prompt with:

```json
{
  "collection_id": null
}
```

and asserted that the final value was `None`.

That test could pass even if the endpoint completely ignored the PATCH field. It did not establish the non-null precondition needed to prove that clearing worked.

### An intermediate validator used the wrong Pydantic pattern

A revised proposal used Pydantic v1-style validators with forced validation of default values.

That could cause an omitted `title` or `content` field to be processed as the default `None` and rejected, even though omission must be valid during a partial update.

The installed project dependency is Pydantic 2.5.3, so the implementation needed to use Pydantic v2 behavior.

## Verification Process

I verified the proposal against:

- `PromptBase`, `PromptUpdate`, and the proposed `PromptPatch` model
- Pydantic 2.5.3 from `backend/requirements.txt`
- The existing storage update behavior
- The required difference between omission and explicit null
- The initial state created by each proposed test
- Focused pytest results
- The complete pytest suite

I used:

```python
patch_data.model_dump(exclude_unset=True)
```

to retrieve only fields explicitly supplied by the client.

This creates the required distinction:

| Request body | Explicit patch fields |
|---|---|
| `{}` | No fields |
| `{"collection_id": null}` | `collection_id` with value `None` |
| `{"title": "New title"}` | `title` with the supplied string |

## Corrected Implementation

The final `PromptPatch` model uses Pydantic 2’s `field_validator`:

```python
class PromptPatch(BaseModel):
    """Request model for partially updating a prompt."""

    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    content: Optional[str] = Field(
        default=None,
        min_length=1,
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
    )
    collection_id: Optional[str] = None

    @field_validator("title", "content")
    @classmethod
    def reject_null_required_fields(
        cls,
        value: Optional[str],
    ) -> str:
        """Reject explicit null values for required prompt fields."""
        if value is None:
            raise ValueError("Field cannot be null")

        return value
```

The endpoint obtains explicitly supplied values with:

```python
patch_values = patch_data.model_dump(exclude_unset=True)
```

It validates `collection_id` only when the field was supplied and its value is non-null:

```python
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
```

The endpoint then merges the explicit patch fields into the existing prompt data, refreshes `updated_at`, constructs a new validated `Prompt`, and stores it.

## Corrected Test

The corrected collection-clearing test:

1. Creates a real collection.
2. Creates a prompt assigned to that collection.
3. Confirms the initial `collection_id` is non-null.
4. Sends `{"collection_id": null}` through PATCH.
5. Checks the PATCH response.
6. Retrieves the stored prompt again.
7. Confirms the stored `collection_id` is now `None`.

This precondition makes it impossible for an endpoint that ignores the field to pass the test.

Additional PATCH tests verify:

- A title-only patch preserves other fields.
- `updated_at` changes.
- A missing prompt returns HTTP 404.
- A nonexistent non-null collection returns HTTP 400.
- `description` can be explicitly cleared.
- Explicitly null `title` returns HTTP 422.
- Explicitly null `content` returns HTTP 422.

## Additional AI Editing Failure

During one automated editing attempt, Continue inserted route functions before the FastAPI `app` object was defined and duplicated functions already present later in `api.py`.

Pylance reported errors including:

- `"app" is not defined`
- Function declarations obscured by duplicate declarations
- Undefined names
- Optional member access errors

The resulting test run also failed previously working tests.

I rejected those edits and restored the affected files from Git:

```powershell
git restore -- backend/app/api.py backend/app/models.py backend/app/utils.py backend/tests/test_api.py
```

I then reapplied the required changes in smaller, independently reviewed steps.

## Final Verification

I ran focused tests after each bug fix and then ran the complete suite:

```powershell
cd backend
python -m pytest tests -v
```

Final result:

```text
24 tests collected
24 tests passed
0 tests failed
```

I also ran:

```powershell
git diff --check
git status --short
```

`git diff --check` produced no whitespace errors, and Git status showed only the intended project files.

The test run produced deprecation warnings from dependencies and `datetime.utcnow()`. These warnings were reviewed and distinguished from test failures.

## Lessons Learned

This exercise demonstrated that:

1. AI-generated code must be checked against the installed library version.
2. Optional types alone do not provide correct PATCH semantics.
3. Tests need meaningful initial conditions or they can produce false confidence.
4. A passing focused test does not replace running the complete suite.
5. Editor diagnostics and Git diffs are valuable verification tools.
6. Large automated edits are riskier than small, independently tested changes.
7. Existing behavior must be preserved even when a helper is not currently called by an API route.
8. AI output is most useful as a hypothesis or implementation proposal, not as a substitute for engineering judgment.