import numpy as np
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing
import os


def brightness(pixel):
    """Calculate brightness of a pixel (RGB)."""
    return (int(pixel[0]) + int(pixel[1]) + int(pixel[2])) / 3.0


def get_sort_intervals(row, threshold):
    """Find intervals in the row where pixels should be sorted."""
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
    """Sort a section of pixels based on the specified mode."""
    if mode == 'brightness':
        key_func = lambda p: brightness(p)
    elif mode == 'red':
        key_func = lambda p: p[0]
    elif mode == 'green':
        key_func = lambda p: p[1]
    elif mode == 'blue':
        key_func = lambda p: p[2]
    elif mode == 'hue':
        key_func = lambda p: rgb_to_hsv(p)[0]
    elif mode == 'saturation':
        key_func = lambda p: rgb_to_hsv(p)[1]
    else:
        key_func = lambda p: brightness(p)
    
    section_list = [tuple(pixel) for pixel in section]
    sorted_section = sorted(section_list, key=key_func, reverse=reverse)
    
    return np.array(sorted_section)


def rgb_to_hsv(pixel):
    """Convert RGB pixel to HSV values."""
    r, g, b = pixel[0] / 255.0, pixel[1] / 255.0, pixel[2] / 255.0
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    diff = max_val - min_val
    
    if diff == 0:
        h = 0
    elif max_val == r:
        h = (60 * ((g - b) / diff) + 360) % 360
    elif max_val == g:
        h = (60 * ((b - r) / diff) + 120) % 360
    else:
        h = (60 * ((r - g) / diff) + 240) % 360
    
    s = 0 if max_val == 0 else (diff / max_val)
    v = max_val
    
    return h, s, v


def process_row(args):
    """Process a single row - designed for parallel execution."""
    row_index, row, mode, threshold, reverse = args
    
    intervals = get_sort_intervals(row, threshold)
    
    for start, end in intervals:
        section = row[start:end]
        sorted_section = sort_section(section, mode, reverse)
        row[start:end] = sorted_section
    
    return row_index, row


def sort_pixels_parallel(image_path, output_path, mode='brightness', direction='horizontal', 
                        threshold=100, reverse=False, preview_mode=False, num_threads=None):
    """
    Parallel pixel sorting using multiple CPU cores.
    
    Args:
        num_threads: Number of threads (None = auto-detect CPU cores)
        preview_mode: If True, resize for faster preview
    """
    # Load image
    img = Image.open(image_path)
    
    # Resize for preview
    if preview_mode:
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
    
    img = img.convert('RGB')
    pixels = np.array(img)
    
    if direction == 'vertical':
        pixels = np.transpose(pixels, (1, 0, 2))
    
    height, width, _ = pixels.shape
    
    # Auto-detect CPU cores
    if num_threads is None:
        num_threads = max(1, multiprocessing.cpu_count() - 1)  # Leave one core free
    
    # Prepare work items
    work_items = [(i, pixels[i].copy(), mode, threshold, reverse) for i in range(height)]
    
    # Process rows in parallel using ThreadPoolExecutor
    # (ThreadPoolExecutor is better than ProcessPoolExecutor for this due to less overhead)
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = list(executor.map(process_row, work_items))
    
    # Reconstruct image from results
    for row_index, sorted_row in results:
        pixels[row_index] = sorted_row
    
    if direction == 'vertical':
        pixels = np.transpose(pixels, (1, 0, 2))
    
    # Save result
    result_img = Image.fromarray(pixels.astype('uint8'))
    result_img.save(output_path, quality=100)
    
    return output_path


def sort_all_pixels(image_path, output_path, mode='brightness', reverse=False):
    """Sort ALL pixels in the image without intervals."""
    img = Image.open(image_path)
    img = img.convert('RGB')
    pixels = np.array(img)
    
    height, width, _ = pixels.shape
    flat_pixels = pixels.reshape(-1, 3)
    sorted_pixels = sort_section(flat_pixels, mode, reverse)
    result = sorted_pixels.reshape(height, width, 3)
    
    result_img = Image.fromarray(result.astype('uint8'))
    result_img.save(output_path)
    
    return output_path


# Alias for compatibility
sort_pixels_optimized = sort_pixels_parallel
