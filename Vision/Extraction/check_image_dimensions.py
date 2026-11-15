
import os
import cv2
from pathlib import Path
from datetime import timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter


# ==================================================
# 1. ADD YOUR VIDEO PATHS HERE
# ==================================================

video_paths = [
    r"- vlc-record-2013-05-09-20h02m27s-udp___X129H03.mp4",
    r"_ISS_20091127_110735 177F001 Movie.mp4",
    r"BASS_GMT49_SAMPLE_207_TEST_O1.ts",
    r"BASS_GMT49_SAMPLE_207_TEST_O1_Still_Sequence.mp4",
    r"BASS_GMT50_SAMPLE_147_TEST_B1.mp4",
    r"BASS_GMT50_SAMPLE_147_TEST_B1_Still_Sequence.mp4",
    r"BASS_GMT188_SAMPLE_173_TESTB10_Still_Sequence.mp4",
    r"Flame View Movie.mp4",
    r"PSI-10_Raw Data_vlc-record-2021-11-24-21h11m32s-udp____21328P1.mp4",
    r"vlc-record-2013-05-16-14h14m13s-udp___X136M05.mp4",
    r"vlc-record-2014-01-13-15h38m35s-udp___X013M02.mp4",

    # Add more video paths here
]


# ==================================================
# 2. HELPER FUNCTIONS
# ==================================================

def format_duration(seconds):
    """Convert seconds into HH:MM:SS format."""

    if seconds is None:
        return "N/A"

    return str(timedelta(seconds=round(seconds)))


def get_codec(cap):
    """Extract video codec information."""

    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))

    codec = "".join(
        chr((fourcc >> (8 * i)) & 0xFF)
        for i in range(4)
    )

    return codec.strip() if codec.strip() else "Unknown"


# ==================================================
# 3. INSPECT A SINGLE VIDEO
# ==================================================

def inspect_video(video_path):

    result = {
        "File Name": Path(video_path).name,
        "File Path": str(video_path),
        "Format": Path(video_path).suffix.lower(),
        "File Size (MB)": None,
        "File Size (GB)": None,
        "Duration (Seconds)": None,
        "Duration (HH:MM:SS)": None,
        "Width (Pixels)": None,
        "Height (Pixels)": None,
        "Resolution": None,
        "Aspect Ratio": None,
        "Frame Rate (FPS)": None,
        "Total Frames": None,
        "Codec": None,
        "Status": None
    }

    try:

        # Check whether file exists
        if not os.path.isfile(video_path):
            result["Status"] = "File Not Found"
            return result

        # File size
        file_size = os.path.getsize(video_path)

        result["File Size (MB)"] = round(
            file_size / (1024 ** 2), 2
        )

        result["File Size (GB)"] = round(
            file_size / (1024 ** 3), 3
        )

        # Open video
        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            result["Status"] = "Unable to Open Video"
            return result

        # Extract video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(
            cap.get(cv2.CAP_PROP_FRAME_COUNT)
        )

        # Resolution
        result["Width (Pixels)"] = width
        result["Height (Pixels)"] = height

        if width > 0 and height > 0:
            result["Resolution"] = f"{width} x {height}"

            result["Aspect Ratio"] = round(
                width / height, 3
            )

        # Frame rate
        if fps > 0:
            result["Frame Rate (FPS)"] = round(fps, 3)

        # Total frames
        result["Total Frames"] = total_frames

        # Duration
        if fps > 0 and total_frames > 0:

            duration = total_frames / fps

            result["Duration (Seconds)"] = round(
                duration, 2
            )

            result["Duration (HH:MM:SS)"] = (
                format_duration(duration)
            )

        # Codec
        result["Codec"] = get_codec(cap)

        cap.release()

        result["Status"] = "Success"

    except Exception as e:

        result["Status"] = f"Error: {str(e)}"

    return result


# ==================================================
# 4. PROCESS ALL VIDEOS
# ==================================================

def main():

    print("\nStarting video inspection...\n")

    all_results = []

    for index, video_path in enumerate(video_paths, start=1):

        print(
            f"[{index}/{len(video_paths)}] "
            f"Inspecting: {Path(video_path).name}"
        )

        result = inspect_video(video_path)

        all_results.append(result)

        print(f"Status: {result['Status']}\n")

    # ==================================================
    # 5. CREATE EXCEL FILE
    # ==================================================

    workbook = Workbook()
    worksheet = workbook.active

    worksheet.title = "Video Inventory"

    headers = list(all_results[0].keys()) if all_results else [
        "File Name", "File Path", "Format",
        "File Size (MB)", "File Size (GB)",
        "Duration (Seconds)", "Duration (HH:MM:SS)",
        "Width (Pixels)", "Height (Pixels)",
        "Resolution", "Aspect Ratio",
        "Frame Rate (FPS)", "Total Frames",
        "Codec", "Status"
    ]

    worksheet.append(headers)

    # Header formatting
    for cell in worksheet[1]:

        cell.font = Font(
            bold=True,
            color="FFFFFF"
        )

        cell.fill = PatternFill(
            start_color="1F4E78",
            end_color="1F4E78",
            fill_type="solid"
        )

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

    # Insert results
    for result in all_results:

        worksheet.append([
            result.get(header)
            for header in headers
        ])

    # Adjust column widths
    for column in worksheet.columns:

        max_length = 0
        column_letter = get_column_letter(
            column[0].column
        )

        for cell in column:

            if cell.value is not None:
                max_length = max(
                    max_length,
                    len(str(cell.value))
                )

        worksheet.column_dimensions[
            column_letter
        ].width = min(max_length + 3, 55)

    # Excel usability
    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions

    worksheet.row_dimensions[1].height = 30

    # Save beside this Python script
    script_directory = Path(__file__).resolve().parent

    output_path = (
        script_directory / "video_inventory.xlsx"
    )

    workbook.save(output_path)

    print("=" * 50)
    print("VIDEO INSPECTION COMPLETED")
    print("=" * 50)

    print(f"Total videos: {len(video_paths)}")

    successful = sum(
        1 for item in all_results
        if item["Status"] == "Success"
    )

    print(f"Successfully inspected: {successful}")
    print(f"Failed: {len(video_paths) - successful}")

    print(f"\nExcel report saved at:\n{output_path}")


# ==================================================
# 6. EXECUTION
# ==================================================

if __name__ == "__main__":
    main()
