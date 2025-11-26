import argparse
from datetime import datetime
from pathlib import Path

from PIL.Image import Resampling

from src.core.config_manager import config_manager
from src.core.scan_creator import (
    calculate_snapshot_times,
    create_scan_image,
    get_video_info,
    take_snapshots,
)
from src.utils.console import cinput, log


def cli_main():
    """
    CLI entry point for generating a video scan image with snapshots and metadata overlay.

    This function performs the following steps:
        1. Accepts the video file path either via CLI argument or interactive input if not provided.
        2. Loads the selected layout preset (default: "zh-CN") or a user-specified layout.
        3. Retrieves detailed video information, such as duration, resolution, and available streams.
        4. Handles multiple video streams:
            - If a stream index is provided via CLI, it will be validated and used.
            - If multiple streams exist and no index is provided, the user is prompted to select one.
            - If only one stream exists, it is automatically selected.
        5. Calculates snapshot times based on the grid layout and optional leading/ending avoidance.
        6. Captures snapshots from the video at specified times.
        7. Composes a scan image with a grid of snapshots, overlaying metadata and optional logo.
        8. Optionally rescales the final image based on configuration before saving.
        9. Saves the final image in the "scans" directory with a timestamped filename.

    Inputs (via CLI arguments or prompts):
        - video_file (str, optional): Path to the video file. If not provided, will prompt interactively.
        - layout (str, optional): Layout preset name. Defaults to "zh-CN".
        - stream (int, optional): Index of the video stream to use. If multiple streams exist and not provided, user is prompted.

    Outputs:
        - PNG file of the scan image containing the arranged snapshots and metadata.

    Raises:
        - FileNotFoundError: If the video file, fonts, or logo cannot be found.
        - ValueError: If snapshot calculation or video stream selection fails.
        - IndexError: If a provided stream index is invalid.

    Example:
        $ python cli.py --file "/path/to/video.mp4" --layout en.json --stream 0
        $ python cli.py --layout zh-CN
        Generates a scan image using the English layout and the first video stream.
    """
    parser = argparse.ArgumentParser(description="Generate a video scan image with snapshots and metadata overlay.")
    parser.add_argument("-f", "--file", type=str, default=None, help="Path to the video file.")
    parser.add_argument("-l", "--layout", type=str, default="zh-CN", help="Layout preset to use (default: zh-CN).")
    parser.add_argument("-s", "--stream", type=int, default=None, help="Index of the video stream to activate.")

    args = parser.parse_args()

    # Layout
    layout_name = args.layout
    config_manager.load_config(layout_name)

    # Video file
    file_path = args.file
    if file_path is None:
        file_path = cinput("File Path: ", color="cyan")
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    video_info = get_video_info(file_path)
    print(video_info)
    if not video_info:
        raise ValueError("Failed to retrieve video information.")

    # Handle multiple video streams
    if len(video_info.video_streams) > 1:
        max_index = len(video_info.video_streams) - 1
        selected_stream_index = None

        if args.stream is not None:
            if 0 <= args.stream <= max_index:
                selected_stream_index = args.stream
            else:
                log.error(f"Invalid stream index {args.stream} in args. Must be between 0 and {max_index}.")
        else:
            log.info(f"\nThere are {len(video_info.video_streams)} video streams available.")

        while selected_stream_index is None:
            try:
                idx = int(cinput(f"Enter a number between 0 and {max_index}: ", color="cyan"))
                if 0 <= idx <= max_index:
                    selected_stream_index = idx
                else:
                    log.error("Index out of range, please try again.")
            except ValueError:
                log.error("Invalid input, please enter an integer.")

        video_info.set_active_video_stream(selected_stream_index)
        log.info(f"Video stream {selected_stream_index} activated.")
    else:
        # Only one stream, auto-select
        video_info.set_active_video_stream(0)

    # Snapshot and scan creation
    grid_shape = tuple(config_manager.layout.grid_shape)
    snapshot_times = calculate_snapshot_times(
        video_info,
        config_manager.config.avoid_leading,
        config_manager.config.avoid_ending,
        snapshot_count=grid_shape[0] * grid_shape[1],
    )
    snapshots = take_snapshots(video_info, snapshot_times)
    scan = create_scan_image(snapshots, grid_shape, snapshot_times, video_info)

    # Resize
    w, h = scan.size
    resize_scale = config_manager.config.resize_scale
    scan = scan.resize((w // resize_scale, h // resize_scale), Resampling.LANCZOS)

    # Save
    out_dir = Path(__file__).parents[0] / "scans"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"{datetime.now().strftime('%H%M%S')}.scan.{video_info.file_name}.png"
    scan.save(out_file)
    log.info(f"Scan saved to: {out_file}")


if __name__ == "__main__":
    # chcp 65001
    try:
        cli_main()
    except (FileNotFoundError, ValueError, IndexError) as e:
        log.error(e)
        exit(1)
