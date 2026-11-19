---
title: "How retrieval-augmented generation works: why your AI assistant knows your documents but still gets them wrong"
date: 2026-11-19T01:31:32.299318+00:00
layout: post.njk
tags: [machines, work, rules]
description: "RAG lets AI read your documents before answering. The failures mostly aren't in the AI — they're in how the archive was built, cut up, and left unrefreshed. The model has a safety card. The archive ha"
search_title: "How RAG works: why your AI assistant still gets your documents wrong"
form: technical
form_label: "how it works"
sources:
  - title: "Lewis et al., 'Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks', NeurIPS 2020"
    url: "https://proceedings.neurips.cc/paper_files/paper/2020/file/6b493230205f780e1bc26945df7481e5-Paper.pdf"
  - title: "Staragile: Retrieval-Augmented Generation Complete 2026 Guide"
    url: "https://staragile.com/blog/retrieval-augmented-generation"
  - title: "Eden AI: The 2025 Guide to Retrieval-Augmented Generation"
    url: "https://www.edenai.co/post/the-2025-guide-to-retrieval-augmented-generation-rag"
  - title: "Digital Applied: RAG Failure Modes — Anthropic Contextual Retrieval, September 2024"
    url: "https://www.digitalapplied.com/blog/rag-failure-modes-research-evidence"
  - title: "Barnett et al., Seven Failure Points When Engineering a RAG System, CAIN 2024, via arXiv:2510.13975"
    url: "https://arxiv.org/pdf/2510.13975"
  - title: "Stanford RegLab / Magesh et al. 2024, legal RAG hallucination audit, via robatdasorvi.com"
    url: "https://www.robatdasorvi.com/chapters/ai-agents/rag-is-not-enough-what-retrieval-still-gets-wrong-in-2026"
  - title: "MDPI Mathematics 2025: Hallucination Mitigation for Retrieval-Augmented Large Language Models: A Review"
    url: "https://doi.org/10.3390/math13050856"
  - title: "Atlan: RAG Accuracy Problems — JMIR Cancer study"
    url: "https://atlan.com/know/rag-accuracy-problems/"
  - title: "Semantic Entanglement in Vector-Based Retrieval — chunking failure modes, arXiv:2604.17677"
    url: "https://arxiv.org/pdf/2604.17677"
  - title: "Top Ten AI Agents UK: RAG Explained for UK businesses 2026"
    url: "https://toptenaiagents.co.uk/blog/rag-retrieval-augmented-generation-uk-enterprise-2026.html"
  - title: "Tricky Wombat: RAG as a service — NHS England productivity trial"
    url: "https://www.trickywombat.ai/signals/rag-as-a-service"
voices:
  - thinker: "Elinor Ostrom"
    kind: "bench"
    lived: "1933 to 2012"
    argument: "Imaginary Ostrom points at the index the way she pointed at a fishery. It's a shared resource. One engineer builds it. Dozens of people draw from it daily. No named person carries the duty to restock it when the guidelines change, to notice when a boundary was cut wrong, to pull the outdated chunk from the 2021 handbook. Her irrigation boards had a water-master with defined duties and a schedule. This system has a commit log and a folder last touched in March."
  - thinker: "Simone de Beauvoir"
    kind: "bench"
    lived: "1908 to 1986"
    argument: "Imaginary de Beauvoir would name what gets treated as a background condition. The archive looks neutral. Someone chose which documents to include. A nurse's verbal handover is not in the index. A consultant's typed letter is. That choice passes as a technical default rather than a decision with authors, which is how it avoids being examined or attributed. The post names this correctly, then stops. The more interesting step is asking what knowledge was always structured to be searchable and what was always structured to disappear."
  - thinker: "Mary Douglas"
    kind: "bench"
    lived: "1921 to 2007"
    argument: "Imaginary Douglas would slow down at the chunking step. Every classification system produces anomalies at its edges, and those anomalies reveal the system's assumptions. The orphaned chunk lost context because the document was written around how clinicians record, not how patients present and staff ask. Moving the boundary placement shifts where the orphan appears. It doesn't close the structural mismatch between the two shapes. The post treats chunking as a solvable engineering problem. Douglas would say the mismatch needs naming before the first chunk is cut, not patched after the first wrong answer arrives."
  - thinker: "information architect"
    kind: "practitioner"
    lived: ""
    argument: "What the post misses is that chunking decisions aren't made once and recorded. They're made wrong the first time, patched when someone complains, then patched again when a new document type arrives that breaks the original scheme. The archive I work with has four different chunk sizes in it because three engineers built three pipelines over eighteen months and nobody agreed on a standard. The model doesn't know that. When a query spans the join between two pipeline generations, the answer is wrong. The blame lands on the AI. It's the join."
---

The engineer who cut the documents is two jobs ago. Nobody supervised that decision. It is now determining whether your firm's AI assistant tells the truth.

That is the thing nobody says about retrieval-augmented generation, the technique that lets a language model answer questions about your own documents rather than only about whatever it absorbed during training. Every explainer focuses on the model. The part that decides reliability is the archive underneath it, and nobody has named who answers for that.

By the end of 2027, at least one UK law firm, NHS trust, or financial services firm will face a formal challenge where the archive, not the model, produced the wrong answer. The model vendor has safety documentation. The firm that built the archive has nothing. Put that prediction down and spend the rest of this post earning it.

**What RAG does**

