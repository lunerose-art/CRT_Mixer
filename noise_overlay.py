"""Noise overlay effects for images."""

import numpy as np
from PIL import Image


def apply_noise_overlay(input_path, output_path, intensity=0.1, noise_type="gaussian"):
    """
    Apply noise overlay to an image.

    Args:
        input_path: Path to input image
        output_path: Path to save output image
        intensity: Noise intensity (0.0 to 1.0)
        noise_type: Type of noise ('gaussian', 'salt_pepper', 'film_grain')
    """
    img = Image.open(input_path)

    # Convert to RGB if necessary (for JPEG compatibility)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGB")

    img_array = np.array(img, dtype=np.float32)

    if noise_type == "gaussian":
        # Gaussian noise
        noise = np.random.normal(0, intensity * 255, img_array.shape)
        noisy_img = img_array + noise

    elif noise_type == "salt_pepper":
        # Salt and pepper noise
        noisy_img = img_array.copy()
        # Salt
        salt_mask = np.random.random(img_array.shape[:2]) < (intensity / 2)
        noisy_img[salt_mask] = 255
        # Pepper
        pepper_mask = np.random.random(img_array.shape[:2]) < (intensity / 2)
        noisy_img[pepper_mask] = 0

    elif noise_type == "film_grain":
        # Film grain - monochrome noise with reduced intensity
        grain = np.random.normal(0, intensity * 128, img_array.shape[:2])
        # Expand grain to all channels
        if len(img_array.shape) == 3:
            grain = np.stack([grain] * img_array.shape[2], axis=2)
        noisy_img = img_array + grain

    else:
        noisy_img = img_array

    # Clip values to valid range
    noisy_img = np.clip(noisy_img, 0, 255).astype(np.uint8)

    # Create result image with proper mode
    if len(noisy_img.shape) == 2:
        result = Image.fromarray(noisy_img, mode="L")
    else:
        result = Image.fromarray(noisy_img, mode="RGB")

    # Save with error handling
    try:
        result.save(output_path, quality=95)
    except (OSError, IOError) as e:
        print(f"Error saving noise overlay: {e}")
        # Try saving as PNG instead
        output_path_png = output_path.replace(".jpg", ".png")
        result.save(output_path_png)
        print(f"Saved as PNG instead: {output_path_png}")
