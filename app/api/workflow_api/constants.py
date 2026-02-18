"""
Whisk Desktop — Workflow API Constants.

Shared constants for the workflow API: URL mappings, aspect ratios, etc.
"""
from app.api.api_config import LABS_BASE_URL

LABS_TRPC_URL = f"{LABS_BASE_URL}/api/trpc/project.createProject"

WHISK_API_URL = "https://aisandbox-pa.googleapis.com/v1/whisk:generateImage"
WHISK_RECIPE_URL = "https://aisandbox-pa.googleapis.com/v1/whisk:runImageRecipe"
WHISK_CREDIT_URL = "https://aisandbox-pa.googleapis.com/v1/whisk:getVideoCreditStatus"
VIDEO_GENERATE_URL = "https://aisandbox-pa.googleapis.com/v1/video:batchAsyncGenerateVideoText"
VIDEO_STATUS_URL = "https://aisandbox-pa.googleapis.com/v1/video:batchCheckAsyncVideoGenerationStatus"

ASPECT_RATIO_MAP = {
    "VIDEO_ASPECT_RATIO_LANDSCAPE": "VIDEO_ASPECT_RATIO_LANDSCAPE",
    "VIDEO_ASPECT_RATIO_PORTRAIT":  "VIDEO_ASPECT_RATIO_PORTRAIT",
    # Legacy short-form fallback
    "16:9":  "VIDEO_ASPECT_RATIO_LANDSCAPE",
    "9:16":  "VIDEO_ASPECT_RATIO_PORTRAIT",
}
