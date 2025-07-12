
# app.py - Main Gradio app for Budget-Aware LLM Reasoning Demo

# This file will be populated in later phases
import gradio as gr
import time
import tiktoken
import os
import requests
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

Please think through this systematically but efficiently. Show your reasoning steps and end with a clear "Final Answer:" statement. Keep your response under {budget_tokens} tokens."""

def query_huggingface_api(prompt, max_tokens=200):
    """Query Hugging Face Inference API with model fallback"""
    try:
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            print("No HF_TOKEN environment variable found")
            return None, "No HF token available"
        
        headers = {"Authorization": f"Bearer {hf_token}"}
        
        # Try models in order of preference
        for model_name in MODELS_TO_TRY:
            api_url = f"https://api-inference.huggingface.co/models/{model_name}"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": min(max_tokens, 200),
                    "temperature": 0.7,
                    "do_sample": True,
                    "top_p": 0.9,
                    "return_full_text": False,
                    "stop": ["<|eot_id|>", "</s>", "<|end|>"]  # Stop tokens for different models
                }
            }
            
            print(f"🔄 Trying model: {model_name}")
            
            try:
                response = requests.post(api_url, headers=headers, json=payload, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Success with {model_name}")
                    
                    if isinstance(result, list) and len(result) > 0:
                        generated_text = result[0].get("generated_text", "")
                        if generated_text.startswith(prompt):
                            generated_text = generated_text[len(prompt):].strip()
                        
                        if len(generated_text.strip()) > 10:  # Valid response
                            print(f"Generated text: {generated_text[:100]}...")
                            return generated_text, None
                        else:
                            print(f"Response too short from {model_name}")
                            continue
                    else:
                        print(f"Invalid response format from {model_name}")
                        continue
                        
                elif response.status_code == 503:
                    print(f"⏳ {model_name} is loading, trying next model...")
                    continue
                elif response.status_code == 401:
                    print(f"🔒 {model_name} requires approval (expected for Llama)")
                    continue
                else:
                    print(f"❌ {model_name} failed: {response.status_code}")
                    continue
                    
            except requests.exceptions.Timeout:
                print(f"⏱️ {model_name} timed out, trying next model...")
                continue
            except Exception as e:
                print(f"❌ {model_name} error: {str(e)}")
                continue
        
        return None, "All models failed - please check your HF token and try again"
            
    except Exception as e:
        error_msg = f"API request failed: {str(e)}"
        print(error_msg)
        return None, error_msg

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
    response_text, error = query_huggingface_api(budget_prompt, budget_tokens)
    
    if response_text is None:
        print(f"❌ All models failed: {error}")
        return f"❌ Unable to generate response. Please try again.\n\nError: {error}", 0, "No response generated"
    
    # Count actual tokens used
    actual_tokens = count_tokens(response_text)
    
    # Extract final answer
    final_answer = extract_final_answer(response_text)
    
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

def generate_response(case_name, budget_level, custom_prompt):
    """Generate live LLM response via API"""
    if custom_prompt.strip():
        prompt = custom_prompt.strip()
        case_identifier = "Custom"
    elif case_name and case_name in CASE_STUDIES:
        prompt = CASE_STUDIES[case_name]['prompt']
        case_identifier = case_name
    else:
        return "❌ No valid prompt available.", "N/A", "N/A"
    
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

def animate_response(case_name, budget_level, custom_prompt):
    """Animate LLM response with typing effect"""
    if custom_prompt.strip():
        prompt = custom_prompt.strip()
        case_identifier = "Custom"
    elif case_name and case_name in CASE_STUDIES:
        prompt = CASE_STUDIES[case_name]['prompt']
        case_identifier = case_name
    else:
        yield "❌ No valid prompt available."
        return
    
    try:
        response_text, actual_tokens, final_answer = generate_dynamic_response(
            prompt, budget_level, case_identifier
        )
        
        # Simulate typing effect for live response
        for partial_text in simulate_typing(response_text):
            yield partial_text
    
    except Exception as e:
        yield f"❌ Error generating response: {str(e)}"

# Custom CSS for Homebrew-style theme (matching the green terminal aesthetic)
homebrew_css = """
/* Homebrew-inspired green terminal theme */
.gradio-container {
    font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace !important;
    background: radial-gradient(ellipse at center, #0a0e0a 0%, #000000 100%) !important;
    color: #00ff41 !important;
    min-height: 100vh !important;
}

.prose h1, .prose h2, .prose h3 {
    color: #00ff41 !important;
    font-weight: 600 !important;
    text-shadow: 0 0 10px rgba(0, 255, 65, 0.3) !important;
}

.prose p, .prose li {
    color: #00cc33 !important;
    line-height: 1.6 !important;
}

.prose a {
    color: #ff6b35 !important;
    text-decoration: none !important;
    text-shadow: 0 0 5px rgba(255, 107, 53, 0.5) !important;
    border-bottom: 1px solid rgba(255, 107, 53, 0.3) !important;
}

.prose a:hover {
    color: #ff4500 !important;
    text-decoration: underline !important;
    text-shadow: 0 0 10px rgba(255, 69, 0, 0.7) !important;
    border-bottom: 1px solid #ff4500 !important;
}

.prose strong {
    color: #00ff41 !important;
    text-shadow: 0 0 8px rgba(0, 255, 65, 0.4) !important;
}

.prose em {
    color: #00cc88 !important;
}

/* Input styling */
.gr-textbox, .gr-dropdown, .gr-radio {
    background: rgba(0, 20, 0, 0.8) !important;
    border: 1px solid #00aa33 !important;
    color: #00ff41 !important;
    border-radius: 4px !important;
    box-shadow: inset 0 0 10px rgba(0, 255, 65, 0.1) !important;
}

.gr-textbox:focus, .gr-dropdown:focus {
    border-color: #00ff41 !important;
    box-shadow: 0 0 0 2px rgba(0, 255, 65, 0.3), inset 0 0 10px rgba(0, 255, 65, 0.2) !important;
}

/* Button styling */
.gr-button {
    background: linear-gradient(135deg, #006600 0%, #00aa33 100%) !important;
    border: 1px solid #00ff41 !important;
    color: #000000 !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
    text-shadow: none !important;
}

.gr-button:hover {
    background: linear-gradient(135deg, #00aa33 0%, #00ff41 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(0, 255, 65, 0.3) !important;
}

/* Panel styling */
.gr-panel {
    background: rgba(0, 20, 0, 0.6) !important;
    border: 1px solid #00aa33 !important;
    border-radius: 6px !important;
    box-shadow: 0 0 20px rgba(0, 255, 65, 0.1) !important;
}

/* Labels */
.gr-label {
    color: #00ff41 !important;
    font-weight: 600 !important;
    margin-bottom: 8px !important;
    text-shadow: 0 0 5px rgba(0, 255, 65, 0.3) !important;
}

/* Accordion/Collapsible styling */
details {
    background: rgba(0, 20, 0, 0.8) !important;
    border: 1px solid #00aa33 !important;
    border-radius: 6px !important;
    margin-bottom: 16px !important;
    padding: 16px !important;
    box-shadow: 0 0 15px rgba(0, 255, 65, 0.1) !important;
}

details summary {
    color: #00ff41 !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    padding: 8px 0 !important;
    font-size: 1.1em !important;
    text-shadow: 0 0 8px rgba(0, 255, 65, 0.4) !important;
}

details summary:hover {
    color: #00ff88 !important;
    text-shadow: 0 0 12px rgba(0, 255, 136, 0.6) !important;
}

details[open] summary {
    border-bottom: 1px solid #00aa33 !important;
    margin-bottom: 16px !important;
    padding-bottom: 16px !important;
}

/* Reasoning trace special styling */
.reasoning-trace {
    background: rgba(0, 10, 0, 0.9) !important;
    border: 1px solid #00aa33 !important;
    border-radius: 6px !important;
    padding: 16px !important;
    font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace !important;
    line-height: 1.5 !important;
    white-space: pre-wrap !important;
    color: #00ff41 !important;
    box-shadow: inset 0 0 20px rgba(0, 255, 65, 0.1) !important;
}

/* Metrics styling */
.metrics {
    background: rgba(0, 20, 0, 0.8) !important;
    border: 1px solid #00aa33 !important;
    border-radius: 4px !important;
    padding: 12px !important;
    color: #00ff88 !important;
    font-weight: 600 !important;
    text-shadow: 0 0 5px rgba(0, 255, 136, 0.3) !important;
}

/* Title styling */
.app-title {
    text-align: center !important;
    color: #00ff41 !important;
    font-size: 2.5em !important;
    font-weight: 700 !important;
    margin-bottom: 8px !important;
    text-shadow: 0 0 20px rgba(0, 255, 65, 0.6) !important;
}

.app-subtitle {
    text-align: center !important;
    color: #00cc33 !important;
    font-size: 1.1em !important;
    margin-bottom: 24px !important;
    text-shadow: 0 0 10px rgba(0, 204, 51, 0.4) !important;
}

/* Animation for typing effect */
.typing::after {
    content: '▋' !important;
    color: #00ff41 !important;
    animation: blink 1s infinite !important;
}

@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
}

/* Additional terminal-like effects */
.gradio-container::before {
    content: '' !important;
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100% !important;
    height: 100% !important;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0, 255, 65, 0.03) 2px,
        rgba(0, 255, 65, 0.03) 4px
    ) !important;
    pointer-events: none !important;
    z-index: 1000 !important;
}

