"""
Whisk Desktop — Workflow API Client.

Handles workflow creation on Google Labs, linking to the server flow,
and image generation via the whisk:generateImage endpoint:
- Create workflow (POST labs.google/fx/api/trpc/media.createOrUpdateWorkflow)
- Link workflow to flow (POST {FLOW_BASE_URL}/tools/upload/frame/run?type=WHISK)
- Generate image (POST aisandbox-pa.googleapis.com/v1/whisk:generateImage)
"""
import json
import logging
import time
import urllib.request
import urllib.error
import urllib.parse
import random
from app.api.api_config import LABS_BASE_URL, flow_url
from app.api.models import ApiResponse
from app.api.workflow_api.constants import (
    LABS_TRPC_URL, WHISK_API_URL, WHISK_RECIPE_URL, WHISK_CREDIT_URL,
    ASPECT_RATIO_MAP,
)

logger = logging.getLogger("whisk.workflow_api")


class WorkflowApiClient:
    """HTTP client for workflow creation and linking."""

    def __init__(self, access_token: str = ""):
        self._access_token = access_token

    def set_access_token(self, token: str):
        """Update the Bearer token used for server API requests."""
        self._access_token = token

    # ── Create Workflow on Google Labs ─────────────────────────────────

    def create_workflow(self, session_token: str, csrf_token: str = "") -> ApiResponse:
        """
        POST labs.google/fx/api/trpc/media.createOrUpdateWorkflow

        Uses cookie-based auth (session-token) to create a workflow on Labs.
        Returns ApiResponse with data containing workflowId.
        """
        from datetime import datetime
        now = datetime.now()
        workflow_name = f"Whisk: {now.strftime('%-m/%-d/%y')}"
        session_id = f";{int(time.time() * 1000)}"

        payload = {
            "json": {
                "clientContext": {
                    "tool": "BACKBONE",
                    "sessionId": session_id,
                },
                "mediaGenerationIdsToCopy": [],
                "workflowMetadata": {
                    "workflowName": workflow_name,
                },
            }
        }

        # Build cookie header
        cookies = f"__Secure-next-auth.session-token={session_token}"
        if csrf_token:
            cookies += f"; __Host-next-auth.csrf-token={csrf_token}"

        headers = {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Origin": "https://labs.google",
            "Referer": "https://labs.google/fx/vi/tools/whisk/project",
            "Cookie": cookies,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/144.0.0.0 Safari/537.36",
        }

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        try:
            req = urllib.request.Request(
                LABS_TRPC_URL,
                data=body,
                headers=headers,
                method="POST",
            )

            logger.info(f"📤 >>> POST {LABS_TRPC_URL}")
            logger.debug(f"📤 >>> Body: {json.dumps(payload, indent=2, ensure_ascii=False)}")

            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_body = json.loads(resp.read().decode("utf-8"))

            logger.info(f"📥 <<< {resp.status} OK")
            logger.debug(f"📥 <<< Response: {json.dumps(resp_body, indent=2)}")

            # Extract workflowId from nested response
            result = (resp_body
                      .get("result", {})
                      .get("data", {})
                      .get("json", {})
                      .get("result", {}))
            workflow_id = result.get("workflowId", "")

            if workflow_id:
                return ApiResponse(
                    success=True,
                    data={"workflowId": workflow_id, "workflowName": workflow_name},
                    message=f"Workflow created: {workflow_id}",
                )
            else:
                return ApiResponse(
                    success=False,
                    data=resp_body,
                    message="No workflowId in response",
                )

        except urllib.error.HTTPError as e:
            error_data = ""
            try:
                error_data = e.read().decode("utf-8")
            except Exception:
                pass
            logger.error(f"❌ <<< {e.code} Error in create_workflow")
            logger.debug(f"📥 <<< Response: {error_data}")
            return ApiResponse(success=False, message=f"HTTP {e.code}: {error_data[:200]}")
        except urllib.error.URLError as e:
            logger.error(f"❌ <<< Connection failed: {e.reason}")
            return ApiResponse(success=False, message="Cannot connect to Labs")
        except Exception as e:
            logger.error(f"❌ <<< create_workflow exception: {e}")
            return ApiResponse(success=False, message=str(e))

    # ── Link Workflow to Server Flow ──────────────────────────────────

    def link_workflow(
        self,
        flow_id: int,
        project_id: str,
        project_name: str,
        use_credit: bool = True,
    ) -> ApiResponse:
        """
        POST /tools/upload/frame/run?type=WHISK

        Links a workflowId (project_id) to a server flow.
        """
        params = urllib.parse.urlencode({"type": "WHISK"})
        url = f"{flow_url('tools/upload/frame/run')}?{params}"

        payload = {
            "project_name": project_name,
            "flow_id": flow_id,
            "use_credit": use_credit,
            "project_id": project_id,
        }

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._access_token}",
        }

        try:
            req = urllib.request.Request(
                url,
                data=body,
                headers=headers,
                method="POST",
            )

            logger.info(f"📤 >>> POST {url}")
            logger.debug(f"📤 >>> Body: {json.dumps(payload, indent=2, ensure_ascii=False)}")

            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_body = json.loads(resp.read().decode("utf-8"))

            logger.info(f"📥 <<< {resp.status} OK")
            logger.debug(f"📥 <<< Response: {json.dumps(resp_body, indent=2)}")

            status = resp_body.get("status", "")
            return ApiResponse(
                success=(status == "ok"),
                data=resp_body,
                message=resp_body.get("message", f"Linked workflow {project_id}"),
            )

        except urllib.error.HTTPError as e:
            error_data = ""
            try:
                error_data = e.read().decode("utf-8")
            except Exception:
                pass
            logger.error(f"❌ <<< {e.code} Error in link_workflow")
            logger.debug(f"📥 <<< Response: {error_data}")
            return ApiResponse(success=False, message=f"HTTP {e.code}: {error_data[:200]}")
        except urllib.error.URLError as e:
            logger.error(f"❌ <<< Connection failed: {e.reason}")
            return ApiResponse(success=False, message="Cannot connect to server")
        except Exception as e:
            logger.error(f"❌ <<< link_workflow exception: {e}")
            return ApiResponse(success=False, message=str(e))

    # ── Reference Image Upload ────────────────────────────────────────

    MEDIA_CATEGORY_MAP = {
        "title": "MEDIA_CATEGORY_SUBJECT",
        "scene": "MEDIA_CATEGORY_SCENE",
        "style": "MEDIA_CATEGORY_STYLE",
    }

    def caption_image(
        self,
        session_token: str,
        image_base64: str,
        media_category: str = "MEDIA_CATEGORY_SUBJECT",
        workflow_id: str = "",
    ) -> ApiResponse:
        """
        POST labs.google/fx/api/trpc/backbone.captionImage

        Sends an image (as base64 data URI) and returns an AI-generated caption.
        """
        url = f"{LABS_BASE_URL}/api/trpc/backbone.captionImage"
        session_id = f";{int(time.time() * 1000)}"

        payload = {
            "json": {
                "clientContext": {
                    "sessionId": session_id,
                    "workflowId": workflow_id,
                },
                "captionInput": {
                    "candidatesCount": 1,
                    "mediaInput": {
                        "mediaCategory": media_category,
                        "rawBytes": image_base64,
                    },
                },
            }
        }

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Origin": "https://labs.google",
            "Referer": "https://labs.google/",
            "Cookie": f"__Secure-next-auth.session-token={session_token}",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/144.0.0.0 Safari/537.36",
        }

        try:
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            logger.info(f"📸 >>> POST captionImage ({media_category})")

            with urllib.request.urlopen(req, timeout=60) as resp:
                resp_body = json.loads(resp.read().decode("utf-8"))

            result = resp_body.get("result", {}).get("data", {}).get("json", {}).get("result", {})
            candidates = result.get("candidates", [])

            if candidates:
                caption = candidates[0].get("output", "")
                logger.info(f"📸 <<< Caption: {caption[:80]}...")
                return ApiResponse(success=True, data={"caption": caption})

            return ApiResponse(success=False, data=resp_body, message="No caption candidates")

        except urllib.error.HTTPError as e:
            error_data = ""
            try:
                error_data = e.read().decode("utf-8")
            except Exception:
                pass
            logger.error(f"❌ <<< captionImage {e.code}: {error_data[:200]}")
            return ApiResponse(success=False, message=f"HTTP {e.code}: {error_data[:300]}")
        except Exception as e:
            logger.error(f"❌ <<< captionImage exception: {e}")
            return ApiResponse(success=False, message=str(e))

    def upload_image(
        self,
        session_token: str,
        image_base64: str,
        media_category: str = "MEDIA_CATEGORY_SUBJECT",
        workflow_id: str = "",
    ) -> ApiResponse:
        """
        POST labs.google/fx/api/trpc/backbone.uploadImage

        Uploads an image (as base64 data URI) and returns uploadMediaGenerationId.
        """
        url = f"{LABS_BASE_URL}/api/trpc/backbone.uploadImage"
        session_id = f";{int(time.time() * 1000)}"

        payload = {
            "json": {
                "clientContext": {
                    "workflowId": workflow_id,
                    "sessionId": session_id,
                },
                "uploadMediaInput": {
                    "mediaCategory": media_category,
                    "rawBytes": image_base64,
                },
            }
        }

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Origin": "https://labs.google",
            "Referer": "https://labs.google/",
            "Cookie": f"__Secure-next-auth.session-token={session_token}",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/144.0.0.0 Safari/537.36",
        }

        try:
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            logger.info(f"📤 >>> POST uploadImage ({media_category})")

            with urllib.request.urlopen(req, timeout=60) as resp:
                resp_body = json.loads(resp.read().decode("utf-8"))

            result = resp_body.get("result", {}).get("data", {}).get("json", {}).get("result", {})
            upload_id = result.get("uploadMediaGenerationId", "")

            if upload_id:
                logger.info(f"📤 <<< uploadMediaGenerationId: {upload_id[:40]}...")
                return ApiResponse(
                    success=True,
                    data={"uploadMediaGenerationId": upload_id},
                )

            return ApiResponse(success=False, data=resp_body, message="No uploadMediaGenerationId")

        except urllib.error.HTTPError as e:
            error_data = ""
            try:
                error_data = e.read().decode("utf-8")
            except Exception:
                pass
            logger.error(f"❌ <<< uploadImage {e.code}: {error_data[:200]}")
            return ApiResponse(success=False, message=f"HTTP {e.code}: {error_data[:300]}")
        except Exception as e:
            logger.error(f"❌ <<< uploadImage exception: {e}")
            return ApiResponse(success=False, message=str(e))

    def upload_reference_image(
        self,
        session_token: str,
        image_path: str,
        category: str,
        workflow_id: str = "",
    ) -> ApiResponse:
        """
        Convenience: read file → base64 data URI → captionImage + uploadImage.

        Args:
            image_path: Local file path to the image.
            category: One of "title", "scene", "style".

        Returns ApiResponse with data = {uploadMediaGenerationId, caption, mediaCategory}.
        """
        import base64
        import os

        media_category = self.MEDIA_CATEGORY_MAP.get(category, "MEDIA_CATEGORY_SUBJECT")

        # Read file and convert to base64 data URI
        try:
            ext = os.path.splitext(image_path)[1].lower().lstrip(".")
            mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                    "webp": "image/webp", "gif": "image/gif"}.get(ext, "image/png")
            with open(image_path, "rb") as f:
                raw = f.read()
            b64 = base64.b64encode(raw).decode("ascii")
            data_uri = f"data:{mime};base64,{b64}"
        except Exception as e:
            logger.error(f"❌ Failed to read image {image_path}: {e}")
            return ApiResponse(success=False, message=f"Cannot read image: {e}")

        # Step 1: Caption
        caption = ""
        caption_resp = self.caption_image(session_token, data_uri, media_category, workflow_id)
        if caption_resp.success:
            caption = caption_resp.data.get("caption", "")

        # Step 2: Upload
        upload_resp = self.upload_image(session_token, data_uri, media_category, workflow_id)
        if not upload_resp.success:
            return upload_resp

        upload_id = upload_resp.data.get("uploadMediaGenerationId", "")
        return ApiResponse(
            success=True,
            data={
                "uploadMediaGenerationId": upload_id,
                "caption": caption,
                "mediaCategory": media_category,
            },
            message="Reference image uploaded",
        )

    # ── Generate Image via Whisk API ──────────────────────────────────

    def generate_image(
        self,
        google_access_token: str,
        workflow_id: str,
        prompt: str,
        aspect_ratio: str = "16:9",
        image_model: str = "IMAGEN_3_5",
        seed: int | None = None,
        media_inputs: list[dict] | None = None,
        timeout: int = 60,
    ) -> ApiResponse:
        """
        POST aisandbox-pa.googleapis.com/v1/whisk:generateImage

        Uses a Google OAuth access_token (ya29.a0...) to generate an image.
        Returns ApiResponse with data containing base64 encoded image.
        """
        if seed is None:
            seed = random.randint(100000, 999999)

        api_ratio = ASPECT_RATIO_MAP.get(aspect_ratio, "IMAGE_ASPECT_RATIO_LANDSCAPE")
        session_id = f";{int(time.time() * 1000)}"

        # Choose endpoint and payload based on whether ref images are present
        if media_inputs:
            # With reference images → runImageRecipe
            api_url = WHISK_RECIPE_URL
            payload = {
                "clientContext": {
                    "workflowId": workflow_id,
                    "tool": "BACKBONE",
                    "sessionId": session_id,
                },
                "seed": seed,
                "imageModelSettings": {
                    "imageModel": image_model,
                    "aspectRatio": api_ratio,
                },
                "userInstruction": prompt,
                "recipeMediaInputs": [
                    {
                        "caption": mi.get("caption", ""),
                        "mediaInput": {
                            "mediaCategory": mi["mediaCategory"],
                            "mediaGenerationId": mi["uploadMediaGenerationId"],
                        },
                    }
                    for mi in media_inputs
                ],
            }
        else:
            # Without reference images → generateImage
            api_url = WHISK_API_URL
            payload = {
                "clientContext": {
                    "workflowId": workflow_id,
                    "tool": "BACKBONE",
                    "sessionId": session_id,
                },
                "imageModelSettings": {
                    "imageModel": image_model,
                    "aspectRatio": api_ratio,
                },
                "seed": seed,
                "prompt": prompt,
                "mediaCategory": "MEDIA_CATEGORY_BOARD",
            }

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Accept": "*/*",
            "Content-Type": "text/plain;charset=UTF-8",
            "Authorization": f"Bearer {google_access_token}",
            "Origin": "https://labs.google",
            "Referer": "https://labs.google/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/144.0.0.0 Safari/537.36",
        }

        try:
            req = urllib.request.Request(
                api_url,
                data=body,
                headers=headers,
                method="POST",
            )

            logger.info(f"📤 >>> POST {api_url} (prompt={prompt[:50]}...)")
            logger.debug(f"📤 >>> Body: {json.dumps(payload, indent=2, ensure_ascii=False)}")

            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp_body = json.loads(resp.read().decode("utf-8"))

            logger.info(f"📥 <<< {resp.status} OK — image generated")

            # Extract first generated image
            panels = resp_body.get("imagePanels", [])
            if not panels:
                return ApiResponse(success=False, data=resp_body, message="No imagePanels in response")

            images = panels[0].get("generatedImages", [])
            if not images:
                return ApiResponse(success=False, data=resp_body, message="No generatedImages in response")

            img = images[0]
            return ApiResponse(
                success=True,
                data={
                    "encoded_image": img.get("encodedImage", ""),
                    "seed": img.get("seed", seed),
                    "media_generation_id": img.get("mediaGenerationId", ""),
                    "workflow_id": resp_body.get("workflowId", workflow_id),
                    "prompt": img.get("prompt", prompt),
                },
                message="Image generated successfully",
            )

        except urllib.error.HTTPError as e:
            error_data = ""
            try:
                error_data = e.read().decode("utf-8")
            except Exception:
                pass
            logger.error(f"❌ <<< {e.code} Error in generate_image")
            logger.debug(f"📥 <<< Response: {error_data}")
            return ApiResponse(success=False, message=f"HTTP {e.code}: {error_data[:300]}")
        except urllib.error.URLError as e:
            logger.error(f"❌ <<< Connection failed: {e.reason}")
            return ApiResponse(success=False, message="Cannot connect to Google API")
        except Exception as e:
            logger.error(f"❌ <<< generate_image exception: {e}")
            return ApiResponse(success=False, message=str(e))

    def get_credits(self, google_access_token: str, timeout: int = 10) -> ApiResponse:
        """
        POST aisandbox-pa.googleapis.com/v1/whisk:getVideoCreditStatus

        Returns ApiResponse with data containing credits count.
        """
        body = b"{}"
        headers = {
            "Accept": "*/*",
            "Content-Type": "text/plain;charset=UTF-8",
            "Authorization": f"Bearer {google_access_token}",
            "Origin": "https://labs.google",
            "Referer": "https://labs.google/",
        }

        try:
            req = urllib.request.Request(
                WHISK_CREDIT_URL,
                data=body,
                headers=headers,
                method="POST",
            )
            logger.info("📤 >>> POST getVideoCreditStatus")

            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp_body = json.loads(resp.read().decode("utf-8"))

            credits = resp_body.get("credits", 0)
            logger.info(f"📥 <<< 200 OK — credits={credits}")
            return ApiResponse(success=True, data=resp_body)

        except urllib.error.HTTPError as e:
            logger.error(f"❌ <<< {e.code} Error in get_credits")
            return ApiResponse(success=False, message=f"HTTP {e.code}")
        except Exception as e:
            logger.error(f"❌ <<< get_credits exception: {e}")
            return ApiResponse(success=False, message=str(e))

