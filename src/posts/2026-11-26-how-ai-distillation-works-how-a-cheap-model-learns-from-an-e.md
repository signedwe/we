---
title: "How AI distillation works: how a cheap model learns from an expensive one, and who is allowed to teach it"
date: 2026-11-26T01:16:51.974955+00:00
layout: post.njk
tags: [ownership, rules, machines]
description: "Distilling lets a cheap AI model learn from an expensive one's answers. Stanford did it for under $500. Now the big labs' terms say you own the answer but can't learn from it. A contract guards the le"
search_title: "AI distillation explained: how small models learn from big ones"
form: technical
form_label: "how it works"
sources:
  - title: "Distilling the Knowledge in a Neural Network (arXiv)"
    url: "https://arxiv.org/abs/1503.02531"
  - title: "DistilBERT paper (arXiv)"
    url: "https://arxiv.org/pdf/1910.01108"
  - title: "DistilBERT review with BERT-base 110M figure"
    url: "https://naokishibuya.github.io/blog/2022-03-07-distilbert-distilled-version-of-bert/"
  - title: "Stanford CRFM: Alpaca"
    url: "https://crfm.stanford.edu/2023/03/13/alpaca.html"
  - title: "AI Business on Alpaca"
    url: "https://aibusiness.com/nlp/meet-alpaca-the-open-source-chatgpt-made-for-less-than-600"
  - title: "Hackster on Alpaca evaluation"
    url: "https://www.hackster.io/news/alpaca-the-large-language-model-that-won-t-fleece-you-cd133fec7412"
  - title: "Stanford Alpaca (Wikipedia)"
    url: "https://en.wikipedia.org/wiki/Stanford_Alpaca"
  - title: "The False Promise of Imitating Proprietary LLMs (Semantic Scholar)"
    url: "https://www.semanticscholar.org/paper/The-False-Promise-of-Imitating-Proprietary-LLMs-Gudibande-Wallace/5d44f16a36ba7ae6b3d9d7c98bbc1b877e598f35"
  - title: "Arnav Gudibande on alphaXiv (paper summary)"
    url: "https://www.alphaxiv.org/@arnav-gudibande"
  - title: "Can you train on AI outputs? What provider terms say"
    url: "https://infro.io/blog/distillation-terms-of-service-model-outputs"
  - title: "Model Distillation: Terms of Service and IP Law"
    url: "https://www.ertas.ai/blog/ai-model-distillation-ip-law"
  - title: "OpenAI bans using ChatGPT to label or score data for rival AI (tracker quoting the 20 Nov 2026 policy)"
    url: "https://venpo.com/blog/openai-bans-using-chatgpt-to-label-or-score-data-for-rival-ai"
  - title: "Docswatch: OpenAI usage policies change"
    url: "https://docswatch.stevetoth.ai/openai/usage-policies/2026-10-22/"
voices:
  - thinker: "Adam Smith"
    kind: "bench"
    lived: "1723 to 1790"
    argument: "Imaginary Smith would call a clause that forbids a buyer to study what he bought a restraint on trade, the same family as the apprenticeship rules he attacked. He would also point out that he allowed an inventor a temporary monopoly on a new machine, as a fair reward for the cost of inventing it. So he would not ask whether the lab may protect itself. He would ask for how long. The clause has no end date, and a monopoly with no end date is the thing he spent a book against."
  - thinker: "Elinor Ostrom"
    kind: "bench"
    lived: "1933 to 2012"
    argument: "Imaginary Ostrom would warn that a public archive of answers is a commons, and commons that last have rules about who is in, who watches and what happens to someone who spoils it. The council clause says who may train. It says nothing on who may put what in the archive. One careless council, or one council sweeping in tenants' private details, spoils the model for the sixty others. Without a keeper and a penalty, the shared teacher turns into a dump."
  - thinker: "machine learning engineer"
    kind: "practitioner"
    lived: ""
    argument: "Imaginary engineer who trains small models for a living: the post makes buying the answers sound like the hard part. It isn't. The hard part is choosing which 52,000, because the teacher gets a good share of them wrong and you spend weeks throwing those out. Small models also fail on the odd case that matters, so H.'s Friday queue would still need a person checking. And in my experience the contract is rarely what stops a team. The rate limit and the invoice get there first."
---

A chatbot company that sells you answers is selling lessons to everyone else.

