"""
Whisk Desktop — Workflow API Client.

Handles workflow creation on Google Labs, linking to the server flow,
and image generation via the whisk:generateImage endpoint:
- Create workflow (POST labs.google/fx/api/trpc/media.createOrUpdateWorkflow)
- Link workflow to flow (POST {FLOW_BASE_URL}/tools/upload/frame/run?type=VEO3_V2)
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
    VIDEO_GENERATE_URL, VIDEO_STATUS_URL, ASPECT_RATIO_MAP,
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
        POST labs.google/fx/api/trpc/project.createProject

        Uses cookie-based auth (session-token) to create a project on Labs.
        Returns ApiResponse with data containing workflowId (projectId).
        """
        from datetime import datetime
        now = datetime.now()
        project_title = now.strftime("%b %d - %H:%M")

        payload = {
            "json": {
                "projectTitle": project_title,
                "toolName": "PINHOLE",
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
            "Referer": "https://labs.google/fx/vi/tools/flow",
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

            # Extract projectId from nested tRPC response
            result = (resp_body
                      .get("result", {})
                      .get("data", {})
                      .get("json", {})
                      .get("result", {}))
            project_id = result.get("projectId", "")
            project_info = result.get("projectInfo", {})
            project_title_resp = project_info.get("projectTitle", project_title)

            if project_id:
                return ApiResponse(
                    success=True,
                    data={
                        "workflowId": project_id,
                        "workflowName": project_title_resp,
                    },
                    message=f"Project created: {project_id}",
                )
            else:
                return ApiResponse(
                    success=False,
                    data=resp_body,
                    message="No projectId in response",
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
        POST /tools/upload/frame/run?type=VEO3_V2

        Links a workflowId (project_id) to a server flow.
        """
        params = urllib.parse.urlencode({"type": "VEO3_V2"})
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
        aspect_ratio: str = "VIDEO_ASPECT_RATIO_LANDSCAPE",
        image_model: str = "veo_3_1_t2v_fast",
        seed: int | None = None,
        media_inputs: list[dict] | None = None,
        timeout: int = 60,
        recaptcha_token: str = "",
    ) -> ApiResponse:
        """
        POST aisandbox-pa.googleapis.com/v1/video:batchAsyncGenerateVideoText

        Uses a Google OAuth access_token (ya29.a0...) to generate a video.
        Returns ApiResponse with data containing video generation info.
        """
        import uuid

        if seed is None:
            seed = random.randint(1000, 99999)

        api_ratio = ASPECT_RATIO_MAP.get(aspect_ratio, "VIDEO_ASPECT_RATIO_LANDSCAPE")
        session_id = f";{int(time.time() * 1000)}"
        scene_id = str(uuid.uuid4())

        api_url = VIDEO_GENERATE_URL
        payload = {
            "clientContext": {
                "sessionId": session_id,
                "projectId": workflow_id,
                "tool": "PINHOLE",
                "userPaygateTier": "PAYGATE_TIER_ONE",
            },
            "requests": [
                {
                    "aspectRatio": api_ratio,
                    "seed": seed,
                    "textInput": {
                        "prompt": prompt,
                    },
                    "videoModelKey": image_model,
                    "metadata": {
                        "sceneId": scene_id,
                    },
                }
            ],
        }

        # Add recaptcha context if token is provided
        if recaptcha_token:
            payload["clientContext"]["recaptchaContext"] = {
                "token": recaptcha_token,
                "applicationType": "RECAPTCHA_APPLICATION_TYPE_WEB",
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

            logger.info(f"📥 <<< {resp.status} OK — video generation started")
            logger.debug(f"📥 <<< Response: {json.dumps(resp_body, indent=2, ensure_ascii=False)}")

            return ApiResponse(
                success=True,
                data={
                    "response": resp_body,
                    "seed": seed,
                    "scene_id": scene_id,
                    "workflow_id": workflow_id,
                    "prompt": prompt,
                },
                message="Video generation started",
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

    # ── Check video generation status (polling) ───────────────────────

    def check_video_status(
        self,
        google_access_token: str,
        operation_name: str,
        scene_id: str,
        current_status: str = "MEDIA_GENERATION_STATUS_ACTIVE",
        timeout: int = 30,
    ) -> ApiResponse:
        """
        POST aisandbox-pa.googleapis.com/v1/video:batchCheckAsyncVideoGenerationStatus

        Polls the status of an async video generation operation.
        Returns ApiResponse with status and video URL when complete.
        """
        payload = {
            "operations": [
                {
                    "operation": {
                        "name": operation_name,
                    },
                    "sceneId": scene_id,
                    "status": current_status,
                }
            ]
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
                VIDEO_STATUS_URL,
                data=body,
                headers=headers,
                method="POST",
            )

            logger.info(f"📤 >>> POST {VIDEO_STATUS_URL} (op={operation_name[:16]}...)")
            logger.debug(f"📤 >>> Body: {json.dumps(payload, indent=2)}")

            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp_body = json.loads(resp.read().decode("utf-8"))

            logger.debug(f"📥 <<< Response: {json.dumps(resp_body, indent=2)}")

            operations = resp_body.get("operations", [])
            if not operations:
                return ApiResponse(
                    success=False,
                    data=resp_body,
                    message="No operations in status response",
                )

            op = operations[0]
            status = op.get("status", "")
            remaining_credits = resp_body.get("remainingCredits")

            result_data = {
                "status": status,
                "operation_name": operation_name,
                "scene_id": scene_id,
                "remaining_credits": remaining_credits,
            }

            if status == "MEDIA_GENERATION_STATUS_SUCCESSFUL":
                # Extract video URL from metadata
                metadata = op.get("operation", {}).get("metadata", {})
                video = metadata.get("video", {})
                fife_url = video.get("fifeUrl", "")
                media_gen_id = video.get("mediaGenerationId", "")
                prompt = video.get("prompt", "")
                seed = video.get("seed")

                result_data.update({
                    "fife_url": fife_url,
                    "media_generation_id": media_gen_id,
                    "prompt": prompt,
                    "seed": seed,
                    "video_metadata": video,
                })

                logger.info(f"📥 <<< ✅ Video ready! URL={fife_url[:80]}...")
                return ApiResponse(
                    success=True,
                    data=result_data,
                    message="Video generation completed",
                )

            elif status == "MEDIA_GENERATION_STATUS_FAILED":
                error_msg = op.get("error", {}).get("message", "Generation failed")
                logger.error(f"📥 <<< ❌ Video generation failed: {error_msg}")
                return ApiResponse(
                    success=False,
                    data=result_data,
                    message=f"Video generation failed: {error_msg}",
                )

            else:
                # Still active/processing
                logger.info(f"📥 <<< ⏳ Status: {status}")
                return ApiResponse(
                    success=True,
                    data=result_data,
                    message=f"Status: {status}",
                )

        except urllib.error.HTTPError as e:
            error_data = ""
            try:
                error_data = e.read().decode("utf-8")
            except Exception:
                pass
            logger.error(f"❌ <<< {e.code} Error in check_video_status")
            return ApiResponse(success=False, message=f"HTTP {e.code}: {error_data[:200]}")
        except urllib.error.URLError as e:
            logger.error(f"❌ <<< Connection failed: {e.reason}")
            return ApiResponse(success=False, message="Cannot connect to Google API")
        except Exception as e:
            logger.error(f"❌ <<< check_video_status exception: {e}")
            return ApiResponse(success=False, message=str(e))

    def get_credit_status(self, google_access_token: str, timeout: int = 10) -> ApiResponse:
        """
        POST aisandbox-pa.googleapis.com/v1/whisk:getVideoCreditStatus

        Fetches the user's remaining Google Labs credits.
        Returns ApiResponse with data = {"credits": int, ...}.
        """
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
                WHISK_CREDIT_URL,
                data=b"{}",
                headers=headers,
                method="POST",
            )

            logger.info(f"📤 >>> POST {WHISK_CREDIT_URL}")

            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp_body = json.loads(resp.read().decode("utf-8"))

            credits_val = resp_body.get("credits", 0)
            logger.info(f"📥 <<< 200 OK — credits: {credits_val}")

            return ApiResponse(success=True, data=resp_body)

        except urllib.error.HTTPError as e:
            error_data = ""
            try:
                error_data = e.read().decode("utf-8")
            except Exception:
                pass
            logger.error(f"❌ <<< {e.code} Error in get_credit_status")
            return ApiResponse(success=False, message=f"HTTP {e.code}: {error_data[:200]}")
        except Exception as e:
            logger.error(f"❌ <<< get_credit_status exception: {e}")
            return ApiResponse(success=False, message=str(e))
