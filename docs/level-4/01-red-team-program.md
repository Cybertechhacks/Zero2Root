# Red Team Program Design

!!! info "Reference"
    Red team program metrics, staffing, and purple teaming are covered in the [Threat Modeling](02-threat-modeling.md) module. This file covers the operational and reporting side of running a red team program.

---

## Defining Engagement Objectives

A red team without objectives is just noisy. Every engagement must start with specific, measurable objectives derived from what the organization actually wants to know.

**Poor objective:** "Test our security posture."

**Good objectives:**
- "Determine whether an external attacker with no prior access can reach and exfiltrate data from the Finance file share within a 4-week engagement."

- "Assess whether our SOC can detect credential theft and lateral movement within 72 hours of initial compromise."

- "Simulate a ransomware operator's behavior post-initial access and measure containment effectiveness."

Objectives drive scope, tactics, and success metrics. Without them, you can't write a meaningful report.

---

## Engagement Types by Maturity

**Assumed Breach:** The most efficient starting point for organizations new to red teaming. Red team starts with a simulated compromised workstation (e.g., a low-privilege user session inside the network) rather than having to obtain initial access. Tests the response to internal threats without the time cost of initial access phase.

**Full Scope:** Red team must obtain initial access (phishing, external vulnerability exploitation) and then achieve objectives. More realistic, but initial access can consume most of the engagement budget without adding much security insight for internally focused organizations.

**Targeted:** Focus on a specific objective, system, or attack vector (e.g., "Can we breach the OT network from IT?" or "Test our response to a supply chain scenario").

**Continuous Red Teaming:** Ongoing engagement (quarterly or annual rotations) that allows testing across seasonal periods, after major changes, and as the organization's controls mature. Builds a long-term picture of security improvement.

---

## Red Team Report Structure

Red team reports differ from pentest reports. The finding is the attack *path*, not individual vulnerabilities.

```
1. Executive Summary
   - Engagement objectives and outcomes (achieved / not achieved)
   - Overall security posture assessment
   - Key recommendations (strategic level)

2. Engagement Overview
   - Scope, dates, constraints
   - Team structure
   - Rules of engagement

3. Attack Narrative
   - Chronological story of the engagement
   - How initial access was obtained (or attempted)
   - How the team moved through the environment
   - What was achieved vs what was detected
   - Timeline of events

4. Objective Outcomes
   - For each defined objective: achieved / partially achieved / not achieved
   - Evidence and explanation for each

5. MITRE ATT&CK Mapping
   - Heat map showing which techniques were used and which were detected
   - Detection gap analysis

6. Findings (supporting detail)
   - Individual vulnerabilities exploited during the engagement
   - Misconfigurations observed
   - Human factors (who was phished, how)

7. Detection and Response Analysis
   - Which actions triggered SOC alerts?
   - Response time and effectiveness
   - Where detection failed and why

8. Recommendations
   - Technical: specific fixes
   - Process: detection rule improvements, IR playbook gaps
   - People: training needs

9. Purple Team Roadmap (optional)
   - Specific techniques to validate detection in follow-up sessions
```

---

## Deconfliction and Emergency Stop

Every red team engagement needs a clear emergency stop procedure. If the blue team detects activity and initiates a real incident response, the red team must be able to identify themselves to stop unnecessary effort and cost.

**Deconfliction code word:** A pre-agreed word or phrase that red team members can use if contacted by the IR team. "I'm on the red team, the code word is [PHRASE]."

**Authorization letter:** A signed letter from executive authority that the red team member can present (physically or electronically) confirming the activity is authorized.

**Deconfliction hotline:** A phone number for the CISO or security director that both teams have access to — for immediate verification.

**Why this matters:** Without clear deconfliction, an IR team might wipe compromised systems, block red team C2 infrastructure, or escalate unnecessarily — wasting resources and potentially delaying a real incident response in the future.

---

## Measuring Red Team Effectiveness Over Time

