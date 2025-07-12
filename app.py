# app.py - Main Gradio app for Budget-Aware LLM Reasoning Demo

import gradio as gr
import time
import tiktoken
import os
from huggingface_hub import InferenceClient
from huggingface_hub.utils import HfHubHTTPError
from case_studies import CASE_STUDIES

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env file loaded")
except ImportError:
    print("💡 Install python-dotenv for automatic .env loading: pip install python-dotenv")
except Exception as e:
    print(f"⚠️ Could not load .env file: {e}")

# Initialize tokenizer for token counting
try:
    tokenizer = tiktoken.get_encoding("cl100k_base")
except:
    tokenizer = None

# Models to try in order of preference
MODELS_TO_TRY = [
    "meta-llama/Llama-3.1-8B-Instruct",     # Best quality (requires approval)
    "microsoft/Phi-3-mini-4k-instruct",     # Good reasoning, no approval needed
    "HuggingFaceH4/zephyr-7b-beta",         # Strong instruction following
    "mistralai/Mistral-7B-Instruct-v0.1"    # Good performance
]

# Budget token limits
BUDGET_MAPPING = {
    'Low': 50,
    'Medium': 110, 
    'High': 200
}

def count_tokens(text):
    """Count tokens using tiktoken or fallback to word count"""
    if tokenizer:
        return len(tokenizer.encode(text))
    else:
        # Fallback: estimate 1.3 tokens per word
        return int(len(text.split()) * 1.3)

def simulate_typing(text, speed=0.03):
    """Simulate typing effect word by word"""
    words = text.split()
    for i in range(len(words)):
        partial_text = ' '.join(words[:i+1])
        yield partial_text
        time.sleep(speed)

def create_budget_prompt(original_prompt, budget_tokens, case_type="general"):
    """Create budget-constrained prompt optimized for instruction-following models"""
    if case_type == "agentic":
        return f"""You are a helpful AI assistant with a thinking budget of {budget_tokens} tokens. Use a structured approach to solve this problem efficiently.

{original_prompt}

Please use this format:
Thought: [your reasoning process]
Action: [what you would do or search for]
Observation: [result or information found]
Final Answer: [your conclusion]

Keep your total response under {budget_tokens} tokens while being thorough."""
    
    else:
        return f"""You are a helpful AI assistant with a thinking budget of {budget_tokens} tokens. Solve this problem step by step, but be concise and efficient.

{original_prompt}

Please think through this systematically and efficiently. Show your reasoning steps and end with a clear "Final Answer:" statement. Keep your response under {budget_tokens} tokens."""

def query_huggingface_api(prompt, max_tokens=200):
    """Query Hugging Face Inference API with model fallback using the official client."""
    try:
        # The InferenceClient automatically uses the HF_TOKEN environment variable.
        client = InferenceClient(timeout=30)
        
        # Try models in order of preference
        for model_name in MODELS_TO_TRY:
            print(f"🔄 Trying model: {model_name}")
            
            try:
                # Use the chat_completion for modern conversational models
                response = client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    model=model_name,
                    max_tokens=min(max_tokens, 200),
                    temperature=0.7,
                    top_p=0.9,
                    stop=["<|eot_id|>", "</s>", "<|end|>"],
                )
                
                # Extract the message content and finish reason from the response
                response_text = response.choices[0].message.content
                finish_reason = response.choices[0].finish_reason

                if response_text and response_text.strip():
                    print(f"✅ Success with {model_name}")
                    print(f"Generated text: {response_text[:100]}...")
                    return response_text, finish_reason, None
                else:
                    print(f"⚠️ Empty response from {model_name}, trying next model...")
                    continue
            
            except HfHubHTTPError as e:
                # Handle specific HTTP errors from the Hub client
                status_code = e.response.status_code
                if status_code == 401:
                    print(f"🔒 {model_name} requires approval (expected for Llama)")
                elif status_code == 404:
                     print(f"❌ Model {model_name} not found or not available via API.")
                elif status_code == 503:
                    print(f"⏳ {model_name} is loading, trying next model...")
                else:
                    print(f"❌ Error with {model_name} (HTTP {status_code}): {e}")
                continue
            except Exception as e:
                # Handle other exceptions like timeouts
                print(f"❌ An unexpected error occurred with {model_name}: {str(e)}")
                continue
        
        return None, None, "All models failed. Please check your HF token, model access permissions, and network connection."
            
    except Exception as e:
        error_msg = f"API request failed during client initialization: {str(e)}"
        print(error_msg)
        return None, None, error_msg

