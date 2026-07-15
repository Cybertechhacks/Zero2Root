# Resume & Portfolio Guide

!!! info "The Fundamental Truth"
    A security resume gets you 30 seconds of attention before the recruiter decides whether to pass it to a technical reviewer. Your job is to make those 30 seconds unambiguous. Depth comes in the interview — the resume just has to get you there.

---

## Format Fundamentals

**Length:** One page for under 5 years of experience. Two pages maximum for 5+ years. No exceptions — security hiring managers read dozens of resumes.

**Format:** Clean, readable, reverse-chronological. PDF only (Word docs lose formatting). Use standard fonts (Calibri, Helvetica, Georgia).

**Sections order:**
1. Name + contact (top)
2. Professional summary (optional but useful for career changers)
3. Certifications (high on the page — this is what gets you past the recruiter filter)
4. Skills (technical, concise)
5. Experience (reverse-chronological)
6. Education (bottom)

**What not to include:**
- Photo (irrelevant in most markets; can introduce bias)

- Date of birth

- Marital status

- "References available on request" (implied)

- Objective statement (replaced by professional summary)

- Every single tool you've ever touched

---

## The Certifications Section

Put this near the top. In security hiring, certifications are often the first filter — especially for recruiters who can't evaluate your technical depth directly.

```
CERTIFICATIONS
─────────────────────────────────────────────
CEH Master                           EC-Council    2023
CRTA (Certified Red Team Analyst)   Altered Security  2023
CNSP                                 SecOps Group  2022
```

**Format:** Certification name | Issuer | Year obtained. No need to include expiry.

If you have in-progress certifications approaching completion: "OSCP — In Progress (Expected Q3 2024)" is acceptable and shows trajectory.

---

## The Skills Section

Don't list every tool you've touched — list what you can actually demonstrate. Group by category.

```
TECHNICAL SKILLS
─────────────────────────────────────────────
Assessment Types:    IVA, IPT, EVA, EPT, ASV, Web App, API, Android Mobile,
                     Source Code Review, Configuration Review, Segmentation Testing

Web & API:          Burp Suite, OWASP ZAP, sqlmap, gobuster, ffuf, nuclei

Infrastructure:     Nmap, Nessus, CrackMapExec, Impacket suite, BloodHound,
                    Wireshark, Metasploit

Mobile:             apktool, jadx, MobSF, Frida, objection, ADB

Active Directory:   BloodHound/SharpHound, Impacket, Rubeus, CrackMapExec

Cloud:              AWS CLI, Scout Suite, basic Azure assessment

Source Code:        Semgrep, Bandit, manual review (Python, PHP, JavaScript, Java)

Scripting:          Python (automation, PoC development), Bash

Platforms:          Kali Linux, Parrot OS, Windows Server 2019/2022

Reporting:          CVSS v3.1, executive summary, technical findings, remediation roadmap
```

**Key principle:** Assessment types listed upfront signal breadth at a glance. This answers the question "what have you actually done?" before they read your experience.

---

## The Experience Section

This is where most security resumes fail — they describe job duties instead of achievements.

**Weak (duties-based):**
```
Security Analyst | XYZ Corp | 2022–Present
• Performed web application penetration testing
• Conducted vulnerability assessments
• Wrote security reports
```

**Strong (achievement-based):**
```
Penetration Tester | XYZ Corp | 2022–Present
• Led 12+ web application assessments for BFSI and e-commerce clients,
  identifying Critical/High findings including SQLi, IDOR, and auth bypass
• Delivered internal penetration tests of AD environments (200–2000 endpoints),
  achieving full domain compromise in 8 of 9 engagements via Kerberoasting
  and ACL abuse — documented and remediated
• Developed reusable reporting templates that reduced average report delivery
  time from 5 to 3 business days
• Conducted Android mobile assessments per OWASP MASTG, including
  certificate pinning bypass and dynamic analysis using Frida and objection
```

**Formula:** [Action verb] + [what you did specifically] + [scale/quantity] + [outcome]

**Strong action verbs:** Led, Identified, Discovered, Developed, Delivered, Conducted, Reduced, Improved, Trained, Automated

---

## Presenting Vexonis / Co-Founder Experience

When you're co-founding a firm while working elsewhere, positioning matters for different audiences.

**For enterprise clients who need to see experience:**
Emphasize the technical work done, clients served, and findings delivered. The fact that it's your own firm is secondary.

```
Co-Founder & Lead Penetration Tester | Vexonis Technologies | 2023–Present
• Co-founded cybersecurity consulting firm offering VAPT, GRC gap assessments,
  and security training services
• Delivered web, mobile, and infrastructure penetration tests for [N] clients
  across BFSI, healthcare, and e-commerce sectors
• Conducted [N]+ assessments covering IVA, IPT, EVA, EPT, ASV, Web, Android
  Mobile, Source Code Review, and Configuration Review
• Authored comprehensive security reports for CISO-level and technical audiences,
  with findings ranging from SQL injection to Active Directory misconfigurations
```

