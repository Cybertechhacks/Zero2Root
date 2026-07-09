# Level 2 — Mid-Level Pentester

**Target audience:** 1–3 years of hands-on VAPT experience across web, infrastructure, mobile, and specialized assessments.

**Goal:** At this level you stop being someone who follows methodology and start being someone who *builds* methodology. You understand why techniques work, not just how to run them. You can handle client conversations, manage complex assessments independently, and write findings that stand up to scrutiny from experienced security teams.

---

## What You Will Learn

| Module | What It Covers |
|--------|---------------|
| [Web Application — Advanced](01-web-advanced.md) | Auth bypass, IDOR chains, business logic, XXE, advanced XSS, JWT attacks, CORS, OAuth, deserialization |
| [API Security](02-api-security.md) | OWASP API Top 10, REST/GraphQL/SOAP, BOLA, mass assignment, API fuzzing |
| [Mobile Security — Android](03-mobile-android.md) | Android architecture, OWASP MASTG, static/dynamic analysis, Frida, certificate pinning bypass |
| [Infrastructure Pentesting](04-infrastructure.md) | Internal recon, SMB/LDAP/SNMP deep enum, credential attacks, Responder, relay attacks, pivoting |
| [Active Directory](05-active-directory.md) | AD architecture, Kerberos mechanics, BloodHound, Kerberoasting, AS-REP roasting, Pass-the-Hash |
| [Source Code Review](06-source-code-review.md) | Methodology, taint analysis, dangerous functions by language, SAST tools, manual vs automated |
| [Configuration Review](07-config-review.md) | CIS benchmarks, Linux/Windows/network hardening, cloud configuration review |
| [Segmentation Testing](08-segmentation-testing.md) | Testing methodology, VLAN hopping, firewall rule testing, common failures |
| [Interview Q&A — Mid-Level](09-interview-qa.md) | 35+ questions with three-layer model answers |

---

## Estimated Time

**4–6 weeks** at ~2 hours/day. This level has the most modules — take them one at a time and practice each in the lab before moving on.

---

## What Interviewers Probe

At this level, "I know the concept" is the floor, not the ceiling. Interviewers probe:

**Depth over breadth:** "You said JWT attacks — walk me through the algorithm confusion attack. What's the actual HS256 secret you'd use, and why?"

**Chain thinking:** "You found an SSRF and an IDOR in the same application — how do you chain them for greater impact?"

**Methodology ownership:** "You're scoping an Android assessment for a banking app. What's your testing plan? What tools? What does your setup look like?"

**Real engagement stories:** "Tell me about a finding you're most proud of." They want specifics — what was the application, what was the vulnerability, how did you find it manually when scanners missed it, what was the business impact.

**Your differentiation:** What do you do that a scanner doesn't? The answer should be: chain findings, find business logic flaws, test authentication/authorization in context, identify vulnerabilities in custom code that signature-based tools never catch.
