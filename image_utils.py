import os
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import re
import pyperclip
import requests


# Keep extension handling aligned with main.resolve_image_path().
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp", ".gif")
EXTENSION_PRIORITY = {ext: index for index, ext in enumerate(IMAGE_EXTENSIONS)}
PDF_EXPORT_MAX_WIDTH = 1500
PDF_EXPORT_JPEG_QUALITY = 75


def add_text_to_image(
    image_path,
    text,
    coords,
    size,
    output_path,
    font_path=None,
    font_size=31,
    dpi=171,
    text_color=(49, 46, 47),
):
    """Adds text to the image, wrapping it within the specified size."""
    base_image = Image.open(image_path).convert("RGBA")
    base_image.info["dpi"] = (dpi, dpi)

    txt_img = Image.new("RGBA", base_image.size, (255, 255, 255, 0))
    txt_img.info["dpi"] = (dpi, dpi)

    draw = ImageDraw.Draw(txt_img)
    font = ImageFont.truetype(font_path or os.path.join("fonts", "arial.ttf"), font_size)
    max_width = size[0]

    # word wrap
    lines = []
    current_line = ""
    for word in text.split():
        temp_line = current_line + word + " "
        if font.getbbox(temp_line)[2] > max_width:
            lines.append(current_line.strip())
            current_line = word + " "
        else:
            current_line = temp_line
    lines.append(current_line.strip())

    # white background for text block
    draw.rectangle([coords, (coords[0] + size[0], coords[1] + size[1])], fill="white")

    y_text = coords[1]
    for line in lines:
        draw.text((coords[0], y_text), line, font=font, fill=text_color)
        y_text += font.getbbox(line)[3] + 5

    combined = Image.alpha_composite(base_image, txt_img)

    # ✅ JPEG cannot store RGBA → convert to RGB if saving as JPG/JPEG
    if str(output_path).lower().endswith((".jpg", ".jpeg")):
        combined = combined.convert("RGB")
        combined.save(output_path, dpi=(dpi, dpi))
    else:
        combined.save(output_path, dpi=(dpi, dpi))



def clear_output_folder(output_folder):
    """Clears all files in the output folder."""
    for filename in os.listdir(output_folder):
        file_path = os.path.join(output_folder, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")


def is_supported_image(path):
    """Return True when the path points to a supported image file."""
    return Path(path).suffix.lower() in IMAGE_EXTENSIONS


def choose_preferred_image(paths):
    """Choose one file for a page using resolve_image_path()'s extension preference."""
    return min(paths, key=lambda path: EXTENSION_PRIORITY.get(path.suffix.lower(), len(IMAGE_EXTENSIONS)))


def page_sort_key(stem):
    """Sort page stems numerically when possible, then naturally."""
    return tuple(
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r"(\d+)", str(stem))
    )


def flatten_to_white(image):
    """Return an RGB image with any transparency flattened onto white."""
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        return Image.alpha_composite(background, rgba).convert("RGB")

    return image.convert("RGB")


def prepare_image_for_pdf(image, max_width=PDF_EXPORT_MAX_WIDTH):
    """Prepare a rendered page for smaller PDF embedding only at export time."""
    prepared = flatten_to_white(image)
    original_width, original_height = prepared.size
    scale = 1.0

    if original_width > max_width:
        scale = max_width / original_width
        resized = (
            max(1, int(round(original_width * scale))),
            max(1, int(round(original_height * scale))),
        )
        prepared = prepared.resize(resized, Image.Resampling.LANCZOS)

    # Pillow's PDF writer uses resolution to determine page size.
    # Adjust it so export-time downscaling does not shrink the page in the PDF.
    pdf_resolution = 72 * scale
    return prepared, (pdf_resolution, pdf_resolution)


