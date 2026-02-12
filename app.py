import gradio as gr


def greet(name):
    """Simple greeting function for the demo."""
    if not name:
        return "Hello! Please enter your name."
    return f"Hello, {name}! Welcome to Apertus Demo."


def process_text(text, operation):
    """Process text with various operations."""
    if not text:
        return "Please enter some text."

    if operation == "Uppercase":
        return text.upper()
    elif operation == "Lowercase":
        return text.lower()
    elif operation == "Reverse":
        return text[::-1]
    elif operation == "Count Words":
        word_count = len(text.split())
        return f"Word count: {word_count}"
    else:
        return text


# Create the Gradio interface with tabs
with gr.Blocks(title="Apertus Demo", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🐨 Apertus Demo")
    gr.Markdown("A simple demonstration of Gradio capabilities")

    with gr.Tab("Greeting"):
        with gr.Row():
            with gr.Column():
                name_input = gr.Textbox(
                    label="Your Name",
                    placeholder="Enter your name here...",
                    lines=1
                )
                greet_btn = gr.Button("Greet Me", variant="primary")
            with gr.Column():
                greet_output = gr.Textbox(label="Greeting", lines=2)

        greet_btn.click(fn=greet, inputs=name_input, outputs=greet_output)

    with gr.Tab("Text Processor"):
        with gr.Row():
            with gr.Column():
                text_input = gr.Textbox(
                    label="Input Text",
                    placeholder="Enter some text...",
                    lines=5
                )
                operation = gr.Radio(
                    choices=["Uppercase", "Lowercase", "Reverse", "Count Words"],
                    label="Operation",
                    value="Uppercase"
                )
                process_btn = gr.Button("Process", variant="primary")
            with gr.Column():
                text_output = gr.Textbox(label="Result", lines=5)

        process_btn.click(fn=process_text, inputs=[text_input, operation], outputs=text_output)

    gr.Markdown("---")
    gr.Markdown("Built with [Gradio](https://gradio.app)")


if __name__ == "__main__":
    demo.launch()