"""
Whisk Desktop — Mock API Sample Data Generators.

Mixin class providing sample data generation for development and testing.
"""
import random
import uuid
from datetime import datetime, timedelta

from app.api.models import TaskItem, CookieItem, ProjectItem, TokenItem


class SampleDataMixin:
    """Mixin providing sample data generators for MockApi."""

    SAMPLE_PROMPTS = [
        "+Herring Gull (Larus argentatus), pale yellow eye, winter-streaked gray-brown lines on white head/neck",
        "+Herring Gull (Larus argentatus), pale yellow eye, winter-streaked head/neck, yellow bill with red spot",
        "+Herring Gull (Larus argentatus), same identifying features (pale yellow eye; winter streaks; yellow bill)",
        "+Golden Eagle soaring over mountain ridge, wingspan fully extended, dramatic cloudy sky background",
        "+Red Fox (Vulpes vulpes) in autumn forest, bushy tail, alert posture, golden-orange fur",
        "+Atlantic Puffin on coastal cliff, colorful beak, black and white plumage, ocean background",
        "+Snow Leopard in Himalayan landscape, spotted grey coat, long bushy tail, rocky terrain",
        "+Monarch Butterfly on purple coneflower, orange and black wings spread, macro photography",
        "+Blue Whale surfacing, massive body emerging from deep blue ocean, water spray from blowhole",
        "+Japanese Macaque in hot spring, snow on head, steam rising, winter forest background",
    ]

    MODELS = ["Nano Banana Pro", "Flux Standard", "SDXL Ultra"]
    RATIOS = ["16:9", "9:16", "1:1", "4:3"]
    QUALITIES = ["1K", "2K", "4K"]

    def _generate_sample_tokens(self) -> list[TokenItem]:
        """Generate sample tokens for development."""
        import string
        now = datetime.now()
        return [
            TokenItem(
                id=str(uuid.uuid4()),
                name="Whisk API Key",
                value="whsk_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=32)),
                token_type="api_key",
                status="active",
                expires_at=now + timedelta(days=30),
                created_at=now - timedelta(days=5),
            ),
            TokenItem(
                id=str(uuid.uuid4()),
                name="Google OAuth Token",
                value="ya29." + ''.join(random.choices(string.ascii_letters + string.digits, k=40)),
                token_type="oauth",
                status="expired",
                expires_at=now - timedelta(hours=2),
                created_at=now - timedelta(days=10),
            ),
            TokenItem(
                id=str(uuid.uuid4()),
                name="Bearer Access Token",
                value="eyJhbGciOiJSUzI1NiIs..." + ''.join(random.choices(string.ascii_letters, k=20)),
                token_type="bearer",
                status="active",
                expires_at=now + timedelta(days=7),
                created_at=now - timedelta(days=1),
            ),
        ]

    def _generate_sample_projects(self) -> list[ProjectItem]:
        """Generate sample projects for development."""
        now = datetime.now()
        samples = [
            ("Bird Photography Collection", "High-quality bird images for nature magazine"),
            ("Product Marketing Assets", "E-commerce product photos with white background"),
            ("Fantasy Art Series", "Digital fantasy landscapes and character art"),
        ]
        projects = []
        for i, (name, desc) in enumerate(samples):
            projects.append(ProjectItem(
                id=str(uuid.uuid4()),
                name=name,
                description=desc,
                status="active" if i < 2 else "archived",
                created_at=now - timedelta(days=random.randint(1, 30)),
                updated_at=now - timedelta(hours=random.randint(1, 48)),
            ))
        return projects

    def _generate_sample_cookies(self) -> list[CookieItem]:
        """Generate sample cookies for development."""
        import string
        now = datetime.now()

        def _rand_name():
            suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            return f"cookie_{suffix}"

        return [
            CookieItem(
                id=str(uuid.uuid4()),
                name=_rand_name(),
                value="abc123def456ghi789jkl012mno345pqr678...",
                domain="labs.google",
                status="valid",
                expires_at=now + timedelta(days=7),
                added_at=now - timedelta(hours=2),
            ),
            CookieItem(
                id=str(uuid.uuid4()),
                name=_rand_name(),
                value="xyz789ghi012mno345pqr678stu901vwx234...",
                domain="labs.google",
                status="expired",
                expires_at=now - timedelta(hours=1),
                added_at=now - timedelta(days=3),
            ),
            CookieItem(
                id=str(uuid.uuid4()),
                name=_rand_name(),
                value="mno345pqr678stu901vwx234yza567bcd890...",
                domain="labs.google",
                status="unknown",
                expires_at=None,
                added_at=now - timedelta(days=1),
            ),
        ]

    def _generate_sample_queue(self) -> list[TaskItem]:
        """Generate 5 sample tasks matching the reference screenshot."""
        tasks = []
        now = datetime.now()
        statuses = ["completed", "completed", "completed", "completed", "running"]

        for i in range(5):
            status = statuses[i] if i < len(statuses) else "pending"
            task = TaskItem(
                id=str(uuid.uuid4()),
                stt=i + 1,
                task_name="Task 1",
                model="veo_3_1_t2v_fast",
                aspect_ratio="VIDEO_ASPECT_RATIO_LANDSCAPE",
                quality="1K",
                reference_images=[],
                prompt=self.SAMPLE_PROMPTS[i % len(self.SAMPLE_PROMPTS)],
                output_images=[],
                status=status,
                elapsed_seconds=random.randint(8, 25) if status != "pending" else 0,
                error_message="",
                created_at=now - timedelta(minutes=random.randint(0, 60)),
            )
            tasks.append(task)
        return tasks