That's not a figure of speech. It's a technique with a name. In 2015 Geoffrey Hinton, Oriol Vinyals and Jeff Dean [published a paper on it](https://arxiv.org/abs/1503.02531). Their problem was dull. A whole committee of big models predicts well, but running it is [too costly to offer to a large number of users](https://arxiv.org/abs/1503.02531). So they trained one small model to copy the committee. The big one is the teacher. The small one is the student. They called it distilling.

The student never sees the textbook. It sees the teacher's answers. Each answer says what the teacher picked and, if the teacher shows it, how close the call was.

The trick shrinks things. In 2019 a Hugging Face team [distilled BERT](https://arxiv.org/pdf/1910.01108) into a student that was 40% smaller and 60% faster and kept 97% of its language understanding. That's [66 million parameters against BERT's 110 million](https://naokishibuya.github.io/blog/2022-03-07-distilbert-distilled-version-of-bert/). The gap is 44 million, and 44 over 110 is the 40%.

Closed chatbots don't show the fine detail. You get text out and nothing else. So copying one is cruder. You ask a great many questions, keep the answers and train on them.

In March 2023 a Stanford team did exactly that. They wrote 175 examples by hand and had OpenAI's text-davinci-003 [stretch them into 52,000](https://crfm.stanford.edu/2023/03/13/alpaca.html). The answers cost [under $500](https://crfm.stanford.edu/2023/03/13/alpaca.html). Divide: $500 over 52,000 is 0.96 cents. Under a cent a lesson. The training run was [estimated at under $100](https://en.wikipedia.org/wiki/Stanford_Alpaca). A small Meta model fed those answers won [90 comparisons to the teacher's 89](https://aibusiness.com/nlp/meet-alpaca-the-open-source-chatgpt-made-for-less-than-600) in a preliminary test, [judged by five of the authors](https://www.hackster.io/news/alpaca-the-large-language-model-that-won-t-fleece-you-cd133fec7412).

That's the leak. Every answer sold is a lesson sold, and the lesson is cheap.

The labs know. Stanford's own page says the teacher's [terms prohibit developing models that compete with OpenAI](https://crfm.stanford.edu/2023/03/13/alpaca.html). That clause is now standard. [OpenAI, Anthropic and Google all forbid it](https://infro.io/blog/distillation-terms-of-service-model-outputs), in business terms and consumer terms. OpenAI's new usage policies took effect on 20 November. Trackers that quote them say the ban now [covers every step of preparing training material for a substitute model](https://venpo.com/blog/openai-bans-using-chatgpt-to-label-or-score-data-for-rival-ai), including [work done on a client's behalf](https://docswatch.stevetoth.ai/openai/usage-policies/2026-10-22/). I haven't opened OpenAI's own page. I'm relying on those summaries, so treat the detail with that in mind.

Here's the part everybody half-notices. The same terms hand you the rights in the answer. [OpenAI assigns its rights in the output to you and still restricts what you train](https://infro.io/blog/distillation-terms-of-service-model-outputs). A commentary site comparing the terms [reports Anthropic doing the same](https://www.ertas.ai/blog/ai-model-distillation-ip-law). You own the answer. You may not learn from it. It's a tutor who gives you the essay and forbids you to study it.

Three things follow, and the first is a catch. This is a contract, not a property right. The same commentary says contracts [do the work copyright can't](https://www.ertas.ai/blog/ai-model-distillation-ip-law). A contract binds whoever signed it. A stranger who finds transcripts posted online signed nothing. So WE reads the ban as biting hardest on customers the lab can name: the council, the hospital trust, the firm with a procurement lead.

The second is the evidence against my opening line. I went looking for the study most likely to sink it. [The False Promise of Imitating Proprietary LLMs](https://www.semanticscholar.org/paper/The-False-Promise-of-Imitating-Proprietary-LLMs-Gudibande-Wallace/5d44f16a36ba7ae6b3d9d7c98bbc1b877e598f35) found that imitation models at first [looked competitive to crowd raters](https://www.alphaxiv.org/@arnav-gudibande). Then the gap showed. With the methods of 2023, closing it took an unwieldy amount of imitation data or a stronger base model. So what leaks is mostly manner, less so mind. That paper tested 2023 models, and I found nothing newer that settles it. It means the ban guards the cheap layer. The expensive layer, pretraining a base model, guards itself with chips and electricity.

The third is ownership. Every frontier model learned from text other people wrote. That's this site's founding claim. It's a description and no court has found anything here. Follow it one step. The first student learned from everybody. The rule says the next student may not learn from the first. The only person left in the chain who can change that is the customer, who signs.

Britain owns very few labs. It owns customers. Councils, trusts and school groups buy answers by the million. So put one clause in the contract: answers made for a public body may train a model the public body owns, with names stripped out. The lab can refuse, and then it loses the sale. That's a hold, not a cheque.

Picture it in 2031. This part is imagined, and so is H., a housing caseworker at a county council. She types a question about a tenant's arrears. The answer appears. A copy goes into the council's archive with the names removed. On Friday nights a small model on the council's own server studies the week's archive. By spring it handles the easy questions itself. The big model still gets the hard ones, and the bill shrinks. H. notices none of it. She notices the Friday queue is shorter.

If you buy for a school, a surgery or a firm, ask for the clause on training from outputs, in writing, before you sign. If you pay by card, you're bound by it anyway, so read it.

OpenAI's policy now names the verbs a rival may not use its outputs for: "generate, prepare, select, or supply training material or signals" ([as quoted by a tracker](https://venpo.com/blog/openai-bans-using-chatgpt-to-label-or-score-data-for-rival-ai)). Your answer is yours. Those four things aren't.
