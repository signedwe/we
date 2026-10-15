---
title: "How tokenization works — and why it costs more if you don't speak English"
date: 2026-10-15T07:49:54.326089+00:00
layout: post.njk
tags: [rules, money, machines]
description: "The tokeniser is a pricing tool nobody called a pricing tool. A Yoruba speaker gets 42% of an English speaker's effective context window at the same price. That's 2.38x more per usable token. It came "
search_title: "How AI tokenization works and why non-English speakers pay more per token"
form: technical
form_label: "how it works"
sources:
  - title: "Measuring the Tokenization Premium: A Cost Audit for Underserved Language Communities — TEA benchmark (arXiv 2608.09046)"
    url: "https://arxiv.org/html/2608.09046"
  - title: "Not speaking English to ChatGPT costs you millions of tokens"
    url: "https://kathane.substack.com/p/not-speaking-english-to-chatgpt-costs"
  - title: "How Your LLM Costs 5X More If You Don't Speak English"
    url: "https://medium.com/@programmerraja/how-your-llm-costs-5x-more-if-you-dont-speak-english-e65912a870e0"
  - title: "Large Language Model Tokenizer Bias: A Case Study on GPT-4o (arXiv 2406.11214)"
    url: "https://arxiv.org/html/2406.11214v2"
  - title: "KL3M Tokenizers — BPE algorithm (arXiv 2503.17247)"
    url: "https://arxiv.org/pdf/2503.17247"
  - title: "Qwen Technical Report — vocabulary augmentation (arXiv 2309.16609)"
    url: "https://arxiv.org/pdf/2309.16609"
  - title: "Anything Goes? A Crosslinguistic Study — Turkish word count (arXiv 2502.18795)"
    url: "https://arxiv.org/pdf/2502.18795"
  - title: "An Empirical Study of Tokenization Strategies — BPE history (arXiv 2010.02534)"
    url: "https://arxiv.org/pdf/2010.02534"
  - title: "What Is a Token in AI? (Couchbase)"
    url: "https://www.couchbase.com/blog/what-is-a-token-in-ai/"
  - title: "Tokens Explained: The Currency of Generative AI (SentiSight)"
    url: "https://www.sentisight.ai/tokens-explained-new-currency-of-generative-ai/"
  - title: "Why Non-English Text Costs More Tokens in LLMs"
    url: "https://ai-tldr.dev/learn/llm-fundamentals/tokens-and-tokenization/tokenization-other-languages/"
  - title: "GitHub — karpathy/minbpe: Minimal BPE tokenizer"
    url: "https://github.com/karpathy/minbpe"
voices:
  - thinker: "Karen Spärck Jones"
    kind: "bench"
    lived: "1935 to 2007"
    argument: "Imaginary Spärck Jones looks at the 2.38 figure and sees a spec gap, not a scandal. You wrote inverse document frequency to fix the problem of common words drowning out rare ones. Same idea here. You retrain the vocabulary on balanced data. You publish the efficiency numbers. You price per usable context unit, not per nominal token. Any of her students could build this in a month. Her objection to the post: it treats a missing line in a product spec as though it were something darker. Name the missing line. Ask for it. Asking for a better spec is not the same as writing an indictment."
  - thinker: "Fatema Mernissi"
    kind: "bench"
    lived: "1940 to 2015"
    argument: "Imaginary Mernissi reads the technical framing and finds a familiar move. In her research she found that rules presented as original and neutral were built later, by people, for reasons. The vocabulary came from available data. The tokeniser reflects the corpus. True, true. But the pricing page is updated every quarter. Whoever sets the price knows that a Yoruba speaker gets less context for the same money. They write the page anyway. That is not a hangover from 1994. It is this quarter's decision. The post should end there, not with Philip Gage."
  - thinker: "Ibn Khaldun"
    kind: "bench"
    lived: "1332 to 1406"
    argument: "Imaginary Khaldun finds none of this surprising. Every medium in every period encodes the dominant language cheapest. Manuscripts favoured Arabic. Print favoured Latin, then English. This medium favours the language that filled the corpus first. The correction comes when the group paying more earns enough to be worth serving. The post's prediction is just the cycle running. It will happen. It is not justice. It is commerce finding its own level."
  - thinker: "Cyril Connolly"
    kind: "bench"
    lived: "1903 to 1974"
    argument: "Imaginary Connolly finds the opening sentence the best thing here. Short, flat, arguable. The post earns it in the fourth paragraph and then keeps going for five more. The Yoruba-in-Lagos sentence near the end is the one worth keeping. Put that first. The Karen Spärck Jones paragraph is the second-best thing. Cut the rest by a third."
  - thinker: "software developer building a yoruba-language fintech product in lagos"
    kind: "practitioner"
    lived: ""
    argument: "The 2.38 number is right and I am glad someone wrote it down. What the post misses: the cost problem and the memory problem are not the same problem. We pay more per token, yes. We also hit the context limit faster, so the model forgets earlier in the conversation, so the product feels worse to the user. The English competitor gets better quality at lower cost. Those compound. Prompt compression helps with the memory side. It adds latency. Every workaround is something an English-language team never has to build. The 2.38 is the price. The worse product is the other cost."
