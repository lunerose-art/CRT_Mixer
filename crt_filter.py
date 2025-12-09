import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter


def apply_scanlines(pixels, intensity=0.15, thickness=1, spacing=2):
    """
    Apply CRT scanlines effect.

    Args:
        pixels: Image array
        intensity: Darkness of scanlines (0.0-1.0, higher = darker)
        thickness: Thickness of each scanline in pixels
        spacing: Space between scanlines in pixels
    """
    height, width = pixels.shape[:2]

    for y in range(0, height, spacing):
        for t in range(thickness):
            if y + t < height:
                pixels[y + t] = pixels[y + t] * (1.0 - intensity)

    return pixels


def apply_phosphor_glow(pixels, glow_amount=0.3):
    """
    Apply phosphor glow effect (subtle bloom).

    Args:
        pixels: Image array
        glow_amount: Amount of glow (0.0-1.0)
    """
    if glow_amount <= 0:
        return pixels

    # Apply gaussian blur for glow
    glowed = gaussian_filter(pixels, sigma=2.0)

    # Blend original with glowed version
    result = pixels * (1.0 - glow_amount) + glowed * glow_amount

    return np.clip(result, 0, 1)


def apply_shadow_mask(pixels, mask_dark=0.9, mask_light=1.05, spacing=3):
    """Apply RGB phosphor shadow mask."""
    height, width = pixels.shape[:2]

    for x in range(0, width, spacing):
        if x % (spacing * 3) == 0:
            # Boost red
            pixels[:, x, 0] = np.clip(pixels[:, x, 0] * mask_light, 0, 1)
            pixels[:, x, 1] = pixels[:, x, 1] * mask_dark
            pixels[:, x, 2] = pixels[:, x, 2] * mask_dark
        elif x % (spacing * 3) == spacing:
            # Boost green
            pixels[:, x, 0] = pixels[:, x, 0] * mask_dark
            pixels[:, x, 1] = np.clip(pixels[:, x, 1] * mask_light, 0, 1)
            pixels[:, x, 2] = pixels[:, x, 2] * mask_dark
        else:
            # Boost blue
            pixels[:, x, 0] = pixels[:, x, 0] * mask_dark
            pixels[:, x, 1] = pixels[:, x, 1] * mask_dark
            pixels[:, x, 2] = np.clip(pixels[:, x, 2] * mask_light, 0, 1)

    return pixels


def apply_display_warp(pixels, warp_x=0.02, warp_y=0.02, edge_fade=True):
    """
    Apply barrel distortion (curved screen effect) with anti-aliased edges.

    Args:
        pixels: Image array
        warp_x: Horizontal barrel distortion
        warp_y: Vertical barrel distortion
        edge_fade: If True, fade to black at edges for smooth corners
    """
    height, width = pixels.shape[:2]

    # Create output array
    warped = np.zeros_like(pixels)

    # Center coordinates
    center_x = width / 2.0
    center_y = height / 2.0

    for y in range(height):
        for x in range(width):
            # Normalize coordinates to [-1, 1]
            nx = (x - center_x) / center_x
            ny = (y - center_y) / center_y

            # Calculate distance from center
            r2 = nx * nx + ny * ny

            # Apply barrel distortion
            f = 1.0 - r2 * (warp_x + warp_y)

            if f > 0:
                # Inverse mapping
                src_x = center_x + nx * center_x / f
                src_y = center_y + ny * center_y / f

                # Bounds check with margin for interpolation
                if 0 <= src_x < width - 1 and 0 <= src_y < height - 1:
                    # Bilinear interpolation for anti-aliasing
                    x0, y0 = int(src_x), int(src_y)
                    x1, y1 = x0 + 1, y0 + 1

                    dx = src_x - x0
                    dy = src_y - y0

                    warped[y, x] = (
                        pixels[y0, x0] * (1 - dx) * (1 - dy)
                        + pixels[y0, x1] * dx * (1 - dy)
                        + pixels[y1, x0] * (1 - dx) * dy
                        + pixels[y1, x1] * dx * dy
                    )

                    # Edge fade for smooth corners
                    if edge_fade:
                        # Calculate distance from valid source area
                        margin = 5.0
                        edge_dist_x = min(src_x, width - 1 - src_x)
                        edge_dist_y = min(src_y, height - 1 - src_y)
                        edge_dist = min(edge_dist_x, edge_dist_y)

                        # Smooth fade in the margin area
                        if edge_dist < margin:
                            fade_factor = edge_dist / margin
                            warped[y, x] = warped[y, x] * fade_factor

    return warped


def apply_crt_filter(
    image_path,
    output_path,
    hard_scan=-8.0,
    display_warp_x=0.02,
    display_warp_y=0.02,
    mask_dark=0.9,
    mask_light=1.05,
    brightness=1.2,
    scanline_intensity=0.15,
    scanline_thickness=1,
    scanline_count=600,
    phosphor_glow=0.0,
):
    """
    Apply CRT monitor filter to an image.

    Args:
        image_path: Input image path
        output_path: Output image path
        hard_scan: Scanline intensity (legacy, negative value)
        display_warp_x: Horizontal barrel distortion amount
        display_warp_y: Vertical barrel distortion amount
        mask_dark: Shadow mask dark multiplier
        mask_light: Shadow mask light multiplier
        brightness: Overall brightness multiplier
        scanline_intensity: Darkness of scanlines (0.0-1.0)
        scanline_thickness: Thickness of scanlines in pixels
        scanline_count: Target number of scanlines (affects spacing)
        phosphor_glow: Phosphor glow amount (0.0-1.0)
    """
    # Load image
    img = Image.open(image_path)
    img = img.convert("RGB")
    pixels = np.array(img).astype(np.float32) / 255.0

    height, width = pixels.shape[:2]

    # Scale effects based on image size
    scale_factor = min(width, height) / 800.0
    scaled_warp_x = display_warp_x / scale_factor
    scaled_warp_y = display_warp_y / scale_factor

    # Apply CRT effects
    if scaled_warp_x > 0.001 or scaled_warp_y > 0.001:
        pixels = apply_display_warp(pixels, scaled_warp_x, scaled_warp_y)

    # Calculate scanline spacing from count
    if scanline_count > 0:
        scanline_spacing = max(1, int(height / scanline_count))
    else:
        scanline_spacing = max(2, int(height / 600))

    pixels = apply_scanlines(
        pixels, scanline_intensity, scanline_thickness, scanline_spacing
    )

    mask_spacing = max(3, int(width / 800))
    pixels = apply_shadow_mask(pixels, mask_dark, mask_light, mask_spacing)

    # Apply phosphor glow
    if phosphor_glow > 0:
        pixels = apply_phosphor_glow(pixels, phosphor_glow)

    # Apply brightness
    pixels = pixels * brightness

    # Convert back to 8-bit
    pixels = np.clip(pixels * 255, 0, 255).astype(np.uint8)

    # Save result
    result_img = Image.fromarray(pixels)
    result_img.save(output_path, quality=100)

    return output_path


if __name__ == "__main__":
    # Example usage
    apply_crt_filter(
        "images/girl/girl.jpg",
        "images/girl/girl_crt.jpg",
        hard_scan=-8.0,
        display_warp_x=0.02,
        display_warp_y=0.02,
        mask_dark=0.9,
        mask_light=1.05,
        brightness=1.2,
        scanline_intensity=0.15,
        scanline_thickness=1,
        scanline_count=600,
        phosphor_glow=0.2,
    )
