---
title: "Why your AI goes fast on the boring words and slow on the hard ones: how speculative decoding works"
date: 2026-10-29T01:16:23.757976+00:00
layout: post.njk
tags: [machines, money]
description: "The GPU generating your AI responses spends most of each step waiting for data, not computing. Speculative decoding fills that idle time with a small model's guesses. Correctly tuned, it cuts compute "
search_title: "How speculative decoding works: why AI inference is faster than the hardware should allow"
form: technical
form_label: "how it works"
sources:
  - title: "Fast Inference from Transformers via Speculative Decoding (Leviathan et al., ICML 2023)"
    url: "https://www.alphaxiv.org/abs/2211.17192"
  - title: "Speculative Decoding Explained: How Draft Models Make AI Agents Faster (MindStudio)"
    url: "https://www.mindstudio.ai/blog/speculative-decoding-explained-ai-agents"
  - title: "Decode Is Memory-Bound. Speculation Is the Arbitrage (The Software Frontier)"
    url: "https://www.thesoftwarefrontier.com/p/decode-is-memory-bound-speculation"
  - title: "Speculative Decoding for On-Device LLMs (TechVeda 2026)"
    url: "https://www.techveda.live/2026/08/05/speculative-decoding-on-device-llm/"
  - title: "KV Cache Optimization Strategies for Scalable and Efficient LLM Inference (arXiv:2603.20397)"
    url: "https://arxiv.org/pdf/2603.20397"
  - title: "KV Cache Optimization: Memory Efficiency for Production LLMs (Introl)"
    url: "https://introl.com/blog/kv-cache-optimization-memory-efficiency-production-llms-guide"
  - title: "Speculative Decoding (Wikipedia)"
    url: "https://en.wikipedia.org/wiki/Speculative_decoding"
  - title: "Eagle-3 Speculative Decoding on GPU Cloud: 3-4x Faster LLM Inference (Spheron 2026)"
    url: "https://www.spheron.network/blog/eagle-3-speculative-decoding-gpu-cloud/"
  - title: "EAGLE-3 Speculative Decoding in Production (ATOMSH)"
    url: "https://atomsh.net/en/atelier/ai-engineering/read/phases/17-infrastructure-and-production/05-eagle3-speculative-decoding/"
  - title: "Speculative Decoding Knowledge Base (Yobitel)"
    url: "https://yobitel.com/knowledge-base/speculative-decoding"
  - title: "Speculative Decoding in Production LLM Inference 2026 (AppScale Blog)"
    url: "https://appscale.blog/en/blog/speculative-decoding-production-llm-inference-eagle-medusa-vllm-2026"
  - title: "Speculative Decoding in vLLM: Complete Guide to Faster LLM Inference (JarvisLabs)"
    url: "https://jarvislabs.ai/blog/speculative-decoding-vllm-faster-llm-inference"
voices:
  - thinker: "Ibn Khaldun"
    kind: "bench"
    lived: "1332 to 1406"
    argument: "Imaginary Ibn Khaldun would say the post mistakes a lag for a wall. He wrote about how craft knowledge moves: the people at the frontier hold it first, the provinces close the gap, the advantage flattens. He watched this with irrigation, with weaving, with fortification. The code is public. The papers exist. The thing slowing people down is not secrecy. It's that nobody has paid to write the debugging down. Once someone does, the gap closes fast. He'd push back on the 2028 prediction and say the knowledge will spread quicker than that. Two years in the Maghreb, two years here."
  - thinker: "Elinor Ostrom"
    kind: "bench"
    lived: "1933 to 2012"
    argument: "Imaginary Ostrom sees the debugging knowledge as a shared resource being wasted. Every team re-derives the same hard lessons: which workloads break, what acceptance rate to aim for, when to switch the technique off. She watched fishing communities do this with fish stocks before they built common rules. The fix isn't a secret: publish acceptance rate benchmarks by workload type, let teams compare notes, stop each one paying the full cost of learning what the last one already learned. She'd call the current arrangement a commons without a keeper."
  - thinker: "ml infrastructure engineer"
    kind: "practitioner"
    lived: ""
    argument: "The post gets the maths right and the 58-per-cent number is honest about its assumptions. What it doesn't convey is that the acceptance rate isn't a fixed number you measure once. A customer-support bot and a coding assistant run at very different rates on the same draft head. You benchmark it, ship it, and then spend six weeks working out why response times spiked on Tuesdays when the user questions got harder. The code being open and the knowledge being closed is accurate. But what's closed isn't a secret. It's accumulated debugging. That takes time to spread regardless of whether anyone wants to keep it private."
---

By the end of 2028, the gap in running costs between AI providers who have tuned their serving stacks and those who have not will be large enough to show up in published price comparisons. If it doesn't, the technique stayed a curiosity.

The technique is speculative decoding, and most teams deploying their own models in 2026 have not touched it. Not because it's hard to understand. Because the debugging knowledge isn't written down anywhere obvious, and the papers don't tell you what happens on a Tuesday.

**The GPU is waiting**

The bottleneck in generating an AI response is not the maths. It's the memory. [Leviathan and colleagues at Google named it in 2022](https://www.alphaxiv.org/abs/2211.17192): producing one token means streaming every weight in the model from memory into the chip, doing a small multiplication, and discarding it. The arithmetic takes microseconds. [The chip then waits for the next block of weights to arrive.](https://www.techveda.live/2026/08/05/speculative-decoding-on-device-llm/) Most of the time, it's waiting.

This is the thing you've felt. The AI types "the" and "and" fast. It slows down on a name, a number, a word it has to work out. You assume it's thinking harder. Partly. But "the" is also easier to guess, and somebody has been cashing in on that since 2022.

