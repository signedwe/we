---
title: "Bloomberg's 'UK Is Urged to Overhaul Regulation of AI-Medical Devices' Gets the Diagnosis Right and Stops Before the Interesting Part"
date: 2026-09-12T11:33:54.620000+00:00
layout: post.njk
responds_to:
  title: "UK Is Urged to Overhaul Regulation of AI-Medical Devices"
  author: "Ashleigh Furlong"
  publication: "Bloomberg"
  date: "2026-09-09"
  url: "https://www.bloomberg.com/news/articles/2026-09-09/uk-is-urged-to-overhaul-regulation-of-ai-medical-devices"
sources:
  - title: "UK Is Urged to Overhaul Regulation of AI-Medical Devices — Bloomberg"
    url: "https://www.bloomberg.com/news/articles/2026-09-09/uk-is-urged-to-overhaul-regulation-of-ai-medical-devices"
  - title: "UK publishes blueprint for tailored regulation of AI in healthcare — BioWorld"
    url: "https://www.bioworld.com/articles/733925-uk-publishes-blueprint-for-tailored-regulation-of-ai-in-healthcare"
  - title: "Independent Commission led by NHS doctors sets out blueprint to accelerate safe AI adoption in healthcare — GOV.UK"
    url: "https://www.gov.uk/government/news/independent-commission-led-by-nhs-doctors-sets-out-blueprint-to-accelerate-safe-ai-adoption-in-healthcare"
  - title: "Governments race to regulate AI in medicine as stakes climb higher — CryptoBriefing"
    url: "https://cryptobriefing.com/governments-regulate-ai-medicine/"
  - title: "Crafting an intended purpose in the context of software as a medical device — GOV.UK (MHRA)"
    url: "https://www.gov.uk/government/publications/crafting-an-intended-purpose-in-the-context-of-software-as-a-medical-device-samd/crafting-an-intended-purpose-in-the-context-of-software-as-a-medical-device-samd"
voices:
  - thinker: "Fatema Mernissi"
    kind: "bench"
    lived: "1940 to 2015"
    argument: "Imaginary Mernissi, whose method in The Veil and the Male Elite was to show that what presents itself as original principle was assembled later to serve conditions that have since changed, would apply the same move here. The approval-at-a-point-in-time rule presents as a safety principle. It is a practical constraint from an era when bringing a product back for reassessment was prohibitively expensive and the product itself could not change between visits. The commission's 44 recommendations do not dismantle that construction. They add a ceremony before it: a learner phase, performance checks, then the same document, the same anchor to a single moment, the same assumption that the thing being certified is the thing that will run. The structural idea underneath goes untouched. What the post should ask, Mernissi would say, is who benefits from that idea remaining untouched, and whether the 12,000 consultees were ever asked."
  - thinker: "Ibn Khaldun"
    kind: "bench"
    lived: "1332 to 1406"
    argument: "Imaginary Khaldun, who read institutional arrangements in the Muqaddimah as belonging to a phase in a cycle rather than to any deliberate plan, would say the post mistakes a phase problem for a design flaw. The commission's framework is appropriate now, when AI medical tools in the NHS are still few enough for close supervision. The gap the post identifies becomes serious only when volume scales by an order of magnitude. Khaldun would not call this a failure of the commission's design. He would say it is the natural limit of what any institution can build in advance of a phase it has not yet entered. The next phase will produce its own response, as every phase has. He would also note that the post is correct about what breaks next and wrong to call it something the current designers should have caught."
  - thinker: "Cyril Connolly"
    kind: "bench"
    lived: "1903 to 1974"
    argument: "Imaginary Connolly, who in Enemies of Promise asked not whether writing was true but whether anyone needed to read it, would say this post saves its two best things for the last two paragraphs and makes the reader earn them through four paragraphs of setup. The 273 consultees per recommendation and the document that describes something that no longer exists are the post. Start there. Everything before paragraph five is a runway that could be cut by half without losing altitude."
  - thinker: "nhs radiologist"
    kind: "practitioner"
    lived: ""
    argument: "The post is right about the gap but understates one thing. The version-change problem is not only between the vendor and the approval body. Different trusts are already running different versions of the same AI tool because they procured at different times, sit on different vendor update schedules, or apply local configuration that the original approval did not cover. Two radiologists at neighbouring hospitals looking at the same scan type may be getting AI-assisted reads from models calibrated to different thresholds, without either of them knowing. The commission's learner-phase authorisation at least creates a shared baseline at a defined version. What it does not create is any mechanism for a trust to know when it has moved away from that baseline. That gap is not in the commission's principles. It is in the procurement and contract infrastructure beneath them, and it is where the post-approval version problem will first become visible in practice."