**For startup-friendly employers:** The entrepreneurial angle is a positive signal — shows initiative, business understanding, and ability to manage client relationships.

---

## Quantifying Your Work

Numbers on a security resume are powerful. Think about:

- Number of engagements completed

- Severity of findings (how many Critical/High findings across your career)

- Team size you've worked with or led

- Client size (100-endpoint companies vs 10,000-endpoint enterprises)

- Report delivery time improvements

- Reduction in false positive rate

- Training sessions delivered and attendees

If you don't know exact numbers, use ranges or approximations: "15+ engagements," "100–5000 endpoint environments."

---

## The Professional Summary

Optional but useful if you're changing careers (military to security) or entering a specialized role.

**What to include:** Your specialist angle, years of relevant experience, 2-3 key technical capabilities, what you're looking for.

**Example:**
"Penetration tester with 1.5+ years of hands-on VAPT experience across web, mobile, infrastructure, and GRC assessments. CEH Master and CRTA certified. Former [military branch] with [N] years of operations experience. Seeking senior pentesting role where I can apply deep technical skills and continue developing AD and cloud security expertise."

---

## Portfolio — What to Build

A technical portfolio separates you from candidates with identical credentials.

**Blog:** Document findings from CTFs, HackTheBox, or research (never real clients). Explain the vulnerability, your approach, and what you learned. One genuine, well-written post per month builds a library that interviewers reference.

**GitHub:**
- Custom scripts (Python tools for automation, custom Burp extensions)

- Sanitized methodology checklists

- CTF writeups (with permission/after content is public)

- Contributions to open-source security tools

**HackTheBox/TryHackMe profile:** A visible profile with machine completions shows continuous practice. Some employers ask for your HTB username.

**Vexonis website blog:** Company blog posts establish dual credibility — yours as a technical writer and the firm's as a thought leader.

---

## Common Resume Mistakes in Security

**Listing tools without context:** "Proficient in Metasploit" tells me nothing. "Used Metasploit's EternalBlue module during an IPT engagement to demonstrate RCE on unpatched Windows 7 hosts" tells me something real.

**Vague experience descriptions:** "Performed penetration tests" — what kind? How many? What did you find?

**No certifications or wrong placement:** Certs buried at the bottom after two pages of experience are invisible to the recruiter's 30-second scan.

**Lying or embellishing:** Interviewers probe resume claims deeply. If you list a skill, you will be asked to demonstrate it. List only what you can defend in a technical interview.

**Generic objective statement:** "Seeking a challenging position where I can utilize my skills" — says nothing, wastes space.

**Too much education, too little experience:** If you're a working pentester with 18 months of experience, your CEH and 3 real engagements are worth more than your university thesis. Education goes at the bottom.

**Not tailoring for the role:** A resume for a red team role should lead with AD and evasion experience. A resume for a web app security role should lead with Burp Suite and OWASP experience. One resume fits all is usually sub-optimal.

---

## Tailoring for Different Role Types

**Junior/Associate Penetration Tester:**
Emphasize: breadth of assessment types, tools used, certifications, and learning trajectory (in-progress certs, HackTheBox profile).

**Mid-Level Web Application Tester:**
Emphasize: Burp Suite depth, OWASP expertise, manual testing vs automated, specific findings (auth bypass, IDOR, business logic).

**Internal Security Team (In-house):**
Emphasize: communication with developers and non-technical stakeholders, GRC exposure, remediation tracking, process improvement.

**Red Team / Advanced:**
Emphasize: AD experience, evasion techniques, CRTO/CRTE certifications, engagement management, C2 tool experience.

**Boutique VAPT Firm:**
Emphasize: breadth, client communication, report quality, efficiency, and ability to work independently without hand-holding.

---

## LinkedIn Profile

Your LinkedIn should mirror your resume but with more space for context.

- **Headline:** Not just your job title. "Penetration Tester | CEH Master | CRTA | Web • Mobile • Infrastructure • AD"

- **About:** 3-4 paragraphs — your technical background, specializations, and what you're building toward

- **Featured:** Link to your blog posts, GitHub, or HTB profile

- **Skills section:** List your top 50 technical skills — these drive recruiter search results

- **Recommendations:** Two or three from colleagues or clients carries significant weight

- **Activity:** Share relevant security news, write short posts about recent CTF findings — builds visibility

**For Vexonis:** Listing yourself as Co-Founder is appropriate and positive on LinkedIn. Keep descriptions focused on deliverables and skills, not company-internal details.
