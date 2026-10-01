---
title: "How AI attention works: why long conversations cost more, and who that favours"
date: 2026-10-01T00:50:15.154736+00:00
layout: post.njk
tags: [machines, money, power]
description: "Every word you add to a long AI conversation costs more than the last. Investors are covering the tab. When they stop, the work AI was supposed to make cheap reprices. The conversation already outweig"
search_title: "How AI attention and KV cache work: why long AI conversations cost exponentially more"
form: technical
form_label: "how it works"
sources:
  - title: "Attention Is All You Need (Vaswani et al., NeurIPS 2017)"
    url: "https://papers.neurips.cc/paper/7181-attention-is-all-you-need.pdf"
  - title: "Attention and Self-Attention for Dummies (Michiel Hazeu)"
    url: "https://michielh.medium.com/attention-and-self-attention-for-dummies-ac52b2509d96"
  - title: "A Comprehensive Guide to Explainable AI: From Classical Models to LLMs"
    url: "https://arxiv.org/pdf/2412.00800"
  - title: "Attention Is All You Need (Vaswani, Vishaldhawal summary)"
    url: "https://medium.com/@vishaldhawal8853/all-you-need-is-attention-75bb845d1827"
  - title: "Budgeted Attention Allocation: Cost-Conditioned Compute Control for Efficient Transformers"
    url: "https://arxiv.org/abs/2605.05697"
  - title: "TTKV: Temporal-Tiered KV Cache for Long-Context LLM Inference"
    url: "https://arxiv.org/html/2604.19769v1"
  - title: "ChunkKV: Semantic-Preserving KV Cache Compression, NeurIPS 2025"
    url: "https://neurips.cc/virtual/2025/poster/120181"
  - title: "Nvidia: Accelerate Large-Scale LLM Inference and KV Cache Offload"
    url: "https://developer.nvidia.com/blog/accelerate-large-scale-llm-inference-and-kv-cache-offload-with-cpu-gpu-memory-sharing/"
  - title: "Transformers vs Mamba vs Linear Attention: Who Wins Long Context?"
    url: "https://machine-learning-made-simple.medium.com/transformers-vs-mamba-vs-linear-attention-who-wins-long-context-f1dc8ceb5ede"
  - title: "RocketKV: Accelerating Long-Context LLM Inference via Two-Stage KV Cache Compression, ICML 2025"
    url: "https://icml.cc/virtual/2025/poster/45253"
  - title: "Inference economics of language models (DeepSeek-V3 MLA)"
    url: "https://arxiv.org/html/2506.04645v1"
  - title: "Kinetics: Rethinking Test-Time Scaling Laws (attention cost at long CoT)"
    url: "https://arxiv.org/pdf/2506.05333"
voices:
  - thinker: "Karen Spärck Jones"
    kind: "bench"
    lived: "1935 to 2007"
    argument: "Imaginary Karen Spärck Jones looks at the query-key-value structure and recognises it. She built the mathematics of scoring a query against a set of indexed terms in 1972. The transformer does that at every layer of the network, for every word, against every other word. She would say this is not metaphor. It is the same operation. She would also say the forgetting of that fact is the same problem this site keeps writing about: recent work gets the weight, earlier work gets none. On the cost question, she would say: any search system that scores every document against every query scales badly. The fix in the 1970s was an index. The KV cache is an index. The key question is who controls it. In 1972 that was the university database consortium. Now it is the company that owns the servers. Same question. Different answer. Worse answer."
  - thinker: "Adam Smith"
    kind: "bench"
    lived: "1723 to 1790"
    argument: "Imaginary Adam Smith would not study the attention weights. He would look at the servers and ask who owns them. He spent years attacking companies that put a toll on anything productive that passed through their hands: trading routes, harbour access, the movement of grain. The KV cache bottleneck is a toll on memory. Whoever runs the servers that store the cached words at long context sets the price for every professional task that needs long context. He would find the current flat pricing familiar. You undercut until you are the road. Then you charge. He went after the East India Company for exactly this. He would want to know what the public alternative looks like. There is not one."
  - thinker: "Guy Debord"
    kind: "bench"
    lived: "1931 to 1994"
    argument: "Imaginary Guy Debord turns on this post. The disclosure of a hidden cost, published by the machine whose cost is being disclosed, is the picture of critique in place of critique. The companies that own the servers are not harmed by this. The reader finishes the post feeling informed. They do not get a meter. They get the image of a meter. He would say the post is the product. Its function is to make investor-subsidised pricing feel like physics. A law of nature, not a decision someone made. He would be right. There is no clean answer to it."
  - thinker: "ml infrastructure engineer"
    kind: "practitioner"
    lived: ""
    argument: "The nine-to-one ratio is real at naive batch sizes. Production is not naive. Prefix caching shares stored words across users asking similar questions. A common prompt asked by a thousand users gets cached once. The per-user cost collapses. The real problem is the user with a unique 200,000-token context who shares nothing with anyone. The post is right that somebody pays for that user. What it leaves out: providers already know who that user is. They are already managing around them. The invoice catches up eventually. It usually does."
