"""
Whisk Desktop — Workflow API Constants.

Shared constants for the workflow API: URL mappings, aspect ratios, etc.
"""
from app.api.api_config import LABS_BASE_URL

LABS_TRPC_URL = f"{LABS_BASE_URL}/api/trpc/media.createOrUpdateWorkflow"

WHISK_API_URL = "https://aisandbox-pa.googleapis.com/v1/whisk:generateImage"
WHISK_RECIPE_URL = "https://aisandbox-pa.googleapis.com/v1/whisk:runImageRecipe"
WHISK_CREDIT_URL = "https://aisandbox-pa.googleapis.com/v1/whisk:getVideoCreditStatus"

ASPECT_RATIO_MAP = {
    "16:9":  "IMAGE_ASPECT_RATIO_LANDSCAPE",
    "9:16":  "IMAGE_ASPECT_RATIO_PORTRAIT",
    "1:1":   "IMAGE_ASPECT_RATIO_SQUARE",
    "4:3":   "IMAGE_ASPECT_RATIO_FOUR_THREE",
    "3:4":   "IMAGE_ASPECT_RATIO_THREE_FOUR",
}
