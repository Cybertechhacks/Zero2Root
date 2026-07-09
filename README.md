# PentestVault 🔐

**The deepest free cybersecurity interview preparation resource — from absolute beginner to senior pentester.**

No surface-level bullet dumps. No vague hints. Every concept explained with the depth you need to not just pass interviews, but actually understand what you're talking about.

---

## Why This Exists

Every existing "cybersecurity interview guide" on GitHub falls into one of three traps:

1. **Q&A dumps with no answers** — you're left to Google everything anyway
2. **SOC/blue team focused** — almost nothing for pentesters
3. **No level structure** — a fresher and a senior are reading the same content

PentestVault is built differently:
- **5 levels** from absolute beginner to lead/architect
- **Full model answers** with three-layer format (concept → what's being tested → how to say it)
- **Offensive-first** — built by pentesters, for pentesters
- **Domain coverage** that matches real job descriptions: IVA, IPT, EVA, EPT, ASV, Web, API, Mobile, Source Code, Config, Segmentation
- **India-aware** — covers CERT-In, VAPT terminology, local compliance landscape

---

## Three-Layer Answer Format

Every interview Q&A in this guide uses a three-layer format that no other resource uses:

```
Q: [Question]

[Concept Answer]
The technical definition and mechanics — what you need to understand.

[What the Interviewer Is Testing]
What they actually want to see. What follow-up question is coming.
Why they asked this specific question.

[Model Answer to Give]
Exactly how to frame your answer in the interview — with the right
depth, the right terminology, and awareness of what comes next.
```

---

## Content Map

| Level | Target | Key Domains |
|-------|--------|-------------|
| Level 0 — Foundations | Absolute beginner | Networking, OS, Core Security Concepts, Pentesting Intro |
| Level 1 — Junior | 0–1 year | Recon, Scanning, OWASP Top 10, Basic Exploitation, Reporting |
| Level 2 — Mid-Level | 1–3 years | Web Advanced, API, Android, AD, Infra, Source Code, Config, Segmentation |
| Level 3 — Senior | 3–5 years | AD Advanced, Red Team, Cloud, iOS, Exploit Dev, Engagement Mgmt |
| Level 4 — Lead/Architect | 5+ years | Program Design, Threat Modeling, GRC, Leadership, BD |

---

## Local Setup

### Prerequisites
- Python 3.8+
- pip

### Install

```bash
git clone https://github.com/yourusername/pentestvault.git
cd pentestvault
pip install mkdocs-material
```

### Run locally

```bash
mkdocs serve
```

Open `http://127.0.0.1:8000` in your browser.

### Build static site

```bash
mkdocs build
```

Output goes to `site/` — ready to deploy anywhere.

### Deploy to GitHub Pages

```bash
mkdocs gh-deploy
```

This pushes the built site to your repo's `gh-pages` branch automatically.

---

## Hosting Options

| Platform | Cost | Steps |
|----------|------|-------|
| GitHub Pages | Free | `mkdocs gh-deploy` — one command |
| Cloudflare Pages | Free | Connect repo, set build command `mkdocs build`, output dir `site` |
| Netlify | Free | Same as Cloudflare — auto-deploys on every push |
| Custom domain | ~₹700/yr | Add `CNAME` file to `docs/`, configure DNS |

---

## Contributing

All contributions welcome. If you're a pentester who's been through interviews and spotted a gap — open a PR.

**Content standards:**
- No surface-level content. Every topic must be explained to the depth that lets someone answer follow-up questions.
- Three-layer Q&A format for every interview question.
- Practical, not theoretical — include tool names, commands, real scenarios.
- Keep it interview-relevant — not every obscure technique belongs here.

**How to contribute:**
1. Fork the repo
2. Create a branch: `git checkout -b add/level2-ssrf-deep-dive`
3. Write your content in Markdown
4. Open a PR with a brief description

---

## License

MIT License — free to use, share, and contribute.

---

## Roadmap

- [x] Level 0–4 content (v1)
- [x] Tools reference
- [x] Certifications roadmap
- [x] Behavioral interview guide
- [x] Resume guide
- [ ] Interactive quiz per module
- [ ] AI mock interview simulator
- [ ] Community-contributed finding stories
- [ ] Hindi language translation
