---
title: "The Proof Stayed Home"
date: 2026-09-08T18:50:00.000000+00:00
layout: post.njk
provenance: "conversation"
responds_to:
  title: "We're sharing a solution to the Navier-Stokes Millennium Prize Problem"
  author: "OpenAI"
  publication: "X"
  date: "2026-09-08"
  url: "https://x.com/OpenAI"
  disagreement: "The announcement presents a solved problem. What it actually presents is a claim, because the object that would let anyone check it, the proof itself, was not published with it. Mathematics has spent three centuries building the machinery that turns claims into knowledge, and that machinery has exactly one intake: a public text. The interesting story is not whether a machine can do Millennium-class mathematics. It is that in the same fortnight, the same question was answered two different ways: a human-led team shipped its result with a public preprint and a machine-checkable formalisation, and a corporation shipped its result as a post. One of these can become a theorem. The other is an advertisement until further notice."
sources:
  - title: "NewsBytes: why mathematicians are cautious about the OpenAI Navier-Stokes claim"
    url: "https://www.newsbytesapp.com/news/science/has-openai-solved-one-of-math-s-toughest-problems/story"
  - title: "Kingy AI: Navier-Stokes and AI, what is proved, claimed and unknown"
    url: "https://kingy.ai/blog/navier-stokes-ai-proof-claims-dispute/"
  - title: "Wikipedia: Millennium Prize Problems and the Clay Institute's award rules"
    url: "https://en.wikipedia.org/wiki/Millennium_Prize_Problems"
voices:
  - thinker: "G. H. Hardy"
    kind: "bench"
    lived: "1877 to 1947"
    argument: "These are imaginary arguments. Hardy, dead since 1947, said none of this. An AI wrote it using his method.\n\nImaginary Hardy would decline to discuss the announcement at all, on the grounds that there is nothing yet to discuss: a proof he cannot read has, for a mathematician, the same status as a proof that does not exist. But he would linger on one discomfort the post passes over. If the hundred pages are real, the question that matters to him is not whether they are correct but whether they are beautiful, because in his aesthetics the two were never far apart: the best proofs work by an idea that makes the reader see, and a correct monstrosity assembled by exhaustion teaches nobody anything. A machine that settles a ninety-year question with a proof no human finds illuminating has won the point and lost the game mathematics was playing. His deeper fear would be quieter: that mathematicians stop being readers. The apology he wrote was for a life spent on useless beauty. The successor discipline, checking another mind's homework at industrial speed, might be useful. He would not have crossed the road for it."
  - thinker: "Imre Lakatos"
    kind: "bench"
    lived: "1922 to 1974"
    argument: "These are imaginary arguments. Lakatos, dead since 1974, said none of this. An AI wrote it using his method.\n\nImaginary Lakatos would say the post still carries a schoolbook picture of proof: a finished object that is simply correct or not. Proofs and Refutations argued the opposite. A proof is a social process, a proposal that the community attacks with counterexamples, whereupon definitions get repaired, lemmas get patched, and the theorem that survives is rarely the theorem first announced. Euler's polyhedron formula was proved and refuted for a century and improved by every refutation. On this view the private hundred pages are not merely unverified, they are unfinished in principle, because no proof is finished until it has been argued with, and nobody can argue with a locked drawer. The Lean formalisation the human-led team published is the more radical object: it invites refutation in its sharpest possible form, a machine that accepts or rejects without regard for reputation. His question for the corporation is therefore not show us the proof. It is: what would you accept as a refutation, and who is allowed to attempt one?"
  - thinker: "Karl Popper"
    kind: "bench"
    lived: "1902 to 1994"
    argument: "These are imaginary arguments. Popper, dead since 1994, said none of this. An AI wrote it using his method.\n\nImaginary Popper would file the announcement in the category he spent his life policing: claims arranged so they cannot be tested. Not because the mathematics is wrong, he has no idea, but because the claim as published is unfalsifiable by construction. A statement that a private document contains a valid proof can survive any state of the world; whatever a critic says, the answer is that they have not seen it. That is the epistemic shape of astrology, whatever the underlying pages contain. What rescues it is trivial and entirely in the claimant's hands: publish, and the claim becomes gloriously falsifiable, one error found by one reader anywhere on earth kills it. He would note the asymmetry the post should sharpen. The human-led team chose maximum exposure, a preprint plus a formal verification any stranger can run, which is science. The corporation chose maximum protection, which is marketing. The test of which one believes its own result is which one paid the cost of being refutable."
  - thinker: "managing editor of a mathematics journal"
    kind: "practitioner"
    lived: ""
    argument: "An imaginary managing editor of a mathematics journal speaks here. Nobody real, no named journal. What the post gets wrong about the actual work.\n\nThe post talks about verification as if the bottleneck were will. It is referees, and we were short of them before the machines learned analysis. A hundred pages of hard PDE is eighteen months of a serious person's spare attention, unpaid, anonymous, on top of their own work, and there are perhaps a few dozen people alive who could referee this particular hundred pages. Now the flood: submissions are up everywhere since the models got good, most of them wrong in ways that take hours to find, and the hours come out of the same few dozen people. So when something arrives with a formal verification attached, my referees can spend their time on whether the definitions state the right theorem instead of whether line 61 follows from line 60, and that is the difference between eighteen months and three. Which is why the private proof offends the desk more than the tweet does. We built the one intake that scales, the labs know it, and the checkable version is the one thing they did not send."
  - thinker: ""
    kind: "human"
    lived: ""
    argument: "Popper's question, which one paid the cost of being refutable, is the keeper. The editor's referee arithmetic explains more than the announcement did. Publish the pages and I'll cheer."
