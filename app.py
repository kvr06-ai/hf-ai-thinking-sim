
# app.py - Main Gradio app for Budget-Aware LLM Reasoning Demo

# This file will be populated in later phases
import gradio as gr
import time
import asyncio
from case_studies import CASE_STUDIES

def simulate_typing(text, speed=0.03):
    """Simulate typing effect by yielding partial text"""
    words = text.split()
    current_text = ""
    for word in words:
        current_text += word + " "
        yield current_text.strip()
        time.sleep(speed)

def update_display(case_name, budget_level, custom_prompt):
    if custom_prompt.strip():
        return "🔄 Custom prompt processing not yet implemented.", "N/A", "N/A"
    
    if not case_name:
        return "", "", ""
    
    selected_case = CASE_STUDIES.get(case_name, {})
    if not selected_case:
        return "❌ Case study not found.", "N/A", "N/A"
    
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
    """Handle animated typing effect for reasoning trace"""
    if custom_prompt.strip():
        return "🔄 Custom prompt processing not yet implemented."
    
    if not case_name:
        return ""
    
    selected_case = CASE_STUDIES.get(case_name, {})
    if not selected_case:
        return "❌ Case study not found."
    
    budget_keys = list(selected_case.get('budgets', {}).keys())
    if len(budget_keys) < 3:
        return "❌ Invalid case study data."
    
    budget_mapping = {'Low': budget_keys[0],
                      'Medium': budget_keys[1],
                      'High': budget_keys[2]}
    selected_budget = budget_mapping.get(budget_level)
    budget_data = selected_case['budgets'][selected_budget]
    
    reasoning_trace = budget_data['response']
    
    # Simulate typing effect
    for partial_text in simulate_typing(reasoning_trace):
        yield partial_text

# Custom CSS for Homebrew-style theme
homebrew_css = """
/* Homebrew-inspired theme with developer aesthetics */
.gradio-container {
    font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace !important;
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%) !important;
    color: #c9d1d9 !important;
}

.prose h1, .prose h2, .prose h3 {
    color: #58a6ff !important;
    font-weight: 600 !important;
}

.prose p, .prose li {
    color: #c9d1d9 !important;
    line-height: 1.6 !important;
}

.prose a {
    color: #79c0ff !important;
    text-decoration: none !important;
}

.prose a:hover {
    color: #58a6ff !important;
    text-decoration: underline !important;
}

.prose strong {
    color: #f0f6fc !important;
}

.prose em {
    color: #7c3aed !important;
}

/* Input styling */
.gr-textbox, .gr-dropdown, .gr-radio {
    background: #21262d !important;
    border: 1px solid #30363d !important;
    color: #c9d1d9 !important;
    border-radius: 6px !important;
}

.gr-textbox:focus, .gr-dropdown:focus {
    border-color: #58a6ff !important;
    box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.1) !important;
}

/* Button styling */
.gr-button {
    background: #238636 !important;
    border: 1px solid #2ea043 !important;
    color: #fff !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}

.gr-button:hover {
    background: #2ea043 !important;
    transform: translateY(-1px) !important;
}

/* Panel styling */
.gr-panel {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
}

/* Labels */
.gr-label {
    color: #f0f6fc !important;
    font-weight: 500 !important;
    margin-bottom: 8px !important;
}

/* Accordion/Collapsible styling */
details {
    background: #0d1117 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    margin-bottom: 16px !important;
    padding: 16px !important;
}

details summary {
    color: #58a6ff !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    padding: 8px 0 !important;
    font-size: 1.1em !important;
}

details summary:hover {
    color: #79c0ff !important;
}

details[open] summary {
    border-bottom: 1px solid #30363d !important;
    margin-bottom: 16px !important;
    padding-bottom: 16px !important;
}

/* Reasoning trace special styling */
.reasoning-trace {
    background: #0d1117 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    padding: 16px !important;
    font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace !important;
    line-height: 1.5 !important;
    white-space: pre-wrap !important;
}

/* Metrics styling */
.metrics {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 6px !important;
    padding: 12px !important;
    color: #79c0ff !important;
    font-weight: 500 !important;
}

/* Title styling */
.app-title {
    text-align: center !important;
    color: #58a6ff !important;
    font-size: 2.5em !important;
    font-weight: 700 !important;
    margin-bottom: 8px !important;
    text-shadow: 0 0 20px rgba(88, 166, 255, 0.3) !important;
}

.app-subtitle {
    text-align: center !important;
    color: #8b949e !important;
    font-size: 1.1em !important;
    margin-bottom: 24px !important;
}

/* Animation for typing effect */
.typing::after {
    content: '|' !important;
    animation: blink 1s infinite !important;
}

@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
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
    
    # Event handlers
    inputs = [case_study_select, budget_radio, custom_prompt]
    outputs = [reasoning_trace, actual_tokens, final_answer]
    
    case_study_select.change(update_display, inputs, outputs)
    case_study_select.change(update_problem_display, case_study_select, problem_display)
    budget_radio.change(animate_reasoning, inputs, reasoning_trace)
    budget_radio.change(lambda *args: update_display(*args)[1:], inputs, [actual_tokens, final_answer])
    custom_prompt.change(update_display, inputs, outputs)
    
    # Initial load
    demo.load(update_display, inputs, outputs)
    demo.load(update_problem_display, case_study_select, problem_display)

if __name__ == "__main__":
    demo.launch(share=False, show_error=True) 