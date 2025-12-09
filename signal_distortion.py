import random

import numpy as np
from PIL import Image


def apply_scanline_shift(image_path, output_path, intensity=10, probability=0.1):
    """
    Shift random scanlines horizontally (VHS tracking error effect).

    Args:
        image_path: Input image path
        output_path: Output image path
        intensity: Maximum pixel shift amount
        probability: Chance each line gets shifted (0.0-1.0)
    """
    # Load image
    img = Image.open(image_path)
    img = img.convert("RGB")
    pixels = np.array(img)

    height, width = pixels.shape[:2]
    result = pixels.copy()

    for y in range(height):
        if random.random() < probability:
            # Random shift for this scanline
            shift = random.randint(-intensity, intensity)

            if shift > 0:
                # Shift right
                result[y, shift:] = pixels[y, :-shift]
                result[y, :shift] = pixels[y, -shift:]
            elif shift < 0:
                # Shift left
                result[y, :shift] = pixels[y, -shift:]
                result[y, -shift:] = pixels[y, :shift]

    # Save result
    result_img = Image.fromarray(result.astype("uint8"))
    result_img.save(output_path, quality=100)

    print(f"✓ Scanline shift applied: {output_path}")
    return output_path


def apply_signal_noise(image_path, output_path, amount=0.05):
    """
    Add analog signal noise (TV static effect).

    Args:
        image_path: Input image path
        output_path: Output image path
        amount: Noise intensity (0.0-1.0)
    """
    # Load image
    img = Image.open(image_path)
    img = img.convert("RGB")
    pixels = np.array(img).astype(np.float32)

    # Generate random noise
    noise = np.random.randn(*pixels.shape) * amount * 255

    # Add noise to image
    noisy = pixels + noise
    noisy = np.clip(noisy, 0, 255)

    # Save result
    result_img = Image.fromarray(noisy.astype("uint8"))
    result_img.save(output_path, quality=100)

    print(f"✓ Signal noise applied: {output_path}")
    return output_path


def apply_interlacing(image_path, output_path, strength=0.5):
    """
    Apply interlacing effect (odd/even scanline offset).

    Args:
        image_path: Input image path
        output_path: Output image path
        strength: Interlacing strength (0.0-1.0)
    """
    # Load image
    img = Image.open(image_path)
    img = img.convert("RGB")
    pixels = np.array(img).astype(np.float32)

    height, width = pixels.shape[:2]
    result = pixels.copy()

    # Darken alternating scanlines
    for y in range(0, height, 2):
        result[y] = result[y] * (1.0 - strength * 0.3)

    # Save result
    result_img = Image.fromarray(result.astype("uint8"))
    result_img.save(output_path, quality=100)

    print(f"✓ Interlacing applied: {output_path}")
    return output_path


def apply_vertical_hold(image_path, output_path, shift_amount=20):
    """
    Apply vertical hold sync error (image rolls vertically).

    Args:
        image_path: Input image path
        output_path: Output image path
        shift_amount: How many pixels to shift vertically
    """
    # Load image
    img = Image.open(image_path)
    img = img.convert("RGB")
    pixels = np.array(img)

    height, width = pixels.shape[:2]
    result = np.zeros_like(pixels)

    # Shift image vertically
    if shift_amount > 0:
        result[shift_amount:, :] = pixels[:-shift_amount, :]
        result[:shift_amount, :] = pixels[-shift_amount:, :]
    elif shift_amount < 0:
        shift_amount = abs(shift_amount)
        result[:-shift_amount, :] = pixels[shift_amount:, :]
        result[-shift_amount:, :] = pixels[:shift_amount, :]

    # Save result
    result_img = Image.fromarray(result.astype("uint8"))
    result_img.save(output_path, quality=100)

    print(f"✓ Vertical hold applied: {output_path}")
    return output_path


def apply_color_bleed(image_path, output_path, amount=3):
    """
    Apply color bleeding effect (chroma signal bleeding).

    Args:
        image_path: Input image path
        output_path: Output image path
        amount: Blur amount in pixels
    """
    # Load image
    img = Image.open(image_path)
    img = img.convert("RGB")
    pixels = np.array(img).astype(np.float32)

    height, width = pixels.shape[:2]
    result = pixels.copy()

    # Blur only the color channels horizontally
    for y in range(height):
        for x in range(amount, width - amount):
            # Average neighboring pixels for red and blue
            result[y, x, 0] = np.mean(pixels[y, x - amount : x + amount + 1, 0])
            result[y, x, 2] = np.mean(pixels[y, x - amount : x + amount + 1, 2])

    # Save result
    result_img = Image.fromarray(result.astype("uint8"))
    result_img.save(output_path, quality=100)

    print(f"✓ Color bleed applied: {output_path}")
    return output_path


def apply_signal_dropout(image_path, output_path, block_count=10, block_size=50):
    """
    Apply signal dropout (random rectangular blocks of corruption).

    Args:
        image_path: Input image path
        output_path: Output image path
        block_count: Number of dropout blocks
        block_size: Maximum size of each block
    """
    # Load image
    img = Image.open(image_path)
    img = img.convert("RGB")
    pixels = np.array(img)

    height, width = pixels.shape[:2]
    result = pixels.copy()

    for _ in range(block_count):
        # Random block position and size
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        w = random.randint(10, block_size)
        h = random.randint(5, block_size // 2)

        # Ensure block fits in image
        x2 = min(x + w, width)
        y2 = min(y + h, height)

        # Fill with random noise or black
        if random.random() < 0.5:
            result[y:y2, x:x2] = 0  # Black dropout
        else:
            result[y:y2, x:x2] = np.random.randint(0, 255, (y2 - y, x2 - x, 3))  # Noise

    # Save result
    result_img = Image.fromarray(result.astype("uint8"))
    result_img.save(output_path, quality=100)

    print(f"✓ Signal dropout applied: {output_path}")
    return output_path


if __name__ == "__main__":
    # Example usage
    apply_scanline_shift(
        "images/girl/girl.jpg",
        "images/girl/girl_signal.jpg",
        intensity=20,
        probability=0.15,
    )