[The term comes from a 2020 NeurIPS paper](https://proceedings.neurips.cc/paper_files/paper/2020/file/6b493230205f780e1bc26945df7481e5-Paper.pdf) that paired a generative model with a separate document store. You ask a question. The system searches that store. It pastes the best-matching chunks into the prompt alongside your question. The model reads those chunks and writes an answer.

[RAG works through five stages](https://staragile.com/blog/retrieval-augmented-generation): index a knowledge base in advance, retrieve relevant data at query time, augment the prompt with that data, generate an answer, refresh the index as new material arrives.

Your solicitor's AI assistant can answer questions about your firm's contracts. Your GP's assistant can answer questions about your trust's clinical guidelines. Those five stages hide the decision that determines everything.

**Chunking: the choice nobody records**

[The retrieval system converts both the query and the knowledge base documents into dense vectors](https://www.edenai.co/post/the-2025-guide-to-retrieval-augmented-generation-rag), lists of numbers representing meaning, then finds the closest match. Before that happens, someone cuts the documents into chunks. Paragraphs, usually. Sometimes sentences.

[On 19 September 2024, Anthropic published "Introducing Contextual Retrieval"](https://www.digitalapplied.com/blog/rag-failure-modes-research-evidence) and named what goes wrong. Once a document splits into chunks, each chunk loses its surrounding context. A paragraph reading "the exception applies where the client notified us in writing" makes sense inside the original contract. Extracted, it's useless: which exception? Notified whom? The vector encodes the orphan. The search never finds it.

[Anthropic measured their own retrieval system and found a 5.7% miss rate](https://www.digitalapplied.com/blog/rag-failure-modes-research-evidence): the right chunk failed to surface in the top twenty results on about one query in eighteen.

**Where the numbers stop adding up**

5.7% sounds survivable. Here's the problem.

[The Stanford RegLab's 2024 audit tested Lexis+AI, Westlaw AI-Assisted Research, and Ask Practical Law AI](https://www.robatdasorvi.com/chapters/ai-agents/rag-is-not-enough-what-retrieval-still-gets-wrong-in-2026) on 200 legal research queries. These tools run on curated legal databases. Custom embeddings. Retrieval stacks built specifically for a domain where a wrong citation ends a career.

[Lexis+AI hallucinated on roughly 17% of queries. Westlaw on more than 33%.](https://www.robatdasorvi.com/chapters/ai-agents/rag-is-not-enough-what-retrieval-still-gets-wrong-in-2026)

Subtract: 17 minus 5.7 leaves 11.3 percentage points. 33 minus 5.7 leaves 27.3. That 11 to 27 point spread has to come from somewhere other than the retrieval miss rate. [Hallucinations in RAG systems arise from two stages: retrieval failure and generation deficiency](https://doi.org/10.3390/math13050856). The sales pitch fixed on the first. The second produced those numbers. When the right chunks land in the prompt but don't quite answer the question, the model writes a confident answer anyway. The retrieval worked. The generation confabulated.

[A 2024 experience report by Barnett and colleagues at Deakin University](https://arxiv.org/pdf/2510.13975), drawn from three deployed systems, named seven failure points. The strangest sits at the end of the list: sometimes the model ignores the retrieved evidence entirely and answers from training weights instead. You built a document lookup. The model decided it already knew.

**The archive decides the answer**

[A JMIR Cancer study ran the same retrieval setup twice](https://atlan.com/know/rag-accuracy-numbers/): once against a curated, domain-specific knowledge base, once against general web search. The curated archive produced 6% hallucination. Web search produced 35%. Same model. Same retrieval setup. The hallucination rate is a property of the archive, not the AI.

So who built the archive? Who cut the documents? Who refreshes it when guidelines change?

In UK law firms, [client confidentiality and Legal Professional Privilege prohibit sending data to public API endpoints](https://toptenaiagents.co.uk/blog/rag-retrieval-augmented-generation-uk-enterprise-2026.html), so firms run self-hosted vector databases within UK borders. The expensive decision isn't the model licence. It's the engineer who chose paragraph-length chunks over page-length ones, included the 2021 version of the compliance handbook, and left before anyone noticed the 2023 update never went in.

[The NHS England trial of Microsoft 365 Copilot across 30,000 staff in 90 organisations](https://www.trickywombat.ai/signals/rag-as-a-service) recovered an average of 43 minutes per worker per day. The retrieval worked because it ran against the knowledge base already living in Microsoft 365, inside existing NHS data rules. The archive was pre-built, structured, and clean. Most new deployments start with a folder of PDFs somebody uploaded last March.

[A 2025 controlled study of four chunking strategies on a clinical decision-support task](https://arxiv.org/pdf/2604.17677) found that retrieval failures dominated when boundary placement didn't match the structure of real queries. The clinical staff were asking questions shaped by how patients present. The documents were structured around how clinicians write. Those two shapes have never matched, and nobody building the index had asked both groups.

**The safety card covers the wrong component**

[Barnett's key finding: validation of a RAG system only becomes possible during operation, and robustness evolves rather than being designed in at the start.](https://arxiv.org/pdf/2604.17677) That means the first sign that the archive was cut wrong is a wrong answer. In a law firm, that wrong answer might name a case that doesn't exist. In a trust, it might cite a drug dosage from guidelines the index never updated.

The model vendor has documentation for all of this. A safety card. An audit trail for the weights. The ICO's AI agents consultation, which closed 20 November 2026, asks who controls the data and who runs the model. It asks nothing about who last updated the vector index or what their refresh schedule was.

The firm that built the archive has the engineer's name in a commit log, if the commit log still exists, and a folder of PDFs last touched in March.

That is the thing the challenge at the end of 2027 will turn on. Not what the model did. What the index missed, when it was last rebuilt, and who was supposed to notice.
