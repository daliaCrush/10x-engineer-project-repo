"""API tests for PromptLab."""

import time
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.models import Prompt
from app.utils import sort_prompts_by_date


class TestHealth:
    """Tests for the health endpoint."""

    def test_health_check(self, client: TestClient):
        """Verify that the health endpoint reports a healthy API."""
        response = client.get("/health")

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestPrompts:
    """Tests for prompt endpoints and utilities."""

    def test_create_prompt(
        self,
        client: TestClient,
        sample_prompt_data,
    ):
        """Verify that a prompt can be created."""
        response = client.post(
            "/prompts",
            json=sample_prompt_data,
        )

        assert response.status_code == 201

        data = response.json()
        assert data["title"] == sample_prompt_data["title"]
        assert data["content"] == sample_prompt_data["content"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_list_prompts_empty(self, client: TestClient):
        """Verify that an empty prompt list is returned initially."""
        response = client.get("/prompts")

        assert response.status_code == 200

        data = response.json()
        assert data["prompts"] == []
        assert data["total"] == 0

    def test_list_prompts_with_data(
        self,
        client: TestClient,
        sample_prompt_data,
    ):
        """Verify that stored prompts appear in the prompt list."""
        client.post("/prompts", json=sample_prompt_data)

        response = client.get("/prompts")

        assert response.status_code == 200

        data = response.json()
        assert len(data["prompts"]) == 1
        assert data["total"] == 1

    def test_get_prompt_success(
        self,
        client: TestClient,
        sample_prompt_data,
    ):
        """Verify that an existing prompt can be retrieved."""
        create_response = client.post(
            "/prompts",
            json=sample_prompt_data,
        )
        prompt_id = create_response.json()["id"]

        response = client.get(f"/prompts/{prompt_id}")

        assert response.status_code == 200
        assert response.json()["id"] == prompt_id

    def test_get_prompt_not_found(self, client: TestClient):
        """Verify that requesting a missing prompt returns HTTP 404."""
        response = client.get("/prompts/nonexistent-id")

        assert response.status_code == 404
        assert response.json()["detail"] == "Prompt not found"

    def test_delete_prompt(
        self,
        client: TestClient,
        sample_prompt_data,
    ):
        """Verify that a prompt can be deleted."""
        create_response = client.post(
            "/prompts",
            json=sample_prompt_data,
        )
        prompt_id = create_response.json()["id"]

        delete_response = client.delete(f"/prompts/{prompt_id}")

        assert delete_response.status_code == 204

        get_response = client.get(f"/prompts/{prompt_id}")
        assert get_response.status_code == 404

    def test_update_prompt(
        self,
        client: TestClient,
        sample_prompt_data,
    ):
        """Verify that PUT replaces a prompt and updates its timestamp."""
        create_response = client.post(
            "/prompts",
            json=sample_prompt_data,
        )
        original = create_response.json()
        prompt_id = original["id"]

        updated_data = {
            "title": "Updated Title",
            "content": "Updated content for the prompt",
            "description": "Updated description",
            "collection_id": None,
        }

        time.sleep(0.1)

        response = client.put(
            f"/prompts/{prompt_id}",
            json=updated_data,
        )

        assert response.status_code == 200

        updated = response.json()
        assert updated["id"] == original["id"]
        assert updated["title"] == updated_data["title"]
        assert updated["content"] == updated_data["content"]
        assert updated["description"] == updated_data["description"]
        assert updated["collection_id"] is None
        assert updated["created_at"] == original["created_at"]
        assert updated["updated_at"] != original["updated_at"]

    def test_update_prompt_not_found(
        self,
        client: TestClient,
        sample_prompt_data,
    ):
        """Verify that updating a missing prompt returns HTTP 404."""
        response = client.put(
            "/prompts/nonexistent-id",
            json=sample_prompt_data,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Prompt not found"

    def test_update_prompt_collection_not_found(
        self,
        client: TestClient,
        sample_prompt_data,
    ):
        """Verify that PUT rejects a nonexistent collection."""
        create_response = client.post(
            "/prompts",
            json=sample_prompt_data,
        )
        prompt_id = create_response.json()["id"]

        updated_data = {
            **sample_prompt_data,
            "collection_id": "nonexistent-collection-id",
        }

        response = client.put(
            f"/prompts/{prompt_id}",
            json=updated_data,
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Collection not found"

    def test_sorting_order(self, client: TestClient):
        """Verify that the prompt endpoint returns newest prompts first."""
        first_prompt = {
            "title": "First",
            "content": "First prompt content",
        }
        second_prompt = {
            "title": "Second",
            "content": "Second prompt content",
        }

        client.post("/prompts", json=first_prompt)
        time.sleep(0.1)
        client.post("/prompts", json=second_prompt)

        response = client.get("/prompts")

        assert response.status_code == 200

        prompts = response.json()["prompts"]
        assert [prompt["title"] for prompt in prompts] == [
            "Second",
            "First",
        ]

    def test_sorting_utility_respects_direction(self):
        """Verify that the sorting utility honors both directions."""
        older = Prompt(
            title="Older",
            content="Older prompt content",
            description=None,
            created_at=datetime(2026, 1, 1),
        )
        newer = Prompt(
            title="Newer",
            content="Newer prompt content",
            description=None,
            created_at=datetime(2026, 1, 2),
        )

        descending = sort_prompts_by_date(
            [older, newer],
            descending=True,
        )
        ascending = sort_prompts_by_date(
            [newer, older],
            descending=False,
        )

        assert [prompt.title for prompt in descending] == [
            "Newer",
            "Older",
        ]
        assert [prompt.title for prompt in ascending] == [
            "Older",
            "Newer",
        ]

    def test_patch_prompt_title_only(
        self,
        client: TestClient,
        sample_prompt_data,
    ):
        """Verify that PATCH changes only explicitly supplied fields."""
        create_response = client.post(
            "/prompts",
            json=sample_prompt_data,
        )
        original = create_response.json()
        prompt_id = original["id"]

        time.sleep(0.1)

        response = client.patch(
            f"/prompts/{prompt_id}",
            json={"title": "New Title"},
        )

        assert response.status_code == 200

        updated = response.json()
        assert updated["id"] == original["id"]
        assert updated["title"] == "New Title"
        assert updated["content"] == original["content"]
        assert updated["description"] == original["description"]
        assert updated["collection_id"] == original["collection_id"]
        assert updated["created_at"] == original["created_at"]
        assert updated["updated_at"] != original["updated_at"]

    def test_patch_prompt_not_found(self, client: TestClient):
        """Verify that patching a missing prompt returns HTTP 404."""
        response = client.patch(
            "/prompts/nonexistent-id",
            json={"title": "New Title"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Prompt not found"

    def test_patch_prompt_collection_not_found(
        self,
        client: TestClient,
        sample_prompt_data,
    ):
        """Verify that PATCH rejects a nonexistent collection."""
        create_response = client.post(
            "/prompts",
            json=sample_prompt_data,
        )
        prompt_id = create_response.json()["id"]

        response = client.patch(
            f"/prompts/{prompt_id}",
            json={
                "collection_id": "nonexistent-collection-id",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Collection not found"

    def test_patch_prompt_clear_collection_id(
        self,
        client: TestClient,
        sample_collection_data,
        sample_prompt_data,
    ):
        """Verify that PATCH can explicitly clear collection_id."""
        collection_response = client.post(
            "/collections",
            json=sample_collection_data,
        )
        collection_id = collection_response.json()["id"]

        prompt_data = {
            **sample_prompt_data,
            "collection_id": collection_id,
        }
        create_response = client.post(
            "/prompts",
            json=prompt_data,
        )
        original = create_response.json()
        prompt_id = original["id"]

        assert original["collection_id"] == collection_id

        response = client.patch(
            f"/prompts/{prompt_id}",
            json={"collection_id": None},
        )

        assert response.status_code == 200
        assert response.json()["collection_id"] is None

        stored_response = client.get(f"/prompts/{prompt_id}")
        assert stored_response.status_code == 200
        assert stored_response.json()["collection_id"] is None

    def test_patch_prompt_clear_description(
        self,
        client: TestClient,
        sample_prompt_data,
    ):
        """Verify that PATCH can explicitly clear a description."""
        create_response = client.post(
            "/prompts",
            json=sample_prompt_data,
        )
        prompt_id = create_response.json()["id"]

        response = client.patch(
            f"/prompts/{prompt_id}",
            json={"description": None},
        )

        assert response.status_code == 200
        assert response.json()["description"] is None

        stored_response = client.get(f"/prompts/{prompt_id}")
        assert stored_response.json()["description"] is None

    @pytest.mark.parametrize("field_name", ["title", "content"])
    def test_patch_prompt_rejects_null_required_fields(
        self,
        client: TestClient,
        sample_prompt_data,
        field_name: str,
    ):
        """Verify that title and content cannot be explicitly null."""
        create_response = client.post(
            "/prompts",
            json=sample_prompt_data,
        )
        prompt_id = create_response.json()["id"]

        response = client.patch(
            f"/prompts/{prompt_id}",
            json={field_name: None},
        )

        assert response.status_code == 422


class TestCollections:
    """Tests for collection endpoints."""

    def test_create_collection(
        self,
        client: TestClient,
        sample_collection_data,
    ):
        """Verify that a collection can be created."""
        response = client.post(
            "/collections",
            json=sample_collection_data,
        )

        assert response.status_code == 201

        data = response.json()
        assert data["name"] == sample_collection_data["name"]
        assert "id" in data
        assert "created_at" in data

    def test_list_collections(
        self,
        client: TestClient,
        sample_collection_data,
    ):
        """Verify that stored collections appear in the list."""
        client.post(
            "/collections",
            json=sample_collection_data,
        )

        response = client.get("/collections")

        assert response.status_code == 200

        data = response.json()
        assert len(data["collections"]) == 1
        assert data["total"] == 1

    def test_get_collection_not_found(
        self,
        client: TestClient,
    ):
        """Verify that requesting a missing collection returns 404."""
        response = client.get(
            "/collections/nonexistent-id",
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Collection not found"

    def test_delete_collection_with_prompts(
        self,
        client: TestClient,
        sample_collection_data,
        sample_prompt_data,
    ):
        """Verify that collection deletion detaches its prompts."""
        collection_response = client.post(
            "/collections",
            json=sample_collection_data,
        )
        collection_id = collection_response.json()["id"]

        prompt_data = {
            **sample_prompt_data,
            "collection_id": collection_id,
        }
        prompt_response = client.post(
            "/prompts",
            json=prompt_data,
        )
        original_prompt = prompt_response.json()
        prompt_id = original_prompt["id"]

        assert original_prompt["collection_id"] == collection_id

        time.sleep(0.1)

        delete_response = client.delete(
            f"/collections/{collection_id}",
        )

        assert delete_response.status_code == 204

        collection_lookup = client.get(
            f"/collections/{collection_id}",
        )
        assert collection_lookup.status_code == 404

        prompt_lookup = client.get(f"/prompts/{prompt_id}")
        assert prompt_lookup.status_code == 200

        updated_prompt = prompt_lookup.json()
        assert updated_prompt["collection_id"] is None
        assert (
            updated_prompt["updated_at"]
            != original_prompt["updated_at"]
        )

    def test_delete_collection_not_found(
        self,
        client: TestClient,
    ):
        """Verify that deleting a missing collection returns 404."""
        response = client.delete(
            "/collections/nonexistent-id",
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Collection not found"