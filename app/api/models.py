"""
Whisk Desktop — Data Models.

Defines data structures for the image creation queue,
cookie management, and project management.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class TaskItem:
    """Represents one row in the image creation queue."""

    id: str
    stt: int                                    # Row number (1-indexed)
    task_name: str = ""                         # e.g. "Task 1"
    model: str = "IMAGEN_3_5"                  # AI model name
    aspect_ratio: str = "16:9"                  # e.g. "16:9", "9:16", "1:1"
    quality: str = "1K"                         # "1K", "2K", or "4K"
    reference_images: list[str] = field(default_factory=list)  # Up to 10 paths
    reference_images_by_cat: dict = field(default_factory=lambda: {"title": [], "scene": [], "style": []})  # By category
    prompt: str = ""                            # Generation prompt text
    images_per_prompt: int = 1                    # Number of output images per prompt
    output_images: list[str] = field(default_factory=list)  # Paths to generated outputs
    status: str = "pending"                     # pending | running | completed | error
    progress: int = 0                           # 0-100 progress percentage
    elapsed_seconds: int = 0                    # Time for running / completed tasks
    error_message: str = ""                     # Error detail if status == "error"
    output_folder: str = ""                     # Folder to save generated images
    filename_prefix: str = ""                   # Prefix for filenames
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "stt": self.stt,
            "task_name": self.task_name,
            "model": self.model,
            "aspect_ratio": self.aspect_ratio,
            "quality": self.quality,
            "reference_images": list(self.reference_images),
            "reference_images_by_cat": dict(self.reference_images_by_cat),
            "prompt": self.prompt,
            "images_per_prompt": self.images_per_prompt,
            "output_images": list(self.output_images),
            "status": self.status,
            "progress": self.progress,
            "elapsed_seconds": self.elapsed_seconds,
            "error_message": self.error_message,
            "output_folder": self.output_folder,
            "filename_prefix": self.filename_prefix,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TaskItem":
        """Deserialize from dictionary."""
        created = data.get("created_at")
        if isinstance(created, str):
            try:
                created = datetime.fromisoformat(created)
            except ValueError:
                created = datetime.now()
        elif not isinstance(created, datetime):
            created = datetime.now()

        return cls(
            id=data.get("id", ""),
            stt=data.get("stt", 0),
            task_name=data.get("task_name", ""),
            model=data.get("model", "IMAGEN_3_5"),
            aspect_ratio=data.get("aspect_ratio", "16:9"),
            quality=data.get("quality", "1K"),
            reference_images=data.get("reference_images", []),
            prompt=data.get("prompt", ""),
            output_images=data.get("output_images", []),
            status=data.get("status", "pending"),
            progress=data.get("progress", 0),
            elapsed_seconds=data.get("elapsed_seconds", 0),
            error_message=data.get("error_message", ""),
            output_folder=data.get("output_folder", ""),
            filename_prefix=data.get("filename_prefix", ""),
            created_at=created,
        )


@dataclass
class ApiResponse:
    """Standardized API response wrapper."""

    success: bool
    data: Any = None
    message: str = ""
    total: int = 0


@dataclass
class CookieItem:
    """Represents a stored cookie for API authentication."""

    id: str
    name: str = ""
    value: str = ""
    domain: str = ""
    status: str = "unknown"  # valid | expired | unknown
    expires_at: Optional[datetime] = None
    added_at: datetime = field(default_factory=datetime.now)

    @property
    def is_expired(self) -> bool:
        """Check if cookie has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "value": self.value,
            "domain": self.domain,
            "status": self.status,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "added_at": self.added_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CookieItem":
        expires = data.get("expires_at")
        if isinstance(expires, str):
            try:
                expires = datetime.fromisoformat(expires)
            except ValueError:
                expires = None
        added = data.get("added_at")
        if isinstance(added, str):
            try:
                added = datetime.fromisoformat(added)
            except ValueError:
                added = datetime.now()
        elif not isinstance(added, datetime):
            added = datetime.now()

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            value=data.get("value", ""),
            domain=data.get("domain", ""),
            status=data.get("status", "unknown"),
            expires_at=expires,
            added_at=added,
        )


@dataclass
class ProjectItem:
    """Represents a user project."""

    id: str
    name: str = ""
    description: str = ""
    status: str = "active"  # active | archived
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectItem":
        created = data.get("created_at")
        if isinstance(created, str):
            try:
                created = datetime.fromisoformat(created)
            except ValueError:
                created = datetime.now()
        elif not isinstance(created, datetime):
            created = datetime.now()
        updated = data.get("updated_at")
        if isinstance(updated, str):
            try:
                updated = datetime.fromisoformat(updated)
            except ValueError:
                updated = datetime.now()
        elif not isinstance(updated, datetime):
            updated = datetime.now()

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            status=data.get("status", "active"),
            created_at=created,
            updated_at=updated,
        )