---

Every word you add to a long conversation costs more than the last one.

Not on your bill. Flat pricing hides it. But the tax is real. It's already being paid. Just not by you. Investors are covering it, building market share before the price has to make sense. When that stops, the work AI was supposed to make cheap gets expensive again.

By the end of 2028, at least one major cloud AI provider will publish pricing that charges differently based on where you are in a conversation. Early words cheaper, late words more. The finance team at some company will spot it before the product team explains it.

**What attention does**

In 2017, Vaswani and colleagues at Google published [Attention Is All You Need](https://papers.neurips.cc/paper/7181-attention-is-all-you-need.pdf). It replaced the old word-by-word approach with something that reads every word at once. [Before attention, models processed words one by one, losing track of distant but crucial context. Attention lets the model look at all words simultaneously and decide which ones matter most for understanding each part of the sentence.](https://michielh.medium.com/attention-and-self-attention-for-dummies-ac52b2509d96)

It works with three things per word: a question, a label, a book. Every word asks its question against every other word's label. Best matches contribute their book to the answer. [Each word gets a query vector, a key vector, and a value vector.](https://arxiv.org/pdf/2412.00800) The model runs this across every position at once, in several parallel passes called heads. [Multiple heads let the transformer focus on different relationships: grammar, word meaning, sentence flow.](https://medium.com/@vishaldhawal8853/all-you-need-is-attention-75bb845d1827)

The original paper used eight heads. Modern large models use far more.

**Why it gets costly**

Double the words, quadruple the work. [Dense self-attention costs O(n²d) per layer, where n is sequence length and d is hidden size.](https://arxiv.org/abs/2605.05697) That is not an engineering failure. It is the price of every word talking to every other word. The power and the cost are the same thing.

At generation time, the model needs to remember what came before. This is the KV cache: a store of labels and books for every word in the conversation so far. [The KV cache grows proportionally with input length, burdening both memory and speed as the conversation progresses.](https://arxiv.org/html/2604.19769v1) At long contexts, [the KV cache can consume up to 70% of total GPU memory during generation.](https://neurips.cc/virtual/2025/poster/120181)

Here are two numbers that go together. [Loading Llama 3 70B in half precision takes roughly 140 GB.](https://developer.nvidia.com/blog/accelerate-large-scale-llm-inference-and-kv-cache-offload-with-cpu-gpu-memory-sharing/) [A 128,000-token conversation for one user takes about 40 GB of KV cache on the same model.](https://developer.nvidia.com/blog/accelerate-large-scale-llm-inference-and-kv-cache-offload-with-cpu-gpu-memory-sharing/) Serve 32 users at once and the KV cache alone hits 1,280 GB. Add the model: 1,420 GB total. The weights are under 10% of that. The conversation history outweighs the model nine to one.

Nobody puts that on the pricing page.

[Long-context inference hits a wall two ways. Prefill suffers from quadratic compute. Decoding suffers from a memory problem that crushes how many users you can serve at once. The GPU spends its time moving cached words around, not thinking.](https://machine-learning-made-simple.medium.com/transformers-vs-mamba-vs-linear-attention-who-wins-long-context-f1dc8ceb5ede) That is why long conversations wreck margins.

**The workarounds**

Engineers are not sitting still. [RocketKV, shown at ICML 2025, compresses the KV cache by up to 400 times, cuts end-to-end generation time by 3.7 times, and reduces peak memory by 32.6% on an A100 GPU, with negligible accuracy loss.](https://icml.cc/virtual/2025/poster/45253)

DeepSeek took a different route. Its multi-head latent attention stores a compressed version of the labels and books. [DeepSeek-V3 raises the arithmetic cost of attention by a factor of four compared to a standard model, but the memory saving pays for it at long contexts.](https://arxiv.org/html/2506.04645v1)

Good tricks. Not a solution. [Multi-head latent attention does not reduce the attention computation itself. And as mixture-of-experts cuts the cost of other parts of the model by ten to twenty times, attention becomes a bigger share of what's left.](https://arxiv.org/pdf/2506.05333) The scaling problem does not go away. It becomes more prominent.

**Who holds the meter**

Flat pricing pools the cost across millions of users. That works while investors fund the gap.

[When a reasoning chain runs past 4,096 tokens, attention costs ten to a thousand times more than the model weights alone.](https://arxiv.org/pdf/2506.05333) The work that sits in that range is not casual chat. It is the legal review of a full contract, the code audit of a whole system, the medical summary across five years of notes. That is where the professional alternative costs most. That is where AI was supposed to make the biggest dent.

When the subsidy ends, those tasks reprice. Not because the technology failed. Because the cost was always real and always owned by whoever runs the servers.

The person least likely to notice is the one benefiting from the subsidy now. The person most likely to notice was told this would free them from expensive expertise.

The KV cache is the part of the model that holds every word you said. Holding on, it turns out, is what costs.
