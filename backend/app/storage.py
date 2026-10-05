"""Provide process-local in-memory storage for PromptLab.

The storage holds prompts and collections for the lifetime of the application
process. Restarting the application clears all stored data.
"""

from typing import Dict, List, Optional

from app.models import Collection, Prompt


class Storage:
    """Manage prompts and collections using process-local memory.

    Attributes:
        _prompts: Prompts stored by prompt identifier.
        _collections: Collections stored by collection identifier.
    """

    def __init__(self):
        """Initialize empty prompt and collection stores."""
        self._prompts: Dict[str, Prompt] = {}
        self._collections: Dict[str, Collection] = {}

    # ============== Prompt Operations ==============

    def create_prompt(self, prompt: Prompt) -> Prompt:
        """Store a prompt.

        Args:
            prompt: Prompt to store.

        Returns:
            The stored prompt.
        """
        self._prompts[prompt.id] = prompt
        return prompt

    def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        """Retrieve a prompt by its identifier.

        Args:
            prompt_id: Identifier of the prompt to retrieve.

        Returns:
            The matching prompt, or None if it does not exist.
        """
        return self._prompts.get(prompt_id)

    def get_all_prompts(self) -> List[Prompt]:
        """Return all stored prompts.

        Returns:
            A list containing all stored prompts.
        """
        return list(self._prompts.values())

    def update_prompt(
        self, prompt_id: str, prompt: Prompt
    ) -> Optional[Prompt]:
        """Replace an existing prompt.

        Args:
            prompt_id: Identifier of the prompt to replace.
            prompt: Replacement prompt.

        Returns:
            The replacement prompt, or None if the identifier does not exist.
        """
        if prompt_id not in self._prompts:
            return None
        self._prompts[prompt_id] = prompt
        return prompt

    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt by its identifier.

        Args:
            prompt_id: Identifier of the prompt to delete.

        Returns:
            True if the prompt was deleted; otherwise, False.
        """
        if prompt_id in self._prompts:
            del self._prompts[prompt_id]
            return True
        return False

    # ============== Collection Operations ==============

    def create_collection(self, collection: Collection) -> Collection:
        """Store a collection.

        Args:
            collection: Collection to store.

        Returns:
            The stored collection.
        """
        self._collections[collection.id] = collection
        return collection

    def get_collection(
        self, collection_id: str
    ) -> Optional[Collection]:
        """Retrieve a collection by its identifier.

        Args:
            collection_id: Identifier of the collection to retrieve.

        Returns:
            The matching collection, or None if it does not exist.
        """
        return self._collections.get(collection_id)

    def get_all_collections(self) -> List[Collection]:
        """Return all stored collections.

        Returns:
            A list containing all stored collections.
        """
        return list(self._collections.values())

    def delete_collection(self, collection_id: str) -> bool:
        """Delete a collection by its identifier.

        This method deletes only the collection. It does not modify prompts
        that reference the collection.

        Args:
            collection_id: Identifier of the collection to delete.

        Returns:
            True if the collection was deleted; otherwise, False.
        """
        if collection_id in self._collections:
            del self._collections[collection_id]
            return True
        return False

    def get_prompts_by_collection(
        self, collection_id: str
    ) -> List[Prompt]:
        """Return prompts assigned to a collection.

        Args:
            collection_id: Identifier of the collection.

        Returns:
            Prompts whose collection identifier matches `collection_id`.
        """
        return [
            prompt
            for prompt in self._prompts.values()
            if prompt.collection_id == collection_id
        ]

    # ============== Utility ==============

    def clear(self):
        """Remove every stored prompt and collection."""
        self._prompts.clear()
        self._collections.clear()


# Global storage instance
storage = Storage()