---
description: Add a new API endpoint module to the api layer
---

# Add API Endpoint

## Inputs

- `API_NAME`: e.g., `analytics` (snake_case)
- `BASE_URL`: either `https://tools.1nutnhan.com/` (admin) or `https://labs.google/f` (generation)

## Steps

1. **Create the API file** at `app/api/<API_NAME>_api.py`

```python
"""
Whisk Desktop — <API_NAME> API Client.

HTTP client for <description> operations.
"""
import requests
from app.api.models import ApiResponse
from app.api.api_config import ApiConfig


class <ClassName>Api:
    """API client for <description>."""

    def __init__(self, config: ApiConfig = None):
        self.config = config or ApiConfig()
        self.base_url = "<BASE_URL>"

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.token}",
        }

    def list_items(self) -> ApiResponse:
        """Fetch all items."""
        try:
            resp = requests.get(
                f"{self.base_url}/api/<endpoint>",
                headers=self._headers(),
                timeout=30,
            )
            data = resp.json()
            return ApiResponse(success=True, data=data)
        except Exception as e:
            return ApiResponse(success=False, message=str(e))
```

2. **Add data models** to `app/api/models.py` if needed

3. **Create test file** at `tests/test_<API_NAME>_api.py`

```python
"""
Tests for <ClassName>Api.
"""
import pytest
from unittest.mock import patch, MagicMock

class Test<ClassName>Api:
    def test_list_items_success(self):
        from app.api.<API_NAME>_api import <ClassName>Api
        api = <ClassName>Api()
        with patch("requests.get") as mock_get:
            mock_get.return_value.json.return_value = {"items": []}
            mock_get.return_value.status_code = 200
            result = api.list_items()
            assert result.success is True
```

// turbo

4. **Run tests**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && python3 -m pytest tests/test_<API_NAME>_api.py -v
```

## Base URL Reference

| URL                           | Purpose          | Modules                  |
| ----------------------------- | ---------------- | ------------------------ |
| `https://tools.1nutnhan.com/` | Admin operations | `flow_api`, `cookie_api` |
| `https://labs.google/f`       | Image generation | `workflow_api`           |

## Rules

- All methods MUST return `ApiResponse`
- Always set `timeout=30` on requests
- Catch all exceptions and return `ApiResponse(success=False, message=...)`
- Never import widgets or pages from API modules
