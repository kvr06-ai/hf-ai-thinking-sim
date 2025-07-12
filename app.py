
# app.py - Main Gradio app for Budget-Aware LLM Reasoning Demo

# This file will be populated in later phases
import gradio as gr
import time
import asyncio
import tiktoken
import os
import requests
from transformers import pipeline, AutoTokenizer
from case_studies import CASE_STUDIES

# Configuration
BUDGET_MAPPING = {
    'Low': 50,
    'Medium': 110, 
    'High': 200
}

# Initialize tokenizer for counting tokens
try:
    tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
except:
    # Fallback tokenizer
    tokenizer = tiktoken.get_encoding("cl100k_base")

# Initialize local model pipeline (fallback option)
try:
    # Use a smaller model for demo purposes
    local_model = pipeline("text-generation", model="microsoft/DialoGPT-medium", 
                          tokenizer="microsoft/DialoGPT-medium", device=-1)
    local_tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
except Exception as e:
    print(f"Local model not available: {e}")
    local_model = None
    local_tokenizer = None

def count_tokens(text):
    """Count tokens in text using tiktoken"""
    try:
        return len(tokenizer.encode(text))
    except:
        # Fallback: rough estimation
        return len(text.split()) * 1.3

def simulate_typing(text, speed=0.03):
    """Simulate typing effect by yielding partial text"""
    words = text.split()
    current_text = ""
    for word in words:
        current_text += word + " "
        yield current_text.strip()
        time.sleep(speed)

def create_budget_prompt(original_prompt, budget_tokens, case_type="general"):
    """Create a prompt with budget constraints"""
    if case_type == "agentic":
        # For agentic cases like Capital City Finder
        budget_prompt = f"""You are an AI assistant that uses a structured thinking process. You have a thinking budget of {budget_tokens} tokens for your response.

Use this format:
Thought: [your reasoning]
Action: [action you would take, like Search('query')]  
Observation: [simulated result]
Final Answer: [your final answer]

Keep your total response under {budget_tokens} tokens. Be concise but thorough.

Problem: {original_prompt}"""
    else:
        # For general cases
        budget_prompt = f"""You have a thinking budget of {budget_tokens} tokens for your response. Please solve this problem step by step, but keep your total response under {budget_tokens} tokens.

Problem: {original_prompt}"""
    
    return budget_prompt

def query_huggingface_api(prompt, max_tokens=200):
    """Query Hugging Face Inference API"""
    try:
        # This would use HF_TOKEN environment variable
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            return None, "No HF token available"
        
        headers = {"Authorization": f"Bearer {hf_token}"}
        
        # Using a free model for demo
        api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.7,
                "do_sample": True
            }
        }
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get("generated_text", "")
                # Clean up the response
                if generated_text.startswith(prompt):
                    generated_text = generated_text[len(prompt):].strip()
                return generated_text, None
            else:
                return None, "Invalid response format"
        else:
            return None, f"API error: {response.status_code}"
            
    except Exception as e:
        return None, f"API request failed: {str(e)}"

def query_local_model(prompt, max_tokens=200):
    """Query local model as fallback"""
    try:
        if local_model is None:
            return None, "Local model not available"
        
        # Generate response
        response = local_model(prompt, max_length=len(prompt.split()) + max_tokens, 
                              num_return_sequences=1, temperature=0.7)
        
        if response and len(response) > 0:
            generated_text = response[0]["generated_text"]
            # Clean up the response
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()
            return generated_text, None
        else:
            return None, "No response generated"
            
    except Exception as e:
        return None, f"Local model error: {str(e)}"

def generate_dynamic_response(prompt, budget_level, case_name):
    """Generate response using LLM with budget constraints"""
    budget_tokens = BUDGET_MAPPING[budget_level]
    
    # Determine case type for appropriate prompting
    case_type = "agentic" if "Capital City Finder" in case_name else "general"
    
    # Create budget-constrained prompt
    budget_prompt = create_budget_prompt(prompt, budget_tokens, case_type)
    
    # Try HF API first, then local model, then fallback to static
    response_text, error = query_huggingface_api(budget_prompt, budget_tokens)
    
    if response_text is None:
        # Try local model
        response_text, error = query_local_model(budget_prompt, budget_tokens)
        
        if response_text is None:
            # Fallback to static response
            return get_static_fallback(case_name, budget_level)
    
    # Count actual tokens used
    actual_tokens = count_tokens(response_text)
    
    # Extract final answer (simple heuristic)
    final_answer = extract_final_answer(response_text)
    
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

