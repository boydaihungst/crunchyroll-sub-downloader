# Require aegisub-cli in PATH environment variables: https://github.com/HengXin666/aegisub-cli
# Resample subtitles to a specific video resolution
import argparse
import glob
import os
import subprocess
from pathlib import Path

# Path to the current script
script_dir = Path(__file__).resolve().parent


def create_sample_empty_video(video_resolution: str):
    video_resolution = video_resolution or "1920x1080"
    empty_video_path = script_dir / f"empty_video_{video_resolution}.mp4"

    if not os.path.exists(empty_video_path):
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "color=size=" + video_resolution + ":rate=30:color=black",
                "-t",
                "1",
                "-c:v",
                "libx264",
                "-preset",
                "veryslow",
                "-crf",
                "51",
                "-pix_fmt",
                "yuv420p",
                str(empty_video_path),
            ]
        )
    return empty_video_path


def resample_by_video_resolution(input_file: str, output_file: str, aegisubcli: str, video_resolution: str):
    aegisubcli = aegisubcli or "aegisub-cli"
    empty_video_path = create_sample_empty_video(video_resolution)

    result = subprocess.run(
        [aegisubcli, "--video", str(empty_video_path), "--loglevel", "2", input_file, output_file, "tool/resampleres"],
        capture_output=True,
        text=True,
        check=True,
    )

    if result.stdout:
        print("stdout:", result.stdout)
    elif result.stderr:
        print("stderr:", result.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Resample an .ass subtitle file or all .ass files in a directory.")

    parser.add_argument(
        "inputs",
        nargs="+",  # Accept one or more input paths
        help="Path(s) to input .ass file(s) or directories containing .ass files.",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        help="Path to the output .ass file or directory. Defaults to overwriting the input file(s).",
    )
    parser.add_argument(
        "-a",
        "--aegisubcli",
        dest="aegisubcli",
        help="Path to the aegisub-cli tool. Defaults to searching for aegisub-cli in the PATH environment variable.",
    )
    parser.add_argument(
        "-v",
        "--video-resolution",
        dest="video_resolution",
        help="Video resolution to resample subtitles to. Defaults to 1920x1080.",
    )

    args = parser.parse_args(argv)
    aegisubcli = args.aegisubcli
    video_resolution = args.video_resolution

    for input_path in args.inputs:
        if os.path.isdir(input_path):
            # Input is a directory: process all .ass files recursively
            for file_path in glob.glob(os.path.join(input_path, "**", "*.ass"), recursive=True):
                output_dir = args.output if args.output else os.path.dirname(file_path)
                os.makedirs(output_dir, exist_ok=True)
                filename = os.path.basename(file_path)
                output_path = os.path.join(output_dir, filename)
                resample_by_video_resolution(file_path, output_path, aegisubcli, video_resolution)
        elif os.path.isfile(input_path):
            # Input is a single file
            if args.output:
                # If multiple inputs but single output is provided, treat output as directory
                output_dir = args.output
                os.makedirs(output_dir, exist_ok=True)
                filename = os.path.basename(input_path)
                output_path = os.path.join(output_dir, filename)
            else:
                output_path = input_path
            resample_by_video_resolution(input_path, output_path, aegisubcli, video_resolution)
        else:
            print(f"⚠️ Warning: {input_path} does not exist, skipping...")


if __name__ == "__main__":
    import sys

    main(sys.argv[1:])  # pass real CLI args
