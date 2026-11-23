# inkwash

A reproducible lab that measures how robust LLM text watermarks are, and what defenders can rely on.

## Why

Since August 2026, the EU AI Act (Art. 50) requires AI providers to mark the content their systems generate.
Systems already on the market before then have until December 2026. Google watermarks Gemini's text, and Anthropic
does the same for new Claude models. This creates a new expectation:
"we can tell whether a text was written by an AI."

People will start relying on that. Companies want to flag AI-written phishing mails and fake job applications.
Platforms want to trace disinformation. Compliance teams need evidence.

Once people rely on a watermark, attackers have a reason to remove it or to fake it. This project asks three questions:

- How easily can a text watermark be removed, and what does it cost the attacker?
- Can a watermark be forged onto text that no AI wrote?
- When is a watermark valid evidence, and when is it not?

## How it works

An LLM writes one token at a time. At each step it gives every token in its vocabulary a score and then picks one at
random, weighted by probabilities computed from those scores.

The watermark changes that pick. A secret key and the previous token decide which tokens count as "green" for this
step, about 25% of the vocabulary. The generator gives green tokens a small bonus. When several words fit equally
well, it tends to choose a green one. The goal is that the text still reads normally.

To check a text, the detector uses the key to recompute the green lists and counts how many tokens are green. For a
writer who doesn't know the key, every token is like a coin that lands on green with a chance of 0.25. A watermarked
text lands on green far more often.

The detector turns the count into a z-score. For n scored pairs (previous token, token):

```text
expected = n × 0.25                  green tokens chance alone would give
spread   = √(n × 0.25 × 0.75)        how far the count typically lands from that
z        = (green − expected) / spread
```

z says how many spreads the count sits above what chance would give. Longer texts written without the key land between
−2 and 2 about 95% of the time. A bell curve puts about 3 in 100,000 above 4. The real share is a little higher,
because with a chance of 0.25 the count leans to the right. For texts of 50 to 200 tokens, between about 5 and 15
in 100,000 land above 4, depending on the exact length. z = 4 is the usual threshold.

Without the key, the green lists look like noise. Only the key holder can check for the watermark.

