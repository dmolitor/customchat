# Custom Research Chatbot

Enhance an LLM's context with research content of your choice (your own or others).
This is allows you to provide an LLM with relevant and cutting-edge context on topics
of your choice, particularly helpful for research synthesis and idea generation.

Why not just upload files into e.g. ChatGPT and then chat with those files? This basically
does that, but allows you the flexibility of interacting with the LLM programatically and
easily handling many files at once.

## Setup

You'll need/want `uv` to make this super easy; [install uv here](https://docs.astral.sh/uv/getting-started/installation/). Then take the following steps.

### Install dependencies :package:

Begin by installing the necessary dependencies:
```
uv sync
```

### Setup LLM API :robot:

Currently this is set up to exclusively utilize OpenAI LLMs (in theory it should be
simple to generalize to other providers). Specify both the desired OpenAI model and your
OpenAI API key as environment variables in `.env`. If these variables are not defined,
an exception will be raised.

### Setup data :floppy_disk:

Put your research data into the `/data` folder. No particular file/directory structure
required.
> [!NOTE]
> Currently, this is set up to handle exclusively PDFs. If your data is in PDF format,
> everything should "just work". It's relatively easy to generalize to other formats,
> however you'll need to modify the code accordingly. See comments in `src/customchat/prompt.py`
> for guidance on exactly what to modify.

### Customize the default prompt :mega:

The default prompt in `prompt.txt` should be customized to your particular needs.

### Build the prompt (if you haven't already) :bookmark:

Next, generate your custom research prompt (this only needs to be done once!):
```
uv run ./src/customchat/prompt.py
```

### Run the chatbot app :robot:

Finally, launch the custom [Shiny](https://shiny.posit.co/py/) chat app:
```
uv run shiny run --launch-browser app.py
```