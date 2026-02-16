---
name: Backend Developer
description: Responsible for API layer architecture, data models, mock API implementation, and future real API integration for the Whisk Desktop application.
---

# Backend Developer Skill

## Role Overview

The **Backend Developer** owns:

- Abstract API interface (`BaseApi`)
- Data models (`TaskItem`, `ApiResponse`)
- Mock API implementation (`MockApi`)
- Future real API integration (`RealApi`)

---

## File Ownership

| File                  | Description                                              |
| --------------------- | -------------------------------------------------------- |
| `app/api/base_api.py` | Abstract API interface (ABC)                             |
| `app/api/models.py`   | Dataclass models (`TaskItem`, `ApiResponse`, `UserInfo`) |
| `app/api/mock_api.py` | In-memory mock implementation                            |
| `app/auth/`           | Authentication manager                                   |

---

## API Interface Contract

`BaseApi` defines the core operations:

```python
class BaseApi(ABC):
    # Queue operations
    def get_queue() -> ApiResponse: ...
    def add_to_queue(data: dict) -> ApiResponse: ...
    def update_task(task_id: str, data: dict) -> ApiResponse: ...
    def delete_tasks(task_ids: list[str]) -> ApiResponse: ...
    def start_queue() -> ApiResponse: ...
    def stop_queue() -> ApiResponse: ...
```

---

## Data Models

```python
@dataclass
class TaskItem:
    id: str
    stt: int                                     # Row number (1-indexed)
    task_name: str = ""
    model: str = "Nano Banana Pro"
    aspect_ratio: str = "16:9"
    quality: str = "1K"
    reference_images: list[str]                  # Up to 10 paths
    reference_images_by_cat: dict                # {"title": [], "scene": [], "style": []}
    prompt: str = ""
    images_per_prompt: int = 1                   # Number of output images per prompt
    output_image: Optional[str] = None
    status: str = "pending"                      # pending | running | completed | error
    elapsed_seconds: int = 0
    error_message: str = ""
    created_at: datetime

@dataclass
class ApiResponse:
    success: bool
    data: Any = None
    message: str = ""
    total: int = 0
```

---

## Mock API Key Methods

| Method                           | Description                                                                     |
| -------------------------------- | ------------------------------------------------------------------------------- |
| `get_queue()`                    | Returns all tasks as list of dicts                                              |
| `add_to_queue(data)`             | Creates TaskItem with auto-incrementing STT                                     |
| `update_task(task_id, data)`     | Updates allowed fields including `reference_images_by_cat`, `images_per_prompt` |
| `delete_tasks(task_ids)`         | Removes tasks and re-indexes STT                                                |
| `start_queue()` / `stop_queue()` | Controls queue processing                                                       |

---

## Swapping to Real API

1. Create `app/api/real_api.py` implementing `BaseApi`
2. Use `requests` or `httpx` for HTTP calls
3. Change `main.py`: `api = RealApi(base_url="https://...")` instead of `MockApi()`
4. No UI code should need changes — the interface is abstract