A red team program that can't show year-over-year improvement loses executive support. Build measurement in from the start.

### Core Metrics Dashboard

**Dwell time before detection:** Track per engagement. If the red team operated for 3 weeks in Year 1 before the SOC detected them, and 4 days in Year 2, that's a meaningful improvement signal. Goal is not zero — some dwell is expected — but trending downward.

**Objective completion rate:** Of defined objectives per engagement, what percentage were achieved? Year 1: 90% completion (defenses too weak). Year 3: 40% (stronger defenses, detection working). This metric tells you the program is working when the number goes down.

**Technique detection coverage:** After each engagement, map every technique used to MITRE ATT&CK. Which generated alerts? Which didn't? Build a heat map that shows coverage gaps. Year-over-year, this map should show fewer blind spots.

**Mean time to detect (MTTD):** When the red team executed a specific technique, how many minutes/hours elapsed before the SOC raised an alert? Track by technique category. Initial access and execution are usually fastest to detect; lateral movement and credential access are often blind spots.

**Mean time to respond (MTTR):** After detection, how long to contain? A 2-minute detect with a 3-day contain is not a good outcome.

### Annual Program Review

At the end of each program year, produce an annual red team summary for CISO and executive leadership:

```
Red Team Program Annual Summary — FY2024

Engagements completed: 4
Total operator-hours: 480

Objectives achieved: 9 of 23 (39%) — down from 67% in FY2023
Initial access success: 3 of 4 engagements
Domain compromise: 2 of 4 engagements
Data exfiltration: 1 of 4 engagements

Detection metrics:
  Mean dwell time before detection: 4.2 days (down from 18 days in FY2023)
  Fastest detection: 6 hours (phishing simulation)
  Slowest detection: 14 days (supply chain simulation)

ATT&CK coverage: 67 techniques tested
  Detected: 41 (61%) — up from 34% in FY2023
  Not detected: 26 (39%)

Top 5 detection gaps (by risk):
  1. Kerberoasting — no detection (high priority)
  2. LSASS memory access — no detection (high priority)
  3. DCSync — detected but 72h delay (medium priority)
  4. DNS tunneling C2 — no detection (medium priority)
  5. BITS job persistence — no detection (low priority)

Recommendations:
  [Strategic: 3 items]
  [Technical: 8 items]
  [Process: 4 items]
```

This summary demonstrates value, justifies continued investment, and gives the blue team a prioritized improvement roadmap.

---

## Building the Purple Team Capability

Purple teaming is the fastest path to improving detection capability. Once you've done at least one traditional red team engagement, shift toward regular purple team sessions.

### Session Planning

**Select techniques based on risk:** Prioritize ATT&CK techniques associated with the threat actors most relevant to your industry. For a bank, simulate FIN7 or Carbanak TTPs. For critical infrastructure, simulate ICS-targeting groups.

**Pre-session preparation:**
- Red team: document exact command syntax for each technique to be executed

- Blue team: gather relevant detection hypotheses ("we think we detect this via Event ID X")

- Both teams: agree on the execution environment (production vs isolated)

### Session Execution Template

```
Purple Team Session — Credential Access Focus
Date: [Date]
Duration: 4 hours
Techniques: T1003.001, T1558.003, T1110.003

Technique 1: T1003.001 — LSASS Memory Dump
  Red team executes: [specific technique]
  Blue team observes: Sysmon Event ID 10 (ProcessAccess to lsass.exe)
  Result: DETECTED — alert fired 2 minutes after execution
  Alert fidelity: High (minimal false positives)
  Action: Document rule, no change needed

Technique 2: T1558.003 — Kerberoasting
  Red team executes: [specific technique]
  Blue team observes: Event ID 4769 with encryption type 0x17 (RC4)
  Result: NOT DETECTED — no alert generated
  Root cause: SIEM rule exists but threshold too high (30 tickets/hour)
  Action: Lower threshold to 3 RC4 tickets in 5 minutes, retest next session

Technique 3: T1110.003 — Password Spraying
  Red team executes: [specific technique]
  Blue team observes: Multiple 4625 events from single source
  Result: DETECTED — but 45 minute delay
  Root cause: Alert batch aggregation delay
  Action: Reduce alert delay to 5 minutes for this rule
```

