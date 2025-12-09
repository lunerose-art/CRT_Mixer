import argparse

from pixel_sorter import sort_all_pixels, sort_pixels


def main():
    parser = argparse.ArgumentParser(
        description="Pixel Sorter - Create glitch art by sorting pixels"
    )
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", help="Output image path")
    parser.add_argument(
        "-m",
        "--mode",
        choices=["brightness", "red", "green", "blue", "hue", "saturation"],
        default="brightness",
        help="Sorting criteria (default: brightness)",
    )
    parser.add_argument(
        "-d",
        "--direction",
        choices=["horizontal", "vertical"],
        default="horizontal",
        help="Sorting direction (default: horizontal)",
    )
    parser.add_argument(
        "-t",
        "--threshold",
        type=int,
        default=100,
        help="Brightness threshold for sorting intervals 0-255 (default: 100)",
    )
    parser.add_argument(
        "-r", "--reverse", action="store_true", help="Reverse sorting order"
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Sort all pixels (ignores threshold and direction)",
    )

    args = parser.parse_args()

    print(f"Processing {args.input}...")

    if args.all:
        sort_all_pixels(args.input, args.output, args.mode, args.reverse)
    else:
        sort_pixels(
            args.input,
            args.output,
            args.mode,
            args.direction,
            args.threshold,
            args.reverse,
        )

    print("Done!")


if __name__ == "__main__":
    main()
