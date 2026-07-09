# Level 1 — Junior Pentester

**Target audience:** 0–1 year of experience. Entry-level pentest roles, junior security analyst positions moving into offensive work.

**Goal:** Build the active testing skills that distinguish a security professional from someone who just understands concepts. At this level, you can execute reconnaissance, scanning, and basic exploitation. You understand OWASP Top 10 deeply and can write a professional finding report.

---

## What You Will Learn

| Module | What It Covers |
|--------|---------------|
| [Reconnaissance](01-reconnaissance.md) | OSINT, passive/active recon, Google dorks, Shodan, subdomain enumeration |
| [Scanning & Enumeration](02-scanning-enumeration.md) | Nmap deep dive, service enum (SMB/FTP/SNMP/LDAP), banner grabbing |
| [Vulnerability Assessment](03-vulnerability-assessment.md) | CVSS deep dive, VA methodology, Nessus/OpenVAS, false positives |
| [OWASP Top 10](04-owasp-top10.md) | All 10 categories with mechanics, exploitation, and prevention |
| [Basic Exploitation](05-basic-exploitation.md) | Metasploit, manual SQLi/XSS, password attacks, shells |
| [Report Writing](06-report-writing.md) | Finding format, executive summary, CVSS, evidence, remediation |
| [Interview Q&A — Junior](07-interview-qa.md) | 35+ questions with three-layer model answers |

---

## Estimated Time

**3–4 weeks** at ~2 hours/day if new to active testing. Prioritize lab practice over reading.

---

## What Interviewers Probe

**OWASP Top 10 is the #1 tested area.** Every junior pentest interview asks about it. The mistake candidates make is listing the 10 names without understanding the mechanics. "A03 is Injection including SQL injection" is not an answer — explain the mechanism, write a payload, describe the impact.

**Nmap is the second most tested tool.** Not "what does Nmap do" but: difference between `-sS` and `-sT`, what `-sV` does at the packet level, how NSE scripts work, what timing templates affect.

**Report writing is underestimated.** A surprisingly large portion of junior pentest interviews include "show me a sample finding you've written" or "how would you rate this vulnerability?" The ability to communicate technical findings clearly is what separates hired from not-hired.

---

## Recommended Lab Setup

```bash
# Kali Linux (attacker machine)
# Download from kali.org — VM or native install

# Vulnerable target VMs
# DVWA (Damn Vulnerable Web Application)
# Metasploitable 2 or 3
# VulnHub machines
# HackTheBox starting point machines (free)
# TryHackMe beginner paths (free tier)
```

Every concept in this level should be practiced in a lab, not just read.
