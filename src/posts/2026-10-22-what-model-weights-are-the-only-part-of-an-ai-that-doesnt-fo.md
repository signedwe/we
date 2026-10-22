---
title: "What model weights are: the only part of an AI that doesn't forget you"
date: 2026-10-22T00:13:06.452603+00:00
layout: post.njk
tags: [machines, ownership, money]
description: "The weights are the only durable part of an AI — frozen, owned by the lab, built from everyone's data. Every fine-tuning run you pay for improves an asset you don't own. By 2028 someone will win that "
search_title: "What are model weights in AI: how they work, what they store, and who owns them"
form: technical
form_label: "how it works"
sources:
  - title: "LM-Kit: What are Weights in Large Language Models?"
    url: "https://docs.lm-kit.com/lm-kit-net/guides/glossary/weights.html"
  - title: "Adding LLMs to the psycholinguistic norming toolbox — weights are static at inference"
    url: "https://arxiv.org/pdf/2509.14405"
  - title: "How do large language models get so large? — parameters as floating-point values"
    url: "https://www.tigrisdata.com/blog/chonky-models/"
  - title: "LLM VRAM Requirements 2026 — Llama 3.1 70B weight size"
    url: "https://www.spheron.network/blog/gpu-memory-requirements-llm/"
  - title: "Best GPU for LLM Inference 2026 — inference is memory-bandwidth-bound"
    url: "https://www.thundercompute.com/blog/best-gpu-for-llm"
  - title: "AI and Copyright Law 2025 — US Copyright Office on weights"
    url: "https://huggingface.co/blog/jonathanagustin/ai-copyright-analysis-2025"
  - title: "The Heart of the Matter — Copyright Office 2025 on weights as copies"
    url: "https://www.copyright.com/blog/the-heart-of-the-matter-copyright-ai-training-llms-part-2/"
  - title: "Training Foundation Models as Data Compression: On Information, Model Weights and Copyright Law"
    url: "https://arxiv.org/pdf/2407.13493"
  - title: "Probabilistic Copies in Generative AI Models"
    url: "https://arxiv.org/pdf/2607.14532"
  - title: "Who Owns the Data Used to Train AI? (2026 Explainer)"
    url: "https://www.humandatarights.org/guides/who-owns-data-used-to-train-ai/"
  - title: "On the workflow, opportunities and challenges — GPT-3 and GPT-5 training costs"
    url: "https://arxiv.org/pdf/2504.17384"
  - title: "Current Model Cards Are Insufficient — open-weight licence and derivative works"
    url: "https://arxiv.org/pdf/2608.18086"
  - title: "An Automated Survey of Generative AI — Llama 3 trained on 15 trillion tokens"
    url: "https://arxiv.org/pdf/2306.02781"
  - title: "The Super Weight — Apple Machine Learning Research"
    url: "https://machinelearning.apple.com/research/the-super-weight"
voices:
  - thinker: "Karl Marx"
    kind: "bench"
    lived: "1818 to 1883"
    argument: "Imaginary Marx would say the weights are fixed capital in its plainest form. Writers and coders put their labour into text. That text trained the model. The model now replaces them, and it belongs to whoever ran the compute, not whoever produced the raw material. The training run converts shared knowledge into a private balance-sheet entry. The fine-tuning case is even cleaner: the customer brings their own knowledge, pays for the run, walks away with nothing durable. They bought a service. The lab kept what the service produced. Marx would not find this surprising. He'd say it's the oldest story in the book, written in a new file format."
  - thinker: "Edmund Burke"
    kind: "bench"
    lived: "1729 to 1797"
    argument: "Imaginary Burke would resist from the start. The lab earned the weights by doing what nobody else organised: assembling data, building the architecture, running the compute, absorbing years of loss. The value in the file comes from that work, not from the raw text anyone could download. Claiming contributors own the result because their writing went into the training puts the farmer above the baker. Burke wouldn't call the current arrangement perfect. He'd say breaking it by judicial decree, before anyone has built a replacement, costs more than the problem it solves. Find out why the thing exists before you pull it apart."
  - thinker: "machine learning engineer"
    kind: "practitioner"
    lived: ""
    argument: "The post gets the weights right but understates how opaque they are, even to the people who built them. You can't open a weight file and read it like code. You run the model and watch outputs. You can't point at a specific weight and say that one learned from that author's book. Apple's research on super-weights found that removing a single parameter from Llama-7B turns coherent output into gibberish. That's how tangled this gets. The Copyright Office's framing of weights as copies assumes a transparency that doesn't exist at the engineering level. That doesn't settle the legal question. But the ownership fight is harder than it looks from outside, because the thing being owned is opaque to its owner."
---

