---
title: "How AI memory works: what you own, what the model owns, and where your two years of training actually live"
date: 2026-10-08T01:15:50.136320+00:00
layout: post.njk
tags: [machines, ownership, money]
description: "AI has three kinds of memory. The weights (140 GB, the company's). The context window (1.3 GB, gone when you close the tab). Your 'memory' (a note in their database). The portability tools give you a "
search_title: "How AI memory works: weights, context window and external memory explained"
form: technical
form_label: "how it works"
sources:
  - title: "LLM Weights Context and Memory Explained Simply"
    url: "https://medium.com/@tahirbalarabe2/llm-weights-context-and-memory-explained-simply-03685b6789c0"
  - title: "AI Hardware Accelerators for Large Language Models: Architectures and the Memory Wall"
    url: "https://arxiv.org/pdf/2608.28048"
  - title: "Externalization in LLM Agents"
    url: "https://arxiv.org/pdf/2604.08224"
  - title: "Memory Power Asymmetry in Human-AI Relationships"
    url: "https://arxiv.org/pdf/2512.06616"
  - title: "What Are LLM Parameters? Model Size Explained"
    url: "https://sqmagazine.co.uk/glossary/llm-parameters/"
  - title: "Transfer Memory Between Grok, ChatGPT and Claude"
    url: "https://plurality.network/blogs/transfer-memory-between-grok-chatgpt-claude/"
  - title: "Claude Memory Import and Export: Complete Guide"
    url: "https://aicostboard.com/blog/posts/claude-memory-import-export-guide"
  - title: "Gemini Now Imports Your ChatGPT and Claude History"
    url: "https://mywrittenword.com/2026/03/27/gemini-chatgpt-claude-memory-import-portability-2026/"
voices:
  - thinker: "Frantz Fanon"
    kind: "bench"
    lived: "1925 to 1961"
    argument: "Imaginary Fanon asks who doesn't know the export button exists. Not random. She's the one with less time to read settings pages, less habit of treating software as a contract, less proximity to jobs where a colleague says back up your tools before you leave. The platform puts the export three menus deep. That choice is not neutral. The person who loses the stored context when the employer switches vendor is the same person who didn't know she had it. The post calls this an ownership problem. Fanon would say that's the wrong frame. It's a distribution of knowledge problem dressed as a contract."
  - thinker: "Karl Marx"
    kind: "bench"
    lived: "1818 to 1883"
    argument: "Imaginary Marx points at the 140 GB. That file holds crystallised labour. Coders, writers, forum users, people who typed things into the internet for free built it. The compute was expensive. The raw material was not paid for. The value landed in a file the company owns entirely. Your note in the database says you prefer short sentences and work in healthcare. That note is yours. The 140 GB that makes the note useful is not. This is not a new story. It is a very old one with a new file format."
  - thinker: "Cyril Connolly"
    kind: "bench"
    lived: "1903 to 1974"
    argument: "Imaginary Connolly says the last three lines are the post. They kept the 140 GB. You had the 1.3 GB. They sent you the notes. That is the whole thing. Everything before it is throat-clearing. He'd start on page four, cut backwards, and call this a strong idea that took too long to trust itself."
  - thinker: "ml engineer"
    kind: "practitioner"
    lived: ""
    argument: "The 1.3 GB figure is a ceiling. Most chats don't fill 128,000 tokens. A normal exchange uses a fraction of that cache. So 108 to 1 is the widest gap, not the usual one. The post should say so. The point holds. But anyone who runs models will spot the extreme-case arithmetic and stop trusting the rest."
---

By the end of 2028, enterprise AI contracts will carry a clause about who owns the stored context when a deployment ends. The weights fight is already happening. This one isn't yet. Bet it.

Your AI forgot you. You switched apps and it started again from zero. Not a bug. The architecture.

There are three things called AI memory. They don't live in the same place. They're not owned by the same party. The one you think you're building is the one you have the least claim to.

