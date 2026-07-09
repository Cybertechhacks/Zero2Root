# Level 0 — Foundations

**Target audience:** Absolute beginners, IT graduates, career switchers with no prior security background.

**Goal:** Build the foundational knowledge that every security professional is expected to have by default. These topics will be tested at *every* interview level — a senior interviewing for a principal role can still be asked "explain the TCP handshake." The difference is in the depth and application expected.

---

## What You Will Learn

| Module | What It Covers |
|--------|---------------|
| [Networking Fundamentals](01-networking.md) | TCP/IP, DNS, HTTP/S, TLS, protocols, ARP, firewalls, VLANs |
| [OS Fundamentals](02-os-fundamentals.md) | Linux filesystem, permissions, Windows internals, AD intro, CLI essentials |
| [Core Security Concepts](03-security-concepts.md) | CIA triad, authentication, encryption, hashing, PKI, security controls |
| [Introduction to Pentesting](04-intro-pentesting.md) | Types of tests, methodology, ROE, legal framework, ethics |
| [Interview Q&A — Fresher](05-interview-qa.md) | 40+ questions with three-layer model answers |

---

## Estimated Time

**2–3 weeks** at ~2 hours/day if starting from zero. Don't rush it — every level above builds on this one.

---

## What Interviewers Probe

Interviewers for junior roles will spend 20–30% of the technical round on fundamentals. Common mistakes:

- **Memorizing steps without understanding why** — "SYN, SYN-ACK, ACK" is the right answer but "because TCP needs to establish sequence numbers for reliable ordered delivery and the three steps confirm both sides can transmit and receive" is what gets you the job.
- **Knowing tool names, not what they do at the packet level** — "I used Nmap" vs "Nmap SYN scans work because we send a SYN, receive SYN-ACK, then send RST instead of completing the handshake, so we enumerate open ports without completing a TCP session."
- **Skipping OS internals** — Windows process injection, Linux SUID binaries, and file permission exploitation come up even at junior level.

---

!!! tip "Study Tip"
    After reading each module, close the page and try to explain the concept out loud as if you're in an interview. If you stumble, you don't know it yet — you've only read it.
