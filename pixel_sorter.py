import numpy as np
from PIL import Image


def brightness(pixel):
    """Calculate brightness of a pixel (RGB)."""
    return sum(pixel[:3]) / 3


def sort_pixels(
    image_path,
    output_path,
    mode="brightness",
    direction="horizontal",
    threshold=100,
    reverse=False,
):
    """
    Sort pixels in an image to create glitch art effects.

    Args:
        image_path: Path to input image
        output_path: Path to save sorted image
        mode: Sorting criteria - 'brightness', 'red', 'green', 'blue', 'hue', 'saturation'
        direction: 'horizontal' or 'vertical'
        threshold: Brightness threshold to start/stop sorting intervals (0-255)
        reverse: Reverse the sorting order
    """
    # Load image
    img = Image.open(image_path)
    img = img.convert("RGB")
    pixels = np.array(img)

    if direction == "vertical":
        pixels = np.transpose(pixels, (1, 0, 2))

    height, width, _ = pixels.shape

    # Sort each row
    for i in range(height):
        row = pixels[i]
        intervals = get_sort_intervals(row, threshold)

        for start, end in intervals:
            section = row[start:end]
            sorted_section = sort_section(section, mode, reverse)
            row[start:end] = sorted_section

        pixels[i] = row

    if direction == "vertical":
        pixels = np.transpose(pixels, (1, 0, 2))

    # Save result
    result_img = Image.fromarray(pixels.astype("uint8"))
    result_img.save(output_path)
    print(f"Sorted image saved to {output_path}")


def get_sort_intervals(row, threshold):
    """
    Find intervals in the row where pixels should be sorted.
    Sorting occurs between pixels darker than threshold.
    """
    intervals = []
    start = None

    for i, pixel in enumerate(row):
        if brightness(pixel) < threshold:
            if start is not None:
                intervals.append((start, i))
                start = None
        else:
            if start is None:
                start = i

    if start is not None:
        intervals.append((start, len(row)))

    return intervals


def sort_section(section, mode, reverse):
    if mode == "brightness":
        key_func = lambda p: brightness(p)
    elif mode == "red":
        key_func = lambda p: p[0]
    elif mode == "green":
        key_func = lambda p: p[1]
    elif mode == "blue":
        key_func = lambda p: p[2]
    elif mode == "hue":
        key_func = lambda p: rgb_to_hsv(p)[0]
    elif mode == "saturation":
        key_func = lambda p: rgb_to_hsv(p)[1]
    else:
        key_func = lambda p: brightness(p)

    # Convert to list for sorting
    section_list = [tuple(pixel) for pixel in section]
    sorted_section = sorted(section_list, key=key_func, reverse=reverse)

    return np.array(sorted_section)


def rgb_to_hsv(pixel):
    """Convert RGB pixel to HSV values."""
    r, g, b = pixel[0] / 255.0, pixel[1] / 255.0, pixel[2] / 255.0
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    diff = max_val - min_val

    # Hue calculation
    if diff == 0:
        h = 0
    elif max_val == r:
        h = (60 * ((g - b) / diff) + 360) % 360
    elif max_val == g:
        h = (60 * ((b - r) / diff) + 120) % 360
    else:
        h = (60 * ((r - g) / diff) + 240) % 360

    # Saturation calculation
    s = 0 if max_val == 0 else (diff / max_val)

    # Value
    v = max_val

    return h, s, v


def sort_all_pixels(image_path, output_path, mode="brightness", reverse=False):
    """
    Sort ALL pixels in the image without intervals (more extreme effect).
    """
    img = Image.open(image_path)
    img = img.convert("RGB")
    pixels = np.array(img)

    height, width, _ = pixels.shape

    # Flatten all pixels
    flat_pixels = pixels.reshape(-1, 3)

    # Sort
    sorted_pixels = sort_section(flat_pixels, mode, reverse)

    # Reshape back
    result = sorted_pixels.reshape(height, width, 3)

    # Save
    result_img = Image.fromarray(result.astype("uint8"))
    result_img.save(output_path)
    print(f"Sorted image saved to {output_path}")
