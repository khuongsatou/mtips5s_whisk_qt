"""
Whisk Desktop — Workflow API Package.

Re-exports WorkflowApiClient and ASPECT_RATIO_MAP for backward compatibility.
"""
from app.api.workflow_api.workflow_api import WorkflowApiClient
from app.api.workflow_api.constants import ASPECT_RATIO_MAP

__all__ = ["WorkflowApiClient", "ASPECT_RATIO_MAP"]