def get_static_fallback(case_name, budget_level):
    """Get static response as fallback"""
    if case_name in CASE_STUDIES:
        budget_keys = list(CASE_STUDIES[case_name]['budgets'].keys())
        budget_mapping = {'Low': budget_keys[0], 'Medium': budget_keys[1], 'High': budget_keys[2]}
        selected_budget = budget_mapping[budget_level]
        budget_data = CASE_STUDIES[case_name]['budgets'][selected_budget]
        
        return (
            f"[STATIC FALLBACK] {budget_data['response']}", 
            budget_data['tokens'], 
            budget_data['answer']
        )
    
    return "Fallback data not available", 0, "N/A"

def update_display(case_name, budget_level, custom_prompt):
    """Update display with either dynamic LLM response or static fallback"""
    if custom_prompt.strip():
        # Handle custom prompts with dynamic LLM
        try:
            response_text, actual_tokens, final_answer = generate_dynamic_response(
                custom_prompt.strip(), budget_level, "Custom"
            )
            budget_tokens = BUDGET_MAPPING[budget_level]
            return response_text, f"🔢 {actual_tokens} / {budget_tokens} tokens", f"✅ {final_answer}"
        except Exception as e:
            return f"❌ Error processing custom prompt: {str(e)}", "N/A", "N/A"
    
    if not case_name:
        return "", "", ""
    
    selected_case = CASE_STUDIES.get(case_name, {})
    if not selected_case:
        return "❌ Case study not found.", "N/A", "N/A"
    
    # For pre-defined case studies, use static responses for consistency
    # But add option to use dynamic inference
    budget_keys = list(selected_case.get('budgets', {}).keys())
    if len(budget_keys) < 3:
        return "❌ Invalid case study data.", "N/A", "N/A"
    
    budget_mapping = {'Low': budget_keys[0],
                      'Medium': budget_keys[1],
                      'High': budget_keys[2]}
    selected_budget = budget_mapping.get(budget_level)
    budget_data = selected_case['budgets'][selected_budget]
    
    reasoning_trace = budget_data['response']
    actual_tokens = f"🔢 {budget_data['tokens']} / {selected_budget} tokens"
    final_answer = f"✅ {budget_data['answer']}"
    
    return reasoning_trace, actual_tokens, final_answer

def animate_reasoning(case_name, budget_level, custom_prompt):
    """Handle animated typing effect for reasoning trace with dynamic LLM support"""
    if custom_prompt.strip():
        # For custom prompts, use dynamic LLM with typing animation
        try:
            response_text, actual_tokens, final_answer = generate_dynamic_response(
                custom_prompt.strip(), budget_level, "Custom"
            )
            # Simulate typing effect for dynamic response
            for partial_text in simulate_typing(response_text):
                yield partial_text
        except Exception as e:
            yield f"❌ Error processing custom prompt: {str(e)}"
        return
    
    if not case_name:
        yield ""
        return
    
    selected_case = CASE_STUDIES.get(case_name, {})
    if not selected_case:
        yield "❌ Case study not found."
        return
    
    budget_keys = list(selected_case.get('budgets', {}).keys())
    if len(budget_keys) < 3:
        yield "❌ Invalid case study data."
        return
    
    budget_mapping = {'Low': budget_keys[0],
                      'Medium': budget_keys[1],
                      'High': budget_keys[2]}
    selected_budget = budget_mapping.get(budget_level)
    budget_data = selected_case['budgets'][selected_budget]
    
    reasoning_trace = budget_data['response']
    
    # Simulate typing effect for static response
    for partial_text in simulate_typing(reasoning_trace):
        yield partial_text

def generate_live_response(case_name, budget_level, custom_prompt):
    """Generate live LLM response for dynamic inference mode"""
    if custom_prompt.strip():
        prompt = custom_prompt.strip()
    elif case_name and case_name in CASE_STUDIES:
        prompt = CASE_STUDIES[case_name]['prompt']
    else:
        return "❌ No valid prompt available.", "N/A", "N/A"
    
    try:
        response_text, actual_tokens, final_answer = generate_dynamic_response(
            prompt, budget_level, case_name
        )
        budget_tokens = BUDGET_MAPPING[budget_level]
        
        # Add indicator for live vs static
        if "[STATIC FALLBACK]" in response_text:
            token_display = f"🔢 {actual_tokens} / {budget_tokens} tokens (Static)"
        else:
            token_display = f"🔢 {actual_tokens} / {budget_tokens} tokens (Live)"
        
        return response_text, token_display, f"✅ {final_answer}"
    
    except Exception as e:
        return f"❌ Error generating live response: {str(e)}", "N/A", "N/A"

