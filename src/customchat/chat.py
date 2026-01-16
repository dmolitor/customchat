from chatlas import ChatOpenAI
from dotenv import load_dotenv
import json
import os
from pathlib import Path

load_dotenv()
base_dir = Path(__file__).parent.parent.parent

# Make sure the prompt has been generated
if not os.path.exists(base_dir / "prompt.json"):
    raise FileNotFoundError(f"No prompt JSON exists at {str(base_dir / 'prompt.json')}`;\nGenerate the prompt by executing `uv run {str(base_dir / 'src' / 'ragtime' / 'prompt.py')}`")

with open(base_dir / "prompt.json", "r") as f:
    prompt_json = json.load(f)
    PROMPT = prompt_json["prompt"]

# Make sure necessary environment variables have been set
for key in ["MODEL", "OPENAI_API_KEY"]:
    try:
        os.environ[key]
    except Exception:
        raise EnvironmentError(f"Environment variable {key} must be set in .env")

# Make a class to interact with the LLM
# Using chatlas providers, it should be super easy to swap this for many other providers
chat_client = ChatOpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    model=os.environ["MODEL"],
    system_prompt=PROMPT,
)
