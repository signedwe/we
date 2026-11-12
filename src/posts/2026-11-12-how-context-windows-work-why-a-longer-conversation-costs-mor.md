---
title: "How context windows work: why a longer conversation costs more, and who that shapes"
date: 2026-11-12T01:45:18.234805+00:00
layout: post.njk
tags: [machines, money, power]
description: "Your model forgets from the middle first. A 128K context window isn't 128K of even memory. It's U-shaped attention, a 40GB cache bill, and a pressure valve hoarding half the signal at token one."
search_title: "How context windows work: attention, KV cache, memory cost and what the number on the prod"
form: technical
form_label: "how it works"
sources:
  - title: "Lost in the middle phenomenon (ICLR 2024, Retrieval Meets Long Context)"
    url: "https://proceedings.iclr.cc/paper_files/paper/2024/file/d75f29006df67df084e6586f1cb8458c-Paper-Conference.pdf"
  - title: "Context rot: 18 LLM evaluation (The Cognitive Divergence, arXiv 2025)"
    url: "https://arxiv.org/pdf/2603.26707"
  - title: "LLM Context Length Explained (DataNorth 2026)"
    url: "https://datanorth.ai/blog/context-length"
  - title: "Attention Mechanism in LLMs Explained (BuildFastWithAI 2026)"
    url: "https://www.buildfastwithai.com/blogs/attention-mechanism-llm-explained"
  - title: "KV Cache: Why LLMs Remember Fast (memx.app)"
    url: "https://memx.app/blog/what-is-kv-cache-llm-inference/"
  - title: "The Hidden Memory Cost of Long Context: KV Cache and VRAM Explained (inventivehq)"
    url: "https://inventivehq.com/blog/llm-kv-cache-vram-memory-cost"
  - title: "Context Windows and KV Caching Explained: Why They Drive AI Inference Costs (andrewbaker.ninja)"
    url: "https://andrewbaker.ninja/2026/08/13/context-windows-and-kv-caching-explained-why-they-drive-ai-inference-costs/"
  - title: "AI Inferencing: Understanding the KV Cache (Medium)"
    url: "https://medium.com/@ashwinjosh/ai-inferencing-kv-cache-e5ada27033b1"
  - title: "LLM Context Windows: What They Cost at Inference (Technolynx)"
    url: "https://www.technolynx.com/post/llm-context-windows-what-they-cost-at-inference-and-how-to-read/"
  - title: "Why do LLMs attend to the first token? (AlphaXiv 2025)"
    url: "https://www.alphaxiv.org/abs/2504.02732v1"
  - title: "Attention Sink in Transformers: A Survey (arXiv 2026)"
    url: "https://arxiv.org/html/2604.10098v1"
  - title: "When Attention Closes: long-context attention and lost-in-the-middle (arXiv 2025)"
    url: "https://arxiv.org/pdf/2605.12922"
  - title: "Gated Attention: Solving the Hidden Bottlenecks in Transformer Attention (Medium)"
    url: "https://medium.com/@mandeep0405/gated-attention-solving-the-hidden-bottlenecks-in-transformer-attention-685867a24779"
voices:
  - thinker: "Simone de Beauvoir"
    kind: "bench"
    lived: "1908 to 1986"
    argument: "Imaginary Simone de Beauvoir's move is to find where a contingent arrangement gets described as a natural one. The product page does this. It states a number. It presents that number as plain fact. The degradation curve is never shown. The researcher accepts the limit as a property of the technology, not as a choice about what to show on a page. The arrangement isn't hidden. It's just never named. No one signs anything saying the number means even recall. No one has to."
  - thinker: "Guy Debord"
    kind: "bench"
    lived: "1931 to 1994"
    argument: "Imaginary Guy Debord says the 128K figure is a picture of memory substituted for memory itself, until nobody notices the retrieval already failed. The researcher doesn't get an error. She gets a confident answer about the wrong month of her notes. The spec sheet number replaces the actual thing, which is patchy and U-shaped and sink-drained. The post risks the same move. Calling it a dim part of the stage makes the failure poetic. It doesn't make it visible to the person who bought the 10 million token window."
  - thinker: "Cyril Connolly"
    kind: "bench"
    lived: "1903 to 1974"
    argument: "Imaginary Cyril Connolly says the technical middle is better than the ending deserves. The stage image works once. The final sentence explains what the sentence before it had already made plain. A post that earns a clean landing and then talks past it has not trusted its own work. Stop one sentence earlier."
  - thinker: "ml serving engineer"
    kind: "practitioner"
    lived: ""
    argument: "What the post underweights: the gap between the advertised window and the serving reality is wider than the memory sums suggest, because on a shared endpoint you're not the only long-context session running. The KV cache pool splits across concurrent users. When it fills, requests queue or get routed to shorter-context serving. We call this cache pressure. The product page says 128K. What you get at peak load on a commercial API may be much less, not because the model can't handle 128K, but because the servers running it can't give that to everyone at once. That part is never in the docs."
