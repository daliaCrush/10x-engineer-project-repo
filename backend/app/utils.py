"""Utility functions for filtering, searching, and sorting prompts."""

from typing import List

from app.models import Prompt


def sort_prompts_by_date(
    prompts: List[Prompt],
    descending: bool = True,
) -> List[Prompt]:
    """Sort prompts by creation time.

    Args:
        prompts: Prompts to sort.
        descending: Whether to return newest prompts first.

    Returns:
        A new list sorted by each prompt's creation time.
    """
    return sorted(
        prompts,
        key=lambda prompt: prompt.created_at,
        reverse=descending,
    )


def filter_prompts_by_collection(
    prompts: List[Prompt],
    collection_id: str,
) -> List[Prompt]:
    """Filter prompts by collection identifier.

    Args:
        prompts: Prompts to filter.
        collection_id: Collection identifier to match.

    Returns:
        Prompts belonging to the specified collection.
    """
    return [
        prompt
        for prompt in prompts
        if prompt.collection_id == collection_id
    ]


def search_prompts(
    prompts: List[Prompt],
    query: str,
) -> List[Prompt]:
    """Search prompt titles, content, and descriptions.

    Args:
        prompts: Prompts to search.
        query: Case-insensitive search text.

    Returns:
        Prompts containing the search text in a searchable field.
    """
    normalized_query = query.lower()

    return [
        prompt
        for prompt in prompts
        if normalized_query in prompt.title.lower()
        or normalized_query in prompt.content.lower()
        or (
            prompt.description is not None
            and normalized_query in prompt.description.lower()
        )
    ]