**The bet**

Instead of making the big model produce every token, you run a small, fast draft model first. It guesses the next four or five tokens quickly. Then the big model checks all those guesses in one pass. [Because the big model's bottleneck is memory, not arithmetic, checking five candidates costs roughly the same as producing one token would have.](https://www.mindstudio.ai/blog/speculative-decoding-explained-ai-agents) The output is identical to what the big model would have produced on its own. [This is a theorem, proved by Leviathan et al. at Google and independently by Chen et al. at DeepMind in 2023.](https://www.alphaxiv.org/abs/2211.17192) A reject-and-correct rule ensures the distribution is preserved even when the draft is wrong.

The small model guesses: "the", "city", "of", "London", "has". The big model checks all five, accepts "the", "city", "of", rejects "London" (it would have said "London's"), resamples that one correctly, drops "has". Three tokens for the cost of one big-model step. [On the right content, acceptance rates above 80 per cent are common, giving 2 to 3x more tokens per second.](https://www.mindstudio.ai/blog/speculative-decoding-explained-ai-agents)

**Why the hardware makes this better every year**

[Between the V100 and the B200, GPU compute throughput grew roughly thirty-six times. Memory bandwidth over the same generations grew about nine times.](https://www.thesoftwarefrontier.com/p/decode-is-memory-bound-speculation) Compute outran memory by a factor of four. Each new chip leaves more arithmetic sitting idle during token generation. The gap speculative decoding fills keeps getting wider.

The KV cache piles on top. [It stores a record of every token produced so far, so the model doesn't redo that work. Its size grows linearly with conversation length.](https://arxiv.org/pdf/2603.20397) [A 70B model at 8,000 tokens needs roughly 20GB of that cache per conversation.](https://introl.com/blog/kv-cache-optimization-memory-efficiency-production-llms-guide) [Push the context to 128,000 tokens and even a 7B model's cache exceeds 80GB, the full capacity of an A100.](https://arxiv.org/pdf/2603.20397) Long conversations are expensive not because the thinking gets harder. The memory gets fuller.

**How the draft got smarter**

The original papers used a separate small model as the guesser. Acceptance rates depended on how well that model matched the big one. [EAGLE (Li et al., 2024) changed this: train a small draft head that plugs into the big model's own internal signals, rather than running separately.](https://en.wikipedia.org/wiki/Speculative_decoding) [It adds under 5 per cent extra weight to a 70B model](https://jarvislabs.ai/blog/speculative-decoding-vllm-faster-llm-inference) while pushing acceptance rates to 80 per cent or above on typical chat.

[EAGLE-3 (NeurIPS 2025, arXiv:2503.01840) trains the draft head on signals from early, middle, and late layers of the big model, not just the final one.](https://atomsh.net/en/atelier/ai-engineering/read/phases/17-infrastructure-and-production/05-eagle3-speculative-decoding/) [Later EAGLE versions reached 3 to 6.5x faster token output on some tasks.](https://en.wikipedia.org/wiki/Speculative_decoding) [It is now the recommended high-performance serving option in vLLM.](https://www.spheron.network/blog/eagle-3-speculative-decoding-gpu-cloud/) [Google deployed speculative decoding in AI Overviews in 2025.](https://atomsh.net/en/atelier/ai-engineering/read/phases/17-infrastructure-and-production/05-eagle3-speculative-decoding/) [Anthropic, OpenAI and Google all run proprietary variants in their APIs.](https://yobitel.com/knowledge-base/speculative-decoding)

**Where it fails**

Two places.

First: many users at once. When hundreds of conversations are running together, the chip is already busier during token generation, and the draft model competes with the main model for the same hardware. [vLLM's recommended settings include an automatic fallback: switch speculation off when batch size exceeds 32.](https://www.spheron.network/blog/eagle-3-speculative-decoding-gpu-cloud/)

Second: hard, unpredictable content. Mathematical reasoning, unusual names, multi-step problems. The draft guesses wrong more often, the big model rejects more tokens, and you pay for the draft's work without getting the speed. [Teams that turn speculation on without measuring the acceptance rate on their real traffic sometimes see slower responses, not faster.](https://atomsh.net/en/atelier/ai-engineering/read/phases/17-infrastructure-and-production/05-eagle3-speculative-decoding/)

**The number**

With an acceptance rate of 0.8, five tokens guessed per round, and the draft costing about 8 per cent of what the main model costs, [the formula (1 minus 0.8 to the power of 6) divided by ((1 minus 0.8) times (5 times 0.08 plus 1))](https://appscale.blog/en/blog/speculative-decoding-production-llm-inference-eagle-medusa-vllm-2026) gives roughly 2.4x. Same hardware, 2.4x the tokens per hour. The same tokens now cost the provider about 42 per cent of what they cost before: a saving of 58 per cent in compute, per token.

That 58 per cent does not move. It stays in the serving stack, invisible to the pricing page, invisible to you.

**What this rearranges**

Inference costs have been falling. The credit goes to better chips, smaller models, quantisation. A substantial share comes from serving-stack engineering like this, buried two layers below the API.

The gap compounds. Training a draft head, tuning the acceptance rate for your traffic, handling the failure modes: every major provider has done this work. [Most deployments in 2026 have not.](https://appscale.blog/en/blog/speculative-decoding-production-llm-inference-eagle-medusa-vllm-2026) Not because it's exotic. Because the debugging is not written down anywhere. The code is open. The knowledge is not.

When you talk to an AI and the words come fast, a small model is guessing what the big model would say. Usually right. The GPU's waiting time becomes your speed. The 58 per cent saving accrues to whoever ran the tuning.
