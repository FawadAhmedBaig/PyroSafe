
import cv2
from pathlib import Path

# =====================================
# CONFIGURATION
# =====================================

# Folder containing your original images
input_folder = Path(r"C:\Users\mtayy\Desktop\PyroSafe\Original videos\SAFFIRE\S1C1")

# Folder where resized images will be saved
output_folder = Path(r"C:\Users\mtayy\Desktop\PyroSafe\Original videos\SAFFIRE\S1C1_Resized")

# Target dimensions
TARGET_WIDTH = 720
TARGET_HEIGHT = 480

# Gray padding color (YOLO-style padding)
PADDING_COLOR = (114, 114, 114)

# Supported image formats
IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"
}


# =====================================
# CREATE OUTPUT DIRECTORY
# =====================================

output_folder.mkdir(parents=True, exist_ok=True)

# Find all images
image_files = [
    path for path in input_folder.iterdir()
    if path.is_file()
    and path.suffix.lower() in IMAGE_EXTENSIONS
]

processed = 0
failed = 0


# =====================================
# RESIZE FUNCTION
# =====================================

def resize_image(image_path):

    image = cv2.imread(str(image_path))

    if image is None:
        print(f"Could not read: {image_path.name}")
        return False

    original_height, original_width = image.shape[:2]

    # Calculate scaling factor while preserving aspect ratio
    scale = min(
        TARGET_WIDTH / original_width,
        TARGET_HEIGHT / original_height
    )

    new_width = round(original_width * scale)
    new_height = round(original_height * scale)

    # Resize image
    resized = cv2.resize(
        image,
        (new_width, new_height),
        interpolation=cv2.INTER_AREA
    )

    # Create target-size canvas
    canvas = cv2.copyMakeBorder(
        resized,
        (TARGET_HEIGHT - new_height) // 2,
        TARGET_HEIGHT - new_height - (TARGET_HEIGHT - new_height) // 2,
        (TARGET_WIDTH - new_width) // 2,
        TARGET_WIDTH - new_width - (TARGET_WIDTH - new_width) // 2,
        cv2.BORDER_CONSTANT,
        value=PADDING_COLOR
    )

    # Save with original filename
    output_path = output_folder / image_path.name

    success = cv2.imwrite(str(output_path), canvas)

    if success:
        print(
            f"Processed: {image_path.name} | "
            f"{original_width}x{original_height} -> "
            f"{TARGET_WIDTH}x{TARGET_HEIGHT}"
        )

    return success


# =====================================
# PROCESS ALL IMAGES
# =====================================

print(f"Found {len(image_files)} images.\n")

for image_path in image_files:

    if resize_image(image_path):
        processed += 1
    else:
        failed += 1


# =====================================
# FINAL SUMMARY
# =====================================

print("\n========== SUMMARY ==========")
print(f"Total images found: {len(image_files)}")
print(f"Successfully resized: {processed}")
print(f"Failed: {failed}")
print(f"Output folder: {output_folder}")
print("=============================")
