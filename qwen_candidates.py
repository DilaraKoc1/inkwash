"""Qwen2.5 numbers from blog part 1: token ids, vocabulary size, top candidates and eight cells.

Needs torch, transformers and a GPU. The first run downloads the model (about 3 GB).
The percentages depend on the hardware: on a CPU they come out differently.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from prf import keyed_uniform

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"


if __name__ == "__main__":
    tokenizer = AutoTokenizer.from_pretrained(MODEL)

    # 1. How the tokenizer splits a sentence
    sentence = "The cat sat on the mat."
    for token_id in tokenizer.encode(sentence):
        print(f"{token_id:<6} {tokenizer.decode(token_id)!r}")
    print()

    # 2. Real tokens versus scores the model gives out
    model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16).to("cuda")
    print(f"real tokens: {len(tokenizer):,}")
    print(f"scores:      {model.config.vocab_size:,}")
    print()

    # 3. Top candidates after a prompt, plain text without chat template, temperature 1
    prompt = "The weather today is very"
    input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to("cuda")
    with torch.no_grad():
        scores = model(input_ids).logits[0, -1].float()
    probs = torch.softmax(scores, dim=-1)
    top_probs, top_ids = probs.topk(6)
    print(f"after {prompt!r}:")
    for prob, token_id in zip(top_probs, top_ids):
        print(f"{tokenizer.decode(token_id)!r:<10} {prob.item():6.1%}")
    print()

    # 4. Eight cells of the green-list table
    key = "secret"
    words = [" mat", " couch", " rug", " floor"]
    word_ids = [tokenizer.encode(word)[0] for word in words]
    print(" " * 16 + "".join(f"{word!r:>10}" for word in words))
    for prev_word in [" the", " cat"]:
        prev_id = tokenizer.encode(prev_word)[0]
        cells = "".join(f"{keyed_uniform(key, prev_id, word_id):>10.3f}" for word_id in word_ids)
        print(f"after {prev_word!r:<10}{cells}")
