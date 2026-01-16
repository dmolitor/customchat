from dotenv import load_dotenv
import json
from pathlib import Path
from pypdf import PdfReader

load_dotenv()

base_dir = Path(__file__).parent.parent.parent 
data_dir = base_dir / "data"

## To generalize code to other non-PDF formats, tweak the code below --------

# This recursively identifies all PDF files in the /data directory
# This can be modified to return a list of any type of files
files = [x for x in data_dir.rglob("*.pdf")]

# This function currently extracts text from a PDF file
# This can be modified to extract text from any file format
def extract_text(file: str, y_min: float = 50) -> str:
    """Intake a file path and extract its text as a string"""
    reader = PdfReader(file)
    parts = []
    def visitor_body(text, cm, tm, font_dict, font_size):
        y = tm[5]
        if (y_min < y) or (y == 0):
            parts.append(text)
    for page in reader.pages:
        page.extract_text(visitor_text=visitor_body)
    return "".join(parts)

# ---------------------------------------------------------------------------

if __name__ == "__main__":

    with open(base_dir / "prompt.txt", "r") as p:
        DEV_PROMPT = "".join(p.readlines())

    # Initialize the developer prompt for the LLM with custom instructions.
    # Skip any pdf abstracts that fail while parsing.
    for path in files:
        try:
            text = extract_text(path)
        except Exception:
            continue
        DEV_PROMPT = DEV_PROMPT + "\n\n---\n\n" + text

    DEV_PROMPT = (
        DEV_PROMPT
        + "\n---\n\n"
        + "Make your responses as concise as possible while still being robust."
    )

    dev_prompt_json = {"prompt": DEV_PROMPT}

    with open(base_dir / "prompt.json", "w") as f:
        json.dump(dev_prompt_json, f, indent=2)