def animate_live_response(case_name, budget_level, custom_prompt):
    """Animate live LLM response with typing effect"""
    if custom_prompt.strip():
        prompt = custom_prompt.strip()
    elif case_name and case_name in CASE_STUDIES:
        prompt = CASE_STUDIES[case_name]['prompt']
    else:
        yield "❌ No valid prompt available."
        return
    
    try:
        response_text, actual_tokens, final_answer = generate_dynamic_response(
            prompt, budget_level, case_name
        )
        
        # Simulate typing effect for live response
        for partial_text in simulate_typing(response_text):
            yield partial_text
    
    except Exception as e:
        yield f"❌ Error generating live response: {str(e)}"

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
            <p>Imagine asking an AI (like ChatGPT) to solve a complex problem. If you give it more time and space to "think" through the steps, it can often produce a more detailed and accurate answer. This "thinking time" is measured in <strong>tokens</strong> (pieces of words).</p>
            
            <p>This simulator demonstrates that concept. It shows how the quality of an AI's reasoning changes when we give it a different <strong>"thinking budget."</strong></p>
            
            <p><strong>How to use:</strong></p>
            <ol>
                <li><strong>Select a Problem:</strong> Pick a problem for the AI to solve from the dropdown menu.</li>
                <li><strong>Choose a Thinking Level:</strong> Select a "Low," "Medium," or "High" thinking budget.</li>
                <li><strong>Observe the Results:</strong> You'll see the AI's step-by-step "thought process" and its final answer for the budget you selected.</li>
            </ol>
            
            <p>Play around with the levels to see how a bigger budget can change the AI's path to the answer!</p>
            
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
            
            # Dynamic inference toggle
            dynamic_mode = gr.Checkbox(
                label="🚀 Enable Dynamic LLM Inference", 
                value=False,
                info="Use live LLM calls instead of static responses"
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
    def update_status(dynamic_mode_enabled, custom_prompt):
        if custom_prompt.strip():
            if dynamic_mode_enabled:
                return "🚀 Dynamic mode: Processing custom prompt..."
            else:
                return "⚡ Static mode: Processing custom prompt..."
        elif dynamic_mode_enabled:
            return "🚀 Dynamic mode: Ready for live LLM inference"
        else:
            return "⚡ Static mode: Using pre-computed responses"
    
    # Main response handler
    def handle_response(case_name, budget_level, custom_prompt, dynamic_mode_enabled):
        if dynamic_mode_enabled:
            return generate_live_response(case_name, budget_level, custom_prompt)
        else:
            return update_display(case_name, budget_level, custom_prompt)
    
    # Main animation handler
    def handle_animation(case_name, budget_level, custom_prompt, dynamic_mode_enabled):
        if dynamic_mode_enabled:
            for partial_text in animate_live_response(case_name, budget_level, custom_prompt):
                yield partial_text
        else:
            for partial_text in animate_reasoning(case_name, budget_level, custom_prompt):
                yield partial_text
    
    # Event handlers with dynamic/static mode support
    inputs = [case_study_select, budget_radio, custom_prompt, dynamic_mode]
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
        lambda case_name, budget_level, custom_prompt, dynamic_mode_enabled: 
        update_status(dynamic_mode_enabled, custom_prompt),
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
        lambda case_name, budget_level, custom_prompt, dynamic_mode_enabled: 
        update_status(dynamic_mode_enabled, custom_prompt),
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
        lambda case_name, budget_level, custom_prompt, dynamic_mode_enabled: 
        update_status(dynamic_mode_enabled, custom_prompt),
        inputs, status_display
    )
    
    # Dynamic mode toggle
    dynamic_mode.change(
        handle_animation, inputs, reasoning_trace
    )
    dynamic_mode.change(
        lambda *args: handle_response(*args)[1:], inputs, [actual_tokens, final_answer]
    )
    dynamic_mode.change(
        lambda case_name, budget_level, custom_prompt, dynamic_mode_enabled: 
        update_status(dynamic_mode_enabled, custom_prompt),
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
        lambda case_name, budget_level, custom_prompt, dynamic_mode_enabled: 
        update_status(dynamic_mode_enabled, custom_prompt),
        inputs, status_display
    )

if __name__ == "__main__":
    demo.launch(share=False, show_error=True) 