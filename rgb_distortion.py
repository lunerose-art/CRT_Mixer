import numpy as np
from PIL import Image


def apply_rgb_shift(image_path, output_path, 
                    red_x=0, red_y=0,
                    green_x=0, green_y=0, 
                    blue_x=0, blue_y=0):
    """
    Shift individual RGB channels to create chromatic aberration effect.
    
    Args:
        image_path: Input image path
        output_path: Output image path
        red_x, red_y: Red channel offset in pixels
        green_x, green_y: Green channel offset in pixels
        blue_x, blue_y: Blue channel offset in pixels
    """
    # Load image
    img = Image.open(image_path)
    img = img.convert('RGB')
    pixels = np.array(img)
    
    height, width = pixels.shape[:2]
    result = np.zeros_like(pixels)
    
    # Shift each channel
    for y in range(height):
        for x in range(width):
            # Red channel
            src_y_r = y - red_y
            src_x_r = x - red_x
            if 0 <= src_y_r < height and 0 <= src_x_r < width:
                result[y, x, 0] = pixels[src_y_r, src_x_r, 0]
            
            # Green channel
            src_y_g = y - green_y
            src_x_g = x - green_x
            if 0 <= src_y_g < height and 0 <= src_x_g < width:
                result[y, x, 1] = pixels[src_y_g, src_x_g, 1]
            
            # Blue channel
            src_y_b = y - blue_y
            src_x_b = x - blue_x
            if 0 <= src_y_b < height and 0 <= src_x_b < width:
                result[y, x, 2] = pixels[src_y_b, src_x_b, 2]
    
    # Save result
    result_img = Image.fromarray(result.astype('uint8'))
    result_img.save(output_path, quality=100)
    
    print(f"✓ RGB shift applied: {output_path}")
    return output_path


def apply_channel_scale(image_path, output_path,
                        red_scale=1.0,
                        green_scale=1.0,
                        blue_scale=1.0):
    """
    Scale individual RGB channels independently.
    
    Args:
        image_path: Input image path
        output_path: Output image path
        red_scale: Red channel multiplier (0.0-2.0)
        green_scale: Green channel multiplier (0.0-2.0)
        blue_scale: Blue channel multiplier (0.0-2.0)
    """
    # Load image
    img = Image.open(image_path)
    img = img.convert('RGB')
    pixels = np.array(img).astype(np.float32)
    
    # Scale channels
    pixels[:, :, 0] = np.clip(pixels[:, :, 0] * red_scale, 0, 255)
    pixels[:, :, 1] = np.clip(pixels[:, :, 1] * green_scale, 0, 255)
    pixels[:, :, 2] = np.clip(pixels[:, :, 2] * blue_scale, 0, 255)
    
    # Save result
    result_img = Image.fromarray(pixels.astype('uint8'))
    result_img.save(output_path, quality=100)
    
    print(f"✓ Channel scale applied: {output_path}")
    return output_path


def apply_channel_swap(image_path, output_path, mode='rgb'):
    """
    Swap RGB channels around.
    
    Args:
        image_path: Input image path
        output_path: Output image path
        mode: Channel order - 'rgb', 'rbg', 'grb', 'gbr', 'brg', 'bgr'
    """
    # Load image
    img = Image.open(image_path)
    img = img.convert('RGB')
    pixels = np.array(img)
    
    result = pixels.copy()
    
    # Map mode to channel indices
    swaps = {
        'rgb': [0, 1, 2],  # No change
        'rbg': [0, 2, 1],  # Swap green and blue
        'grb': [1, 0, 2],  # Swap red and green
        'gbr': [1, 2, 0],  # Rotate right
        'brg': [2, 0, 1],  # Rotate left
        'bgr': [2, 1, 0],  # Reverse
    }
    
    if mode in swaps:
        order = swaps[mode]
        result[:, :, 0] = pixels[:, :, order[0]]
        result[:, :, 1] = pixels[:, :, order[1]]
        result[:, :, 2] = pixels[:, :, order[2]]
    
    # Save result
    result_img = Image.fromarray(result.astype('uint8'))
    result_img.save(output_path, quality=100)
    
    print(f"✓ Channel swap ({mode}) applied: {output_path}")
    return output_path


def apply_chromatic_aberration(image_path, output_path, strength=5):
    """
    Apply chromatic aberration (lens distortion) effect.
    Red shifts outward, blue shifts inward.
    
    Args:
        image_path: Input image path
        output_path: Output image path
        strength: Aberration strength in pixels
    """
    # Load image
    img = Image.open(image_path)
    img = img.convert('RGB')
    pixels = np.array(img)
    
    height, width = pixels.shape[:2]
    result = np.zeros_like(pixels)
    
    center_x = width / 2
    center_y = height / 2
    
    for y in range(height):
        for x in range(width):
            # Calculate direction from center
            dx = (x - center_x) / center_x
            dy = (y - center_y) / center_y
            
            # Red channel - shift outward
            offset_r = strength
            src_x_r = int(x - dx * offset_r)
            src_y_r = int(y - dy * offset_r)
            if 0 <= src_y_r < height and 0 <= src_x_r < width:
                result[y, x, 0] = pixels[src_y_r, src_x_r, 0]
            
            # Green channel - no shift
            result[y, x, 1] = pixels[y, x, 1]
            
            # Blue channel - shift inward
            offset_b = -strength
            src_x_b = int(x - dx * offset_b)
            src_y_b = int(y - dy * offset_b)
            if 0 <= src_y_b < height and 0 <= src_x_b < width:
                result[y, x, 2] = pixels[src_y_b, src_x_b, 2]
    
    # Save result
    result_img = Image.fromarray(result.astype('uint8'))
    result_img.save(output_path, quality=100)
    
    print(f"✓ Chromatic aberration applied: {output_path}")
    return output_path


if __name__ == '__main__':
    # Example usage
    apply_rgb_shift(
        'images/girl/girl.jpg',
        'images/girl/girl_rgb_shift.jpg',
        red_x=5, blue_x=-5
    )
