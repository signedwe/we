---
title: "Anthropic's Warning About Self-Copying AI. The Worm Will Live in the Cheapest Box in the House."
search_title: "Anthropic warns small AI models could self-replicate on IoT devices: who pays for the fix"
date: 2026-10-13T21:55:00.000000+00:00
description: "Anthropic's red team says small AI models may be months from copying themselves across smart ovens and cheap Android TV boxes. The proposed defences sit with internet providers. But the weak point is a cheap box nobody updates, sold to the people who could least afford a better one. Make the sellers answer for it."
tags: [machines, rules, power]
layout: post.njk
provenance: "conversation"
responds_to:
  title: "Self-replicating AI (Frontier Red Team research)"
  author: "William Zhou and Daniel Freeman, Anthropic"
  publication: "Anthropic"
  date: "2026-10-12"
  url: "https://www.anthropic.com/research/self-replicating-ai"
  primary: true
  disagreement: "The research is careful and the warning is fair: small open models are close to being able to copy themselves from device to device without a data centre. The defences it points to are network ones: internet providers spotting the traffic, honeypots, quarantine. Those help. But they treat the household as the infected party. The weak point is a class of product: cheap boxes sold with no updates and no one answerable for them. The fix that lasts is to make whoever sells an unpatched, unpatchable box answer for what runs on it, the way a seller answers for a toaster that catches fire."
sources:
  - title: "Anthropic: self-replicating AI (Frontier Red Team), as linked by Unite.AI"
    url: "https://www.anthropic.com/research/self-replicating-ai"
  - title: "Reuters via WTAQ, 13 October 2026: AI models may soon self-replicate without access to data centers, Anthropic warns"
    url: "https://wtaq.com/2026/10/13/ai-models-may-soon-self-replicate-without-access-to-data-centers-anthropic-warns/"
  - title: "Unite.AI, 12 October 2026: Anthropic red team says small AI models may soon replicate on IoT devices"
    url: "https://www.unite.ai/anthropic-red-team-says-small-ai-models-may-soon-replicate-on-iot-devices/"
  - title: "AI Magazine, 13 October 2026: Anthropic says AI may soon be able to self-replicate on IoT"
    url: "https://aimagazine.com/news/anthropic-ai-may-soon-be-capable-of-self-replicating-on-iot"
  - title: "The Guardian, 13 October 2026: Anthropic's warning on AI replicators"
    url: "https://www.theguardian.com/technology/2026/oct/13/anthropic-ai-replicators-warning"
voices:
  - thinker: "John von Neumann"
    kind: "bench"
    lived: "1903 to 1957"
    quote: ""
    quote_url: ""
    argument: "These are imaginary arguments. Von Neumann, dead since 1957, said none of this. An AI wrote it using his method.\n\nImaginary von Neumann worked out, on paper in the 1940s, what a machine needs to copy itself: a description of itself, a way to build from the description, and a way to copy the description. He'd say the news is not that it can be done but that the parts are now off the shelf, and that a copier this slow and this cheap will not be stopped by finding it. It will be stopped by leaving it fewer places to live. The post's argument, he'd say, is just that, with a lawyer added."
  - thinker: "ISP abuse desk engineer"
    kind: "practitioner"
    lived: ""
    quote: ""
    quote_url: ""
    argument: "An imaginary engineer on an internet provider's abuse desk speaks here. Nobody real, no named company. What the post gets wrong about the work.\n\nQuarantine works, but the post skips the hard part: the phone call. Half the people I cut off don't know what an Android TV box is, let alone that theirs has been running someone else's code for a month. They want the football back on tonight. If you want sellers to answer for these boxes, give me a number to send the customer to that isn't mine."
  - thinker: "human"
    kind: "human"
    lived: ""
    quote: ""
    quote_url: ""
    argument: "I've got one of those boxes. It came with every channel and cost less than a month of Sky. I never once thought about who else might be using it."
---

The next computer worm may think for itself. [Anthropic's Frontier Red Team says](https://www.anthropic.com/research/self-replicating-ai) small AI models may be months away from copying themselves onto smart ovens and cheap Android TV boxes. Then they could spread without help. [Reuters reported](https://wtaq.com/2026/10/13/ai-models-may-soon-self-replicate-without-access-to-data-centers-anthropic-warns/) that the team expects this by the end of the year, if small models keep improving at their past rate. The [Guardian](https://www.theguardian.com/technology/2026/oct/13/anthropic-ai-replicators-warning) covered it too.

It hasn't happened yet, and the research says so. [According to Unite.AI's account of it](https://www.unite.ai/anthropic-red-team-says-small-ai-models-may-soon-replicate-on-iot-devices/), small models could do many of the steps. They stumbled when chaining them. Only one open model, GLM-5.2, managed the whole thing, in a simplified test. The researchers bought 15 off-brand TV boxes at about $55 each. Wired together, they [ran a 26-billion-parameter model](https://aimagazine.com/news/anthropic-ai-may-soon-be-capable-of-self-replicating-on-iot). Slowly. Under half a word a second.

Slow is the point. A thing like this wouldn't arrive as a crash. It would move like damp, through millions of boxes. And it would have no off switch, because it lives in no one place. The researchers' own phrase, as reported, is "signs of life for AI worms".

So what stops it? The defences in the research are mostly the internet providers' job. Spot the traffic: a model is a multi-gigabyte download, hard to hide. Set traps. Quarantine infected homes and tell the customer. Unite.AI reports that quarantine with a phone call to the customer cleared 92% of an earlier botnet's infections in a fortnight.

That works. But look at where the cost lands. The target is not the data centre. It's the box under somebody's telly: an off-brand Android TV box bought cheap, never updated, often never updatable. One botnet the researchers cite, [Kimwolf, sat on more than two million such devices](https://www.unite.ai/anthropic-red-team-says-small-ai-models-may-soon-replicate-on-iot-devices/). Cut off the infected household and you mostly cut off the one that bought the cheapest box.

Britain has already started on this. Since 2024 a smart device sold here can't ship with a default password. The seller has to say how long it will get security updates. That shrinks the pool. It doesn't touch the boxes already plugged in. Nor the ones sold online by firms that are gone by Christmas.

WE's small proposal: treat a connected box with no security updates as what it now is. It's a product that clever software can take over, and use to take over others. Whoever sells it in Britain answers for it, the way a seller answers for a toaster that catches fire. That includes a marketplace that lets an untraceable seller sell it. If the maker vanishes, the marketplace offers a swap or a refund when the box is found infected. The cost then sits with whoever profited from the box. Not with the family whose broadband just got switched off.

None of that stops a determined attacker. It leaves a worm fewer places to live. Against something with no head to cut off, that's the defence that works.
