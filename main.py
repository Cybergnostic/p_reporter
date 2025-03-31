import json
import os
from image_utils import (
    add_text_to_image,
    clear_output_folder,
    copy_unprocessed_images,
    compile_images_to_pdf,
    log_run,
)

LOG_FILE = os.path.abspath("answers_log.txt")

def main():
    data_file = "image_data.json"
    image_folder = "design"
    output_folder = "output"
    pdf_output_folder = "reports_finished"

    clear_output_folder(output_folder)

    with open(data_file, "r") as f:
        image_data = json.load(f)

    # Sort image_data by question number
    image_data = dict(
        sorted(image_data.items(), key=lambda item: int(item[0].replace(".png", "")))
    )

    processed_images = set()
    filenames = list(image_data.keys())
    answers = [""] * len(filenames)
    index = 0

    while index < len(filenames):
        filename = filenames[index]
        data = image_data[filename]
        image_path = os.path.join(image_folder, filename)
        output_path = os.path.join(output_folder, filename.replace(".", "_modified."))

        question = data["question"]
        text_blocks = data["text_blocks"]
        coords = tuple(data["coords"])
        size = tuple(data["size"])

        while True:  # Loop until a valid answer is provided
            print(question)
            answer = input(
                "Enter the number corresponding to your answer, or 'b' to go back: "
            ).strip()

            if answer.lower() == "b" and index > 0:
                index -= 1
                break
            elif answer in text_blocks:
                answers[index] = answer

                if filename == "22.png" and answer == "1":
                    # Special case for question 22
                    boys_count = int(input("How many boys? "))
                    girls_count = int(input("How many girls? "))
                    text = f"I have examined your image and can see that you may have {girls_count} girl{'s' if girls_count > 1 else ''} and {boys_count} boy{'s' if boys_count > 1 else ''} in your lifetime."
                else:
                    text = (
                        text_blocks[answer]
                        if isinstance(text_blocks[answer], str)
                        else text_blocks[answer]["text"]
                    )

                add_text_to_image(image_path, text, coords, size, output_path)
                print(f"Modified image saved to {output_path}")
                processed_images.add(filename)
                index += 1
                break  # Exit the inner loop
            else:
                print("Invalid answer. Try again.")

    # Get the client's name directly 
    client_name = log_run(LOG_FILE, answers)

    copy_unprocessed_images(image_folder, output_folder, processed_images)
    compile_images_to_pdf(output_folder, pdf_output_folder, client_name)

if __name__ == "__main__":
    main()