# ------------------------------------------------------------------------------------
# A basic Shiny Chat example powered by OpenAI.
# ------------------------------------------------------------------------------------
from shiny.express import ui

from customchat.chat import chat_client

# Set some Shiny page options
ui.page_opts(
    title="Custom Research Chat",
    fillable=True,
    fillable_mobile=True,
)

# Create and display a Shiny chat component
chat = ui.Chat(
    id="chat",
    messages=["Hello! How can I help you today?"],
)
chat.ui()

# Store chat state in the url when an "assistant" response occurs
chat.enable_bookmarking(chat_client, bookmark_store="url")


# Generate a response when the user submits a message
@chat.on_user_submit
async def handle_user_input(user_input: str):
    response = await chat_client.stream_async(user_input)
    await chat.append_message_stream(response)
