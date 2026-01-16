import plotnine as pn
import pandas as pd
from shiny import App, reactive, render, ui

from customchat.chat import CustomChat, pull_response_data

app_ui = ui.page_fillable(
    ui.div(
        ui.h2("Custom Research Chatbot", style="text-align: center; margin-bottom: 30px;"),
        
        # Tab navigation - NO style parameter here
        ui.navset_tab(
            ui.nav_panel(
                "Chat",
                ui.div(
                    # Chat history container
                    ui.div(
                        ui.output_ui("chat_history"),
                        id="chat_container",
                        style="""
                            flex: 1;
                            overflow-y: auto; 
                            margin-bottom: 20px; 
                            padding: 15px;
                            width: min(60%, 800px);
                            max-width: 90%;
                            margin-left: auto;
                            margin-right: auto;
                            background-color: white;
                            min-height: 300px;
                        """
                    ),
                    
                    # Input container at bottom
                    ui.div(
                        ui.div(
                            ui.input_text_area(
                                "user_message",
                                label=None,
                                placeholder="Type your message here...",
                                rows=1,
                                width="100%",
                                resize="none"
                            ),
                            ui.input_action_button(
                                "submit", 
                                "➤",
                                class_="btn btn-primary",
                                style="""
                                    position: absolute; 
                                    right: 8px; 
                                    top: 50%;
                                    transform: translateY(-50%);
                                    border-radius: 50%;
                                    width: 36px;
                                    height: 36px;
                                    padding: 0;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    border: none;
                                    font-size: 16px;
                                    font-weight: bold;
                                """
                            ),
                            style="""
                                position: relative; 
                                width: min(60%, 800px);
                                max-width: 90%;
                                margin: 0 auto;
                            """
                        ),
                        style="""
                            position: sticky;
                            bottom: 0;
                            background-color: white;
                            padding: 10px 0 20px 0;
                        """
                    ),
                    style="""
                        height: 100%;
                        display: flex;
                        flex-direction: column;
                    """
                )
            ),
            
            ui.nav_panel(
                "Token caching",
                ui.div(
                    ui.div(
                        ui.output_plot("token_plot"),
                        style="""
                            width: 80%;
                            height: 500px;
                            margin: 20px auto;
                            border: 2px solid #e0e0e0;
                            border-radius: 8px;
                            padding: 20px;
                            background-color: #f8f9fa;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        """
                    ),
                    ui.div(
                        ui.input_action_button(
                            "plot_token_caching",
                            "Plot token caching",
                            class_="btn btn-primary btn-lg",
                            style="""
                                padding: 12px 30px;
                                font-size: 16px;
                                font-weight: bold;
                                border-radius: 8px;
                            """
                        ),
                        style="""
                            text-align: center;
                            margin-top: 30px;
                        """
                    ),
                    style="""
                        width: 100%;
                        max-width: 1000px;
                        margin: 0 auto;
                        padding: 20px;
                        display: flex;
                        flex-direction: column;
                    """
                )
            )

        ),
        
        # CSS for textarea styling and responsive behavior
        ui.tags.style("""
            #user_message {
                padding: 12px 50px 12px 15px !important;
                border: 2px solid #e0e0e0 !important;
                border-radius: 25px !important;
                outline: none !important;
                font-size: 14px !important;
                line-height: 1.4 !important;
                min-height: 45px !important;
                max-height: 200px !important;
                overflow-y: auto !important;
                resize: none !important;
            }
            #user_message:focus {
                border-color: #007bff !important;
                box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25) !important;
            }
            
            /* Tab content should fill height */
            .tab-content {
                flex: 1;
                display: flex;
                flex-direction: column;
                height: 100%;
            }
            
            .tab-pane {
                flex: 1;
                display: flex;
                flex-direction: column;
                height: 100%;
            }
            
            /* Responsive width adjustments */
            @media (max-width: 768px) {
                #chat_container,
                #chat_container + div > div {
                    width: 90% !important;
                    max-width: 90% !important;
                }
            }
            
            @media (min-width: 1200px) {
                #chat_container,
                #chat_container + div > div {
                    width: 50% !important;
                }
            }
        """),
        
        # JavaScript for auto-expanding textarea, button positioning, and auto-scroll
        ui.tags.script("""
            document.addEventListener('DOMContentLoaded', function() {
                function autoResize() {
                    const textarea = document.getElementById('user_message');
                    const button = document.getElementById('submit');
                    if (textarea && button) {
                        textarea.style.height = 'auto';
                        const newHeight = Math.min(textarea.scrollHeight, 200);
                        textarea.style.height = newHeight + 'px';
                        
                        // Position button - centered for single line, bottom-right for multi-line
                        if (newHeight <= 45) {
                            // Single line - center the button
                            button.style.top = '50%';
                            button.style.bottom = 'auto';
                            button.style.transform = 'translateY(-50%)';
                        } else {
                            // Multi-line - pin to bottom right
                            button.style.top = 'auto';
                            button.style.bottom = '8px';
                            button.style.transform = 'none';
                        }
                    }
                }
                
                function resetToSingleLine() {
                    const textarea = document.getElementById('user_message');
                    const button = document.getElementById('submit');
                    if (textarea && button) {
                        textarea.style.height = '45px';
                        button.style.top = '50%';
                        button.style.bottom = 'auto';
                        button.style.transform = 'translateY(-50%)';
                    }
                }
                
                function scrollToBottom() {
                    const chatContainer = document.getElementById('chat_container');
                    if (chatContainer) {
                        setTimeout(() => {
                            chatContainer.scrollTop = chatContainer.scrollHeight;
                        }, 100);
                    }
                }
                
                // Auto-resize on input
                document.addEventListener('input', function(e) {
                    if (e.target.id === 'user_message') {
                        autoResize();
                    }
                });
                
                // Monitor textarea value using polling to catch when it's cleared by Shiny
                let lastValue = '';
                const textarea = document.getElementById('user_message');
                if (textarea) {
                    lastValue = textarea.value;
                    
                    // Poll every 50ms to check if textarea was cleared
                    setInterval(() => {
                        const currentValue = textarea.value;
                        if (lastValue !== '' && currentValue === '') {
                            // Textarea was just cleared - reset to single line
                            resetToSingleLine();
                        } else if (currentValue !== lastValue && currentValue !== '') {
                            // Content changed and not empty - auto resize
                            setTimeout(autoResize, 10);
                        }
                        lastValue = currentValue;
                    }, 50);
                    
                    // Initial resize
                    autoResize();
                }
                
                // Observer for chat container changes (new messages)
                const chatObserver = new MutationObserver(function(mutations) {
                    mutations.forEach(function(mutation) {
                        if (mutation.type === 'childList' || mutation.type === 'subtree') {
                            scrollToBottom();
                        }
                    });
                });
                
                const chatContainer = document.getElementById('chat_container');
                if (chatContainer) {
                    chatObserver.observe(chatContainer, { 
                        childList: true, 
                        subtree: true 
                    });
                }
                
                // Initial scroll to bottom
                scrollToBottom();
            });
        """),
        
        style="""
            width: 100%; 
            height: 100vh;
            margin: 0 auto; 
            padding: 20px;
            display: flex;
            flex-direction: column;
        """
    ),
    title="Custom Research Chatbot"
)


