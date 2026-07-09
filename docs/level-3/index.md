# Level 3 — Senior Pentester

**Target audience:** 3–5 years of hands-on penetration testing. Leading engagements independently, mentoring juniors, working on complex AD and red team scope.

**Goal:** At this level you're expected to have deep domain expertise in at least two areas, breadth across all major domains, and the ability to manage an engagement from scoping through reporting with minimal supervision. Interviewers test judgment as much as technique.

---

## What You Will Learn

| Module | What It Covers |
|--------|---------------|
| [Active Directory — Advanced](01-ad-advanced.md) | DCSync, Golden/Silver Tickets, delegation abuse, ADCS attacks, trust exploitation |
| [Red Team Concepts](02-red-team.md) | Adversary simulation, C2 frameworks, OPSEC, living-off-the-land, detection evasion concepts |
| [Cloud Security](03-cloud-security.md) | AWS/Azure/GCP attack paths, IAM privilege escalation, cloud-specific tools |
| [Mobile Security — iOS](04-mobile-ios.md) | iOS architecture, IPA analysis, Frida on iOS, keychain extraction, pinning bypass |
| [Exploit Development Basics](05-exploit-dev.md) | Memory layout, stack buffer overflow, SEH, introduction to ROP concepts |
| [Engagement Management](06-engagement-management.md) | Scoping, ROE, client communication, escalation, post-engagement |
| [Interview Q&A — Senior](07-interview-qa.md) | 30+ questions with three-layer model answers |

---

## Estimated Time

**4–6 weeks** at ~2–3 hours/day. These are the deepest technical topics — expect to spend significant time in the lab for AD advanced and exploit dev.

---

## What Interviewers Probe

**Attack chain thinking:** "Walk me through how you'd go from initial foothold to Domain Admin in an environment where Defender is running and LLMNR is disabled." They want systematic thinking, fallback techniques, and OPSEC awareness.

**Judgment over technique:** "A client's production database went down during your test. What do you do?" The right answer isn't technical — it's about professional responsibility, communication, and minimizing harm.

**Deep specialization:** You should have at least one area you know at publication depth — AD attacks, cloud security, mobile, exploit development. "Tell me something most pentesters don't know about ADCS" is a real senior interview question.

**Red team vs pentest distinction:** If you claim red team experience, you must be able to articulate the philosophy difference — red team is adversary simulation focused on detection and response, not vulnerability enumeration. Confusing these disqualifies you.