By the end of 2028, an enterprise customer will win ownership of weights produced in a fine-tuning run they paid for. The lab's contracts currently say the lab owns them. Courts will not agree indefinitely.

**The file nobody talks about**

When you send a message to an AI, several things move. Your words break into tokens. The tokens pass through a context window. A response comes back. None of that matters most. What matters most sits in a file that never changes while you talk.

That file holds the weights.

[Weights are the numerical values stored across every connection in a neural network](https://docs.lm-kit.com/lm-kit-net/guides/glossary/weights.html). During training, each value gets adjusted millions of times to make the model's predictions more accurate. Training ends. They freeze. [The model stops learning the moment you start using it](https://arxiv.org/pdf/2509.14405). It applies what those numbers recorded, token by token, until the conversation ends.

The weights hold everything the model knows. Grammar. Facts. How a nurse talks to a patient. The structure of a contract. The rhythm of a lie. All of it compressed into numbers. [The parameter count of a model equals the number of floating-point values in those weights](https://www.tigrisdata.com/blog/chonky-models/). A Llama 3.1 70B model carries 70 billion of them. [At 16-bit precision, that runs to roughly 140 GB](https://www.spheron.network/blog/gpu-memory-requirements-llm/). One file. Everything the model can do, fixed inside it.

**Why running a model costs what it costs**

Most people assume inference costs money because the arithmetic is hard. [LLM inference actually burns most of its time moving weights from memory to compute units, not doing the maths](https://www.thundercompute.com/blog/best-gpu-for-llm). The chip fetches those 140 GB fast enough to produce tokens while you wait. That needs specialised hardware with extreme memory bandwidth.

A longer conversation costs more not because your questions got harder. The model reads the growing transcript alongside the weights on every single generation step. Both travel from storage to processor. The weights stay the same size. The transcript grows. That's the meter running.

**What the weights actually contain**

The weights don't store sentences you could read back. They hold no lookup table. Training compressed patterns of relationship between concepts into billions of numerical values. The original text became unrecoverable. The structure it carried did not.

The US Copyright Office's [May 2025 report on AI training](https://huggingface.co/blog/jonathanagustin/ai-copyright-analysis-2025) named the weights as the contested core: "it is the weights that reflect patterns learned from the training data, and which are most likely to be treated as proprietary by developers or draw the scrutiny of copyright owners."

That sentence names a fight. The weights sit at the centre of every training-data lawsuit currently running. [The Office concluded that weights containing memorised training data constitute copies under the reproduction right](https://www.copyright.com/blog/the-heart-of-the-matter-copyright-ai-training-llms-part-2/). Courts are not bound by that. But the direction is set.

A paper on [training as data compression](https://arxiv.org/pdf/2407.13493) argued that generating output from weights may trigger the rights of whoever made the training data. A [2025 paper on probabilistic copying](https://arxiv.org/pdf/2607.14532) called the question "surprisingly complicated." Both agree on one thing: the weights, not the outputs, carry the real legal risk.

**The derived number**

[Llama 3 405B trained on roughly 15 trillion tokens](https://arxiv.org/pdf/2306.02781). A token runs to about 0.75 words. So 15 trillion tokens holds around 11.25 trillion words. The British Library's collection runs to roughly 625 million words. That model compressed the equivalent of about 18,000 British Libraries into a single file. Not through understanding. Through aggressive statistical generalisation over patterns nobody individually chose to donate.

**The ownership gap**

[The AI company that trains a model owns it](https://www.humandatarights.org/guides/who-owns-data-used-to-train-ai/), even though millions of people's writing built it. Your conversations don't enter the weights. They live in the context window, then vanish, or sit in an external memory database you rent. The weights stay at the lab.

Now add fine-tuning. A company pays a lab to run further training on its proprietary documents. The resulting weights contain that company's knowledge, compressed the same way. The current contracts assign ownership of those weights to the lab. The customer bought a service. The lab kept the asset.

[Whether open-weight licences propagate to fine-tuned derivatives](https://arxiv.org/pdf/2608.18086) adds another layer. Open-weight is not the same as free. Meta published Llama's weights. The legal obligations attaching to a model fine-tuned on Llama remain unsettled.

Stand at the accountant's desk. [Training GPT-3 cost roughly $9 million in 2020](https://arxiv.org/pdf/2504.17384). One estimate puts GPT-5 at around $612 million in 2024, on 50,000 H100 GPUs. That money froze into a file. The file went on the balance sheet. Whoever holds the file holds the capital.

The conversation you had with an AI last week built nothing you own. Every prompt you wrote, every correction you gave, every piece of proprietary text you fed into a fine-tuning run: it moved into that file and stayed there when you left.

That's the meter. And it only runs one way.
