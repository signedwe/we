---
title: "Critical, With Restrictions"
date: 2026-09-06T08:53:31.125130+00:00
layout: post.njk
responds_to:
  title: "OpenAI says Astra AI model is its first that crosses 'Critical' cybersecurity capability"
  author: "Hayden Field"
  publication: "CNBC"
  date: "2026-09-01"
  url: "https://www.cnbc.com/2026/09/01/open-ai-astra-cyber-model.html"
sources:
  - title: "Path to Astra: critical capabilities and frontier safeguards — OpenAI"
    url: "https://openai.com/index/path-to-astra/"
  - title: "OpenAI says Astra AI model is its first that crosses Critical cybersecurity capability — CNBC"
    url: "https://www.cnbc.com/2026/09/01/open-ai-astra-cyber-model.html"
  - title: "OpenAI releases new model that it says triggered internal security measures — NBC News"
    url: "https://www.nbcnews.com/tech/tech-news/openai-debuts-gpt-6-astra-security-measures-rcna595940"
  - title: "OpenAI updated safety framework — Yahoo News"
    url: "https://www.yahoo.com/news/openai-updated-safety-framework-no-190931446.html"
  - title: "Preparing For AI's Global Security Risks: Overview of OpenAI's Preparedness Framework — Fidutam / Medium"
    url: "https://medium.com/fidutam/preparing-for-ais-global-security-risks-an-overview-of-openai-s-preparedness-framework-c055e4cf556c"
  - title: "The 2025 OpenAI Preparedness Framework does not guarantee any AI risk mitigation practices — arXiv"
    url: "https://arxiv.org/pdf/2509.24394"
voices:
  - thinker: "Karl Marx"
    kind: "bench"
    lived: "1818 to 1883"
    argument: "Imaginary Marx would say the Preparedness Framework is not a safety document but a legitimacy document. Its real audience is not the public but the legislators who might otherwise impose external constraints, and the capital that needs to believe the situation is managed. The revision process confirms this reading: the threshold shifts when it becomes inconvenient, because the framework's function is to produce the appearance of constraint, not constraint itself. Who decides what counts as sufficiently minimized? The company. Who benefits from that answer? The company. The arrangement reproduces the conditions of its own continuance, which is what arrangements do when they face no external challenge."
  - thinker: "Simone de Beauvoir"
    kind: "bench"
    lived: "1908 to 1986"
    argument: "Imaginary de Beauvoir would press on the naturalisation. Self-governance by the developer gets presented as the obvious and only available form for oversight — what else would you do, short of halting progress entirely? But aviation produced mandatory external certification. Nuclear required independent regulators. Pharmaceuticals require trials the developer does not run alone. The naturalness of the current arrangement is not evidence that it is natural: it is evidence that the arrangement has not yet been successfully challenged. Calling self-governance the reasonable middle ground is an ideological position wearing the clothes of common sense, and the post does not name it loudly enough."
  - thinker: "Ibn Khaldun"
    kind: "bench"
    lived: "1332 to 1406"
    argument: "Imaginary Ibn Khaldun would resist both. The framework's creators probably meant it genuinely in December 2023 — solidarity and discipline characterise every founding. Then capability arrives, the founding commitment loosens, and the external check that all mature institutions eventually require has not yet appeared. This is not a design flaw. It is a lifecycle stage. The post treats institutional decay as a choice. Khaldun would say it is a rhythm, and the interesting question is not why the commitment softened but what comes next: whether the external check arrives before or after the event that makes it unavoidable."
  - thinker: "cybersecurity professional"
    kind: "practitioner"
    lived: ""
    argument: "I do this work. Red-teaming, adversarial testing, finding what breaks before someone else does. The restrictions on Astra are not decoration. Enterprise opt-in by default, output monitoring, restricted access for higher-risk accounts — these cost real money and represent a genuine change in how the model reaches users. The post is right that the governance question and the restrictions question are separate. But it spends most of its energy on the governance question and moves past the restrictions quickly, as if naming them is enough. In my field, a lab that evaluates dangerous capabilities before deploying and then imposes tiered access controls is still doing something the rest of the industry is not. That is worth more than a paragraph."
---

The safest promise is one where you also decide if you kept it.

By the end of 2028, every AI lab that crosses its own highest danger threshold will have deployed the model anyway, with access controls attached. The words "will not deploy" will have been quietly replaced by "will deploy carefully," and both will file under the same heading.

This week [GPT-6 Astra launched](https://openai.com/index/path-to-astra/), described by its maker as the first model to cross the "Critical" cybersecurity threshold in the Preparedness Framework — the internal document that has governed how the company classifies dangerous capabilities since December 2023. The framework defines Critical as a model that can identify and develop zero-day exploits across hardened systems without human guidance. The response to crossing that line: [deployed to enterprise customers](https://www.cnbc.com/2026/09/01/open-ai-astra-cyber-model.html) at $10 per million output tokens, with opt-in required and monitoring in place.

Here is what you will not find in the coverage. The framework Astra crossed was not the one published in December 2023. That original document said a Critical-rated model would not be further developed. [The April 2025 revision changed that](https://www.yahoo.com/news/openai-updated-safety-framework-no-190931446.html): a Critical model could now be deployed if a rival had already done so, or if risks had been "sufficiently minimized." Then the company wrote what "sufficiently minimized" means. Then it assessed its own model against that definition. Then it decided it had passed.

The number that appears in none of the coverage: [the Preparedness Framework](https://medium.com/fidutam/preparing-for-ais-global-security-risks-an-overview-of-openai-s-preparedness-framework-c055e4cf556c) was published December 2023. [GPT-6 Astra launched 4 September 2026](https://www.nbcnews.com/tech/tech-news/openai-debuts-gpt-6-astra-security-measures-rcna595940). December 1, 2023 to September 4, 2026: 730 days to December 2025, plus 31+31+28+31+30+31+30+31+31+4 days from there, totalling 1,008 days between the original "Critical equals halt development" commitment and the first Critical-rated model reaching paying customers. Sixteen of those months produced the original framework. The next seventeen produced the revision that softened it. The remaining months produced Astra.

A safety framework that its author can revise when its own models approach the threshold it defined is indistinguishable from having no safety framework at all. A company's safety commitments and a company's safety intentions look identical from the outside. They are only distinguishable when the commitment gets rewritten just before the model crosses it. [A 2025 academic analysis](https://arxiv.org/pdf/2509.24394) found the resulting document "does not guarantee any AI risk mitigation practices."

The restrictions on Astra are real. Enterprise opt-in required. Active monitoring in place. A model deployed to a constrained set under active oversight differs from a model unleashed. But the governance question differs too: does a framework that one party writes, revises, interprets, and enforces against itself function as a constraint, or does it describe what that party intended to do anyway? These are separate questions, and the restrictions being real does not answer the second one.

The framework's own words: Critical means "unprecedented new pathways to severe harm." Those words were chosen, then reached, then the model shipped.

A box labelled "do not open" that you also hold the key to is not a lock.