/* Radio button styling */
.gr-radio input[type="radio"] {
    accent-color: #00ff41 !important;
}

/* Dropdown styling */
.gr-dropdown select {
    background: rgba(0, 20, 0, 0.8) !important;
    color: #00ff41 !important;
    border: 1px solid #00aa33 !important;
}
"""

# Create the Gradio interface
with gr.Blocks(css=homebrew_css, title="🧠 Budget-Aware LLM Reasoning", theme=gr.themes.Base()) as demo:
    # Header
    gr.HTML("""
    <div class="app-title">🧠 Budget-Aware LLM Reasoning</div>
    <div class="app-subtitle">Explore how thinking budgets affect AI reasoning quality</div>
    """)
    
    # Collapsible help section
    gr.HTML("""
    <details>
        <summary>💡 What is this about and how do I use it?</summary>
        <div style="margin-top: 16px;">
            <p><strong>About this demo:</strong></p>
            <p>This demo showcases <strong>live budget-aware reasoning</strong> using Meta's Llama 3.1 8B Instruct model. Unlike static examples, this generates real-time responses that adapt to different "thinking budgets" (token limits).</p>
            
            <p>When you give an AI more tokens to "think," it can provide more detailed reasoning and often more accurate answers. This demo shows how token budgets directly affect reasoning quality.</p>
            
            <p><strong>How to use:</strong></p>
            <ol>
                <li><strong>Select a Problem:</strong> Choose from pre-built case studies or enter your own custom prompt.</li>
                <li><strong>Choose a Thinking Budget:</strong> Select "Low" (50 tokens), "Medium" (110 tokens), or "High" (200 tokens).</li>
                <li><strong>Watch Live Reasoning:</strong> See how Llama 3.1 adapts its reasoning style to fit within your token budget.</li>
                <li><strong>Compare Results:</strong> Try the same problem with different budgets to see the quality difference.</li>
            </ol>
            
            <p><strong>🚀 Live AI Inference:</strong> All responses are generated in real-time using Meta's Llama 3.1 model - no pre-computed answers!</p>
            
            <p><em>Related research:</em> Li, J., Zhao, W., Zhang, Y., & Gan, C. (2025). <strong>Steering LLM Thinking with Budget Guidance</strong>. <a href="https://arxiv.org/abs/2506.13752" target="_blank">arXiv:2506.13752</a>.</p>
        </div>
    </details>
    """)
    
    # Main interface
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🎯 Configuration")
            case_study_select = gr.Dropdown(
                choices=list(CASE_STUDIES.keys()), 
                label="📝 Select a Case Study", 
                value=list(CASE_STUDIES.keys())[0],
                elem_classes=["gr-dropdown"]
            )
            budget_radio = gr.Radio(
                choices=['Low', 'Medium', 'High'], 
                label="🎚️ Select a Thinking Level", 
                value='Low',
                elem_classes=["gr-radio"]
            )
            
            custom_prompt = gr.Textbox(
                label="✏️ Optional Custom Prompt", 
                placeholder="Enter your own prompt here...", 
                value="",
                lines=2,
                elem_classes=["gr-textbox"]
            )
            
            # Show current problem
            with gr.Group():
                gr.Markdown("### 🔍 Current Problem")
                problem_display = gr.Markdown("", elem_classes=["problem-display"])
                
            # Status indicator
            with gr.Group():
                gr.Markdown("### 📊 Status")
                status_display = gr.Markdown("🔄 Ready", elem_classes=["status-display"])
        
        with gr.Column(scale=2):
            gr.Markdown("### 🤖 AI Reasoning & Response")
            reasoning_trace = gr.Textbox(
                label="💭 Reasoning Trace", 
                lines=12,
                elem_classes=["reasoning-trace"],
                show_copy_button=True
            )
            
            with gr.Row():
                actual_tokens = gr.Textbox(
                    label="📊 Token Usage", 
                    elem_classes=["metrics"],
                    interactive=False
                )
                final_answer = gr.Textbox(
                    label="🎯 Final Answer", 
                    elem_classes=["metrics"],
                    interactive=False
                )
    
    # Update problem display
    def update_problem_display(case_name):
        if case_name and case_name in CASE_STUDIES:
            case_data = CASE_STUDIES[case_name]
            return f"**{case_data['description']}**\n\n*Prompt:* {case_data['prompt']}"
        return ""
    
    # Update status display
    def update_status(custom_prompt):
        if custom_prompt.strip():
            return "🚀 Processing custom prompt with live Llama inference..."
        else:
            return "🚀 Ready for live Llama inference"
    
    # Main response handler
    def handle_response(case_name, budget_level, custom_prompt):
        return generate_response(case_name, budget_level, custom_prompt)
    
    # Main animation handler
    def handle_animation(case_name, budget_level, custom_prompt):
        for partial_text in animate_response(case_name, budget_level, custom_prompt):
            yield partial_text
    
    # Event handlers
    inputs = [case_study_select, budget_radio, custom_prompt]
    outputs = [reasoning_trace, actual_tokens, final_answer]
    
    # Case study changes
    case_study_select.change(
        handle_animation, inputs, reasoning_trace
    )
    case_study_select.change(
        lambda *args: handle_response(*args)[1:], inputs, [actual_tokens, final_answer]
    )
    case_study_select.change(update_problem_display, case_study_select, problem_display)
    case_study_select.change(
        lambda case_name, budget_level, custom_prompt: 
        update_status(custom_prompt),
        inputs, status_display
    )
    
    # Budget changes
    budget_radio.change(
        handle_animation, inputs, reasoning_trace
    )
    budget_radio.change(
        lambda *args: handle_response(*args)[1:], inputs, [actual_tokens, final_answer]
    )
    budget_radio.change(
        lambda case_name, budget_level, custom_prompt: 
        update_status(custom_prompt),
        inputs, status_display
    )
    
    # Custom prompt changes
    custom_prompt.change(
        handle_animation, inputs, reasoning_trace
    )
    custom_prompt.change(
        lambda *args: handle_response(*args)[1:], inputs, [actual_tokens, final_answer]
    )
    custom_prompt.change(
        lambda case_name, budget_level, custom_prompt: 
        update_status(custom_prompt),
        inputs, status_display
    )
    
    # Initial load
    demo.load(
        handle_animation, inputs, reasoning_trace
    )
    demo.load(
        lambda *args: handle_response(*args)[1:], inputs, [actual_tokens, final_answer]
    )
    demo.load(update_problem_display, case_study_select, problem_display)
    demo.load(
        lambda case_name, budget_level, custom_prompt: 
        update_status(custom_prompt),
        inputs, status_display
    )

if __name__ == "__main__":
    demo.launch(share=False, show_error=True) 