### Tracking Improvements

Maintain a detection improvement register:

```
Improvement ID: DI-2024-017
Date Identified: [Purple Team Session Date]
Technique: T1558.003 — Kerberoasting
Original State: No detection
Root Cause: SIEM threshold too high
Action Taken: Lowered threshold, added Kerberoastable account watchlist
Validated: [Retest Date]
Final State: DETECTED — within 3 minutes
```

This register becomes your evidence base for demonstrating program ROI.

---

## Staffing a Red Team

### Role Definitions

**Red Team Lead:** Program strategy, engagement design, client/executive communication, quality review of all work. Typically 5+ years of offensive security experience with strong communication skills. This role spends 40% of time doing technical work and 60% on program management.

**Senior Red Team Operator:** Leads individual engagements, specialized expertise in one or more areas (AD/Windows, cloud, mobile, web). Independently designs and executes complex attack chains. 3-5 years.

**Red Team Operator:** Executes engagements under senior guidance. Works through methodology with coaching. Can independently run focused engagements (web, network). 1-3 years.

**Threat Intelligence Analyst (optional):** Maintains threat actor profiles, tracks TTP evolution, produces intelligence briefs for engagement planning. May be shared with the blue team.

### Minimum Viable Team

For most organizations building an in-house capability:

- **2 operators** is the absolute minimum for any useful red team program — you need at least one person who can review the other's work

- **3-4 operators** allows concurrent engagements and specialization

- **5+ operators** enables a continuous red team program with meaningful coverage

### Skill Matrix for Hiring

```
Core (required for all operators):
□ Network penetration testing (TCP/IP, service exploitation)
□ Active Directory attacks (BloodHound, Kerberoasting, lateral movement)
□ Web application security (OWASP Top 10, manual testing)
□ Report writing and client communication

Specialist tracks (hire for at least one per team):
□ Cloud security (AWS/Azure/GCP attack paths)
□ Physical and social engineering
□ Mobile (Android/iOS)
□ Malware development / payload engineering
□ OT/ICS security

Nice to have:
□ Custom tool development (Python, C#, Go)
□ Threat intelligence analysis
□ Incident response (for blue team perspective)
```

---

## Budgeting a Red Team Program

### In-House Cost Model (Annual, India Market)

```
Personnel costs (per operator, fully loaded):
Junior operator (0-2yr):      ₹8–15L/year
Mid-level operator (2-5yr):   ₹15–35L/year
Senior operator (5+yr):       ₹35–70L/year
Red Team Lead:                ₹60–100L+/year

3-person team example:
1 Lead:                       ₹80L
1 Senior Operator:            ₹45L
1 Operator:                   ₹20L
Total personnel:              ₹1.45 Cr/year

Infrastructure and tooling (annual):
Cobalt Strike license:        ~$5,500/operator/year (~₹4.6L)
Cloud infrastructure (C2):   ₹1–3L/year
Lab environment (AWS):       ₹2–5L/year
Training/conferences:        ₹1–2L/operator/year
Certifications (OSCP, CRTO): ₹1L/operator/year
Total tooling (3-person):    ₹15–25L/year

Total 3-person program:      ₹1.6–1.7 Cr/year
```

### When to Outsource vs Build In-House

**Outsource when:**
- Security program is immature (fix the basics first)

- Budget < ₹1 Cr/year allocated for red team

- Fewer than 500 employees (likely insufficient attack surface to justify dedicated team)

- No mature SOC to test against (red team without blue team feedback is just expensive pentesting)

**Build in-house when:**
- 1,000+ employees in security-sensitive industry

