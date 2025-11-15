"""Image processing and validation service."""

import base64
import os
from typing import Dict, List, Optional, Set, Tuple

import requests
from flask import Request
from PIL import Image

from backend.logger import get_logger

logger = get_logger(__name__)


class ImageService:
    """
    Service for image processing, validation, and URL generation.

    Responsibilities:
    - File validation (allowed extensions)
    - Image quality validation (resolution, aspect ratio, brightness)
    - Image preprocessing (resize, optimize, convert to JPEG)
    - Base64 conversion
    - Public URL generation (Railway or ImgBB)

    No direct database or external API calls.
    """

    ALLOWED_EXTENSIONS: Set[str] = {"png", "jpg", "jpeg"}
    DEFAULT_MAX_DIMENSION = 2000
    DEFAULT_QUALITY = 95

    def __init__(self, upload_folder: str, imgbb_api_key: Optional[str] = None):
        """
        Initialize image service.

        Args:
            upload_folder: Path to upload directory
            imgbb_api_key: Optional ImgBB API key for alternative hosting
        """
        self.upload_folder = upload_folder
        self.imgbb_api_key = imgbb_api_key
        self.logger = get_logger(__name__)

    def validate_file(self, filename: str) -> bool:
        """
        Check if filename has an allowed extension.

        Args:
            filename: Name of the file

        Returns:
            True if extension is allowed, False otherwise
        """
        if "." not in filename:
            return False
        extension = filename.rsplit(".", 1)[1].lower()
        return extension in self.ALLOWED_EXTENSIONS

    def validate_image_quality(self, image_path: str) -> Tuple[bool, List[str]]:
        """
        Validate image quality and provide recommendations.

        Checks:
        - Minimum resolution (512x512)
        - Maximum resolution (2000x2000)
        - Aspect ratio compatibility
        - Brightness levels

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (is_valid: bool, warnings: List[str])
        """
        warnings = []

        try:
            img = Image.open(image_path)
            width, height = img.size

            # Check minimum resolution
            if width < 512 or height < 512:
                warnings.append("Низкое разрешение - рекомендуется минимум 512px")

            # Check if image is too large
            if height > 2000 or width > 2000:
                warnings.append("Изображение будет автоматически уменьшено до 2000px")

            # Check aspect ratio
            aspect_ratio = width / height
            supported_ratios = {
                "1:1": 1.0,
                "3:4": 0.75,
                "4:3": 1.33,
                "9:16": 0.56,
                "16:9": 1.78,
                "2:3": 0.67,
                "3:2": 1.5,
                "4:5": 0.8,
                "5:4": 1.25,
            }

            # Find closest supported ratio
            closest_ratio = min(supported_ratios.values(), key=lambda x: abs(x - aspect_ratio))
            if abs(aspect_ratio - closest_ratio) > 0.15:
                warnings.append("Необычное соотношение сторон - может повлиять на качество")

            # Check brightness (simple histogram analysis)
            grayscale = img.convert("L")
            histogram = grayscale.histogram()
            pixels = sum(histogram)
            brightness = sum(i * histogram[i] for i in range(256)) / pixels

            if brightness < 80:
                warnings.append("Изображение слишком темное - улучшите освещение")
            elif brightness > 200:
                warnings.append("Изображение слишком яркое - проверьте экспозицию")

            self.logger.info(
                f"Image validation: {width}x{height}, brightness: {brightness:.1f}, "
                f"warnings: {len(warnings)}"
            )

            return True, warnings

        except Exception as e:
            self.logger.error(f"Failed to validate {image_path}: {e}", exc_info=True)
            return False, ["Не удалось проанализировать изображение"]

    def preprocess_image(
        self, image_path: str, max_dimension: int = DEFAULT_MAX_DIMENSION, quality: int = DEFAULT_QUALITY
    ) -> str:
        """
        Preprocess image for optimal quality.

        Steps:
        - Convert RGBA/LA/P to RGB (with white background)
        - Resize if any dimension exceeds max_dimension (maintaining aspect ratio)
        - Save as optimized JPEG with specified quality
        - Use LANCZOS resampling for quality preservation

        Important: NanoBanana API requires BOTH width AND height <= 2000 pixels

        Args:
            image_path: Path to input image
            max_dimension: Maximum allowed dimension (default: 2000)
            quality: JPEG quality (default: 95)

        Returns:
            Path to preprocessed image (original_name_optimized.jpg)

        Raises:
            ValueError: If final dimensions exceed max_dimension
        """
        try:
            img = Image.open(image_path)

            # Convert RGBA to RGB if needed
            if img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # Resize if ANY dimension exceeds max_dimension
            width, height = img.size
            original_size = (width, height)

            if width > max_dimension or height > max_dimension:
                # Calculate ratio to fit within max_dimension
                ratio = min(max_dimension / width, max_dimension / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)

                # Ensure both dimensions are within limit
                if new_width > max_dimension:
                    new_width = max_dimension
                if new_height > max_dimension:
                    new_height = max_dimension

                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                self.logger.info(
                    f"Resized image from {original_size[0]}x{original_size[1]} to {new_width}x{new_height}"
                )

                # Double-check dimensions after resize
                final_width, final_height = img.size
                if final_width > max_dimension or final_height > max_dimension:
                    self.logger.warning(
                        f"Final size {final_width}x{final_height} still exceeds {max_dimension}!"
                    )
            else:
                self.logger.info(f"Image size {width}x{height} is within limits (max: {max_dimension})")

            # Save as optimized JPEG
            output_path = image_path.rsplit(".", 1)[0] + "_optimized.jpg"
            img.save(output_path, "JPEG", quality=quality, optimize=True)

            # Verify final dimensions
            final_img = Image.open(output_path)
            final_width, final_height = final_img.size
            self.logger.info(f"Optimized image saved: {output_path} (final size: {final_width}x{final_height})")

            if final_width > max_dimension or final_height > max_dimension:
                raise ValueError(
                    f"Final image dimensions {final_width}x{final_height} exceed maximum {max_dimension} pixels!"
                )

            return output_path

        except Exception as e:
            self.logger.error(f"Failed to preprocess {image_path}: {e}", exc_info=True)
            # Return original path if preprocessing fails (but this might cause API errors)
            return image_path

    def image_to_base64(self, image_path: str) -> str:
        """
        Convert image file to base64 string.

        Args:
            image_path: Path to image file

        Returns:
            Base64-encoded string
        """
        with open(image_path, "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode("utf-8")
        return img_data

    def save_base64_image(self, base64_string: str, output_path: str) -> str:
        """
        Save base64-encoded image to file.

        Args:
            base64_string: Base64-encoded image data (with or without data URL prefix)
            output_path: Path where to save the image

        Returns:
            Path to saved image
        """
        # Remove data URL prefix if present
        if "," in base64_string:
            base64_string = base64_string.split(",", 1)[1]

        img_data = base64.b64decode(base64_string)
        with open(output_path, "wb") as img_file:
            img_file.write(img_data)
        return output_path

    def generate_public_url(self, image_path: str, request_obj: Optional[Request] = None) -> str:
        """
        Get public URL for image (NanoBanana API requires URLs, not base64).

        Strategy:
        1. Use Railway public URL to serve the uploaded file directly
        2. Fallback: Try ImgBB if imgbb_api_key is set
        3. Auto-detect domain from request if available

        Args:
            image_path: Path to image file
            request_obj: Flask request object (optional, for domain auto-detection)

        Returns:
            Public URL to the image
        """
        filename = os.path.basename(image_path)

        # Try to get domain from request first (most reliable)
        domain = None
        if request_obj:
            try:
                # Get host from request headers (works with custom domains)
                host = request_obj.headers.get("Host", "")
                if host:
                    # Remove port if present
                    domain = host.split(":")[0]
                    self.logger.info(f"Detected domain from request: {domain}")
            except Exception as e:
                self.logger.warning(f"Could not get domain from request: {e}")

        # Fallback to environment variable or default
        if not domain:
            domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "taptolook.net")
            self.logger.info(f"Using domain from environment/default: {domain}")

        # Construct public URL for the uploaded file
        public_url = f"https://{domain}/uploads/{filename}"

        self.logger.info(f"Generated public URL: {public_url}")

        # Verify file exists before generating URL
        if not os.path.exists(image_path):
            self.logger.warning(f"Image file does not exist: {image_path}")

        # Optional: Try ImgBB if API key is explicitly set (not required)
        if self.imgbb_api_key and self.imgbb_api_key != "":
            try:
                self.logger.info("Attempting to upload to ImgBB as alternative...")
                image_b64 = self.image_to_base64(image_path)

                imgbb_url = "https://api.imgbb.com/1/upload"
                payload = {"key": self.imgbb_api_key, "image": image_b64, "expiration": 600}  # 10 minutes

                response = requests.post(imgbb_url, data=payload, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        imgbb_public_url = result["data"]["url"]
                        self.logger.info(f"Successfully uploaded to ImgBB: {imgbb_public_url}")
                        return imgbb_public_url
            except Exception as e:
                self.logger.warning(f"ImgBB upload failed, using Railway URL: {e}")

        # Return Railway public URL
        return public_url

    def get_image_dimensions(self, image_path: str) -> Optional[Tuple[int, int]]:
        """
        Get image dimensions.

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (width, height) or None if failed
        """
        try:
            img = Image.open(image_path)
            return img.size
        except Exception as e:
            self.logger.error(f"Failed to get image dimensions: {e}")
            return None
