# Palmistry Report Generator

This project asks a series of questions, writes the selected text onto template
images using fixed coordinates from `image_data.json`, and exports the finished
pages as a PDF report.

The text placement system is coordinate-based. The templates, coordinates, box
sizes, and font settings are intended to match the existing design layout.

## What the project does

1. Loads the page definitions from `image_data.json`
2. Resolves the matching source image from `design/`
3. Draws the answer text onto the page image
4. Copies any untouched pages into `output/`
5. Builds the final PDF in `reports_finished/`

## Requirements

- Python 3.11 or newer
- The files and folders already included in this repo:
  - `design/`
  - `fonts/`
  - `image_data.json`

## Install

### Windows

```bash
git clone https://github.com/Cybergnostic/p_reporter.git
cd p_reporter
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### macOS / Linux

```bash
git clone https://github.com/Cybergnostic/p_reporter.git
cd p_reporter
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

### Windows

```bash
py main.py
```

### macOS / Linux

```bash
python3 main.py
```

## Usage flow

1. The script shows each question in sequence.
2. Enter the answer key shown in the prompt.
3. Enter `b` to go back one page if needed.
4. For question 22, if you choose answer `1`, the script asks for boys/girls counts.
5. At the end, enter the client's name.
6. The finished PDF is written to `reports_finished/`.

## Generated files

- `output/` contains the page images used to assemble the report
- `reports_finished/` contains the final PDF exports
- `answers_log.txt` stores the answer history and client names

These generated files are not meant to be committed to Git.

## Dependencies

The runtime dependencies are listed in `requirements.txt`:

- Pillow
- pyperclip
- requests
