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

To check a text, the detector uses the key to recompute the green lists and counts how many tokens are green. For a writer who doesn't know the key, every token is like a coin that lands on green with a chance of 0.25. A watermarked text lands on green far more often.

The detector turns the count into a z-score. For n scored tokens:

```text
expected = n × 0.25                  green tokens chance alone would give
spread   = √(n × 0.25 × 0.75)        how far the count typically lands from that
z        = (green − expected) / spread
```

z says how many spreads the count sits above what chance would give. Texts written without the key land between −2 and 2 about 95% of the time, and above 4 only about 3 times in 100,000. z = 4 is the usual threshold.

Without the key, the green lists look like noise. Only the key holder can check for the watermark.

In my first test, I simulated texts of 200 tokens, which gives 199 scored pairs. So expected = 199 × 0.25 = 49.75 and spread = √(199 × 0.25 × 0.75) ≈ 6.11:

```text
                                    green   z
random tokens                          50   (50 − 49.75) / 6.11  =  0.04
only green tokens                     199   (199 − 49.75) / 6.11 = 24.4
only green tokens, wrong key           52   (52 − 49.75) / 6.11  =  0.37
```

The [blog post](https://www.dilarakoc.com/blog/ai-watermark-part-1/) walks through every step, including how the key turns into a number between 0 and 1.

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