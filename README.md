# inkwash

A reproducible lab that measures how robust LLM text watermarks are, and what defenders can actually rely on.

## Why

Since August 2026, the EU AI Act (Art. 50) requires AI providers to mark the content their systems generate. Google and Anthropic now embed statistical watermarks in generated text. This creates a new expectation: "we can tell whether a text was written by an AI."

People will start relying on that. Companies want to flag AI-written phishing mails and fake job applications. Platforms want to trace disinformation. Compliance teams need evidence.

Every protection people rely on becomes a target. This project asks three questions:

- How easily can a text watermark be removed, and what does it cost the attacker?
- Can a watermark be forged onto text that no AI wrote?
- When is a watermark valid evidence, and when is it not?

## How it works

An LLM writes one token at a time. At each step it gives every token in its vocabulary a score and then picks one at random, weighted by those scores.

The watermark changes that pick. A secret key and the previous token decide which 25% of the vocabulary counts as "green" for this step. The generator gives green tokens a small bonus. When several words fit equally well, it tends to choose a green one. The text still reads normally.

To check a text, the detector uses the key to recompute the green lists and counts how many tokens are green. A writer who doesn't know the key lands on green about 25% of the time. A watermarked text lands there far more often. The z-score measures how far the count sits above 25%. Above z = 4, the chance of a human text getting there is about 3 in 100,000.

Without the key, the green lists look like noise. Only the key holder can check for the watermark.

In my first test, a simulated 200-token text built only from green tokens scored z = 24.4. Random tokens scored z = 0.04, and the same green text checked with the wrong key scored z = -0.29.

The scheme follows Kirchenbauer et al., [A Watermark for Large Language Models](https://arxiv.org/abs/2301.10226) (2023).

## Status

Work in progress. I build this step by step and write about each step on my blog.

**Done**
- Keyed pseudo-random function
- Green-list detector with z-score

**Next**
- Watermark generation with a real LLM
- Attacks: unicode tricks, word edits, paraphrasing
- Comparison with SynthID-Text
- Forging watermarks (spoofing)
- Recommendations for defenders

## Quickstart

```bash
git clone https://github.com/DilaraKoc1/inkwash.git
cd inkwash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install numpy
python green_list.py
```

## Project structure

| File | Purpose |
|---|---|
| `prf.py` | Keyed pseudo-random function: turns (key, previous token, token) into a number in [0, 1) |
| `green_list.py` | Decides which tokens are green and detects the watermark via z-score |

## Responsible use

This is defensive research. All experiments target my own implementation and open-source reference implementations, not production systems. The goal is to show defenders where the limits are, not to provide a tool for removing watermarks.

## Blog

The full write-up, step by step: [dilarakoc.com](https://dilarakoc.com)

## License

MIT