def server(input, output, session):

    # Initialize chat instance
    chat = CustomChat()

    # Store chat messages
    chat_messages = reactive.value([])
    
    @render.ui
    def chat_history():
        messages = chat_messages()
        if not messages:
            return ui.div(style="height: 100%;")
        
        chat_elements = []
        for msg in messages:
            if msg["type"] == "user":
                chat_elements.append(
                    ui.div(
                        ui.div(
                            msg["content"],
                            style="""
                                background-color: #007bff; 
                                color: white; 
                                padding: 10px 15px; 
                                border-radius: 18px; 
                                max-width: 70%; 
                                margin-left: auto;
                                margin-bottom: 10px;
                                word-wrap: break-word;
                                white-space: pre-wrap;
                            """
                        ),
                        style="display: flex; justify-content: flex-end; margin-bottom: 5px;"
                    )
                )
            else:
                chat_elements.append(
                    ui.div(
                        ui.div(
                            msg["content"],
                            style="""
                                background-color: #f1f3f4; 
                                color: #333; 
                                padding: 10px 15px; 
                                border-radius: 18px; 
                                max-width: 70%; 
                                margin-right: auto;
                                margin-bottom: 10px;
                                word-wrap: break-word;
                                white-space: pre-wrap;
                            """
                        ),
                        style="display: flex; justify-content: flex-start; margin-bottom: 5px;"
                    )
                )
        
        return ui.div(*chat_elements, style="padding: 10px 0;")

    @reactive.effect
    @reactive.event(input.submit)
    def handle_message():

        user_msg = input.user_message().strip()
        
        # Do nothing if message is empty
        if not user_msg:
            return
        
        # Add user message to chat
        current_messages = list(chat_messages())
        current_messages.append({"type": "user", "content": user_msg})
        chat_messages.set(current_messages)
        
        # Clear input
        ui.update_text_area("user_message", value="")
        
        # Add bot response
        bot_response = chat.query(query=user_msg)
        current_messages = list(chat_messages())
        current_messages.append({"type": "bot", "content": bot_response})
        chat_messages.set(current_messages)
    
    @render.plot
    @reactive.event(input.plot_token_caching)
    def token_plot():
        
        data = pd.DataFrame(pull_response_data(chat))
        data = data.assign(chat_id=list(range(len(data["response_id"]))))

        if (len(data) == 0):
            return (
                pn.ggplot(data, pn.aes(x="chat_id", y="cache_pct")) + 
                pn.theme_minimal() +
                pn.labs(
                    title="Token Caching Performance",
                    x="Chat ID",
                    y="Percentage of input tokens cached"
                )
            )
        
        # Create the plot
        plot = (pn.ggplot(data, pn.aes(x="chat_id", y="cache_pct")) +
                pn.geom_point() +
                pn.geom_line() +
                pn.scale_x_continuous(breaks=range(0, int(data["chat_id"].max()) + 1)) +
                pn.scale_y_continuous(limits=(0, 100), breaks=[0, 20, 40, 60, 80, 100]) +
                pn.labs(
                    title="Token Caching Performance",
                    x="Chat ID",
                    y="Percentage of input tokens cached"
                ) +
                pn.theme_minimal())
        
        return plot

app = App(app_ui, server)