def generate_dynamic_response(prompt, budget_level, case_name):
    """Generate response using HF Inference API with budget constraints"""
    budget_tokens = BUDGET_MAPPING[budget_level]
    
    print(f"🚀 Generating response for: {case_name}, budget: {budget_level} ({budget_tokens} tokens)")
    
    # Determine case type for appropriate prompting
    case_type = "agentic" if "Capital City Finder" in str(case_name) else "general"
    
    # Create budget-constrained prompt
    budget_prompt = create_budget_prompt(prompt, budget_tokens, case_type)
    
    print(f"📝 Budget prompt created, length: {len(budget_prompt)} chars")
    
    # Query HF API with fallback models
    response_text, finish_reason, error = query_huggingface_api(budget_prompt, budget_tokens)
    
    if response_text is None:
        print(f"❌ All models failed: {error}")
        return f"❌ Unable to generate response. Please try again.\n\nError: {error}", 0, "No response generated"
    
    # Count actual tokens used
    actual_tokens = count_tokens(response_text)
    
    # Extract final answer
    final_answer = extract_final_answer(response_text)

    # If model ran out of tokens, update the final answer to reflect it.
    if finish_reason == 'length' and "Final Answer:" not in response_text:
        final_answer = "Incomplete: Model ran out of tokens before reaching a conclusion."
    
    print(f"✅ Response generated: {actual_tokens} tokens, answer: {final_answer[:50]}...")
    
    return response_text, actual_tokens, final_answer

def extract_final_answer(response_text):
    """Extract final answer from LLM response"""
    # Look for common patterns
    lines = response_text.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith("Final Answer:"):
            return line.replace("Final Answer:", "").strip()
        elif line.startswith("Answer:"):
            return line.replace("Answer:", "").strip()
    
    # If no explicit final answer, return the last non-empty line
    for line in reversed(lines):
        if line.strip():
            return line.strip()
    
    return "No clear answer found"

def generate_response(case_name, budget_level):
    """Generate live LLM response via API"""
    if case_name and case_name in CASE_STUDIES:
        prompt = CASE_STUDIES[case_name]['prompt']
        case_identifier = case_name
    else:
        return "Please select a case study from the dropdown.", "N/A", "N/A"
    
    try:
        response_text, actual_tokens, final_answer = generate_dynamic_response(
            prompt, budget_level, case_identifier
        )
        budget_tokens = BUDGET_MAPPING[budget_level]
        
        token_display = f"🔢 {actual_tokens} / {budget_tokens} tokens"
        answer_display = f"✅ {final_answer}"
        
        return response_text, token_display, answer_display
    
    except Exception as e:
        return f"❌ Error generating response: {str(e)}", "N/A", "N/A"

def animate_response(case_name, budget_level):
    """Animate LLM response with typing effect"""
    if case_name and case_name in CASE_STUDIES:
        prompt = CASE_STUDIES[case_name]['prompt']
        case_identifier = case_name
    else:
        yield "Please select a case study from the dropdown."
        return
    
    try:
        response_text, _, _ = generate_dynamic_response(
            prompt, budget_level, case_identifier
        )
        
        # Simulate typing effect for live response
        for partial_text in simulate_typing(response_text):
            yield partial_text
    
    except Exception as e:
        yield f"❌ Error animating response: {str(e)}"

# --- Gradio Interface ---

CSS = """
/* General styling */
.gradio-container {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #F8F8F8;
}
.gr-button {
    text-transform: uppercase;
    font-weight: bold;
}
/* Custom classes */
.reasoning-box {
    background-color: #2E2E2E;
    color: #F0F0F0;
    border: 1px solid #444;
    border-radius: 8px;
    padding: 15px;
    font-family: 'IBM Plex Mono', monospace;
    line-height: 1.6;
    height: 400px;
    overflow-y: auto;
}
.final-answer-box {
    font-size: 1.2em;
    font-weight: bold;
    padding: 15px;
    border: 1px solid #4CAF50;
    border-radius: 8px;
    background-color: #E8F5E9;
}
.problem-box {
    background-color: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    padding: 15px;
}
"""