**What the model knows: weights**

[When a model is trained, it adjusts billions of numbers.](https://medium.com/@tahirbalarabe2/llm-weights-context-and-memory-explained-simply-03685b6789c0) Those numbers are the weights. They freeze when training ends. You can't change them without retraining the whole thing.

This is the model's long-term memory. It's shared across every user on earth. It belongs to the company that trained it. [A full-precision copy of Llama 3.1's 70 billion parameters weighs 140 GB.](https://arxiv.org/pdf/2608.28048) That 140 GB contains everything it learnt before you typed a word. You have no copy. No claim. [Changing a single fact inside it requires retraining, or risky patching that can break other things.](https://arxiv.org/pdf/2604.08224)

**What it holds during your chat: the context window**

Every word you send, every reply it gives, goes into the context window. [Think of it as a scratchpad, wiped when the session ends.](https://medium.com/@tahirbalarabe2/llm-weights-context-and-memory-explained-simply-03685b6789c0) Llama 3.1 holds [128,000 tokens](https://sqmagazine.co.uk/glossary/llm-parameters/), roughly a long novel's worth. Gone when you close the tab.

Here's the number none of the sources put side by side. [The key-value cache for a Llama 3.1 70B session at full 128,000-token context runs to about 1.3 GB.](https://arxiv.org/pdf/2608.28048) The weights are 140 GB. Divide one by the other: 108 to 1. What you said in this chat is roughly one per cent of what the model holds, measured in storage. When the session ends, that one per cent is gone. The 140 GB serves the next person.

**What platforms call memory: notes in a database**

When ChatGPT or Claude says it remembers your job title and your tone, it has written a note to itself in a database. Not in the model. [Systems like these hold user profiles and key-value stores outside the weights entirely.](https://arxiv.org/pdf/2512.06616) Next time you open a chat, those notes get loaded in at the start.

This is where it gets commercially interesting.

[In March 2026, ChatGPT, Claude, and Gemini all shipped memory portability features within weeks of each other.](https://plurality.network/blogs/transfer-memory-between-grok-chatgpt-claude/) You can now export a text list of what the platform wrote down about you. [Claude gives you your full profile: tone, personal details, projects, corrections.](https://aicostboard.com/blog/posts/claude-memory-import-export-guide) You can paste it into a rival.

But [the export captures stated preferences, not the patterns that built up across thousands of actual chats.](https://mywrittenword.com/2026/03/27/gemini-chatgpt-claude-memory-import-portability-2026/) [The import tools make a one-time copy. After that, each assistant's notes drift apart.](https://plurality.network/blogs/transfer-memory-between-grok-chatgpt-claude/) Portability hands you a photograph of the relationship. Not the relationship.

**Who this costs**

Not the person who knows about the export button and uses it. Her.

The person on month eighteen with a well-tuned assistant. The one who doesn't know the export exists. Who assumes the relationship is durable. Who finds out, when the employer switches vendor or the platform changes pricing, that memory was a tenancy, not a deed.

The note about her job title lived on the platform's servers. The platform decided the format. The 140 GB stayed exactly where it was. She got a text file.

The weights question, who owns the model itself, gets all the legal attention right now. The stored-context question, who owns what a model built up about this organisation over two years, is the one nobody has litigated. It's coming, and it will cost more when it arrives.

**The refutation**

The load-bearing claim: what you export is not the model's memory, it's a note in a database. The search that tries to break it: does any deployed product write your data back into the weights themselves?

The answer right now is no. [A single set of weights has no way to tell one user from another at the parameter level.](https://arxiv.org/pdf/2604.08224) Per-user weight updates exist as a research idea, not a shipped product at consumer scale. The claim holds for every product you can name today. If that changes, the text-file export misses the main event, and the ownership fight arrives faster.

They kept the 140 GB. You had the 1.3 GB. They sent you the notes.
