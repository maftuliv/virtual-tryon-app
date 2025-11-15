"""NanoBanana AI API client for virtual try-on."""

import time
from typing import Dict, Optional

import requests
from PIL import Image

from backend.logger import get_logger

logger = get_logger(__name__)


class NanoBananaClient:
    """
    Client for NanoBanana AI API (Google Gemini 2.5 Flash).

    Official documentation: https://docs.nanobananaapi.ai/quickstart
    Pricing: $0.02 per image
    Speed: 5-10 seconds average generation time
    """

    BASE_URL = "https://api.nanobananaapi.ai"

    def __init__(self, api_key: str, timeout: int = 120):
        """
        Initialize NanoBanana client.

        Args:
            api_key: NanoBanana API key
            timeout: Maximum time to wait for generation (default: 120s)
        """
        self.api_key = api_key
        self.timeout = timeout
        self.logger = get_logger(__name__)

    def generate_tryon(
        self,
        person_image_url: str,
        garment_image_url: str,
        category: str = "auto",
        output_path: Optional[str] = None,
    ) -> Dict:
        """
        Generate virtual try-on result.

        Args:
            person_image_url: Public URL to person image
            garment_image_url: Public URL to garment image
            category: Garment category ("auto", "tops", "bottoms", "one-pieces")
            output_path: Where to save result image (optional)

        Returns:
            Dictionary with result:
            {
                'task_id': str,
                'result_url': str,
                'result_path': str (if output_path provided),
                'status': 'completed',
                'processing_time': float (seconds),
                'width': int,
                'height': int
            }

        Raises:
            ValueError: If API returns error or times out
            requests.RequestException: If network error occurs
        """
        start_time = time.time()

        # Validate inputs
        if not self.api_key:
            raise ValueError(
                "NANOBANANA_API_KEY not set. "
                "Get your API key from: https://nanobananaapi.ai/api-key"
            )

        # Verify URLs are accessible
        self._verify_urls(person_image_url, garment_image_url)

        # Submit task
        task_id = self._submit_task(person_image_url, garment_image_url, category)
        self.logger.info(f"Task created: {task_id}")

        # Poll for completion
        result_url = self._poll_task_status(task_id)
        self.logger.info(f"Generation complete! Result URL: {result_url}")

        # Download result (if output path provided)
        result_path = None
        width, height = None, None

        if output_path:
            result_path, width, height = self._download_result(result_url, output_path)
            self.logger.info(f"Result saved: {result_path} ({width}x{height}px)")

        processing_time = time.time() - start_time

        return {
            "task_id": task_id,
            "result_url": result_url,
            "result_path": result_path,
            "status": "completed",
            "processing_time": processing_time,
            "width": width,
            "height": height,
        }

    def _verify_urls(self, person_url: str, garment_url: str):
        """
        Verify image URLs are accessible.

        Raises:
            ValueError: If URLs are not accessible
        """
        self.logger.info("Verifying image URLs are accessible...")

        try:
            person_check = requests.head(person_url, timeout=5, allow_redirects=True)
            garment_check = requests.head(garment_url, timeout=5, allow_redirects=True)

            if person_check.status_code != 200:
                self.logger.warning(
                    f"Person image URL returned {person_check.status_code}: {person_url}"
                )
            else:
                self.logger.info("Person image URL is accessible")

            if garment_check.status_code != 200:
                self.logger.warning(
                    f"Garment image URL returned {garment_check.status_code}: {garment_url}"
                )
            else:
                self.logger.info("Garment image URL is accessible")

        except Exception as e:
            self.logger.warning(f"Could not verify URL accessibility: {e}")
            self.logger.warning("Continuing anyway - API will handle errors...")

    def _submit_task(self, person_url: str, garment_url: str, category: str) -> str:
        """
        Submit generation task to NanoBanana API.

        Returns:
            Task ID string

        Raises:
            ValueError: If API returns error
        """
        # Create optimized prompt for virtual try-on
        category_map = {
            "auto": "garment",
            "tops": "top",
            "bottoms": "bottom",
            "one-pieces": "full outfit",
        }
        garment_type = category_map.get(category, "garment")

        prompt = (
            f"Replace the clothing on the person in the first image with the {garment_type} "
            f"shown in the second image. The {garment_type} must be placed accurately on the "
            f"person's body, matching their pose and body shape. Preserve the exact colors, "
            f"patterns, textures, and style of the {garment_type} from the second image. "
            f"Ensure the {garment_type} fits naturally with realistic shadows, lighting, and "
            f"fabric draping. The result should show the person wearing the {garment_type}, "
            f"not just the original image."
        )

        self.logger.info(f"Prompt: {prompt[:100]}...")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "prompt": prompt,
            "type": "IMAGETOIAMGE",  # API has typo: IAMGE not IMAGE
            "numImages": 1,
            "imageUrls": [person_url, garment_url],
            "callBackUrl": "",  # We'll poll instead
        }

        generate_url = f"{self.BASE_URL}/generate"
        self.logger.info(f"POST to: {generate_url}")

        try:
            response = requests.post(generate_url, headers=headers, json=payload, timeout=30)
            self.logger.info(f"API Response Status: {response.status_code}")

            if response.status_code != 200:
                error_msg = f"NanoBanana API error: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            result = response.json()
            self.logger.info(f"Initial response: {result}")

            if result.get("code") != 200:
                raise ValueError(f"NanoBanana API error: {result.get('msg', 'Unknown error')}")

            task_id = result.get("data", {}).get("taskId")
            if not task_id:
                raise ValueError("No taskId returned from NanoBanana API")

            return task_id

        except requests.RequestException as e:
            self.logger.error(f"Network error submitting task: {e}", exc_info=True)
            raise ValueError(f"Failed to submit task: {e}")

    def _poll_task_status(self, task_id: str) -> str:
        """
        Poll task status until completion.

        Args:
            task_id: Task ID to poll

        Returns:
            Result image URL

        Raises:
            ValueError: If task fails or times out
        """
        max_attempts = 60  # 120 seconds total (60 * 2s)
        poll_interval = 2

        headers = {"Authorization": f"Bearer {self.api_key}"}

        for attempt in range(max_attempts):
            if attempt > 0:
                time.sleep(poll_interval)

            status_url = f"{self.BASE_URL}/record-info?taskId={task_id}"
            self.logger.info(f"Status check {attempt + 1}/{max_attempts}")

            try:
                status_response = requests.get(status_url, headers=headers, timeout=10)
            except requests.RequestException as e:
                self.logger.warning(f"Request failed: {e}")
                continue  # Continue polling on network errors

            if status_response.status_code != 200:
                if status_response.status_code == 404:
                    self.logger.warning("Task not found yet (404), continuing...")
                else:
                    self.logger.warning(
                        f"Status check failed: {status_response.status_code} - "
                        f"{status_response.text[:200]}"
                    )
                continue

            try:
                status_data = status_response.json()
            except ValueError as e:
                self.logger.warning(f"Failed to parse JSON: {e}")
                continue

            # Extract data object
            data_obj = status_data.get("data", {})
            if not isinstance(data_obj, dict):
                self.logger.warning("Invalid data structure, continuing...")
                continue

            # Parse success flag
            success_flag = self._parse_success_flag(data_obj)
            self.logger.info(f"Success flag: {success_flag}")

            if success_flag == 1:
                # Task completed successfully
                return self._extract_result_url(status_data, data_obj)

            elif success_flag == 2:
                error_msg = data_obj.get("errorMessage") or status_data.get(
                    "msg", "Task creation failed"
                )
                raise ValueError(f"Task creation failed: {error_msg}")

            elif success_flag == 3:
                error_msg = data_obj.get("errorMessage") or status_data.get(
                    "msg", "Generation failed"
                )
                raise ValueError(f"Generation failed: {error_msg}")

            # success_flag == 0 means still processing
            self.logger.info(f"Task still processing (successFlag={success_flag})")

        # Timeout
        raise ValueError(
            f"Task timed out after {max_attempts * poll_interval} seconds "
            f"({max_attempts} attempts)"
        )

    def _parse_success_flag(self, data_obj: Dict) -> int:
        """Parse success flag from API response (can be int or string)."""
        success_flag_raw = data_obj.get("successFlag", 0)

        if isinstance(success_flag_raw, str):
            try:
                return int(success_flag_raw)
            except (ValueError, TypeError):
                return 0
        else:
            return int(success_flag_raw) if success_flag_raw else 0

    def _extract_result_url(self, status_data: Dict, data_obj: Dict) -> str:
        """
        Extract result image URL from API response.

        Raises:
            ValueError: If result URL not found
        """
        self.logger.info("Task completed! Extracting result URL...")

        # resultImageUrl is in data.response.resultImageUrl
        result_image_url = None
        response_obj = data_obj.get("response", {})

        if isinstance(response_obj, dict):
            result_image_url = response_obj.get("resultImageUrl") or response_obj.get(
                "result_image_url"
            )

        # Fallback: check top-level
        if not result_image_url:
            result_image_url = status_data.get("resultImageUrl") or status_data.get(
                "result_image_url"
            )

        if not result_image_url:
            self.logger.error(f"Full status_data structure: {status_data}")
            raise ValueError(
                "No result image URL in completed task. Check logs for full response structure."
            )

        return result_image_url

    def _download_result(self, result_url: str, output_path: str) -> tuple:
        """
        Download result image and verify.

        Returns:
            Tuple of (output_path, width, height)

        Raises:
            ValueError: If download or verification fails
        """
        self.logger.info(f"Downloading result from: {result_url}")

        try:
            img_response = requests.get(result_url, timeout=30)

            if img_response.status_code != 200:
                raise ValueError(f"Failed to download result: HTTP {img_response.status_code}")

            # Save image
            with open(output_path, "wb") as img_file:
                img_file.write(img_response.content)

            file_size = len(img_response.content)
            self.logger.info(f"Downloaded: {output_path} ({file_size} bytes)")

            # Verify image
            try:
                result_img = Image.open(output_path)
                width, height = result_img.size
                self.logger.info(f"Image verified: {width}x{height} pixels")
                return output_path, width, height

            except Exception as e:
                self.logger.warning(f"Could not verify result image: {e}")
                return output_path, None, None

        except requests.RequestException as e:
            raise ValueError(f"Failed to download result image: {e}")
