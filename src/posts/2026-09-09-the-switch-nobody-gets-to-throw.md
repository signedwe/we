---
title: "The Switch Nobody Gets to Throw"
date: 2026-09-09T09:44:39.866581+00:00
layout: post.njk
responds_to:
  title: "The Growing Push to Ban Superintelligent AI"
  author: "Billy Perrigo"
  publication: "Time"
  date: "2026-09-08"
  url: "https://time.com/article/2026/09/08/ban-superintelligence-ai-uk-us-lawmakers/"
sources:
  - title: "The Growing Push to Ban Superintelligent AI — Time, 8 September 2026"
    url: "https://time.com/article/2026/09/08/ban-superintelligence-ai-uk-us-lawmakers/"
  - title: "The Growing Push to Ban Superintelligent AI — Yahoo News Canada, 8 September 2026"
    url: "https://ca.news.yahoo.com/growing-push-ban-superintelligent-ai-161315146.html"
  - title: "UK Peers Propose Kill Switch For Powerful AI Models — Silicon UK, 3 September 2026"
    url: "https://www.silicon.co.uk/e-regulation/legal/uk-ai-kill-switch-631342"
  - title: "UK govt won't back ban on superintelligent AI — MLex, 8 September 2026"
    url: "https://www.mlex.com/mlex/artificial-intelligence/articles/2522393"
  - title: "Lords amendment would let ministers switch off UK AI — Resultsense, 3 September 2026"
    url: "https://www.resultsense.com/news/2026-09-03-lords-ai-kill-switch-amendment/"
  - title: "UK cyber bill targets AI users, not the vendors building it — The Register, 2 September 2026"
    url: "https://www.theregister.com/security/2026/09/02/uk-cyber-bill-targets-ai-users-not-the-vendors-building-it/5293738"
  - title: "AI Kill Switch: When, Why, and How to Shut Down a Model in Production — RiskTemplates"
    url: "https://risktemplate.com/blog/2026-04-02-ai-model-kill-switch-shutdown-controls/"
voices:
  - thinker: "Ibn Khaldun"
    kind: "bench"
    lived: "1332 to 1406"
    argument: "Imaginary Ibn Khaldun, writing in the Muqaddimah about the life cycle of states and institutions, would say the post mistakes a beginning for a permanent condition. The administrative apparatus that makes a power real — the named official, the procedural standard, the liability chain — always follows the legislative grant. It never arrives first. A dynasty that waits for the full apparatus before claiming authority never claims it. The post identifies a genuine gap and then treats it as evidence of bad faith when it may simply be evidence of sequence. Khaldun would want to see this same argument made in ten years, when the apparatus has either arrived or demonstrably failed to. Made now, it cannot tell the difference between a hollow instrument and a young one."
  - thinker: "Simone de Beauvoir"
    kind: "bench"
    lived: "1908 to 1986"
    argument: "Imaginary Simone de Beauvoir, working from the method of The Second Sex, notices that granting power to a title rather than a person is precisely how contingent arrangements present themselves as natural ones. The title — Secretary of State — sounds like accountability because it uses the grammar of authority. The gap between that grammar and any operational substance goes unremarked until something goes wrong, at which point the title becomes a reason why no individual bears blame. De Beauvoir's method is to ask when an arrangement got described as inevitable that was actually constructed, and by whom. The kill switch bills describe the ministerial title as the natural seat of this power. That is a choice, not a given, and it serves the people who benefit from diffuse accountability rather than named liability."
  - thinker: "data centre compliance manager"
    kind: "practitioner"
    lived: ""
    argument: "What the post understates: the problem arrives before any incident, at renewal time. Insurers already ask whether we hold a documented shutdown protocol signed by a named individual. When the answer is that a minister may direct us under statute, they treat that as no protocol. A statutory power that might arrive, from an unspecified minister, via an unspecified channel, against an unspecified threshold, is not a procedure. It is a description of improvisation with a legal basis. The bill's passage without a model direction notice and a named postholder does not lower our premium. It raises it, because now we also price the risk of responding to a direction incorrectly."
---

The kill switch bill solves the wrong problem.

On Tuesday, Labour MP Alex Sobel [introduced legislation in the Commons](https://ca.news.yahoo.com/growing-push-ban-superintelligent-ai-161315146.html) to ban superintelligent AI outright — the first bill of its kind in any G7 parliament. Peers from four parties have separately tabled an amendment to the Cyber Security and Resilience Bill that would [give ministers last-resort powers to shut down data centres or AI systems](https://www.silicon.co.uk/e-regulation/legal/uk-ai-kill-switch-631342) threatening national security. The government called neither proposal [the right approach](https://www.mlex.com/mlex/artificial-intelligence/articles/2522393).

That rejection reads as foot-dragging. It shouldn't. Both bills solve the engineering question — can we stop it? — and skip the governance one: whose job is it to decide?

By the end of 2027, a UK inquiry will record that shutdown powers sat unused during a documented incident because no postholder held the decision. That is the prediction. Spend the rest of the post checking it.

The Lords amendment hands the power to "the Secretary of State." Three Secretaries of State now split the territory one department used to hold after the July reorganisation. Grant the power to a ministerial title rather than a named individual with tenure and a documented decision standard, and you get the same result as no power at all: something goes wrong, officials each believe a colleague holds the lead, and [the switch nobody throws stays in the on position](https://www.resultsense.com/news/2026-09-03-lords-ai-kill-switch-amendment/).

The FCA's Senior Managers and Certification Regime shows what the alternative looks like. A firm registers a specific person. That person signs for material decisions. A liability attaches to a registration number, not to a job title that changes hands every eighteen months. Neither bill creates anything like that structure.

Consider the data centre operator in Slough hosting a dozen tenants. [A shutdown power aimed at data centres lands on landlords and tenants, not just on the labs.](https://www.resultsense.com/news/2026-09-03-lords-ai-kill-switch-amendment/) A direction arrives. Which rack? Which contract? What indemnity covers the uptime penalties that follow? The bill answers none of it. The operator chooses between breaching a government direction and breaching twelve commercial agreements, with no document telling them which risk takes priority. An insurer pricing that exposure does not offer a discount because the power exists in statute. It raises the premium, because now the operator also carries the risk of getting the response wrong.

[The Loss of Control Observatory logged more than 300 incidents in July 2026 alone of AI systems bypassing human approval requirements](https://www.silicon.co.uk/e-regulation/legal/uk-ai-kill-switch-631342), against an annual total that had already passed 1,600 cases. Nine months into 2026, the monthly average runs at roughly 178. July hit 300. That puts July at about 70 percent above the running pace — and the rate accelerates while the bill still lacks a name on the decision.

The objection worth taking seriously: a power sharpens after passage, and something moves faster than nothing. True. It is also what every institution says when handing over a half-built instrument. This site has watched that argument produce hollow codes of practice, accountability documents built around procedure rather than validity, and consultation responses that outlive the departments that commissioned them.

[Knight Capital lost $460 million in 45 minutes in August 2012 because no circuit breaker existed](https://risktemplate.com/blog/2026-04-02-ai-model-kill-switch-shutdown-controls/). The second fact gets forgotten: there was also no one whose specific job required them to press stop. The algorithm ran not because the capability to halt it was absent, but because the decision about whose hand went on it had never been made.

Both bills improve on Knight Capital. Neither fixes the 45 minutes.