- Existing SOC needs continuous challenging

- Compliance/regulatory requirements mandate internal program

- Long-term commitment to security capability building

- Previous external engagements consistently achieve all objectives (defenses strong enough to warrant internal continuous testing)

**Hybrid (recommended for most):**
- Internal security team runs quarterly purple team exercises

- External firm conducts annual red team assessment

- Internal team handles continuous monitoring and threat hunting

---

## Red Team Technology Stack

### Core Infrastructure

```
C2 Framework (choose one primary):

- Cobalt Strike: Industry standard, expensive, excellent Malleable profiles

- Havoc: Open source, actively developed, good evasion

- Sliver: Open source, multi-protocol, good for training

C2 Infrastructure:

- VPS providers: Vultr, Linode, Hetzner (avoid AWS/Azure/GCP — ASNs are flagged)

- Domain registrar: Namecheap (privacy options), Porkbun

- DNS provider: Cloudflare (free, fast TTL updates)

Redirectors:

- nginx or Apache on VPS

- Cloudflare proxy (masks origin IP, provides SSL)

- AWS CloudFront as domain fronting (policy changes limiting this)
```

### Engagement Tooling

```
Active Directory:

- BloodHound + SharpHound

- Rubeus (Kerberos ticket operations)

- Impacket suite (Linux → Windows protocol)

- CrackMapExec / NetExec

- PowerView

Web Application:

- Burp Suite Professional (non-negotiable)

- Custom nuclei templates

Post-Exploitation:

- Mimikatz (credential extraction)

- Seatbelt (host enumeration)

- SharpHound (AD enumeration)

Custom Development:

- BOF (Beacon Object Files) for Cobalt Strike

- Python for automation

- C# for Windows tooling (less AV detection than PowerShell)
```

### Lab Environment

Every red team needs a lab that mirrors common target environments:

```
Minimum lab:
□ 2-3 Windows Server VMs (DC, member server, workstation)
□ Active Directory domain with realistic configuration
□ Kali Linux attacker VM
□ Team server VM (for C2 practice)

Enhanced lab:
□ Multi-domain AD environment
□ Azure tenant with Entra ID federation
□ AWS account for cloud security practice
□ Vulnerable web applications (DVWA, Juice Shop, WebGoat)
□ Vulnerable Android/iOS apps (DIVA, InsecureBankv2)
□ Packet capture capability (Wireshark on dedicated interface)

Cloud lab options:

- Detection Lab (GitHub) — automated Windows AD lab setup

- BadBlood — populates AD with realistic users and vulnerabilities

- GOAD (Game of Active Directory) — multi-domain AD lab
```

---

## Red Team Capability Maturity Model

Building a red team is a multi-year journey. Set realistic expectations at each stage:

```
Year 1 — Foundation:
Objectives: Build capability, establish methodology, run first engagements
Focus: Standard TTPs, MITRE ATT&CK coverage, reporting excellence
Expected results: Most objectives achieved (low bar — defenses still immature)
Metric: Can we reliably execute a complete attack chain?

Year 2 — Sophistication:
Objectives: Custom tooling, evasion against EDR, cloud coverage
Focus: Evading Defender/CrowdStrike, ADCS attacks, cloud attack paths
Expected results: Mix of successes and detections as defenses mature
Metric: Are we testing techniques that reflect current threat landscape?

Year 3 — Maturity:
Objectives: Threat actor emulation, tight SOC integration, measurable improvement
Focus: Specific threat actor TTPs, purple team cadence, metrics-driven
Expected results: Detection rate improving year-over-year
Metric: Are MTTD and MTTR numbers improving?

Year 5+ — Advanced:
Objectives: Continuous testing, cutting-edge research, program leadership
Focus: Zero-day research, custom implant development, sector threat emulation
Expected results: Program is a recognized internal capability
Metric: Does the program demonstrably reduce organizational risk?
```