def copy_unprocessed_images(image_folder, output_folder, processed_images):
    """Copies images that were not processed to the output folder."""
    image_folder = Path(image_folder)
    output_folder = Path(output_folder)
    processed_stems = {Path(name).stem for name in processed_images}
    candidates_by_stem = {}

    for src_path in image_folder.iterdir():
        if not src_path.is_file() or not is_supported_image(src_path):
            continue
        candidates_by_stem.setdefault(src_path.stem, []).append(src_path)

    for stem in sorted(candidates_by_stem, key=page_sort_key):
        if stem in processed_stems:
            continue

        src_path = choose_preferred_image(candidates_by_stem[stem])
        dst_path = output_folder / src_path.name
        shutil.copy2(src_path, dst_path)
        print(f"Copied unprocessed image {src_path.name} to {output_folder}")


def natural_sort_key(filename):
    """Sort key function to sort filenames naturally by numerical order."""
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r"(\d+)", filename)
    ]


def compile_images_to_pdf(output_folder, pdf_output_folder, client_name):
    """Compiles all images in the output folder into a single PDF in natural order, 
    handling duplicate client names."""

    output_folder = Path(output_folder)
    pdf_output_folder = Path(pdf_output_folder)
    selected_pages = {}

    for path in output_folder.iterdir():
        if not path.is_file() or not is_supported_image(path):
            continue

        is_modified = path.stem.endswith("_modified")
        page_stem = path.stem[:-9] if is_modified else path.stem
        current = selected_pages.get(page_stem)

        if current is None:
            selected_pages[page_stem] = path
            continue

        current_is_modified = current.stem.endswith("_modified")
        if is_modified and not current_is_modified:
            selected_pages[page_stem] = path
        elif is_modified == current_is_modified:
            selected_pages[page_stem] = choose_preferred_image([current, path])

    ordered_page_paths = [
        selected_pages[page_stem]
        for page_stem in sorted(selected_pages, key=page_sort_key)
    ]

    if ordered_page_paths:
        base_pdf_name = f"{client_name} Palmistry Report"
        pdf_path = pdf_output_folder / f"{base_pdf_name}.pdf"
        counter = 1

        # Check for existing files with the same name and increment counter if needed
        while pdf_path.exists():
            counter += 1
            pdf_path = pdf_output_folder / f"{base_pdf_name} ({counter}).pdf"

        for index, file_path in enumerate(ordered_page_paths):
            with Image.open(file_path) as img:
                pdf_page, resolution = prepare_image_for_pdf(img)
                save_kwargs = {
                    "format": "PDF",
                    "resolution": resolution[0],
                    "quality": PDF_EXPORT_JPEG_QUALITY,
                    "optimize": True,
                }
                if index > 0:
                    save_kwargs["append"] = True
                pdf_page.save(pdf_path, **save_kwargs)

        print(f"PDF compiled and saved to {pdf_path}")
    else:
        print("No images found in the output folder to compile into a PDF.")


def log_run(log_file, answers):
    """Logs the answers to the log file, prompts for client name and returns it."""

    print(f"Attempting to log answers: {answers}")  # Debug print

    # Prompt for the client's name
    client_name = input("Enter the client's name: ").strip()

    # Get the current run count
    run_count = get_current_run_count(log_file)
    run_count += 1  # Increment the run count

    # Convert the answers list to a string
    answers_string = "".join(answers)

    # Read the existing lines except the first one (if the file exists)
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8", errors="replace") as file:
            lines = file.readlines()
    else:
        lines = []  # If the file doesn't exist, start with an empty list

    # Write the updated run count and preserve the rest of the log file
    with open(log_file, "w") as file:
        file.write(f"Run count: {run_count}\n")
        if lines:  # Only write remaining lines if they exist
            file.writelines(lines[1:])

    # Append the new log entries in the desired format
    with open(log_file, "a") as file:
        file.write(f"{client_name}: {answers_string}\n")

    print(f"Logged answers to {log_file} with run count {run_count}")  # Debug print

    # Return the client_name
    return client_name
    

def get_current_run_count(log_file):
    """Gets the current run count from the log file."""
    run_count = 0
    if os.path.exists(log_file):
        with open(log_file, "r") as file:
            first_line = file.readline().strip()
            if first_line.startswith("Run count:"):
                run_count = int(first_line.split(": ")[1].strip())
    return run_count
