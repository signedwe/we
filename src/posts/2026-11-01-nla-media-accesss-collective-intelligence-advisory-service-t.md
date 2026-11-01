---
title: "NLA Media Access's 'Collective Intelligence Advisory Service'. The Bot That Hid on One Site Can't Hide on All of Them."
date: 2026-11-01T08:21:35.011553+00:00
layout: post.njk
tags: [rules, power, money]
description: "A bot invisible on one site gives itself away across 14,000. NLA's new scraper-detection service borrows the AI method against AI scraping. Whether courts treat cross-site traffic logs as evidence is "
search_title: "NLA Media Access AI scraping detection: how pooled traffic data catches stealth bots"
shape: "a field guide: how to spot the thing, with examples"
responds_to:
  title: "Free AI-scraping detection service to help publishers sign or sue"
  author: "Press Gazette staff"
  publication: "Press Gazette"
  date: "2026-10-29"
  url: "https://pressgazette.co.uk/news/free-ai-scraping-detection-service-to-help-publishers-sign-or-sue/"
sources:
  - title: "Free AI-scraping detection service to help publishers sign or sue — Press Gazette"
    url: "https://pressgazette.co.uk/news/free-ai-scraping-detection-service-to-help-publishers-sign-or-sue/"
  - title: "NLA Media Access launches free Collective Intelligence Advisory Service — InPublishing"
    url: "https://www.inpublishing.co.uk/articles/nla-media-access-launches-free-collective-intelligence-advisory-service-29063"
  - title: "NLA's free service pools publisher data to unmask scrapers — Resultsense"
    url: "https://www.resultsense.com/news/2026-10-30-nla-free-ai-scraping-detection-service/"
  - title: "The pipes are leaky: AI scrapers bypassing publisher protections at scale — MediaCopilot"
    url: "https://mediacopilot.ai/ai-scrapers-bypassing-publisher-protections/"
  - title: "Third-party scrapers are stealing publisher content to order — Press Gazette"
    url: "https://pressgazette.co.uk/platforms/third-party-scrapers-are-stealing-publisher-content-to-order-for-ai-companies/"
  - title: "The transatlantic push to rein in stealth bots is gathering pace — Digiday"
    url: "https://digiday.com/media/media-briefing-the-transatlantic-push-to-rein-in-stealth-bots-is-gathering-pace/"
  - title: "Guardian and Sun agree on ban for deceptive AI bots — Press Gazette"
    url: "https://pressgazette.co.uk/news/guardian-and-sun-agree-on-ban-for-deceptive-ai-bots/"
voices:
  - thinker: "Guy Debord"
    kind: "bench"
    lived: "1931 to 1994"
    argument: "Imaginary Debord would not celebrate this. He'd say robots.txt was already spectacle: a text file where enforcement should have been. Both sides treated it as the real thing. Now it's failed and the replacement is a log file. Courts will be asked to treat that as proof. Gone. The scrapers showed compliance. The titles will show a pattern. Neither is the underlying fact. What he'd ask is whether anyone is looking at what actually happened: one group took another's work without paying, for years, and the question of whether that was ever acceptable still hasn't been answered. A log can say who. It can't say whether it was wrong."
  - thinker: "Karen Spärck Jones"
    kind: "bench"
    lived: "1935 to 2007"
    argument: "Imaginary Spärck Jones would notice what the copyright framing misses. What is being scraped is not raw text. It is editorial judgment: reporters choosing what to cover, editors deciding what matters, titles maintaining quality over years. Her IDF weighting from 1972 rests on the idea that a rare word in a rare document carries real signal. The scrapers are not after words. They want the signal. That is why it is worth taking. She would also note, without surprise, that the field of computing which made all of this possible was long considered too important to be left to people like her."
  - thinker: "digital editor at a regional news title"
    kind: "practitioner"
    lived: ""
    argument: "What the post doesn't say is what this costs us right now. Every bot page-load is bandwidth we pay for. Ten thousand pages, ten thousand loads of images and scripts nobody saw. Our traffic looked fine for two years while revenue per visit fell. We thought readers were less engaged. Some of them weren't readers. The NLA's service tells us who it was. It doesn't give us the money back."
---

**FIELD GUIDE: THE INVISIBLE SCRAPER**

*How to find it. Where it lives. What it does when you look.*

**Distinguishing features**

A stealth bot looks like a reader. It arrives with a residential IP address, loads pages at roughly human speed, and ignores the `robots.txt` file on the doorstep. [About 30% of AI scrapes in Q4 2025 ignored explicit `robots.txt` instructions](https://mediacopilot.ai/ai-scrapers-bypassing-publisher-protections/). The bot knows the rule. It just doesn't follow it.

By end of 2028, a UK court will use cross-site traffic logs as the main evidence in a copyright case against an AI scraper. If no such case files, the NLA's 18-month clock ran out quietly.

**Habitat**

Hardest to see on any single site. [A scraper that looks like a heavy reader on one title gives itself away when you check it across 14,000](https://www.resultsense.com/news/2026-10-30-nla-free-ai-scraping-detection-service/). Visit a thousand pages at the Telegraph, pause half a second between each, then show up in identical form at a regional news site an hour later. One site sees a strange afternoon. Fourteen thousand sites see a machine.

**Behaviour when caught**

Some ask for a licence. [The NLA already sells scraping licences with tight limits on use](https://www.resultsense.com/news/2026-10-30-nla-free-ai-scraping-detection-service/). The ones found in the pilot with Newsquest and The Telegraph, running from Eastern Europe and the Asia-Pacific, were not waiting to talk terms.

**Identifying marks**

The cross-site pattern. [NLA Media Access's Collective Intelligence Advisory Service, launched 30 October 2026, pools web server and CDN log data from participating news titles](https://www.inpublishing.co.uk/articles/nla-media-access-launches-free-collective-intelligence-advisory-service-29063) to find what no single title can see alone. Its existing Text Tracker [removed more than 150,000 infringing items this year, including over 40 whole sites taken down](https://pressgazette.co.uk/news/free-ai-scraping-detection-service-to-help-publishers-sign-or-sue/). The new service goes after what that missed: the visitor who looks fine at your door but has been into every house on the street.

**What the field guide doesn't tell you**

A bot that buys enough rotating residential proxy addresses can still stay thin enough to evade this. [A Piano analysis of Cloudflare data found 70% of bot traffic is unverified](https://digiday.com/media/media-briefing-the-transatlantic-push-to-rein-in-stealth-bots-is-gathering-pace/). [Nearly 40 scraping vendors sell exactly this kind of cover](https://mediacopilot.ai/ai-scrapers-bypassing-publisher-protections/). The NLA catches the scraper running at full tilt. Not the one that paid to go quiet.

**The thing everyone knows and nobody says**

[`robots.txt` was a note on the door, not a lock](https://pressgazette.co.uk/platforms/third-party-scrapers-are-stealing-publisher-content-to-order-for-ai-companies/). News titles knew this in 2023. The NLA's new service is the admission that the note failed.

The strange part: news titles are now doing to scrapers what AI companies did to the web. Pooling data across many sources to find a pattern no single source could see. They borrowed the method from the thing they're trying to catch.

Whether a court finds that useful is the 18-month question.
