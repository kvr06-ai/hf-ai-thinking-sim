---
title: Budget-Aware LLM Reasoning Demo
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: "4.31.0"
app_file: app.py
pinned: false
---

# Budget-Aware LLM Reasoning Demo

This is an interactive demo showcasing budget-guided LLM reasoning, inspired by the paper "Steering LLM Thinking with Budget Guidance" ([arXiv:2506.13752](https://arxiv.org/abs/2506.13752)).

The demo uses **Meta's Llama 3.1 8B Instruct** model for high-quality reasoning within token budgets.

## How it Works
This Gradio application sends prompts to the Hugging Face Inference API. It attempts to use a series of powerful LLMs, starting with `meta-llama/Llama-3.1-8B-Instruct`.

You can select from pre-defined case studies or enter your own custom prompt. The application will then show the model's reasoning process and the final answer, all while respecting the token budget you set.

## Configuration
To run this Space, you must set a secret for your Hugging Face token:
1.  Go to the **Settings** tab of this Space.
2.  Under **Secrets**, add a new secret.
3.  Set the **Name** to `HF_TOKEN`.
4.  Set the **Value** to your Hugging Face access token. You can get one from [your settings](https://huggingface.co/settings/tokens).
5.  **Important**: Ensure you have accepted the license for [Meta Llama 3.1](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct) to use it for inference. 