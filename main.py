import json
import os
from pathlib import Path
from image_utils import (
    IMAGE_EXTENSIONS,
    add_text_to_image,
    clear_output_folder,
    copy_unprocessed_images,
    compile_images_to_pdf,
    log_run,
)
def resolve_image_path(folder: str | Path, json_key: str) -> Path:
    """Find the actual image regardless of extension using the key's stem."""
    folder = Path(folder)
    stem = Path(json_key).stem

    # try exact key first (in case it already matches)
    p = folder / json_key
    if p.exists():
        return p

    # then try common extensions, preferring JPG/JPEG first
    for ext in IMAGE_EXTENSIONS:
        cand = folder / f"{stem}{ext}"
        if cand.exists():
            return cand

    raise FileNotFoundError(f"Image not found for key '{json_key}' in {folder}")


LOG_FILE = os.path.abspath("answers_log.txt")

def main():
    BASE = Path(__file__).resolve().parent
    data_file = BASE / "image_data.json"
    image_folder = BASE / "design"
    output_folder = BASE / "output"
    pdf_output_folder = BASE / "reports_finished"

    output_folder.mkdir(parents=True, exist_ok=True)
    pdf_output_folder.mkdir(parents=True, exist_ok=True)
    clear_output_folder(output_folder)

    with open(data_file, "r", encoding="utf-8") as f:
        image_data = json.load(f)

    # Sort by the numeric stem (works for .png/.jpg/etc.)
    image_data = dict(sorted(image_data.items(),
                             key=lambda item: int(Path(item[0]).stem)))

    processed_images = set()   # store STEMS, not full filenames
    filenames = list(image_data.keys())
    answers = [""] * len(filenames)
    index = 0

    while index < len(filenames):
        filename = filenames[index]
        data = image_data[filename]

        # Resolve actual file on disk and build output path with real extension
        img_path = resolve_image_path(image_folder, filename)
        stem = img_path.stem
        ext = img_path.suffix

        image_path = str(img_path)
        output_path = str(output_folder / f"{stem}_modified{ext}")

        question = data["question"]
        text_blocks = data["text_blocks"]
        coords = tuple(data["coords"])
        size = tuple(data["size"])

        while True:  # Loop until a valid answer is provided
            print(question)
            answer = input("Enter the number corresponding to your answer, or 'b' to go back: ").strip()

            if answer.lower() == "b" and index > 0:
                index -= 1
                break

            elif answer in text_blocks:
                answers[index] = answer

                # Special case for question 22 (check by stem, not '.png')
                if Path(filename).stem == "22" and answer == "1":
                    boys_count = int(input("How many boys? "))
                    girls_count = int(input("How many girls? "))
                    text = (
                        f"I have examined your image and can see that you may have "
                        f"{girls_count} girl{'s' if girls_count > 1 else ''} and "
                        f"{boys_count} boy{'s' if boys_count > 1 else ''} in your lifetime."
                    )
                else:
                    text = (
                        text_blocks[answer]
                        if isinstance(text_blocks[answer], str)
                        else text_blocks[answer]["text"]
                    )

                add_text_to_image(image_path, text, coords, size, output_path)
                print(f"Modified image saved to {output_path}")

                # track processed by STEM so .png key / .jpg file doesn’t confuse the copy step
                processed_images.add(stem)

                index += 1
                break
            else:
                print("Invalid answer. Try again.")

    # After finishing ALL images:
    client_name = log_run(LOG_FILE, answers)
    copy_unprocessed_images(image_folder, output_folder, processed_images)  # expects stems
    compile_images_to_pdf(output_folder, pdf_output_folder, client_name)

if __name__ == "__main__":
    main()
