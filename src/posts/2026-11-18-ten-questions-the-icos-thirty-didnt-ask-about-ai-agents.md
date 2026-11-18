---
title: "Ten Questions the ICO's Thirty Didn't Ask About AI Agents"
date: 2026-11-18T01:51:21.373221+00:00
layout: post.njk
tags: [rules, machines]
description: "The ICO's agentic AI call closes Thursday. Thirty questions, one gap: nobody defined what agentic AI is. The code that follows will be built on the undefined thing, hardened by whoever gave the most c"
search_title: "ICO agentic AI call for evidence closes November 2026: ten gaps in the questions"
form: top_ten
form_label: "top ten"
sources:
  - title: "ICO: Agentic AI call for evidence"
    url: "https://ico.org.uk/about-the-ico/ico-and-stakeholder-consultations/2026/10/agentic-ai-call-for-evidence/"
  - title: "ICO media centre: ICO secures changes from leading AI developers as scrutiny extends to AI agents"
    url: "https://ico.org.uk/about-the-ico/media-centre/news-and-blogs/2026/10/ico-secures-changes-from-leading-ai-developers-as-scrutiny-extends-to-ai-agents/"
  - title: "io-sphere.io: AI Regulation in the UK 2026, agentic AI guidance timeline"
    url: "https://io-sphere.io/guides/ai-regulation-uk-2026"
  - title: "steelwise.uk: The ICO is asking how businesses control AI agents"
    url: "https://steelwise.uk/filings/the-ico-is-asking-how-businesses-control-ai-agents-can-you-answer"
  - title: "PPC Land: UK ICO puts 30 questions to AI agent builders before November 20"
    url: "https://ppc.land/uk-ico-puts-30-questions-to-ai-agent-builders-before-november-20/"
voices:
  - thinker: "Ibn Khaldun"
    kind: "bench"
    lived: "1332 to 1406"
    argument: "Every regulatory cycle begins the same way. The state asks the merchants to describe the trade. The merchants describe it in terms that suit them. The state writes those terms into law. This is not corruption. It is how knowledge moves from the market to the court. The firms filing evidence on Thursday know their own agents better than the ICO does. Their descriptions will be coherent, specific and useful. They will also be the ones that work for their products. The code that follows will reflect that. This is not a failure of the consultation. It is what consultations do."
  - thinker: "Karen Spärck Jones"
    kind: "bench"
    lived: "1935 to 2007"
    argument: "You build the index after you define the terms, not before. I spent years on exactly this problem: if you let people use their own words before you have a controlled vocabulary, you get retrieval noise dressed as evidence. The ICO should have done a taxonomy study first. Run agents, classify what they do, test where the lines fall, then ask the thirty questions. What comes back on Thursday will be thirty different answers about thirty slightly different things. Synthesising that into a code is not impossible. It is just much harder than it needed to be, and the error was made in October, not now."
  - thinker: "data protection officer"
    kind: "practitioner"
    lived: ""
    argument: "We spent three weeks on this. First question our lawyers asked: does a payment agent that still needs a human sign-off for anything over five hundred pounds count as limited supervision? We decided no and left those systems out. Another firm in our sector runs the same setup and filed on it. The post is right that nobody checked whether the definitions matched. What it misses is that we had no choice but to guess. The form was open. The deadline was real. You pick a line and you file. If the code lands somewhere different, you rebuild. That is just compliance."
---

By the end of 2027, the ICO will publish a code that legally binds every company running AI agents on UK personal data. That code will contain a definition of agentic AI. That definition will look almost exactly like the working phrase the ICO used when it opened [the call for evidence](https://ico.org.uk/about-the-ico/ico-and-stakeholder-consultations/2026/10/agentic-ai-call-for-evidence/) in October: AI that carries out tasks with limited supervision. If the code arrives with a substantially different definition, built from what the evidence actually showed, I was wrong.

The portal closes Thursday. Here are the ten gaps nobody is talking about, ranked from awkward to fatal.

**10. What does the first sentence sound like?**
Not the agent's terms and conditions. The sentence it speaks to someone whose data it's about to touch. The call covers transparency. It says nothing about what transparency sounds like at the moment it matters.

**9. What does it keep when you log off?**
The call asks about data security during a session. It says nothing about what the agent holds afterwards: in its settings, the platform's database, or a memory service the deployer never chose to audit.

**8. When your agent calls a service you don't run, whose data is it?**
The themes cover lawfulness of processing. They don't cover what happens when the agent you built calls an API you don't control, carrying personal data you do.

**7. Same inputs tomorrow. Same answer?**
For most agents in production, no. The model version changes. The index it queries changes. The external data it fetches changes. Nobody at the ICO asked whether a firm has tested this, and the code will not require them to have.

**6. If your agent hands off to a second agent, who answers?**
The call assumes a chain short enough to have one answerable party. Most real deployments have three or four layers. At each hand-off, who answers compounds.

**5. What is the lawful basis for reading something the user never sent?**
Agents browse. They fetch. They read things sitting in a user's environment that never entered any session by choice. Lawfulness of processing is a theme. Reading without being asked is not.

**4. What rule is in force right now?**
Agents are running today. [The ICO's agentic AI guidance is due in spring 2027](https://io-sphere.io/guides/ai-regulation-uk-2026). Nothing in the call for evidence creates any duty to describe what firms are doing in the gap before that code exists.

**3. Can a data subject reach the right version of the agent?**
The agent that acted may not exist in the same form when the complaint arrives. It has been updated, the system prompt changed, the company bought. Rights mechanisms are a theme. Whether those mechanisms can reach the version that actually ran is not.

**2. If the outcome surprises the user, is the user the controller?**
They gave the instruction. The agent did something they didn't expect. The gap between the two is where most harm will happen. The call says nothing about where the lawful basis runs out inside that gap.

**1. What does "limited supervision" mean to you?**
Ten firms ran AI agents this year and filed evidence this week. Each legal team read that phrase and drew a line. Each line landed somewhere different. The code will be built from thirty questions about a thing each respondent defined for themselves. When the code is published, the category hardens. The hardening happens from the inside out, set by whoever wrote the most coherent answer, not by whoever asked the question.

The portal closes Thursday night. The code clock starts Friday.