The scheme follows Kirchenbauer et al., [A Watermark for Large Language Models](https://arxiv.org/abs/2301.10226) (2023).
One difference: their Algorithm 2 hashes the previous token, uses the hash to seed a random generator and splits the
vocabulary into a green list of exactly 25% and a red list. inkwash gives each candidate token its own colour with a
keyed function of (previous token, token), so a green list holds about 25%, a little more or less each time. This
colour rule is close to their Algorithm 3 in Section 5, with one token of context. The bonus for green tokens is the
one from Algorithm 2. For the detector it makes no difference, because without the key every token is green with a
chance of 0.25 either way.

I used Claude, an AI assistant by Anthropic, to summarise the paper for me and to support me in building this project
along the lines of their scheme.

## Results so far

### Detector on simulated texts

I simulated texts of 200 tokens, which gives 199 scored pairs. So expected = 199 × 0.25 = 49.75 and
spread = √(199 × 0.25 × 0.75) ≈ 6.11:

```text
                                    green   z
random tokens                          54   (54 − 49.75) / 6.11  =  0.70
only green tokens                     199   (199 − 49.75) / 6.11 = 24.4
only green tokens, wrong key           54   (54 − 49.75) / 6.11  =  0.70
```

That the first and last row match is chance. They are two different texts, and each count is like 199 coin flips. Two
such counts land on the same number about once in 20 tries.

The [blog post](https://www.dilarakoc.com/blog/ai-watermark-part-1/) explains each step, including how the key turns
into a number between 0 and 1.

### Soft watermark on a toy model

A real model cannot pick only green tokens, so the generator adds a bonus `delta` to the scores of green tokens instead.
Red tokens stay possible, just less likely. Adding `delta` to a score multiplies that token's weight by e^delta before
the probabilities are rescaled to add up to 1. At `delta = 2` that factor is about 7.4.

To see how strong the watermark gets, `experiment.py` uses a toy model that draws random scores for a vocabulary of
1,000 tokens. Its `sharpness` sets how many tokens are real options at each step: at 0.5 almost every token is about
equally likely, at 5.0 a handful of tokens take most of the probability. That stands in for the difference between an
open sentence and one with a single right answer.

20 texts of 200 tokens per setting. `z std` is how much z varies between the texts, `detected` is the share of texts
above z = 4:

```text
sharpness  delta  green  z mean  z std  detected
      0.5    0.0    25%     0.1    1.1        0%
      0.5    1.0    46%     6.9    1.2      100%
      0.5    2.0    71%    15.1    0.9      100%
      0.5    4.0    95%    22.7    0.4      100%
      2.0    0.0    25%     0.0    1.1        0%
      2.0    1.0    46%     6.9    1.4      100%
      2.0    2.0    70%    14.7    1.0      100%
      2.0    4.0    95%    22.8    0.5      100%
      5.0    0.0    26%     0.2    1.0        0%
      5.0    1.0    37%     3.9    1.1       40%
      5.0    2.0    52%     8.9    1.5      100%
      5.0    4.0    79%    17.5    1.0      100%
```

Without a bonus, the share stays at the 25% chance gives, and no text is flagged. With a bonus, the share of green
follows a simple formula as long as the model has enough options:

```text
green = 0.25 × e^delta / (0.25 × e^delta + 0.75)

delta = 1  →  48%     delta = 2  →  71%     delta = 4  →  95%
```

At sharpness 0.5 and 2.0 the measured shares are within two points of that formula. At sharpness 5.0 the model has too
few options for the bonus to reach it: 37% instead of 48% at `delta = 1`. There, the average z of 3.9 sits just below
the threshold, and with z varying by about 1 between texts, only 40% of the watermarked texts are detected. A detector
would report "no watermark" for more than half of them.

## Status

Work in progress. I build this step by step and write about each step on my blog.

**Done**
- Keyed pseudo-random function (HMAC-SHA256), with tests
- Green-list detector with z-score
- Soft watermark: green tokens get a bonus instead of being forced
- Toy experiment on how the bonus and the model's certainty change the signal, 20 texts per setting, with detection rate

**Next**
- Measure what the bonus costs: how often the model picks a different token than it would without the watermark
- Watermark generation with a real LLM
- Count each (previous token, token) pair only once, so repetitive text cannot look watermarked
- Attacks: unicode tricks, word edits, paraphrasing
- Comparison with SynthID-Text
- Forging watermarks (spoofing)
- Recommendations for defenders

## Quickstart

You need Python 3.10 or newer, numpy and pytest.

```bash
git clone https://github.com/DilaraKoc1/inkwash.git
cd inkwash
pip install numpy pytest
python -m pytest        # checks that the random numbers behave as required
python prf.py           # prints the steps for one number and the share of green tokens
python green_list.py    # runs the detector on simulated texts
python experiment.py    # measures how the bonus and the model's certainty change the signal
```

The tests, `prf.py` and `experiment.py` each take a few seconds. In the experiment, each green list is computed once per
previous token and then reused.

`qwen_candidates.py` reproduces the Qwen2.5 numbers from the blog post. It needs `torch`, `transformers` and a GPU, and
downloads about 3 GB on the first run. On a CPU the percentages come out differently.

## Project structure

| File | Purpose |
|---|---|
| `prf.py` | Keyed pseudo-random function: turns (key, previous token, token) into a number in [0, 1) with HMAC-SHA256 |
| `test_prf.py` | Tests for `prf.py`: same inputs give the same number, a different key or previous token gives a different one, and about 25% of tokens are green after each of ten previous tokens |
| `green_list.py` | Colour rule, bonus for green tokens, detector with z-score, and the colour of each token |
| `experiment.py` | Toy model that measures how the bonus and the model's certainty change the watermark |
| `qwen_candidates.py` | Qwen2.5 token ids, vocabulary size, top candidates after a prompt and the eight example cells from the blog post |

## Responsible use

This is defensive research. All experiments target my own implementation and open-source reference implementations, not
production systems. The goal is to show defenders where the limits are, not to provide a tool for removing watermarks.

## Blog

The full write-up, step by step:

- [Part 1: Building One](https://www.dilarakoc.com/blog/ai-watermark-part-1/)
- [Part 2: A Soft Watermark](https://www.dilarakoc.com/blog/ai-watermark-part-2/)

## License

MIT