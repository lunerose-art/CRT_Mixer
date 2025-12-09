# CRT - Pixel Sorter

A Python-based pixel sorting tool for creating glitch art effects on images and videos.

## What is Pixel Sorting?

Pixel sorting is a glitch art technique that sorts pixels in an image based on various criteria (brightness, color channels, hue, etc.). This creates interesting visual effects and distortions.

## Setup

### Prerequisites

For video processing, you need FFmpeg installed:

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html)

### Python Setup

Create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Image Pixel Sorting

### Usage

Basic usage:
```bash
python main.py input.jpg output.jpg
```

### Options

- `-m, --mode`: Sorting criteria
  - `brightness` (default) - Sort by pixel brightness
  - `red` - Sort by red channel
  - `green` - Sort by green channel
  - `blue` - Sort by blue channel
  - `hue` - Sort by hue value
  - `saturation` - Sort by saturation

- `-d, --direction`: Sorting direction
  - `horizontal` (default) - Sort pixels horizontally
  - `vertical` - Sort pixels vertically

- `-t, --threshold`: Brightness threshold (0-255, default: 100)
  - Only pixels brighter than this value will be sorted
  - Lower values = more sorting, higher values = less sorting

- `-r, --reverse`: Reverse the sorting order

- `-a, --all`: Sort ALL pixels in the image (ignores threshold and direction)

### Image Examples

```bash
# Basic horizontal brightness sort
python main.py image.jpg output.jpg

# Sort by hue vertically
python main.py image.jpg output.jpg -m hue -d vertical

# Intense effect with low threshold
python main.py image.jpg output.jpg -t 30

# Sort all pixels (extreme effect)
python main.py image.jpg output.jpg -a

# Reverse sort by saturation
python main.py image.jpg output.jpg -m saturation -r
```

## Video Pixel Sorting (FFmpeg-Powered)

Process videos with the same glitch art effects! FFmpeg provides:
- **Fast processing** - Optimized video encoding/decoding
- **Audio preservation** - Keeps original audio track
- **Better quality** - Superior compression and codec support
- **Smaller files** - Efficient video encoding

### Video Usage

Basic video sorting:
```bash
python video_main.py input.mp4 output.mp4
```

### Video Options

All image options plus:

- `-q, --quality`: Output video quality
  - `low` - Smaller file size, faster encoding
  - `medium` (default) - Balanced quality and size
  - `high` - Best quality, larger file size

### Video Examples

```bash
# Basic horizontal brightness sort
python video_main.py input.mp4 output.mp4

# Intense hue sort with high quality
python video_main.py input.mp4 output_hue.mp4 -m hue -t 30 -q high

# Vertical sort
python video_main.py input.mp4 output_vert.mp4 -d vertical

# Extreme effect - sort all pixels
python video_main.py input.mp4 extreme.mp4 -a

# Red channel sort with medium quality
python video_main.py input.mp4 red_glitch.mp4 -m red -t 50
```

### Video Tips

- **Start with short clips** (5-10 seconds) to test settings
- **Lower thresholds (20-50)** create more dramatic effects
- **Use quality settings wisely:**
  - `low` for quick tests
  - `medium` for most uses
  - `high` for final output
- **Videos with movement and color** work best
- **Audio is automatically preserved** from the original video
- Processing time depends on video length and resolution

## General Tips

- Start with default settings and adjust from there
- Lower threshold values create more dramatic sorting effects
- Try different modes to see which works best for your content
- Vertical sorting often creates different effects than horizontal
- The `--all` flag creates the most extreme effects
- High contrast images/videos work particularly well

## How It Works

The pixel sorter identifies intervals in each row (or column) where pixels should be sorted. By default, it sorts pixels that are brighter than the threshold value. This creates "bands" of sorted pixels that maintain some of the original structure while creating glitch-like distortions.

For videos, each frame is processed individually with the same algorithm, then reassembled using FFmpeg with the original audio track intact.

## Project Structure

```
CRT/
├── main.py                    # Image pixel sorter CLI
├── pixel_sorter.py            # Core sorting algorithms
├── video_main.py              # Video pixel sorter CLI
├── video_sorter_ffmpeg.py     # FFmpeg-based video processing
├── requirements.txt           # Python dependencies
└── images/                    # Image storage
    ├── deer/                  # Organized by subject
    └── girl/
```
# CRT_Mixer
