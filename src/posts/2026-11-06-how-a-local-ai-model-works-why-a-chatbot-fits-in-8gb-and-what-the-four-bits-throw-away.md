---
title: "How a local AI model works: why a chatbot fits in 8GB, what the four bits throw away, and why your laptop's speed is a plumbing number"
date: 2026-11-06T12:30:00.000Z
layout: post.njk
tags: [machines, money, power]
description: "Twelve billion weights take 24GB at full precision and 8GB on your laptop. Here's what quantisation keeps, what it drops, why 4-bit is the floor, and why tokens per second is bandwidth divided by file size."
search_title: "How local LLMs work: quantization, GGUF, memory bandwidth and mixture of experts explained"
form: technical
form_label: "how it works"
provenance: conversation
sources:
  - title: "How Good Are Low-bit Quantized LLaMA3 Models? An Empirical Study — Huang, Ma, Qin et al., arXiv 2404.14047, April 2024"
    url: "https://arxiv.org/html/2404.14047v1"
  - title: "GGUF quantization guide — Toni Sagristà Sellés, March 2026, updated April 2026"
    url: "https://tonisagrista.com/blog/2026/quantization"
  - title: "Local LLM speed calculator — Martin Alderson, 24 April 2026"
    url: "https://martinalderson.com/posts/local-llm-speed-calculator/"
  - title: "Memory bandwidth — APX ML course, Model size and hardware"
    url: "https://apxml.com/courses/llm-model-sizes-hardware/chapter-3-model-size-hardware-connection/memory-bandwidth"
  - title: "Apple MacBook Air M4 13-inch specs — EveryMac"
    url: "https://everymac.com/systems/apple/macbook-air/specs/macbook-air-m4-10-core-cpu-10-core-gpu-13-2025-specs.html"
  - title: "Best Local LLM Tools and Models in 2026: What Fits in 128GB — Pinggy, updated 5 October 2026"
    url: "https://pinggy.io/blog/top_5_local_llm_tools_and_models/"
  - title: "The Best Open Source and Open-Weight LLM Models to Run Locally in 2026 — Hugging Face blog, 13 May 2026"
    url: "https://huggingface.co/blog/daya-shankar/open-source-llm-models-to-run-locally"
  - title: "The Best Open Source LLMs (October 2026) — Morph"
    url: "https://www.morphllm.com/best-open-source-llm"
voices:
  - thinker: "Claude Shannon"
    kind: "bench"
    lived: "1916 to 2001"
    argument: "Imaginary Shannon would say the post has rediscovered his subject. Every number in the model carries some information and some noise, and four bits is a bet that most of the noise sits in the bits you dropped. The bet holds at four and fails at two, which tells you roughly how much of each number was ever doing any work. He would want the curve, not the anecdote: bits on one axis, error on the other, and the knee is the thing worth knowing."
  - thinker: "Grace Hopper"
    kind: "bench"
    lived: "1906 to 1992"
    argument: "Imaginary Hopper carried a foot of wire to show what a nanosecond was. She would carry an 8GB file to show what a model is. Her point would be the one the post makes last: the thing that limits you is not the thinking, it's the distance the data has to travel to be thought about. She spent a career telling admirals that. The admirals now buy memory bandwidth."
  - thinker: "engineer who ships quantised models"
    kind: "practitioner"
    lived: ""
    argument: "What the post skips: 4-bit is the floor on average. On the specific thing you care about, maths, a rare language, long documents, it can be the cliff. We test every quant against the full model on our own tasks before we ship it, and about one time in five the small one fails something the big one passed. The perplexity number in the table won't tell you which. Only your own test will."
---

The chatbot on your laptop came from the same download chart as the big one, at a third of the size. Nobody told you what got left out.

Here's the arithmetic that lets a model run at home, and the three facts that fall out of it.

**Twelve billion dials, and the box they won't fit in**