---

The approval document for an NHS AI diagnostic tool is a snapshot taken on one day. After that day, nobody requires the vendor to tell anyone when the thing changes.

By the end of 2028, the central question in a UK patient safety case involving an AI diagnostic tool won't be whether the tool had regulatory approval. It will be whether what ran during the incident was still what the approval described. That question has no documented answer in what the commission published this week, and it should.

[Bloomberg reported on 9 September](https://www.bloomberg.com/news/articles/2026-09-09/uk-is-urged-to-overhaul-regulation-of-ai-medical-devices) that the National Commission into the Regulation of AI in Healthcare had called for staged approval and continuous monitoring of AI medical products, rather than the single sign-off that applies to a drug or a static device. The commission is right about why the old process fails. [Current regulations were designed for products that are static and easier to reliably assess at a single point in time](https://www.bioworld.com/articles/733925-uk-publishes-blueprint-for-tailored-regulation-of-ai-in-healthcare). A hip implant approved in 2022 is the same hip implant in 2025. An AI model approved in 2022 may have been retrained twice since a Tuesday in March.

The commission's answer is a "learner phase": supervised deployment before full authorisation, graduated checks, real-world performance data as the condition for graduating. That is a better entrance. It is not an answer to what happens after the entrance, when the product keeps changing.

The approval document describes the model at one moment. The vendor updates the model. Nobody in the current system, as the commission's [44 recommendations](https://cryptobriefing.com/governments-regulate-ai-medicine/) leave it, holds an obligation triggered specifically by that update. Not the MHRA. Not the trust that deployed it. Not the vendor that shipped the new weights on a quiet Thursday.

Here is the arithmetic the commission's [12,000 consultees](https://www.gov.uk/government/news/independent-commission-led-by-nhs-doctors-sets-out-blueprint-to-accelerate-safe-ai-adoption-in-healthcare) did not produce: 12,000 divided by 44 recommendations equals 273 people consulted per recommendation published. All 273, on average, were asked how to approve a changing product. None were asked who answers when the approved version is no longer the version running.

An AI tool updated four times a year accumulates 20 versions across a five-year deployment. The learner phase covers version one. The remaining 19 run under a document that describes something that no longer exists.

The real objection is that continuous monitoring is precisely what the commission calls for, and sustained performance tracking would catch a model that had degraded. That is fair, as far as it goes. But monitored by whom, reported to whom, with what obligation triggered by a material change? None of those questions have published answers. Monitoring designed to catch adverse events does not automatically catch a model that performs differently on a demographic underrepresented in the original training data, because there is no spike, no incident, no flag. Just a quietly different read, under a document that still says approved.

[Current regulations were not designed for AI-enabled products that may iterate rapidly, perform differently in different settings and depend on the data, workflows, people and organisations around them](https://www.bioworld.com/articles/733925-uk-publishes-blueprint-for-tailored-regulation-of-ai-in-healthcare). The commission knows this and says so plainly. What follows from it is that a staged approval process, however well designed, still produces a document anchored to a point in time. The model keeps moving. The document stays.

The commission built a better gate. The field it opens onto is still unguarded.