---

The tokeniser is a pricing tool. Nobody said so when they built it.

Philip Gage published a data compression trick in 1994. Find the most common pair of characters in a file. Merge them into one symbol. Repeat until the file is smaller. That's it. [Rico Sennrich's team at Edinburgh adapted it for translation in 2016](https://arxiv.org/pdf/2010.02534). OpenAI put it in GPT-2 two years later. Today [every major language model uses the same approach](https://github.com/karpathy/minbpe). And every API call you make is priced by what it produces: tokens.

Here is what a token is. You type a sentence. [A tokeniser breaks it into fragments its vocabulary recognises, assigns each fragment a number, and sends the numbers to the model](https://www.couchbase.com/blog/what-is-a-token-in-ai/). The model never sees your words. It sees a list of integers. It predicts the next integer. Then the next. Then converts back. [Roughly 1,000 tokens equal about 750 English words](https://www.sentisight.ai/tokens-explained-new-currency-of-generative-ai/). You pay per token in, per token out.

The vocabulary learned its fragments from training data. [BPE starts with individual bytes and iteratively merges the most frequent adjacent pairs until it hits a target size](https://arxiv.org/pdf/2503.17247). Frequent pairs become single tokens. Rare ones stay split. So the vocabulary is a map of what the training data looked like. And [about sixty percent of that data was English](https://medium.com/@programmerraja/how-your-llm-costs-5x-more-if-you-dont-speak-english-e65912a870e0).

English gets tight, efficient tokens. Every other language gets cut up.

[A cost audit published in 2026 measured what this does to the context window a speaker actually gets at the same price](https://arxiv.org/html/2608.09046). On GPT-4o: a Yoruba speaker gets 53,951 usable tokens. An English speaker gets 128,000. Same invoice. Tamil speakers get 61,121. Hindi speakers get 74,461.

Here is the sum that does not appear in that paper. Divide 128,000 by 53,951. You get 2.38. A Yoruba speaker pays 2.38 times as much per usable token as an English speaker. Not per word. Per token of context that fits in the window they paid for. The pricing page does not say this. It says the price per token, and the token is the thing doing the dividing.

By the end of 2029, at least one major API provider will publish a tokeniser track built for non-Latin scripts, with pricing tied to actual context efficiency rather than nominal token count. The push will come from Indian and African enterprise customers reading their invoices, not from a fairness argument.

There has been real progress. GPT-4o's vocabulary covers 200,000 tokens against GPT-4's 100,000. [The same Chinese text that took GPT-4 twelve tokens takes GPT-4o two](https://arxiv.org/html/2406.11214v2). The gap for Hindi has shrunk sharply since 2021. [The 2024 tokeniser costs Hindi speakers 1.89 tokens per word; in 2021 it was 6.55](https://kathane.substack.com/p/not-speaking-english-to-chatgpt-costs). English sat at 1.16 both years. It was already optimised. The improvement happened because the gap was so large that fixing it was easy. The remaining 63 percent premium is the hard part.

Languages with rich word forms face a problem that better training data only partly solves. [Turkish has three times the unique word count of English](https://arxiv.org/pdf/2502.18795). Arabic builds thousands of words from three-letter roots. A vocabulary built from frequency will always be thin on these languages unless it was trained on them from the start. [Some models add script-specific tokens on top of a base vocabulary — Qwen added Chinese tokens to improve its compression rate](https://arxiv.org/pdf/2309.16609). That fix costs engineering time and someone has to decide it's worth doing.

[The 2026 audit](https://arxiv.org/html/2608.09046) also found a negative link between a country's development level and the cost of its tokens. The less wealthy the country, the more expensive the same AI call. Nobody designed this. It came out of a compression algorithm that was pointed at whatever text was available in 1994, 2016, 2019, and kept going.

Karen Spärck Jones invented inverse document frequency in 1972. It weights search results by what is rare, not just what is common. It is the thing underneath every search result you have ever seen. She said computing is too important to be left to men. She meant: the people who build the tools choose, in the building, who the tools work well for. The tokeniser is the cleanest case she probably never saw coming. The people who built it were solving compression. Each step inherited what the last one assumed. Now [a documented cost gap is baked into the tool itself](https://ai-tldr.dev/learn/llm-fundamentals/tokens-and-tokenization/tokenization-other-languages/), and the tool is what the invoice charges for.

A Yoruba-language fintech startup in Lagos is not competing against an English-language rival with more money. It's competing against one that gets 2.38 times more compute per pound spent. That gap sits below the product, below the team, below the pitch deck. It lives in the vocabulary file. Philip Gage did not put it there on purpose. The pricing teams who charge per token without adjusting for it are making a choice every quarter they don't change it.
