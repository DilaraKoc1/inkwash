# inkwash

A reproducible lab that measures how robust LLM text watermarks are, and what defenders can actually rely on.

## Why

Since August 2026, the EU AI Act (Art. 50) requires AI providers to mark the content their systems generate. Google and Anthropic now embed statistical watermarks in generated text. This creates a new expectation: "we can tell whether a text was written by an AI."

People will start relying on that. Companies want to flag AI-written phishing mails and fake job applications. Platforms want to trace disinformation. Compliance teams need evidence.

Once people rely on a watermark, attackers have a reason to remove it or to fake it. This project asks three questions:

- How easily can a text watermark be removed, and what does it cost the attacker?
- Can a watermark be forged onto text that no AI wrote?
- When is a watermark valid evidence, and when is it not?

## How it works

An LLM writes one token at a time. At each step it gives every token in its vocabulary a score and then picks one at random, weighted by those scores.

The watermark changes that pick. A secret key and the previous token decide which 25% of the vocabulary counts as "green" for this step. The generator gives green tokens a small bonus. When several words fit equally well, it tends to choose a green one. The text still reads normally.

To check a text, the detector uses the key to recompute the green lists and counts how many tokens are green. For a writer who doesn't know the key, every token is like a coin that lands on green with a chance of 0.25. A watermarked text lands on green far more often.

The detector turns the count into a z-score. For n scored pairs (previous token, token):

```text
expected = n × 0.25                  green tokens chance alone would give
spread   = √(n × 0.25 × 0.75)        how far the count typically lands from that
z        = (green − expected) / spread
```

z says how many spreads the count sits above what chance would give. Texts written without the key land between −2 and 2 about 95% of the time, and above 4 only about 3 times in 100,000. z = 4 is the usual threshold.

Without the key, the green lists look like noise. Only the key holder can check for the watermark.

The scheme follows Kirchenbauer et al., [A Watermark for Large Language Models](https://arxiv.org/abs/2301.10226) (2023).

## Results so far

### Detector on simulated texts

I simulated texts of 200 tokens, which gives 199 scored pairs. So expected = 199 × 0.25 = 49.75 and spread = √(199 × 0.25 × 0.75) ≈ 6.11:

```text
                                    green   z
random tokens                          50   (50 − 49.75) / 6.11  =  0.04
only green tokens                     199   (199 − 49.75) / 6.11 = 24.4
only green tokens, wrong key           52   (52 − 49.75) / 6.11  =  0.37
```

The [blog post](https://www.dilarakoc.com/blog/ai-watermark-part-1/) explains each step, including how the key turns into a number between 0 and 1.

### Soft watermark on a toy model

A real model cannot pick only green tokens, so the generator adds a bonus `delta` to the scores of green tokens instead. Red tokens stay possible, just less likely. Adding `delta` to a score multiplies that token's weight by e^delta, so `delta = 2` makes a green token about 7.4 times as likely as before.

To see how strong the watermark gets, `experiment.py` uses a toy model that draws random scores for a vocabulary of 1,000 tokens. Its `sharpness` sets how many tokens are real options at each step: at 0.5 almost every token is about equally likely, at 5.0 a handful of tokens take most of the probability. That stands in for the difference between an open sentence and one with a single right answer.

One text of 200 tokens per setting:

```text
sharpness  delta   green     z
  0.5       0.0     25 %    0.0
  0.5       1.0     50 %    8.1
  0.5       2.0     70 %   14.8
  0.5       4.0     96 %   23.3
  2.0       0.0     21 %   -1.4
  2.0       1.0     54 %    9.4
  2.0       2.0     65 %   13.1
  2.0       4.0     93 %   22.1
  5.0       0.0     25 %    0.0
  5.0       1.0     36 %    3.6
  5.0       2.0     55 %    9.7
  5.0       4.0     81 %   18.2
```

Without a bonus, the share stays at the 25% chance gives. A larger bonus gives more green, but even at `delta = 4` some red tokens get through. When the model has few real options (sharpness 5.0) and the bonus is small, the watermark stays below z = 4 on 200 tokens, although every token was generated with it.

Each row is a single text, so the numbers carry noise. The row for sharpness 2.0 and delta 1.0 scores higher than the one for 0.5, which a single run can do.

## Status

Work in progress. I build this step by step and write about each step on my blog.

**Done**
- Keyed pseudo-random function
- Green-list detector with z-score
- Soft watermark: green tokens get a bonus instead of being forced
- Toy experiment on how the bonus and the model's certainty change the signal

**Next**
- Repeat the toy measurements over many texts per setting
- Watermark generation with a real LLM
- Count each (previous token, token) pair only once, so repetitive text cannot look watermarked
- Attacks: unicode tricks, word edits, paraphrasing
- Comparison with SynthID-Text
- Forging watermarks (spoofing)
- Recommendations for defenders

## Quickstart

You need Python 3.11 or newer and numpy.

```bash
git clone https://github.com/DilaraKoc1/inkwash.git
cd inkwash
pip install numpy
python prf.py           # checks that the random numbers behave as required
python green_list.py    # runs the detector on simulated texts
python experiment.py    # measures how the bonus and the model's certainty change the signal
```

`experiment.py` takes about half a minute, because it computes a SHA-256 hash for every token of the vocabulary at every step.

## Project structure

| File | Purpose |
|---|---|
| `prf.py` | Keyed pseudo-random function: turns (key, previous token, token) into a number in [0, 1) |
| `green_list.py` | Colour rule, bonus for green tokens, detector with z-score, and the colour of each token |
| `experiment.py` | Toy model that measures how the bonus and the model's certainty change the watermark |

## Responsible use

This is defensive research. All experiments target my own implementation and open-source reference implementations, not production systems. The goal is to show defenders where the limits are, not to provide a tool for removing watermarks.

## Blog

The full write-up, step by step: [dilarakoc.com](https://dilarakoc.com)

## License

MIT