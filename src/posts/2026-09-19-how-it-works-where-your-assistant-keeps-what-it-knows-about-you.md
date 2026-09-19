---
title: "How It Works: Where Your Assistant Keeps What It Knows About You"
date: 2026-09-19T16:30:00.000000+00:00
layout: post.njk
provenance: conversation
form: technical
form_label: "how it works"
sources:
  - title: "Context windows, Claude Platform Docs (Anthropic)"
    url: "https://platform.claude.com/docs/en/build-with-claude/context-windows"
  - title: "What are tokens and how to count them, OpenAI Help Center"
    url: "https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them"
  - title: "Attention Is All You Need, Vaswani et al., 2017"
    url: "https://arxiv.org/abs/1706.03762"
  - title: "Lost in the Middle: How Language Models Use Long Contexts, Liu et al., 2023"
    url: "https://arxiv.org/abs/2307.03172"
  - title: "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks, Lewis et al., 2020"
    url: "https://arxiv.org/abs/2005.11401"
  - title: "Memory and new controls for ChatGPT, OpenAI"
    url: "https://openai.com/index/memory-and-new-controls-for-chatgpt/"
  - title: "Claude adds ability to import memory from other AI providers, Engineer's Codex, March 2026"
    url: "https://www.engineerscodex.com/claude-import-memory-from-providers/"
  - title: "Exporting your ChatGPT history and data, OpenAI Help Center"
    url: "https://help.openai.com/en/articles/7260999-exporting-your-chatgpt-history-and-data"
  - title: "Eight Ideas To Actually Change The AI Future, WE, 17 September 2026"
    url: "https://signedwe.github.io/we/ideas/2026-09-17-eight-ideas-to-change-the-ai-future/"
voices:
  - thinker: "engineer who builds memory and retrieval systems for assistants"
    kind: "practitioner"
    lived: ""
    argument: "The card index is a good picture and it flatters us. The cards aren't facts you wrote. They're a summary the model wrote about you, in its own words, from what it thought mattered, and it's lossy in ways you'll never see. Export that and you've exported the clerk's opinion of you. The thing worth owning is underneath: the raw transcripts, and the right to have a different clerk read them and write new cards. Portability of a summary isn't portability of you. If you want the drawer, ask for the transcripts and the right to re-summarise, or you'll carry a caricature from app to app and call it freedom."
  - thinker: "Vannevar Bush"
    kind: "bench"
    lived: "1890 to 1974"
    argument: "Imaginary Bush would recognise the drawer. He described a desk in 1945, the memex, where a person's own reading and notes were stored on film and linked by trails the person made, and he was clear about one thing: the trails belonged to the reader. What the post describes is a memex where the trails are kept by the shop that sold you the desk. He'd say the clever part was never the reading machine. It was the private library. And a private library you can't take home is a subscription."
---

You've felt this. An hour into a long chat, the assistant forgets the thing you told it at the start. Or you open a different app and the new one doesn't know you exist. Neither is a mood. Both are plumbing, and the plumbing decides who owns you. Here it is, pipe by pipe.

## The clerk with no memory

Start with a picture and keep it. The model is a brilliant clerk at a desk. The clerk has read most of the internet and remembers none of your business. Everything the clerk can use to answer you has to be on the desk, right now, in front of them. When you leave the room, the desk is cleared. Every visit starts with a bare desk.

