"""Artifacting effects for images - compression, VHS, digital glitches."""

import io

import numpy as np
from PIL import Image, ImageFilter


def apply_artifacting(input_path, output_path, intensity=0.5, artifact_type="jpeg"):
    """
    Apply various artifacting effects to an image.

    Args:
        input_path: Path to input image
        output_path: Path to save output image
        intensity: Artifact intensity (0.0 to 1.0)
        artifact_type: Type of artifacts ('jpeg', 'vhs', 'digital_glitch', 'color_bleed')
    """
    img = Image.open(input_path)

    # Convert to RGB if necessary
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGB")

    if artifact_type == "jpeg":
        result = apply_jpeg_artifacts(img, intensity)
    elif artifact_type == "vhs":
        result = apply_vhs_artifacts(img, intensity)
    elif artifact_type == "digital_glitch":
        result = apply_digital_glitch(img, intensity)
    elif artifact_type == "color_bleed":
        result = apply_color_bleed(img, intensity)
    else:
        result = img

    # Save result
    try:
        result.save(output_path, quality=95)
    except (OSError, IOError) as e:
        print(f"Error saving artifacting result: {e}")
        output_path_png = output_path.replace(".jpg", ".png")
        result.save(output_path_png)


def apply_jpeg_artifacts(img, intensity):
    """Apply JPEG compression artifacts."""
    # Lower quality = more artifacts
    quality = int(100 - (intensity * 90))  # Range: 100 to 10
    quality = max(1, min(100, quality))

    # Save to bytes buffer and reload to get compression artifacts
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    result = Image.open(buffer)

    return result


def apply_vhs_artifacts(img, intensity):
    """Apply VHS-style tracking errors and color bleeding."""
    img_array = np.array(img, dtype=np.float32)
    height, width = img_array.shape[:2]

    # Horizontal tracking lines (random displacement)
    if intensity > 0.1:
        num_lines = int(intensity * 30)
        for _ in range(num_lines):
            y = np.random.randint(0, height)
            line_height = np.random.randint(1, int(5 * intensity) + 1)
            shift = int(np.random.randint(-20, 20) * intensity)

            if y + line_height < height:
                line = img_array[y : y + line_height, :].copy()
                img_array[y : y + line_height, :] = 0

                # Shift the line
                if shift > 0 and shift < width:
                    img_array[y : y + line_height, shift:] = line[:, :-shift]
                elif shift < 0 and abs(shift) < width:
                    img_array[y : y + line_height, :shift] = line[:, abs(shift) :]

    # Color channel separation (VHS color bleeding)
    if intensity > 0.2 and len(img_array.shape) == 3:
        shift_amount = int(3 * intensity)
        if shift_amount > 0:
            # Shift red channel
            img_array[:, shift_amount:, 0] = img_array[:, :-shift_amount, 0]
            # Shift blue channel opposite direction
            img_array[:, :-shift_amount, 2] = img_array[:, shift_amount:, 2]

    # Add some noise to VHS effect
    if intensity > 0.3:
        noise = np.random.normal(0, intensity * 10, img_array.shape)
        img_array = img_array + noise

    img_array = np.clip(img_array, 0, 255).astype(np.uint8)
    return Image.fromarray(img_array, mode="RGB")


def apply_digital_glitch(img, intensity):
    """Apply digital glitch effects - block corruption, bit errors."""
    img_array = np.array(img, dtype=np.uint8)
    height, width = img_array.shape[:2]

    # Block corruption (like corrupted video frames)
    num_blocks = int(intensity * 50)
    for _ in range(num_blocks):
        block_w = np.random.randint(8, int(80 * intensity) + 8)
        block_h = np.random.randint(8, int(60 * intensity) + 8)
        x = np.random.randint(0, max(1, width - block_w))
        y = np.random.randint(0, max(1, height - block_h))

        # Random corruption type
        corruption = np.random.choice(["repeat", "shift", "zero", "noise"])

        if corruption == "repeat" and x > 0:
            # Repeat previous block (ensure dimensions match)
            prev_x_start = max(0, x - block_w)
            prev_block = img_array[y : y + block_h, prev_x_start:x]
            # Only copy if dimensions match
            if prev_block.shape[1] == block_w:
                img_array[y : y + block_h, x : x + block_w] = prev_block
            else:
                # If dimensions don't match, just fill with zeros
                img_array[y : y + block_h, x : x + block_w] = 0
        elif corruption == "shift":
            # Shift block data
            shift = np.random.randint(-block_w // 2, block_w // 2)
            if abs(shift) > 0:
                img_array[y : y + block_h, x : x + block_w] = np.roll(
                    img_array[y : y + block_h, x : x + block_w], shift, axis=1
                )
        elif corruption == "zero":
            # Black blocks
            img_array[y : y + block_h, x : x + block_w] = 0
        elif corruption == "noise":
            # Random noise blocks
            img_array[y : y + block_h, x : x + block_w] = np.random.randint(
                0, 256, (block_h, block_w, img_array.shape[2]), dtype=np.uint8
            )

    # Horizontal line displacement (datamoshing effect)
    if intensity > 0.5:
        num_displaced = int(intensity * 20)
        for _ in range(num_displaced):
            y = np.random.randint(0, height - 1)
            line_height = np.random.randint(1, 5)
            shift = np.random.randint(-width // 4, width // 4)

            if y + line_height < height:
                img_array[y : y + line_height, :] = np.roll(
                    img_array[y : y + line_height, :], shift, axis=1
                )

    return Image.fromarray(img_array, mode="RGB")


def apply_color_bleed(img, intensity):
    """Apply color bleeding/channel separation like old analog video."""
    # Split into RGB channels
    r, g, b = img.split()

    # Convert to arrays for shifting
    r_array = np.array(r, dtype=np.uint8)
    b_array = np.array(b, dtype=np.uint8)

    # Shift channels
    r_shifted = np.roll(r_array, int(intensity * 5), axis=1)
    b_shifted = np.roll(b_array, -int(intensity * 5), axis=1)

    # Convert back to PIL Images
    r_img = Image.fromarray(r_shifted, mode="L")
    g_img = g
    b_img = Image.fromarray(b_shifted, mode="L")

    # Apply blur based on intensity (using PIL instead of scipy)
    if intensity > 0.1:
        blur_radius = min(intensity * 3, 10)  # Cap at 10 to prevent excessive blur
        r_img = r_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        b_img = b_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        g_img = g_img.filter(ImageFilter.GaussianBlur(radius=blur_radius * 0.5))

    # Merge back
    result = Image.merge("RGB", (r_img, g_img, b_img))
    return result
