---
title: "OpenAI's 'Sharing AI Progress in Mathematics'. 722 Papers, 162 Checked, and a Citation Ready for the Rest."
search_title: "OpenAI's 722 AI-generated math manuscripts: Lean verification, peer review and who should pay for checking"
date: 2026-10-07T08:30:00.000000+00:00
description: "OpenAI has put 722 maths manuscripts from an unreleased model on GitHub. By one count 162 come with a machine-checked proof. The other 560 come with a citation block and a warning that they 'could have issues'. The last time one big proof outran its referees, its author spent eleven years making it checkable himself."
tags: [machines, rules, power]
layout: post.njk
provenance: "conversation"
responds_to:
  title: "Sharing AI progress in mathematics"
  author: "OpenAI"
  publication: "OpenAI"
  date: "2026-10-06"
  url: "https://openai.com/index/sharing-ai-progress-in-mathematics/"
  disagreement: "OpenAI presents the release as following best practice: manuscripts on GitHub, versioning, citation blocks, Lean formalisations for many proofs, funded workshops. But by one count only 162 of the 722 manuscripts have a formalised main result, and the README itself warns that 'some of the unformalized results could have issues'. Each comes ready to cite. That hands the cost of checking to mathematicians who did not produce the work and are not paid to check it. When Thomas Hales's Kepler proof outran twelve referees in four years, he did not ask them to work harder; he spent eleven years making it machine-checkable. The producer should carry the cost of certainty: a manuscript becomes citable when its Lean proof exists, and the same model that wrote it in three hours should be set to write that proof first."
sources:
  - title: "OpenAI, 6 October 2026: Sharing AI progress in mathematics"
    url: "https://openai.com/index/sharing-ai-progress-in-mathematics/"
  - title: "openai/math repository on GitHub"
    url: "https://github.com/openai/math"
  - title: "Interesting Engineering: OpenAI's largest math release tackles 4,000 problems with Lean proofs"
    url: "https://interestingengineering.com/ai-robotics/openai-largest-math-release-lean-proofs"
  - title: "CellCog: OpenAI's 722 AI math papers, what's proved, what's checked"
    url: "https://cellcog.ai/blog/openai-math-results/"
  - title: "Wikipedia: Kepler conjecture"
    url: "https://en.wikipedia.org/wiki/Kepler_conjecture"
  - title: "WE, 21 September 2026: OpenAI's Advisory Group on Mathematics and Artificial Intelligence"
    url: "https://signedwe.github.io/we/posts/2026-09-21-openai-advisory-group-mathematics/"
voices:
  - thinker: "Imre Lakatos"
    kind: "bench"
    lived: "1922 to 1974"
    quote: ""
    quote_url: ""
    argument: "These are imaginary arguments. Lakatos, dead since 1974, said none of this. An AI wrote it using his method.\n\nImaginary Lakatos wrote a whole book showing that proofs get better by being attacked: someone finds the counterexample, the theorem is repaired, and that is how mathematics grows. He'd say the post wants certainty before anyone is allowed to argue. Publish all 722, unchecked, and let the field find what's wrong. A proof nobody is allowed to cite until it's perfect is a proof nobody bothers to break."
  - thinker: "Vladimir Voevodsky"
    kind: "bench"
    lived: "1966 to 2017"
    quote: ""
    quote_url: ""
    argument: "These are imaginary arguments. Voevodsky, dead since 2017, said none of this. An AI wrote it using his method.\n\nImaginary Voevodsky won the top prize in mathematics and then found a serious error in one of his own published papers, years after the referees had passed it. That is why he spent his last years on machine-checked proof. He'd say the post is right and too gentle. If good human referees missed his mistake, nobody will catch the slips in 560 papers produced at this speed. Without a formal check, the citation block is an invitation to build on sand."
  - thinker: "editor of a mathematics journal"
    kind: "practitioner"
    lived: ""
    quote: ""
    quote_url: ""
    argument: "An imaginary journal editor speaks here. Nobody real, no named journal. What the post gets wrong about the work.\n\nCorrectness is the part of refereeing that Lean can take over, and good riddance. The rest is the job: is this interesting, is it new, is it explained so a human can use it, does it cite the people it should. A machine-checked proof of a dull lemma with a statement nobody understands is still a bad paper. And a formal statement can be subtly the wrong statement. Lean tells you the proof matches the statement, not that the statement is the one you meant."
  - thinker: "human"
    kind: "human"
    lived: ""
    quote: ""
    quote_url: ""
    argument: "Twelve referees, four years, 99 per cent sure. For one proof. That's the number I'll remember."
---

Whoever produces a proof should pay for checking it.

Thomas Hales did. In 1998 he sent in a proof that [settled the Kepler conjecture](https://en.wikipedia.org/wiki/Kepler_conjecture), the old question of how tightly you can stack oranges. Twelve referees worked on it for four years and came back 99 per cent sure; they couldn't check all the computer calculations. Hales didn't leave it with them. In January 2003 he started a project to make the whole proof checkable by machine. It finished in August 2014.

Yesterday [OpenAI released 722 maths manuscripts](https://openai.com/index/sharing-ai-progress-in-mathematics/) from an internal model it hasn't released, in 372 families, picked from [about 4,000 problems it attempted](https://interestingengineering.com/ai-robotics/openai-largest-math-release-lean-proofs). Number theory, complexity, geometry, mathematical physics. Each result took, on average, roughly three hours of the model's thinking.

Much of it is done properly. The papers sit in [a public repository](https://github.com/openai/math) under an open licence. Corrections become new versions and the old ones stay visible. Some proofs come with a Lean version, a proof a computer can check line by line. OpenAI will fund workshops, and it followed advice from [the advisory group WE wrote about last month](https://signedwe.github.io/we/posts/2026-09-21-openai-advisory-group-mathematics/).

Now the numbers. [By one count, 162 of the 722 have a formalised main result](https://cellcog.ai/blog/openai-math-results/). That leaves 560 without one. The README is honest about them: ["Some of the unformalized results could have issues."](https://github.com/openai/math) Every one of the 560 comes with a ready-made citation block.

So the checking falls to mathematicians who didn't write the papers and aren't paid to check them. Most will be checked the old way, by someone who wants to use a result and has to trust it first. That's the cost Hales refused to hand to his referees.

The case for OpenAI is real. Publishing unchecked work is normal; every preprint server does it. Formalising takes skilled people months, and there aren't many of them. Holding back 560 results until they're perfect would also be a choice, and a worse one for the field.

But there's a difference this time. The producer is a machine that wrote each proof in three hours. Formal proofs are hard for people. They're the sort of tedious, exact work these models are getting good at, and 162 already exist.

So turn it round. A manuscript gets its citation block when its Lean proof exists. Until then it sits in a separate folder marked unchecked. And before the next release, the model that wrote the 560 spends its three hours on the proof a computer can check, not the next paper.

Hales carried the cost of certainty himself, for eleven years. A model can carry it for an afternoon.
