from dotenv import load_dotenv
import json
from openai import OpenAI
import os
from pathlib import Path

import random
from typing import List

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
class CustomChat:

    def __init__(
        self,
        dev_prompt: str = PROMPT,
        model: str = os.environ["MODEL"],
        api_key: str | None = os.environ["OPENAI_API_KEY"],
        **kwargs
    ):
        self.dev_prompt_approx_num_tokens = round(len(dev_prompt)/4)
        self.dev_prompt = [{"role": "developer", "content": dev_prompt}]
        # Create a unique prompt cache key
        self.prompt_cache_key = f"custom-chat-{random.randint(1, 1000000)}"
        # Extract OpenAI API KEY
        if api_key is None:
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key is None:
                raise ValueError("No OpenAI API key was found and none was provided")
        self._api_key = api_key
        # Instantiate OpenAI client and new conversation
        self.model = model
        self.client = OpenAI(**{"api_key": api_key, **kwargs})
        self.conversation = self.client.conversations.create()
        # Instantiate a record of all LLM responses and cache performance
        self.response_history = {
            "response": list(),
            "response_id": list(),
            "cache_pct": list(),
            "n": 0
        }
    
    def query(self, query: str, **kwargs) -> str:
        """
        Intakes a user query, stores the response object, and returns response text
        """
        # If it's the initial response, we must append the dev instructions
        if self.response_history["n"] == 0:
            user_query = self.dev_prompt + [{"role": "user", "content": query}]
        else:
            user_query = [{"role": "user", "content": query}]
        # Ensure that tokens get cached (like we would expect them to)
        response = self.client.responses.create(
            model=self.model,
            conversation=self.conversation.id,
            prompt_cache_key=self.prompt_cache_key,
            input=user_query,
            **kwargs
        )
        usage = response.usage
        cache_percentage = usage.input_tokens_details.cached_tokens/usage.input_tokens
        # Log response information
        self.response_history["response"].append(response)
        self.response_history["response_id"].append(response.id)
        self.response_history["cache_pct"].append(round(cache_percentage*100, 2))
        self.response_history["n"] += 1
        # Return response text
        return response.output_text

def pull_response_data(chat: CustomChat) -> List:
    return {k: chat.response_history[k] for k in ["response_id", "cache_pct"]}