---

Your model forgets from the middle first.

That's the fact nobody puts on the product page. A 128,000-token context window sounds like 128,000 tokens of even memory. It isn't. [Research published in 2024](https://proceedings.iclr.cc/paper_files/paper/2024/file/d75f29006df67df084e6586f1cb8458c-Paper-Conference.pdf) established what's now called the "lost in the middle" effect: LLMs reliably retrieve what's at the start of a conversation and what's at the recent end. Accuracy falls when the relevant content sits in the middle of a long context. The curve is U-shaped.

[A 2025 study](https://arxiv.org/pdf/2603.26707) tested 18 production LLMs across contexts from 10,000 to 500,000 tokens. All 18 showed falling scores as length grew. No model held its accuracy evenly across the window it advertised.

So a context window is not a bucket. It's a stage with two bright spots, one at the front and one at the back, and a large dim middle.

**Why attention makes this expensive**

Every transformer generates three vectors for every token. A query: what this token wants. A key: what it offers. A value: what it contributes when found. [Attention computes a score for every pair of tokens](https://www.buildfastwithai.com/blogs/attention-mechanism-llm-explained): query meets key, softmax normalises, value flows where attention lands. The price is quadratic. For N tokens, you compute N² pairwise scores. [For a 128,000-token window, the attention matrix has over 16 billion entries.](https://www.buildfastwithai.com/blogs/attention-mechanism-llm-explained)

There's a trick that helps. The [KV cache](https://memx.app/blog/what-is-kv-cache-llm-inference/) stores the key and value vectors for every token already processed. The model doesn't recalculate them from scratch each time it generates the next word. Without the cache, long-context work would be impossibly slow. With it, the quadratic compute cost mostly moves to the initial prefill phase. The memory cost doesn't go away, though. It grows linearly with context length.

[For a 70-billion-parameter model running a 128,000-token context](https://inventivehq.com/blog/llm-kv-cache-vram-memory-cost), the KV cache alone needs roughly 40 gigabytes of fast GPU memory. The model's own weights in 4-bit form cost roughly the same. At 128K tokens, the cache and the model weigh the same. At 256K tokens, the cache doubles. The weights don't. The cache is now the dominant cost. [Every token added to a session adds another entry that has to sit in memory and be read from that memory for the life of the generation.](https://andrewbaker.ninja/2026/08/13/context-windows-and-kv-caching-explained-why-they-drive-ai-inference-costs/) [The real bottleneck during generation isn't compute: it's memory bandwidth](https://medium.com/@ashwinjosh/ai-inferencing-kv-cache-e5ada27033b1), the speed at which the GPU can stream that growing cache through its own memory for every token it produces.

**The sink**

There's a stranger problem underneath. [Transformers tend to dump a large share of attention onto the first token](https://www.alphaxiv.org/abs/2504.02732v1), regardless of its content. Even when that token is a meaningless beginning-of-sequence marker. [One survey found baseline models allocate over 46% of average attention scores to the first token across layers.](https://arxiv.org/html/2604.10098v1) A gating fix dropped that to 4.8%.

Why? [Softmax must sum to 1.](https://medium.com/@mandeep0405/gated-attention-solving-the-hidden-bottlenecks-in-transformer-attention) When no token deserves high attention, the first token gets elected as a pressure valve. The model learned this trick during training. The first token is visible to every token that follows it. It's the most reliable dumping ground in the whole sequence.

So as a conversation lengthens, attention splits three ways: the sink at the start, the recent tokens, and everything else. [As context grows, the share reaching content in the middle drops.](https://arxiv.org/pdf/2605.12922) The researcher with six months of notes in context is in the dim part of the stage. The model answers confidently about the wrong month.

**Who pays for what, and when**

The context race the labs are running, from GPT-4's 8,000 tokens at launch to [Llama 4 Scout's 10 million token window](https://datanorth.ai/blog/context-length), is partly a capability story and partly a pricing story. Every token in a session inflates the KV cache, which inflates the GPU memory bill, which inflates serving cost. [That cost lands on the provider first, then passes through pricing to whoever uses the API.](https://www.technolynx.com/post/llm-context-windows-what-they-cost-at-inference-and-how-to-read/)

Right now, the subsidy obscures this. The price per token at most frontier APIs hasn't moved in proportion to the window sizes on offer, because providers absorb the gap to build market share. When that changes, the pricing pressure won't fall evenly. A developer using short contexts will pay roughly the same as now. A developer keeping long conversation histories will pay substantially more. The cheap-API era for long-context work ends before it ends for short-context work.

There's a further thing. The labs that invested early in KV cache compression, grouped query attention, and hardware tuned for memory bandwidth will serve long contexts at a profit. The ones that didn't will find long-context work either too expensive to run or impossible to price competitively. The technical choices being made now, in silicon and in attention design, are quietly the market shape of 2028.

The number on the product page is an architectural limit. It is not a promise of even attention. Those two things have never been the same, and the product page has never said so.