@dataclass
class TokenItem:
    """Represents an API token."""

    id: str
    name: str = ""
    value: str = ""
    token_type: str = "bearer"  # api_key | bearer | oauth
    status: str = "active"  # active | expired | revoked
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "value": self.value,
            "token_type": self.token_type,
            "status": self.status,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TokenItem":
        expires = data.get("expires_at")
        if isinstance(expires, str):
            try:
                expires = datetime.fromisoformat(expires)
            except ValueError:
                expires = None
        elif not isinstance(expires, datetime):
            expires = None
        created = data.get("created_at")
        if isinstance(created, str):
            try:
                created = datetime.fromisoformat(created)
            except ValueError:
                created = datetime.now()
        elif not isinstance(created, datetime):
            created = datetime.now()

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            value=data.get("value", ""),
            token_type=data.get("token_type", "bearer"),
            status=data.get("status", "active"),
            expires_at=expires,
            created_at=created,
        )


@dataclass
class FlowConfig:
    """Configuration for a flow/project."""

    auto_generate: bool = True
    seed: Optional[int] = None
    aspectRatio: str = "VIDEO_ASPECT_RATIO_LANDSCAPE"
    videoModelKey: str = "veo_3_1_t2v_fast_ultra"
    batch_size: int = 5
    concurrent_limit: int = 3
    auto_download: bool = True
    retry_failed: bool = True
    max_retries: int = 2

    def to_dict(self) -> dict:
        return {
            "auto_generate": self.auto_generate,
            "seed": self.seed,
            "aspectRatio": self.aspectRatio,
            "videoModelKey": self.videoModelKey,
            "batch_size": self.batch_size,
            "concurrent_limit": self.concurrent_limit,
            "auto_download": self.auto_download,
            "retry_failed": self.retry_failed,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FlowConfig":
        return cls(
            auto_generate=data.get("auto_generate", True),
            seed=data.get("seed"),
            aspectRatio=data.get("aspectRatio", "VIDEO_ASPECT_RATIO_LANDSCAPE"),
            videoModelKey=data.get("videoModelKey", "veo_3_1_t2v_fast_ultra"),
            batch_size=data.get("batch_size", 5),
            concurrent_limit=data.get("concurrent_limit", 3),
            auto_download=data.get("auto_download", True),
            retry_failed=data.get("retry_failed", True),
            max_retries=data.get("max_retries", 2),
        )


@dataclass
class FlowItem:
    """Represents a flow/project on the server."""

    id: int = 0
    name: str = ""
    description: str = ""
    type: str = "WHISK"
    status: str = "pending"
    config: FlowConfig = field(default_factory=FlowConfig)
    key_code: Optional[str] = None
    upload_count: int = 0
    user_id: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "status": self.status,
            "config": self.config.to_dict(),
            "key_code": self.key_code,
            "upload_count": self.upload_count,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FlowItem":
        created = data.get("created_at")
        if isinstance(created, str):
            try:
                created = datetime.fromisoformat(created)
            except ValueError:
                created = datetime.now()
        elif not isinstance(created, datetime):
            created = datetime.now()
        updated = data.get("updated_at")
        if isinstance(updated, str):
            try:
                updated = datetime.fromisoformat(updated)
            except ValueError:
                updated = datetime.now()
        elif not isinstance(updated, datetime):
            updated = datetime.now()

        config_data = data.get("config", {})
        config = FlowConfig.from_dict(config_data) if isinstance(config_data, dict) else FlowConfig()

        return cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
            description=data.get("description", ""),
            type=data.get("type", "WHISK"),
            status=data.get("status", "pending"),
            config=config,
            key_code=data.get("key_code"),
            upload_count=data.get("upload_count", 0),
            user_id=data.get("user_id", 0),
            created_at=created,
            updated_at=updated,
        )


@dataclass
class ApiKeyItem:
    """Represents an api-key (cookie/token) on the server."""

    id: int = 0
    label: str = ""
    value: str = ""
    provider: str = "WHISK"
    status: str = "active"  # active | expired | error
    billing_type: str = "free"
    credit: float = 0.0
    requests: int = 0
    limit_requests: int = 0
    flow_id: Optional[int] = None
    user_id: int = 0
    error: bool = False
    msg_error: Optional[str] = None
    expired: Optional[str] = None
    deleted_at: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "value": self.value,
            "provider": self.provider,
            "status": self.status,
            "billing_type": self.billing_type,
            "credit": self.credit,
            "requests": self.requests,
            "limit_requests": self.limit_requests,
            "flow_id": self.flow_id,
            "user_id": self.user_id,
            "error": self.error,
            "msg_error": self.msg_error,
            "expired": self.expired,
            "deleted_at": self.deleted_at,
            "metadata": self.metadata,
            "createdAt": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ApiKeyItem":
        created = data.get("createdAt") or data.get("created_at")
        if isinstance(created, str):
            try:
                created = datetime.fromisoformat(created)
            except ValueError:
                created = datetime.now()
        elif not isinstance(created, datetime):
            created = datetime.now()

        return cls(
            id=data.get("id", 0),
            label=data.get("label", ""),
            value=data.get("value", ""),
            provider=data.get("provider", "WHISK"),
            status=data.get("status", "active"),
            billing_type=data.get("billing_type", "free"),
            credit=data.get("credit", 0.0),
            requests=data.get("requests", 0),
            limit_requests=data.get("limit_requests", 0),
            flow_id=data.get("flow_id"),
            user_id=data.get("user_id", 0),
            error=data.get("error", False),
            msg_error=data.get("msg_error"),
            expired=data.get("expired"),
            deleted_at=data.get("deleted_at"),
            metadata=data.get("metadata", {}),
            created_at=created,
        )