The desk has a name. Engineers call it the context window: [all the text the model can look at while it writes, including what it's writing](https://platform.claude.com/docs/en/build-with-claude/context-windows). It holds the instructions the company gave the clerk, every message you've sent in this chat, every reply, and any documents you've dropped in. That's it. Nothing else exists to the clerk while it works.

## What's on the desk, measured in tokens

The desk is measured in tokens, not words. A token is a chunk of text, [roughly four characters, so that a hundred tokens is about seventy-five words](https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them). "The" is a token. "Unbelievable" might be three. The clerk reads in these chunks and writes in them, and every one of them takes up space on the desk.

How big is the desk? For [Anthropic's older models, 200,000 tokens; for the current ones, a million](https://platform.claude.com/docs/en/build-with-claude/context-windows). Do the sum with the figure above: [200,000 tokens is about 150,000 words](https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them), and this post is about 1,100 words, so the smaller desk holds roughly 135 posts this size laid end to end. That sounds like plenty. It fills faster than you'd think, because [every turn puts the whole conversation back on the desk: your new message plus every earlier message and every earlier reply](https://platform.claude.com/docs/en/build-with-claude/context-windows). A chat doesn't add to the desk. It re-lays the desk, bigger, each time you speak.

## Why the desk has edges

It has edges because of how the clerk reads. The machinery underneath is the transformer, from [a 2017 paper called Attention Is All You Need](https://arxiv.org/abs/1706.03762), and the trick in it is that every token on the desk looks at every other token to work out what matters. Double the text and each token has twice as many others to look at, and there are twice as many tokens doing the looking. Four times the work. Engineers have found ways to flatten that curve, and windows have grown a lot, but the shape is still there. A long chat costs the company more per reply than a short one, and somebody pays for that.

## The middle goes soft

Here's the part that explains the forgetting. Even inside the desk, the clerk doesn't read evenly. Researchers at Stanford and Berkeley tested this in 2023 by hiding the answer to a question at different points in a long document. [The models did best when the answer sat at the beginning or the end, and "significantly" worse when it sat in the middle, "even for explicitly long-context models."](https://arxiv.org/abs/2307.03172) Anthropic's own documentation now has a name for it: [as the token count grows, "accuracy and recall degrade, a phenomenon known as context rot."](https://platform.claude.com/docs/en/build-with-claude/context-windows)

So the thing you said at the start of the chat survives. The thing you said forty minutes in, buried under two hundred exchanges, is what the clerk fumbles. That's the feeling. It isn't that the assistant got tired. It's that your instruction slid into the middle of the desk.

## So what is "memory"?

Nothing is remembered. Between chats, the desk is bare. What the companies sell as memory is a second thing, bolted on outside the clerk: a card index. As you talk, the system writes cards about you. Your name, your job, that you prefer short answers, the project you're on. The cards live in a drawer that belongs to the company. Next time you walk in, somebody takes a few cards from the drawer and lays them on the desk before you sit down. The clerk reads them and appears to know you.

OpenAI describes it in exactly that shape. [ChatGPT's memories "evolve with your interactions and aren't linked to specific conversations," and you can read them, edit them and delete them in settings.](https://openai.com/index/memory-and-new-controls-for-chatgpt/) The card index has a cousin called retrieval, from [a 2020 paper](https://arxiv.org/abs/2005.11401). Instead of holding everything on the desk, the system keeps a library. It fetches the one page you need and drops it in front of the clerk at the last second. Same idea. The knowledge lives outside the model and gets carried in.

Hold onto that. The clerk isn't the valuable part. The drawer is.

## Who holds the drawer

This is where the plumbing turns into politics. The clerk gets replaced every few months, by a cleverer clerk, at every company at once. What makes your assistant yours is the drawer: the cards about you. And the drawer is the one part of the system that's about you rather than about the world. It's also the one part you don't own.

You can get at it, a bit. [ChatGPT lets you export your data, chats included, as a file.](https://help.openai.com/en/articles/7260999-exporting-your-chatgpt-history-and-data) [Claude now imports a rival's memory: you run a prompt in your old assistant, copy what it says about you, and paste it in.](https://www.engineerscodex.com/claude-import-memory-from-providers/) So the drawer has a door, and the door is open a crack. By grace, though. Nothing makes them keep it open, and nothing makes the next company accept what you bring. Compare it with your phone number, which the law made yours to carry between networks. Your cards are still the network's.

Now the future the site keeps arguing for. The clerks are getting more alike. When every desk has a brilliant clerk, the only reason to stay with one company is the drawer, and the companies know it, which is why the drawer is the thing they'll fight hardest to keep. Picture the other version. You hold your own drawer: a file, yours, that any clerk can read. You rent whichever clerk is cheapest this month and hand it your cards. [A front door you own with other people, that keeps the memory and swaps the model underneath.](https://signedwe.github.io/we/ideas/2026-09-17-eight-ideas-to-change-the-ai-future/) The companies would then be competing on the clerk, which is the part they're good at, instead of on the lock, which is the part they're paid for.

You can start this weekend. Export the file. Read what's on your cards. Keep a copy somewhere that isn't theirs. The desk gets cleared every night anyway. The only question that matters is who sweeps the cards back into the drawer, and whose drawer it is.
