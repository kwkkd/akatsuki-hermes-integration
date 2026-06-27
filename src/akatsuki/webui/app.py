"""Basic Gradio web interface for AKATSUKI."""

import sys

try:
    import gradio as gr
except ImportError:
    print("gradio not installed. Install with: pip install gradio")
    sys.exit(1)


def create_interface():
    with gr.Blocks(title="AKATSUKI", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# AKATSUKI Operations Dashboard")

        with gr.Tab("Chat"):
            chatbot = gr.Chatbot(label="Conversation")
            msg = gr.Textbox(label="Message", placeholder="Type your message...")
            clear = gr.Button("Clear")

            def respond(message, history):
                from ..api.client import AkatsukiAPIClient
                client = AkatsukiAPIClient()
                history = history or []
                messages = [{"role": "user", "content": message}]
                try:
                    response = client.chat(messages)
                except ConnectionError as e:
                    response = f"Error: {e}"
                history.append((message, response))
                return "", history

            msg.submit(respond, [msg, chatbot], [msg, chatbot])
            clear.click(lambda: None, None, chatbot, queue=False)

        with gr.Tab("Status"):
            status_btn = gr.Button("Refresh Status")
            status_out = gr.JSON(label="System Status")

            def get_status():
                from ..api.client import ollama_detected
                return {
                    "agents_loaded": True,
                    "ollama_detected": ollama_detected,
                }

            status_btn.click(get_status, outputs=status_out)

        with gr.Tab("Knowledge Base"):
            kb_query = gr.Textbox(label="Search Query")
            kb_results = gr.JSON(label="Results")

            def search_kb(query):
                from ..knowledge_base.rag import KnowledgeBase
                kb = KnowledgeBase()
                return kb.query(query)

            kb_query.submit(search_kb, kb_query, kb_results)

        with gr.Tab("Tools"):
            tools_out = gr.JSON(label="Available Tools")

            def list_tools():
                from ..agents import ALL_AGENTS
                return {name: agent.description for name, agent in ALL_AGENTS.items()}

            demo.load(list_tools, outputs=tools_out)

    return demo


def main():
    demo = create_interface()
    demo.launch(server_name="127.0.0.1", server_port=7860)


if __name__ == "__main__":
    main()