INTRO_MARKDOWN = """
# 🤖 Budget-Aware LLM Reasoning Demo

**What is this about?**
This demo showcases how an LLM's reasoning process can be guided by a token budget. You can observe how different budget constraints affect the model's ability to think through a problem and provide a complete answer.

*   **🧠 Select a Case Study**: Choose from a list of pre-defined problems.
*   **⚖️ Set a Budget**: Apply a `Low`, `Medium`, or `High` token budget to constrain the model's response length.
*   **🤖 Budget-Aware Reasoning**: See how token limits affect the quality and completeness of the AI's thinking process.
*   **⚙️ Multi-Model Fallback**: The app automatically tries several top open-source models if one fails or is unavailable.
*   **🚀 Live AI Inference**: All responses are generated in real-time using Meta's Llama 3.1 model.

This demo is inspired by the paper **"Steering LLM Thinking with Budget Guidance"** ([arXiv:2506.13752](https://arxiv.org/abs/2506.13752)).
"""

with gr.Blocks(css=CSS, theme=gr.themes.Soft()) as demo:
    gr.Markdown(INTRO_MARKDOWN)

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("## Controls")
            
            with gr.Row():
                case_study_dd = gr.Dropdown(
                    choices=list(CASE_STUDIES.keys()),
                    label="Select a Case Study",
                    value="Math Word Problem"
                )
                budget_dd = gr.Dropdown(
                    choices=list(BUDGET_MAPPING.keys()),
                    label="Reasoning Budget",
                    value="Medium"
                )
            
            submit_btn = gr.Button("Generate Response", variant="primary", scale=1)
            
            with gr.Box(elem_classes=["problem-box"], visible=True) as problem_box:
                gr.Markdown("### Problem Description")
                problem_desc = gr.Markdown(CASE_STUDIES["Math Word Problem"]['description'])
                gr.Markdown("---")
                gr.Markdown("### Full Prompt")
                problem_prompt = gr.Markdown(f"```\n{CASE_STUDIES['Math Word Problem']['prompt']}\n```")

        with gr.Column(scale=2):
            gr.Markdown("## Reasoning Trace")
            reasoning_output = gr.Markdown("Your model's thinking process will appear here...", elem_classes=["reasoning-box"])
            
            gr.Markdown("## Token Usage")
            token_output = gr.Textbox(label="Actual vs. Budgeted Tokens", value="N/A", interactive=False)
            
            gr.Markdown("## Final Answer")
            final_answer_output = gr.Markdown("The final answer will be displayed here.", elem_classes=["final-answer-box"])

    # --- Event Handlers ---
    def update_problem_display(case_name):
        if case_name in CASE_STUDIES:
            prompt = CASE_STUDIES[case_name]['prompt']
            description = CASE_STUDIES[case_name]['description']
            return gr.update(visible=True), f"```\n{prompt}\n```", description
        return gr.update(visible=False), "", ""

    def handle_response(case_name, budget_level):
        """Wrapper for static response generation for Gradio state"""
        # We only need the final answer part for the dedicated output box
        _, token_display, final_answer_display = generate_response(case_name, budget_level)
        return token_display, final_answer_display

    def handle_animation(case_name, budget_level):
        """Wrapper for animated response generation"""
        # The animated response yields the full text
        for partial_text in animate_response(case_name, budget_level):
            yield partial_text

    # When a case study is selected, update the problem display
    case_study_dd.change(
        fn=update_problem_display,
        inputs=[case_study_dd],
        outputs=[problem_box, problem_prompt, problem_desc]
    )

    # When submit is clicked
    submit_btn.click(
        fn=handle_response,
        inputs=[case_study_dd, budget_dd],
        outputs=[token_output, final_answer_output],
    ).then(
        fn=handle_animation,
        inputs=[case_study_dd, budget_dd],
        outputs=[reasoning_output]
    )

# Launch the app
demo.launch()
