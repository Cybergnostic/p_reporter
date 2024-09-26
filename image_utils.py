import os
import shutil
from PIL import Image, ImageDraw, ImageFont
import re
import pyperclip
import requests


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
    base_image.info["dpi"] = (dpi, dpi)  # Set DPI for higher image quality

    txt_img = Image.new("RGBA", base_image.size, (255, 255, 255, 0))
    txt_img.info["dpi"] = (dpi, dpi)

    draw = ImageDraw.Draw(txt_img)
    font = ImageFont.truetype(font_path or os.path.join("fonts", "arial.ttf"), font_size)
    max_width = size[0]

    # Split text into lines based on available width
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

    # Draw a white rectangle as background for the text
    draw.rectangle([coords, (coords[0] + size[0], coords[1] + size[1])], fill="white")

    y_text = coords[1]
    for line in lines:
        draw.text((coords[0], y_text), line, font=font, fill=text_color)
        y_text += font.getbbox(line)[3] + 5  # Add a small gap between lines

    combined = Image.alpha_composite(base_image, txt_img)
    combined.save(output_path)


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


def copy_unprocessed_images(image_folder, output_folder, processed_images):
    """Copies images that were not processed to the output folder."""
    for filename in os.listdir(image_folder):
        if filename not in processed_images:
            src_path = os.path.join(image_folder, filename)
            dst_path = os.path.join(output_folder, filename)
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dst_path)
                print(f"Copied unprocessed image {filename} to {output_folder}")


def natural_sort_key(filename):
    """Sort key function to sort filenames naturally by numerical order."""
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r"(\d+)", filename)
    ]


def compile_images_to_pdf(output_folder, pdf_output_folder, client_name):
    """Compiles all images in the output folder into a single PDF in natural order, 
    handling duplicate client names."""

    images = []
    for filename in sorted(os.listdir(output_folder), key=natural_sort_key):
        if filename.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif")):
            file_path = os.path.join(output_folder, filename)
            img = Image.open(file_path).convert("RGB")
            images.append(img)

    if images:
        base_pdf_name = f"{client_name} Palmistry Report"
        pdf_path = os.path.join(pdf_output_folder, f"{base_pdf_name}.pdf")
        counter = 1

        # Check for existing files with the same name and increment counter if needed
        while os.path.exists(pdf_path):
            counter += 1
            pdf_path = os.path.join(pdf_output_folder, f"{base_pdf_name} ({counter}).pdf")

        images[0].save(pdf_path, save_all=True, append_images=images[1:])
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
        with open(log_file, "r") as file:
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