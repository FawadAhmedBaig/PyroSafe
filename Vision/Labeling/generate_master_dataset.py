
import csv
import cv2
import zipfile
import xml.etree.ElementTree as ET

from pathlib import Path
from collections import defaultdict


# ============================================================
# 1. PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

VIDEO_DIR = BASE_DIR / "Original_Videos"
CVAT_DIR = BASE_DIR / "CVAT_Exports"
OUTPUT_DIR = BASE_DIR / "Processed_Annotations"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MASTER_CSV = BASE_DIR / "Master_Dataset.csv"
TRACK_CSV = OUTPUT_DIR / "Master_Dataset_With_Tracks.csv"
REPORT_CSV = OUTPUT_DIR / "processing_report.csv"


# ============================================================
# 2. CSV COLUMNS
# ============================================================

# Exact shared team schema
MASTER_COLUMNS = [
    "video_id",
    "frame",
    "time_s",
    "box_x",
    "box_y",
    "box_w",
    "box_h",
    "confidence",
    "mask_path",
    "area_px",
    "sphericity",
    "spread_rate"
]

# Companion file preserves CVAT track IDs
TRACK_COLUMNS = MASTER_COLUMNS + ["track_id"]


# Supported video formats
VIDEO_EXTENSIONS = {
    ".mp4", ".avi", ".mov", ".mkv", ".ts", ".mpeg", ".mpg"
}


# ============================================================
# 3. FIND ORIGINAL VIDEOS
# ============================================================

def find_videos():

    videos = {}

    for path in VIDEO_DIR.rglob("*"):

        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:

            filename = path.name.lower()

            if filename in videos:
                print(f"WARNING: Duplicate video filename: {path.name}")
                videos[filename] = None
            else:
                videos[filename] = path

    return videos


# ============================================================
# 4. FIND CVAT XML FILES
#    Supports loose XML files and XML files inside ZIPs.
# ============================================================

def find_xml_sources():

    sources = []

    for path in CVAT_DIR.rglob("*"):

        if not path.is_file():
            continue

        if path.suffix.lower() == ".xml":

            try:
                xml_bytes = path.read_bytes()
                sources.append((str(path), xml_bytes))
            except Exception as error:
                print(f"Could not read XML: {path} | {error}")

        elif path.suffix.lower() == ".zip":

            try:
                with zipfile.ZipFile(path, "r") as archive:

                    for member in archive.namelist():

                        if Path(member).name.lower() == "annotations.xml":

                            xml_bytes = archive.read(member)

                            source_name = (
                                f"{path} :: {member}"
                            )

                            sources.append((source_name, xml_bytes))

            except zipfile.BadZipFile:
                print(f"Invalid ZIP file: {path}")

            except Exception as error:
                print(f"Could not inspect ZIP: {path} | {error}")

    return sources


# ============================================================
# 5. READ XML INFORMATION
# ============================================================

def parse_xml(xml_bytes):

    root = ET.fromstring(xml_bytes)

    if root.tag != "annotations":
        raise ValueError("Not a CVAT annotations XML file.")

    task = root.find("./meta/task")

    if task is None:
        raise ValueError("CVAT task metadata is missing.")

    source = task.findtext("source", default="").strip()
    task_name = task.findtext("name", default="").strip()

    frame_count = int(task.findtext("size", default="0"))

    width = int(
        task.findtext("original_size/width", default="0")
    )

    height = int(
        task.findtext("original_size/height", default="0")
    )

    if not source:
        raise ValueError("Source video filename is missing.")

    return {
        "root": root,
        "source": Path(source.replace("\\", "/")).name,
        "task_name": task_name,
        "frame_count": frame_count,
        "width": width,
        "height": height
    }


# ============================================================
# 6. READ VIDEO INFORMATION
# ============================================================

