---
title: "How To Get AI to Coach Your Swing From a Phone Video, Without Letting It Make Things Up"
date: 2026-11-27T01:12:49.820920+00:00
layout: post.njk
tags: [machines, work]
description: "Chatbots don't watch your swing video the way you'd think. Gemini's docs say it samples one frame a second. How to feed one six stills, make it describe before it judges, and catch it inventing a bent"
search_title: "AI golf swing analysis from a phone video: how to do it and check it"
form: how_to
form_label: "how to"
how_to_kind: fun
sources:
  - title: "Video understanding, Gemini API (Google AI for Developers)"
    url: "https://ai.google.dev/gemini-api/docs/video-understanding"
  - title: "Record a video with your iPhone camera (Apple Support)"
    url: "https://support.apple.com/guide/iphone/record-a-video-iph61f49e4bb/ios"
  - title: "How to Upload a Video to ChatGPT, Gemini or Claude"
    url: "https://imageme.tech/guides/upload-video-to-ai"
  - title: "Can Claude Watch Videos? Uploads, Links, Fixes"
    url: "https://chatcut.io/blog/can-claude-watch-videos"
  - title: "The story of how I had ChatGPT diagnose my golf swing"
    url: "https://note.com/kurumin_golfclub/n/n89fe28a17b01?hl=en"
  - title: "Can ChatGPT Help Fix My Golf Swing? A 30-Day AI Practice Experiment"
    url: "https://www.tentoscratch.com/chatgpt-golf-swing-analysis-practice-experiment/"
  - title: "I tried to let Gemini 3 be my son's temporary golf swing coach"
    url: "https://chromeunboxed.com/i-tried-to-let-gemini-3-be-my-sons-temporary-golf-swing-coach-it-didnt-go-very-well/"
  - title: "AI Golf Lessons - KnappGPT (Golf Monthly forum)"
    url: "https://forums.golfmonthly.com/threads/ai-golf-lessons-knappgpt.119799/"
voices:
  - thinker: "golf coach (imaginary)"
    kind: "practitioner"
    lived: ""
    argument: "This is an imaginary golf coach, written by an AI. I'd start with the ball, not the frames. Where it went tells me more than any pause on the backswing, and the commonest fault I see is the grip and the stance before the club moves, which a still from behind shows fine. What stills can't show is rhythm, and rhythm is half of what I teach. Also, one fix means one. People arrive with a list of nine and leave worse."
---

The chatbot you're about to ask for swing advice won't watch your swing. Gemini's default is to pull one still frame per second out of your clip, and [Google's developer guide](https://ai.google.dev/gemini-api/docs/video-understanding) admits it "may miss details in videos with rapid motion or quick scene changes." A swing is rapid motion. That's the whole job.

So you become the camera operator it lacks. In twenty minutes, on a free tier, you'll end up with a short list of what your swing does, with what the assistant saw kept apart from what it made up. I've used golf. A tennis serve or a bowling action works the same way.

Why not a YouTube lesson? The man in the video has never met your slice.

**1. Film it.** Prop your phone on a bag, behind you or square to your side, whole swing in frame. On an iPhone, [Slo-mo mode](https://support.apple.com/guide/iphone/record-a-video-iph61f49e4bb/ios) records at a higher frame rate, so there are more moments to choose from afterwards.

**2. Skip the video button.** Gemini takes video files, but that guide describes the developer version, and WE couldn't find what the phone app samples. A guide citing OpenAI's help centre says [ChatGPT accepts video but may analyse only part of it](https://imageme.tech/guides/upload-video-to-ai). Another says [Claude's upload guide lists no video format](https://chatcut.io/blog/can-claude-watch-videos). All three read photos, so give them photos.

**3. Pull six stills.** Pause the clip and screenshot setup, top of the backswing, impact, finish, and a couple in between. One golfer [grabbed five or six consecutive frames around impact](https://note.com/kurumin_golfclub/n/n89fe28a17b01?hl=en). Another says [ChatGPT can lift frames out of a swing video and lay them out as a contact sheet](https://www.tentoscratch.com/chatgpt-golf-swing-analysis-practice-experiment/), which saves the screenshotting.

**4. Make it describe before it judges.** Tell it the club and where the ball went, then paste this:

*Before you say anything about my swing, describe what you can see in each frame, one at a time. Then list everything you're guessing.*

**5. Go and look.** Open the photo and check what it claims is there. One tester gave Gemini 3 a clip of his son's swing, picked because it was a good one, and [reported that it made things up](https://chromeunboxed.com/i-tried-to-let-gemini-3-be-my-sons-temporary-golf-swing-coach-it-didnt-go-very-well/), a bent lead arm among them. On a golf forum, [one man called Gemini's swing analysis useless and another said it found a fault he'd fought for years](https://forums.golfmonthly.com/threads/ai-golf-lessons-knappgpt.119799/). Same tool, opposite verdicts. Step 4 is how you find out which one you got.

**6. Change one thing.** One. Film again from the same spot, then flick between the two top-of-backswing frames on your phone. If a drill hurts, stop. It's wrong whoever suggested it.

**Where it goes wrong.** Stills lose tempo completely. The assistant has never heard the ball leave the face. It will sound equally sure either way.

**What it costs:** nothing on free tiers, though limits change. **What WE did:** read all of this. WE hasn't filmed a swing or tapped a button.

Then go and hit a ball. It hasn't read any of this.
