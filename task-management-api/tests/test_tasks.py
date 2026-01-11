"""Comprehensive tests for Task Management API endpoints."""
import pytest
from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_get_root(self, client: TestClient):
        """Test root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Task Management API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "operational"


class TestCreateTask:
    """Tests for POST /tasks endpoint."""

    def test_create_task_with_title_only(self, client: TestClient):
        """Test creating a task with only a title."""
        response = client.post("/tasks", json={"title": "Test Task"})
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["description"] is None
        assert data["status"] == "pending"
        assert data["id"] is not None
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_task_with_title_and_description(self, client: TestClient):
        """Test creating a task with title and description."""
        response = client.post(
            "/tasks",
            json={"title": "Complete Project", "description": "Finish the API implementation"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Complete Project"
        assert data["description"] == "Finish the API implementation"
        assert data["status"] == "pending"

    def test_create_task_missing_title(self, client: TestClient):
        """Test creating a task without a title returns 422."""
        response = client.post("/tasks", json={"description": "No title task"})
        assert response.status_code == 422

    def test_create_task_empty_title(self, client: TestClient):
        """Test creating a task with empty title returns 422."""
        response = client.post("/tasks", json={"title": ""})
        assert response.status_code == 422

    def test_create_task_title_too_long(self, client: TestClient):
        """Test creating a task with title exceeding max length returns 422."""
        long_title = "a" * 201
        response = client.post("/tasks", json={"title": long_title})
        assert response.status_code == 422


class TestListTasks:
    """Tests for GET /tasks endpoint."""

    def test_list_tasks_empty(self, client: TestClient):
        """Test listing tasks when database is empty."""
        response = client.get("/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_tasks_with_data(self, client: TestClient):
        """Test listing tasks when tasks exist."""
        # Create multiple tasks
        client.post("/tasks", json={"title": "Task 1"})
        client.post("/tasks", json={"title": "Task 2"})
        client.post("/tasks", json={"title": "Task 3"})

        response = client.get("/tasks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["title"] == "Task 1"
        assert data[1]["title"] == "Task 2"
        assert data[2]["title"] == "Task 3"

    def test_list_tasks_filter_by_status_pending(self, client: TestClient):
        """Test filtering tasks by pending status."""
        # Create tasks with different statuses
        task1 = client.post("/tasks", json={"title": "Pending Task"}).json()
        task2 = client.post("/tasks", json={"title": "In Progress Task"}).json()

        # Update second task to in_progress
        client.put(f"/tasks/{task2['id']}", json={"status": "in_progress"})

        # Filter by pending status
        response = client.get("/tasks?status_filter=pending")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Pending Task"
        assert data[0]["status"] == "pending"

    def test_list_tasks_filter_by_status_in_progress(self, client: TestClient):
        """Test filtering tasks by in_progress status."""
        # Create and update task
        task = client.post("/tasks", json={"title": "Active Task"}).json()
        client.put(f"/tasks/{task['id']}", json={"status": "in_progress"})

        response = client.get("/tasks?status_filter=in_progress")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "in_progress"

    def test_list_tasks_filter_by_status_completed(self, client: TestClient):
        """Test filtering tasks by completed status."""
        # Create and complete task
        task = client.post("/tasks", json={"title": "Done Task"}).json()
        client.put(f"/tasks/{task['id']}", json={"status": "completed"})

        response = client.get("/tasks?status_filter=completed")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "completed"

    def test_list_tasks_invalid_status_filter(self, client: TestClient):
        """Test filtering with invalid status returns 400."""
        response = client.get("/tasks?status_filter=invalid_status")
        assert response.status_code == 400
        assert "Invalid status filter" in response.json()["detail"]


class TestGetTask:
    """Tests for GET /tasks/{task_id} endpoint."""

    def test_get_existing_task(self, client: TestClient):
        """Test getting an existing task by ID."""
        # Create a task
        create_response = client.post(
            "/tasks", json={"title": "Test Task", "description": "Test Description"}
        )
        task_id = create_response.json()["id"]

        # Get the task
        response = client.get(f"/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == "Test Task"
        assert data["description"] == "Test Description"

    def test_get_nonexistent_task(self, client: TestClient):
        """Test getting a task that doesn't exist returns 404."""
        response = client.get("/tasks/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestUpdateTask:
    """Tests for PUT /tasks/{task_id} endpoint."""

    def test_update_task_title(self, client: TestClient):
        """Test updating a task's title."""
        # Create a task
        task = client.post("/tasks", json={"title": "Original Title"}).json()

        # Update title
        response = client.put(f"/tasks/{task['id']}", json={"title": "Updated Title"})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] is None
        assert data["status"] == "pending"

    def test_update_task_description(self, client: TestClient):
        """Test updating a task's description."""
        task = client.post("/tasks", json={"title": "Task"}).json()

        response = client.put(
            f"/tasks/{task['id']}", json={"description": "New description"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "New description"

    def test_update_task_status(self, client: TestClient):
        """Test updating a task's status."""
        task = client.post("/tasks", json={"title": "Task"}).json()

        response = client.put(f"/tasks/{task['id']}", json={"status": "in_progress"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"

    def test_update_task_multiple_fields(self, client: TestClient):
        """Test updating multiple fields at once."""
        task = client.post("/tasks", json={"title": "Task"}).json()

        response = client.put(
            f"/tasks/{task['id']}",
            json={
                "title": "Updated Task",
                "description": "Updated description",
                "status": "completed",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Task"
        assert data["description"] == "Updated description"
        assert data["status"] == "completed"

    def test_update_task_invalid_status(self, client: TestClient):
        """Test updating with invalid status returns 400."""
        task = client.post("/tasks", json={"title": "Task"}).json()

        response = client.put(
            f"/tasks/{task['id']}", json={"status": "invalid_status"}
        )
        assert response.status_code == 400
        assert "Invalid status" in response.json()["detail"]

    def test_update_nonexistent_task(self, client: TestClient):
        """Test updating a task that doesn't exist returns 404."""
        response = client.put("/tasks/99999", json={"title": "Updated"})
        assert response.status_code == 404

    def test_update_task_updates_timestamp(self, client: TestClient):
        """Test that updating a task updates the updated_at timestamp."""
        task = client.post("/tasks", json={"title": "Task"}).json()
        original_updated_at = task["updated_at"]

        # Small delay to ensure timestamp difference
        import time

        time.sleep(0.1)

        response = client.put(f"/tasks/{task['id']}", json={"title": "Updated"})
        updated_task = response.json()

        assert updated_task["updated_at"] != original_updated_at


class TestDeleteTask:
    """Tests for DELETE /tasks/{task_id} endpoint."""

    def test_delete_existing_task(self, client: TestClient):
        """Test deleting an existing task."""
        # Create a task
        task = client.post("/tasks", json={"title": "Task to Delete"}).json()
        task_id = task["id"]

        # Delete the task
        response = client.delete(f"/tasks/{task_id}")
        assert response.status_code == 204

        # Verify task is gone
        get_response = client.get(f"/tasks/{task_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_task(self, client: TestClient):
        """Test deleting a task that doesn't exist returns 404."""
        response = client.delete("/tasks/99999")
        assert response.status_code == 404

    def test_delete_task_removed_from_list(self, client: TestClient):
        """Test that deleted task is removed from task list."""
        # Create multiple tasks
        task1 = client.post("/tasks", json={"title": "Task 1"}).json()
        task2 = client.post("/tasks", json={"title": "Task 2"}).json()
        task3 = client.post("/tasks", json={"title": "Task 3"}).json()

        # Delete middle task
        client.delete(f"/tasks/{task2['id']}")

        # Verify only 2 tasks remain
        response = client.get("/tasks")
        data = response.json()
        assert len(data) == 2
        task_ids = [task["id"] for task in data]
        assert task1["id"] in task_ids
        assert task3["id"] in task_ids
        assert task2["id"] not in task_ids


class TestTaskWorkflow:
    """Integration tests for complete task workflows."""

    def test_complete_task_lifecycle(self, client: TestClient):
        """Test the complete lifecycle of a task from creation to deletion."""
        # 1. Create task
        create_response = client.post(
            "/tasks",
            json={"title": "Complete Feature X", "description": "Implement feature X"},
        )
        assert create_response.status_code == 201
        task = create_response.json()
        task_id = task["id"]
        assert task["status"] == "pending"

        # 2. Start working on task
        update1_response = client.put(
            f"/tasks/{task_id}", json={"status": "in_progress"}
        )
        assert update1_response.status_code == 200
        assert update1_response.json()["status"] == "in_progress"

        # 3. Complete the task
        update2_response = client.put(
            f"/tasks/{task_id}", json={"status": "completed"}
        )
        assert update2_response.status_code == 200
        assert update2_response.json()["status"] == "completed"

        # 4. Delete completed task
        delete_response = client.delete(f"/tasks/{task_id}")
        assert delete_response.status_code == 204

        # 5. Verify task is gone
        get_response = client.get(f"/tasks/{task_id}")
        assert get_response.status_code == 404

    def test_filter_tasks_by_workflow_stage(self, client: TestClient):
        """Test filtering tasks at different stages of workflow."""
        # Create tasks at different stages
        pending = client.post("/tasks", json={"title": "Plan feature"}).json()
        in_progress = client.post("/tasks", json={"title": "Build feature"}).json()
        completed = client.post("/tasks", json={"title": "Deploy feature"}).json()

        # Update statuses
        client.put(f"/tasks/{in_progress['id']}", json={"status": "in_progress"})
        client.put(f"/tasks/{completed['id']}", json={"status": "completed"})

        # Test each filter
        pending_tasks = client.get("/tasks?status_filter=pending").json()
        assert len(pending_tasks) == 1
        assert pending_tasks[0]["title"] == "Plan feature"

        in_progress_tasks = client.get("/tasks?status_filter=in_progress").json()
        assert len(in_progress_tasks) == 1
        assert in_progress_tasks[0]["title"] == "Build feature"

        completed_tasks = client.get("/tasks?status_filter=completed").json()
        assert len(completed_tasks) == 1
        assert completed_tasks[0]["title"] == "Deploy feature"

        # Verify total count
        all_tasks = client.get("/tasks").json()
        assert len(all_tasks) == 3
