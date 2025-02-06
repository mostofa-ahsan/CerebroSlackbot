import os
from rich import print
from mlx_lm import load, generate

# Global constants
FALCON_PATH = "/Users/ahsamo6/.cache/huggingface/hub/models--mlx-community--Falcon3-7B-Instruct-8bit/snapshots/4079269959b30471b3b4e7d668d5e598afebb55e"
# FALCON_PATH = os.environ['FALCON_PATH']
# PHI35_4_PATH = os.environ['PHI35_4_PATH']
# PHI35_8_PATH = os.environ['PHI35_8_PATH']

MAX_TOKENS = 2046
TEMPERATURE = 0.7

# Initialize

model, tokenizer = load(FALCON_PATH)

user_query = "What is the primary hex color code for the Verizon company logo?"
context = ("You are a virtual design assistant working for the Verizon company. "
           "Please answer the following questions about the brand design style guide. {}")


# TODO: use phi-3.5 and inference example.. need token max etc. temp
# PHI35_8_PATH

def call_llm(prompt: str) -> str:

    # prompt = mega_prompt.format(question=user_query, context=context)
    # print(f'[blue]prompt = [yellow]"{prompt}"')

    if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template is not None:
        messages = [{"role": "user", "content": prompt}]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

    response = generate(model,
                        tokenizer,
                        prompt=prompt,
                        verbose=True,
                        max_tokens=MAX_TOKENS,)
                        # temp=TEMPERATURE)

    print(f'[blue]response = [yellow][bold]{response}')
    return response
