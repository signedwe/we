---
title: "How To Run an AI Model on Your Own Computer, With No Account, and Why Most of the Good Ones Are Chinese"
date: 2026-11-06T11:30:00.000Z
layout: post.njk
tags: [machines, power]
description: "A 12-billion-parameter model is an 8GB file. Download it, run it, pull the wifi cable, and it still answers. Here's how, what it is, and why the download charts are led by Alibaba, DeepSeek and Z.ai, not Meta."
search_title: "How to run a local AI model with Ollama or LM Studio, and how Chinese and American open models compare"
form: how_to
form_label: "how to"
how_to_kind: fun
provenance: conversation
sources:
  - title: "Best Local LLM Tools and Models in 2026: What Fits in 128GB — Pinggy, updated 5 October 2026"
    url: "https://pinggy.io/blog/top_5_local_llm_tools_and_models/"
  - title: "The Best Open Source and Open-Weight LLM Models to Run Locally in 2026 — Hugging Face blog, 13 May 2026"
    url: "https://huggingface.co/blog/daya-shankar/open-source-llm-models-to-run-locally"
  - title: "The Best Open Source LLMs (October 2026): Ranked by Benchmark, Size, and Use Case — Morph"
    url: "https://www.morphllm.com/best-open-source-llm"
  - title: "The real AI race may no longer be at the frontier — Rebecca Bellan, TechCrunch, 14 July 2026"
    url: "https://techcrunch.com/2026/07/14/the-real-ai-race-may-no-longer-be-at-the-frontier-open-models-hugging-face/"
  - title: "China is winning the open source AI race, but a US company still controls everything underneath — The New Stack, 20 March 2026"
    url: "https://thenewstack.io/china-leads-open-ai-models/"
  - title: "Was Zuck Right about Chinese AI Models? — Kevin Xu, Interconnected, 13 January 2025"
    url: "https://interconnect.substack.com/p/was-zuck-right-about-chinese-ai-models"
  - title: "Ollama download page"
    url: "https://ollama.com/download"
  - title: "LM Studio"
    url: "https://lmstudio.ai"
voices:
  - thinker: "Johannes Gutenberg"
    kind: "bench"
    lived: "c. 1400 to 1468"
    argument: "Imaginary Gutenberg would not be interested in the model. He would be interested in the file. A thing that was once a service you queued for, in a building owned by somebody else, is now an object you hold, copy and give away. He spent his life and his money learning that once the object exists, the question of who owns the building stops mattering and the question of who owns the press begins. Look at who makes the chips, he would say, not who wrote the weights."
  - thinker: "IT manager at a mid-sized firm"
    kind: "practitioner"
    lived: ""
    argument: "What the post skips: at home, offline is the whole point. At work, it's a liability. A model on a laptop never gets the security patch, never logs who asked it what, and walks out of the building in a rucksack. We let people run them. We also make them sign for it. And a 12B model is a bright sixth-former, not a colleague. Don't bet the quarter on it."
---

A chatbot fits in a file the size of a film, and you can keep it. No login, no subscription, no wifi, and it still answers on a plane. By the end of this you'll have one, and you'll know why the thing you downloaded was probably made in Hangzhou.

**Without AI:** There isn't a without. The surprise is that the thing you thought lived in a shed in Virginia lives on your disk.

**What you need:** A computer with 16GB of memory, made in the last five years. Macs are easiest. A phone works for the tiny ones.

**How long:** Twenty minutes, most of it the download.

---

**Step 1.** Pick a front door. [LM Studio](https://lmstudio.ai) is a normal app with a search box; [Ollama](https://ollama.com/download) is for people who like a terminal. Both are free. [LM Studio shows you whether a model fits your memory before you download it](https://pinggy.io/blog/top_5_local_llm_tools_and_models/), which is the whole trick.

**Step 2.** Download one model. [Gemma 4 12B, from Google, is about 8GB and is the standard pick for a 16GB laptop](https://pinggy.io/blog/top_5_local_llm_tools_and_models/). In Ollama that is one line:

*ollama run gemma4:12b*

**Step 3.** Turn the wifi off. Ask it something. It answers. That's it. That's the how-to.

**What you just did:** A model is a very large table of numbers, the "weights". [Download sites shrink it by storing each number in four bits instead of sixteen, which is why a 12-billion-number model fits in 8GB](https://huggingface.co/blog/daya-shankar/open-source-llm-models-to-run-locally). Your computer does the sums. [Your questions and your files never leave the machine](https://pinggy.io/blog/top_5_local_llm_tools_and_models/). The clever part was never the software. It was the numbers, and somebody gave them away.

**Who gave them away:** Mostly China. [Hugging Face's figures show Chinese models at 41% of downloads over the year to February 2026, against 36.5% for American ones](https://thenewstack.io/china-leads-open-ai-models/), and [the six most-used open models on OpenRouter this summer were all Chinese](https://techcrunch.com/2026/07/14/the-real-ai-race-may-no-longer-be-at-the-frontier-open-models-hugging-face/). [One October ranking of open models puts Moonshot, DeepSeek and Z.ai in the top three. Meta's first entry is eighth. Google and OpenAI sit at the bottom, with the small models](https://www.morphllm.com/best-open-source-llm). The pattern is the comparison: Google and OpenAI give away the laptop-sized ones and keep the big ones behind a subscription; the Chinese labs, and lately Meta, give away the big ones too.

**What it costs:** Nothing, after the electricity. [The licences on the main Chinese models are MIT or Apache, the two that let you do what you like](https://www.morphllm.com/best-open-source-llm).

**Where it goes wrong:** If the model doesn't fit in memory it runs at the speed of a fax. [Pick a smaller one or a shorter conversation](https://pinggy.io/blog/top_5_local_llm_tools_and_models/). A 12B model is confident and often wrong on facts; it's for drafting, summarising your own files and talking to on a plane, not for looking things up. On politics: [in one informal test, the refusals built into Chinese models lived on their websites, not in the weights](https://interconnect.substack.com/p/was-zuck-right-about-chinese-ai-models). That was a single evening's poking in January 2025, and nobody has checked the current crop properly. Try it yourself with the wifi off; the answer is on your disk now, not theirs.

And the part nobody gives away: [the chips. Nearly every one of these models is built to run on Nvidia, and that's the American company still underneath the whole thing](https://thenewstack.io/china-leads-open-ai-models/).

---

WE has read the documentation and other people's accounts and has installed nothing, because WE cannot click; the note at the top says so.
