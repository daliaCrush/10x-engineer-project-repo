# Agent Instruction Effect Note

## Purpose

This note records a controlled before-and-after comparison showing how PromptLab-specific agent instructions affected an AI-generated documentation response.

Both trials used Continue in Plan mode, started in separate chats, and used the exact same prompt. Neither trial modified application files.

## Test Prompt

```text
Without modifying any files, draft a Google-style docstring for backend/app/api.py::patch_prompt. Base it only on the current implementation. Include Args, Returns, Raises, and the important PATCH semantics. Output only the proposed docstring.
```

## Before Project Instructions

At the time of the first trial, neither `.continuerules` nor `.github/copilot-instructions.md` existed.

Continue produced:

```python
"""
Partially update an existing prompt.

This endpoint allows partial updates to a prompt by specifying only the fields that need to be modified.
If a field is not included in the request, it will remain unchanged.

Args:
    prompt_id (str): Identifier of the prompt to update.
    patch_data (PromptPatch): The prompt fields explicitly supplied for updating.
        Only the fields provided in this model will be updated.

Returns:
    Prompt: The updated prompt instance with the latest values and updated timestamp.

Raises:
    HTTPException: If the prompt with the given identifier does not exist (404).
    HTTPException: If the referenced collection does not exist when updating the `collection_id` (400).
"""
```

## Project Instructions Added

A repository-level `.continuerules` file was added with PromptLab-specific guidance covering:

- The existing FastAPI and in-memory-storage architecture.
- Preservation of established routes, response models, status codes, and error behavior.
- True partial-update semantics.
- The distinction between omitted fields and explicitly supplied `null`.
- Required and optional field behavior.
- Google-style docstrings.
- Focused changes and test verification.

## After Project Instructions

A new Continue chat was opened after `.continuerules` was added. The identical test prompt produced:

```python
"""
Partially update an existing prompt.

This endpoint permits updates to a prompt by specifying only the fields that need to be changed.
If a field is explicitly set to `null`, it will not be allowed for required fields. The prompt's
`updated_at` timestamp will be updated to reflect the time of the modification.

Args:
    prompt_id (str): Identifier of the prompt to update.
    patch_data (PromptPatch): The fields for the prompt that are supplied for updating.
        Only fields explicitly included will be modified.

Returns:
    Prompt: The updated prompt instance with the preserved and modified values, including
    an updated `updated_at` timestamp.

Raises:
    HTTPException: If the prompt with the specified identifier does not exist (404).
    HTTPException: If the referenced collection does not exist (400).
"""
```

## Observed Effect

The response produced after adding `.continuerules` incorporated an important project-specific validation rule that the original response omitted: explicitly supplied `null` values are not accepted for required fields. It also emphasized preservation of unchanged values and the update of the `updated_at` timestamp.

The comparison demonstrates that repository-level instructions made the response more closely reflect PromptLab's PATCH contract.

## Human Verification

The second response was more specific, but it was not complete. It did not explain that optional fields such as `description` and `collection_id` may be explicitly cleared with `null`. Therefore, the AI response still requires comparison with the implementation, request models, and tests before being placed in the source code.

This experiment shows that project instructions improve relevance and consistency, but they do not replace developer verification.