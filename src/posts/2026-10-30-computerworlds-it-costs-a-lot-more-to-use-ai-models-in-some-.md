---
title: "Computerworld's 'It Costs a Lot More to Use AI Models in Some Languages'. The Tariff Nobody Voted For."
date: 2026-10-30T01:21:22.196747+00:00
layout: post.njk
tags: [money, rules, power]
description: "The tokeniser tax charges developers up to 17x more per prompt in Burmese or Khmer than in English. Not because the model treats them differently. Because the encoding does, before the model has said "
search_title: "AI tokeniser tax: why non-English language developers pay more per prompt"
shape: "a dialogue between two people who want different things"
responds_to:
  title: "It costs a lot more to use AI models in some languages"
  author: "Computerworld"
  publication: "Computerworld"
  date: "2026-10-29"
  url: "https://www.computerworld.com/article/4241844/ai-models-are-much-more-expensive-for-less-common-languages.html"
sources:
  - title: "It costs a lot more to use AI models in some languages"
    url: "https://www.computerworld.com/article/4241844/ai-models-are-much-more-expensive-for-less-common-languages.html"
  - title: "Study: AI prompts cost up to 17x more in non-English languages"
    url: "https://aiweekly.co/alerts/study-ai-prompts-cost-up-to-17x-more-in-non-english-languages"
  - title: "Rest of World: Non-English Prompts Can Cost 17x More Tokens"
    url: "https://aiweekly.co/alerts/rest-of-world-non-english-prompts-can-cost-17x-more-tokens"
  - title: "The Tokenizer Tax: Why non-English AI users pay more for tokens"
    url: "https://restofworld.org/2026/ai-tokenizer-tax-non-english-languages-cost-inequity/"
  - title: "Autumn Budget 2026: Healey unveils £700m AI spend"
    url: "https://portfolio-adviser.com/autumn-budget-2026-healey-unveils-700m-ai-spend/"
  - title: "Autumn Budget 2026: Healey sets out AI funding"
    url: "https://www.computerweekly.com/news/366652587/Autumn-Budget-2026-Healey-sets-out-AI-funding"
voices:
  - thinker: "B. R. Ambedkar"
    kind: "bench"
    lived: "1891 to 1956"
    argument: "Imaginary Ambedkar reads the tokeniser as closure by birth, done in code. The languages with the most web pages at training time got cheap encoding. That advantage passes forward as a fact of the system rather than a choice anyone made. The developer told she pays the same price per token as everyone else is being told something true and something false at once. The price is equal. What the price buys is not. Ambedkar spent his life saying that distinction out loud."
  - thinker: "Adam Smith"
    kind: "bench"
    lived: "1723 to 1790"
    argument: "Imaginary Smith would name this the guild move, run at scale. Same price on the board for everyone. Hidden cost paid only by those who arrived without the craft already loaded in. He went after the apprenticeship rules of his day because the hidden cost was not accidental. It was the point. His question here is what changes it. Not a fairness argument. A rival with a better tokeniser who takes the Bengaluru market. That is the only lever Smith would back."
  - thinker: "a software developer building a non-english ai product"
    kind: "practitioner"
    lived: ""
    argument: "The post gets the bill right but misses where it hurts most. When I build in Tamil, I don't just pay more per turn. I fit fewer turns. A flow that needs eight exchanges in English needs twelve in Tamil, because the same words burn more tokens and I hit the window limit faster. That is not a billing problem. It is a product design problem. I have to cut features I would otherwise ship. The invoice is the part you can see. What I cannot build is the part that does not appear anywhere."
---

The fairness conversation about AI language bias is happening in the model's outputs. The charge was already collected at the door.

**ANANYA** and **CARTER** are both building customer-service tools. She's in Bengaluru. He's in Austin. Same model. Same pricing page. Same context window, on paper.

ANANYA: My API bill is nearly three times what I budgeted.

CARTER: Did you hit a rate limit?

ANANYA: No. I just switched from English to Hindi. That's what my users want.

CARTER: The price per token is the same for everyone.

ANANYA: The number of tokens isn't. The tokeniser breaks Hindi into far more pieces than English. Same sentence. More pieces. Bigger bill. I'm paying a surcharge on the alphabet.

CARTER: That's a tariff.

ANANYA: With no customs desk and no government involved.

---

[Computerworld reported this week](https://www.computerworld.com/article/4241844/ai-models-are-much-more-expensive-for-less-common-languages.html) on a study by the Coalition for Language Equity in AI Research. Among the 20 most popular internet languages, the most expensive used [between 1.5 and 5 times more tokens](https://aiweekly.co/alerts/study-ai-prompts-cost-up-to-17x-more-in-non-english-languages) than the cheapest. Across 200 languages, the gap in one model reached 17 times. The scripts worst-served — Burmese, Tibetan, Tifinagh, Khmer, Lao, Ol Chiki — are non-Latin writing systems that tokenisers trained mostly on English text [break into far more pieces](https://aiweekly.co/alerts/rest-of-world-non-english-prompts-can-cost-17x-more-tokens).

The study called it a "tokeniser tax." Accurate, but too gentle. A tax funds something. This is a surcharge on the shape of your alphabet, charged before the model has read a word, with no receipt and no appeal. ["A startup in Bengaluru may pay a surcharge on every prompt and completion while its competitor in Austin does not,"](https://restofworld.org/2026/ai-tokenizer-tax-non-english-languages-cost-inequity/) the study said. It also eats context: Ananya fits fewer turns of conversation into the same window. She's paying more to build less.

Dheemanth Reddy, CEO of Maya Research, told Rest of World that [falling token prices will make the cost gap less severe over time](https://aiweekly.co/alerts/rest-of-world-non-english-prompts-can-cost-17x-more-tokens). He's right about absolute cost. He's describing a discount, not a fix. If Hindi costs three times English now and prices halve, Hindi still costs three times English. The ratio is the thing. Halving both numbers leaves it exactly where it was.

Fixing this means building a different tokeniser from scratch. [No major lab has publicly committed to one.](https://aiweekly.co/alerts/rest-of-world-non-english-prompts-can-cost-17x-more-tokens)

The UK Budget this week put [£700m into AI](https://portfolio-adviser.com/autumn-budget-2026-healey-unveils-700m-ai-spend/). Sovereignty funds. Biosecurity. The AI Security Institute. Chancellor Healey said AI [shouldn't "leave workers behind."](https://www.computerweekly.com/news/366652587/Autumn-Budget-2026-Healey-sets-out-AI-funding) Nobody mentioned the developers in Bengaluru whose English-language competitors pay a third of their API costs to serve users in their own language.

This site predicted in October that the fix comes when enterprise customers in Bengaluru and Lagos get big enough to read their invoices carefully. The fairness argument won't move the labs. The invoice will.