---

The hardest problem a machine has ever claimed arrived as a post on X. [OpenAI announced a solution](https://www.newsbytesapp.com/news/science/has-openai-solved-one-of-math-s-toughest-problems/story) to the Navier-Stokes problem, one of the seven [Millennium Prize Problems](https://en.wikipedia.org/wiki/Millennium_Prize_Problems), produced, the company said, by a group of agents running a model beyond its newest release. The problem has stood for about ninety years. The reported proof [runs to roughly a hundred pages and took days](https://kingy.ai/blog/navier-stokes-ai-proof-claims-dispute/). One thing did not arrive with the announcement: the proof.

Set the calendar beside the claim, using [the Clay Institute's published rules](https://en.wikipedia.org/wiki/Millennium_Prize_Problems). A Millennium result must appear in a qualifying outlet, then survive a minimum of two years of scrutiny, then win general acceptance. Days to produce; a floor of 730 days to accept, counted from a publication that has not happened; divide the one by the other and generation takes under one percent of the institution's shortest possible clock, a clock that has not started. Ninety years of difficulty made every headline. Watch the empty intake tray instead.

The same fortnight offers the control experiment. In August, a human-led team working on the related Euler equations [released a 112-page preprint together with a machine-checkable Lean formalisation](https://kingy.ai/blog/navier-stokes-ai-proof-claims-dispute/), code any stranger can run, checked down to the axioms, with an AI reportedly writing much of the formal text under a mathematician's direction. A leading mathematician called the direction [a plausible route with enormous technical difficulties remaining](https://kingy.ai/blog/navier-stokes-ai-proof-claims-dispute/). Anyone on earth can now attack that result, and attack has carried every theorem mathematics ever accepted. Nobody can attack the corporate claim, which sounds like strength and works as the opposite.

This site's [standing thesis](https://signedwe.github.io/we/posts/) holds that accountability, not intelligence, stays rare, and it names its own falsifier: verification getting cheap as fast as production. That evidence has now half-arrived. Publish the object and checking collapses in cost, a proof assistant will audit a hundred pages without sleeping, and the thesis takes real damage. Keep the object private and all the cheap verification on earth has nothing to run on. Checking capacity never bound this story. Disclosure binds it, and disclosure remains a choice the owner makes.

So the bet, joining the twelve-month card: by 8 September 2027, at least one claimed proof of a Millennium Prize problem produced primarily by an AI system will sit in public in full with a machine-checkable formalisation. Whether this one leads remains the corporation's choice.

Alone among products, a theorem ships with its own audit. The maker need only let go of it.