def get_video_info(video_path):

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise ValueError("OpenCV could not open this video.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    cap.release()

    if fps <= 0:
        raise ValueError("Invalid video FPS.")

    return {
        "fps": fps,
        "total_frames": total_frames,
        "width": width,
        "height": height
    }


# ============================================================
# 7. EXTRACT FLAME BOXES FROM CVAT XML
# ============================================================

def extract_flame_boxes(root, video_id, fps):

    rows = []
    total_tracks = 0
    total_boxes = 0
    outside_boxes = 0
    visible_frames = set()

    for track in root.findall("track"):

        total_tracks += 1

        label = track.get("label", "")

        # Only export Flame bounding boxes.
        # No-Flame is not a flame bounding box.
        if label.lower() != "flame":
            continue

        track_id = track.get("id", "")

        for box in track.findall("box"):

            total_boxes += 1

            frame = int(box.get("frame", "0"))

            outside = box.get("outside", "0") == "1"

            # Exclude boxes after the object disappears.
            if outside:
                outside_boxes += 1
                continue

            xtl = float(box.get("xtl", "0"))
            ytl = float(box.get("ytl", "0"))
            xbr = float(box.get("xbr", "0"))
            ybr = float(box.get("ybr", "0"))

            box_width = xbr - xtl
            box_height = ybr - ytl

            # Ignore invalid boxes.
            if box_width <= 0 or box_height <= 0:
                continue

            time_seconds = frame / fps

            row = {
                "video_id": video_id,
                "frame": frame,
                "time_s": round(time_seconds, 6),

                "box_x": round(xtl, 3),
                "box_y": round(ytl, 3),
                "box_w": round(box_width, 3),
                "box_h": round(box_height, 3),

                # Manual CVAT annotations have no confidence.
                "confidence": "",

                # These belong to the segmentation work.
                "mask_path": "",
                "area_px": "",
                "sphericity": "",

                # To be calculated later.
                "spread_rate": "",

                "track_id": track_id
            }

            rows.append(row)
            visible_frames.add(frame)

    return {
        "rows": rows,
        "total_tracks": total_tracks,
        "total_boxes": total_boxes,
        "outside_boxes": outside_boxes,
        "visible_frames": visible_frames
    }


# ============================================================
# 8. MAIN PROCESSING
# ============================================================

def main():

    print("\n======================================")
    print(" PyroSafe CVAT XML Dataset Processor")
    print("======================================\n")

    videos = find_videos()
    xml_sources = find_xml_sources()

    print(f"Original videos found: {len(videos)}")
    print(f"CVAT XML exports found: {len(xml_sources)}\n")

    if not videos:
        print("ERROR: No original videos found.")
        return

    if not xml_sources:
        print("ERROR: No CVAT XML files found.")
        return

    master_rows = []
    track_rows = []
    report_rows = []

    processed_sources = set()

    for xml_source, xml_bytes in xml_sources:

        print("--------------------------------------")
        print(f"Processing: {xml_source}")

        report = {
            "xml_source": xml_source,
            "video_id": "",
            "status": "",
            "fps": "",
            "xml_frames": "",
            "video_frames": "",
            "tracks": "",
            "all_boxes": "",
            "visible_flame_boxes": "",
            "outside_boxes": "",
            "frames_with_flame": "",
            "frames_without_flame": "",
            "details": ""
        }

        try:

            xml_info = parse_xml(xml_bytes)

            video_filename = xml_info["source"]
            video_key = video_filename.lower()

            report["video_id"] = video_filename
            report["xml_frames"] = xml_info["frame_count"]

            # Match using the source filename inside CVAT XML.
            video_path = videos.get(video_key)

            if video_path is None:

                if video_key in videos:
                    raise ValueError(
                        "Duplicate original video filename. "
                        "Cannot safely choose a video."
                    )

                raise FileNotFoundError(
                    f"Original video not found: {video_filename}"
                )

            # Avoid accidentally processing the same video twice.
            if video_key in processed_sources:
                raise ValueError(
                    "Duplicate XML export found for this video. "
                    "Resolve the duplicate before processing."
                )

            video_info = get_video_info(video_path)

            fps = video_info["fps"]

            report["fps"] = round(fps, 6)
            report["video_frames"] = video_info["total_frames"]

            # Check dimensions.
            if (
                xml_info["width"] != video_info["width"]
                or xml_info["height"] != video_info["height"]
            ):
                print(
                    "WARNING: XML and video dimensions differ: "
                    f"XML={xml_info['width']}x{xml_info['height']}, "
                    f"Video={video_info['width']}x{video_info['height']}"
                )

            # Check frame counts.
            if xml_info["frame_count"] != video_info["total_frames"]:
                print(
                    "WARNING: XML and video frame counts differ: "
                    f"XML={xml_info['frame_count']}, "
                    f"Video={video_info['total_frames']}"
                )

            extracted = extract_flame_boxes(
                xml_info["root"],
                video_filename,
                fps
            )

            rows = extracted["rows"]

            master_rows.extend(rows)
            track_rows.extend(rows)

            processed_sources.add(video_key)

            total_frames = xml_info["frame_count"]

            frames_with_flame = len(
                extracted["visible_frames"]
            )

            frames_without_flame = max(
                0, total_frames - frames_with_flame
            )

            report.update({
                "status": "SUCCESS",
                "tracks": extracted["total_tracks"],
                "all_boxes": extracted["total_boxes"],
                "visible_flame_boxes": len(rows),
                "outside_boxes": extracted["outside_boxes"],
                "frames_with_flame": frames_with_flame,
                "frames_without_flame": frames_without_flame,
                "details": str(video_path)
            })

            print(f"Video: {video_filename}")
            print(f"FPS: {fps:.3f}")
            print(f"Visible flame boxes: {len(rows)}")
            print(f"Frames containing flame: {frames_with_flame}")
            print("Status: SUCCESS")

        except Exception as error:

            report["status"] = "FAILED"
            report["details"] = str(error)

            print(f"ERROR: {error}")

        report_rows.append(report)

    # ========================================================
    # 9. WRITE MASTER CSV
    # ========================================================

    with open(
        MASTER_CSV,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=MASTER_COLUMNS
        )

        writer.writeheader()

        for row in master_rows:
            writer.writerow({
                column: row[column]
                for column in MASTER_COLUMNS
            })

    # ========================================================
    # 10. WRITE TRACK CSV
    # ========================================================

    with open(
        TRACK_CSV,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=TRACK_COLUMNS
        )

        writer.writeheader()
        writer.writerows(track_rows)

    # ========================================================
    # 11. WRITE PROCESSING REPORT
    # ========================================================

    with open(
        REPORT_CSV,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(report_rows[0].keys())
            if report_rows else []
        )

        if report_rows:
            writer.writeheader()
            writer.writerows(report_rows)

    # ========================================================
    # 12. FINAL SUMMARY
    # ========================================================

    successful = sum(
        1 for row in report_rows
        if row["status"] == "SUCCESS"
    )

    failed = len(report_rows) - successful

    print("\n======================================")
    print(" PROCESSING COMPLETED")
    print("======================================")

    print(f"Videos successfully processed: {successful}")
    print(f"Failed XML exports: {failed}")
    print(f"Total visible flame boxes: {len(master_rows)}")

    print("\nGenerated files:")

    print(f"1. {MASTER_CSV}")
    print(f"2. {TRACK_CSV}")
    print(f"3. {REPORT_CSV}")

    print("\n======================================")


if __name__ == "__main__":
    main()