A language model consists of its weights: billions of learned numbers that pick the next word. [Gemma 4 12B carries twelve billion of them](https://www.morphllm.com/best-open-source-llm). Training stores each one in sixteen bits, two bytes. Twelve billion times two bytes makes 24GB. Your laptop holds 16GB, and the laptop wants most of that for itself.

So each number has to shrink. [Quantisation stores every weight in fewer bits: eight, four, three, two](https://tonisagrista.com/blog/2026/quantization). At four bits a weight takes half a byte; twelve billion halves make 6GB, plus bookkeeping. [The 4-bit file for Gemma 4 12B weighs 7 to 8GB](https://pinggy.io/blog/top_5_local_llm_tools_and_models/). So a film-sized download holds a 24GB brain with twelve of every sixteen bits cut from each number.

**What four bits keeps**

Picture a weight as a dial that points anywhere between minus one and one. [Sixteen bits give the dial tens of thousands of positions; four bits give it sixteen](https://tonisagrista.com/blog/2026/quantization). How much of the model's behaviour ever lived in the fine positions?

Measured: surprisingly little, until suddenly all of it. [Huang and colleagues took Llama 3 8B and tested it at every bit-width](https://arxiv.org/html/2404.14047v1). At sixteen bits it scored 68.6 on a set of common-sense questions. At eight bits, 68.6. At four bits, 67.3 to 68.2 depending on the method. At three bits, 61.7 to 64.4. [At two bits it fell to 35 or 36, close to guessing](https://arxiv.org/html/2404.14047v1). The curve runs flat, then drops off a cliff, and the cliff sits between four bits and three.

Which explains why [the Hugging Face guide calls Q4 "the best starting point"](https://huggingface.co/blog/daya-shankar/open-source-llm-models-to-run-locally) and [the GGUF guide calls Q4_K_M "the most popular default"](https://tonisagrista.com/blog/2026/quantization). At four bits you've thrown away most of the file and almost none of the model.

**How the throwing-away gets done**

Not by rounding each number to the nearest of sixteen. That naive method, called RTN, [collapsed to a score of 40 at three bits, where the clever methods held 62 to 64](https://arxiv.org/html/2404.14047v1).

The clever methods work in blocks. [A block of weights shares one scale factor stored at full precision, and each weight gets stored as a four-bit fraction of it](https://tonisagrista.com/blog/2026/quantization). The "K" in Q4_K_M groups the blocks into super-blocks with scales of their own, so the scales get quantised too. [An importance matrix, built by running real text through the model first, tells the quantiser which weights carry the load and spends bits there](https://tonisagrista.com/blog/2026/quantization). [Q4_K_M lands at about 4.5 bits per weight](https://tonisagrista.com/blog/2026/quantization): four for the numbers, half a bit for the bookkeeping that keeps them honest.

So the 8GB download doesn't hold a worse model. It holds the same model under a lossy compression scheme, tested against the original and tuned until the gap stopped showing on the benchmarks. Whether the gap shows on your task, the practitioner below will tell you.

**Why the speed comes down to plumbing**

Here's the fact that catches people who assume AI runs on computing power. To write one word, the model reads every weight once. All 8GB. Then it writes the next word and reads all 8GB again. [Generation runs memory-bound: the processor spends most of its time waiting for weights to arrive, not calculating with them](https://apxml.com/courses/llm-model-sizes-hardware/chapter-3-model-size-hardware-connection/memory-bandwidth).

So the ceiling on words per second comes from [memory bandwidth divided by bytes read per word](https://martinalderson.com/posts/local-llm-speed-calculator/). [A MacBook Air M4 moves 120GB a second between memory and chip](https://everymac.com/systems/apple/macbook-air/specs/macbook-air-m4-10-core-cpu-10-core-gpu-13-2025-specs.html). The arithmetic: 120GB per second divided by 8GB per word gives 15 words a second, flat out. [Sustained bandwidth runs at 80 to 90% of peak](https://martinalderson.com/posts/local-llm-speed-calculator/), so call it 12 or 13 in practice. Reading speed. Halve the file to 4GB and you double the speed. Double it to 16GB and it stops fitting, [and a model that spills out of memory crawls](https://pinggy.io/blog/top_5_local_llm_tools_and_models/).

That's why quantisation buys speed as well as space. It's also why the spec that matters never appears in the advert: not the processor, not the GPU core count, but gigabytes per second between memory and chip. The 24GB model you couldn't fit was also the model you couldn't afford to read.

**Why a model forty times bigger fits too**

One more trick, and the labs in Hangzhou and Beijing lean on it hardest. A mixture-of-experts model splits its weights into specialist blocks and consults only a few per word. [DeepSeek V4.1 Flash holds 552 billion weights and reads 16 billion of them for each word it writes](https://www.morphllm.com/best-open-source-llm). Enormous on disk, light on the plumbing. [Only the active experts get read, so a huge model with weights spilling into ordinary RAM stays usable where a dense model of the same size would not](https://martinalderson.com/posts/local-llm-speed-calculator/). That's how a model that once needed a rack now runs on a Mac Studio.

**What this rearranges**

Three things follow.

First, the expensive part of a model never lived in the software. The value sits in the numbers, the numbers sit in a file, and files get copied. Everything the labs charge for by the month becomes, on your disk, a one-off download that doesn't expire.

Second, the labs no longer decide what you can run. The chip and memory makers who set bandwidth decide, and so do the quantisers, usually not the lab that trained the model, who choose which weights carry the load. [The importance matrix that shaped your 8GB file was calibrated on text somebody picked](https://tonisagrista.com/blog/2026/quantization). Nobody tells you which text.

Third, you can see the floor. Four bits holds, three wobbles, two fails. Twelve billion weights at four bits, on a laptop with 16GB, read back at a dozen words a second. Not a demo: a working assistant with no account, for the price of the electricity.

What to do with this: when you download, take the Q4_K_M, not the smaller one that looks like a bargain. Check the file size against your free memory, not your total. And when a laptop salesman starts on the processor, ask him for the bandwidth. He'll have to look it up.

The number they never showed you sets the speed.
