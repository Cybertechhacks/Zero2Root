# GRC & Compliance

!!! info "Why This Matters"
    GRC (Governance, Risk, and Compliance) is where security meets business. Senior consultants who can conduct gap assessments, speak fluently about compliance frameworks, and translate technical risk into regulatory and contractual obligations are extremely valuable. Many Vexonis-style boutique VAPT firms earn significant revenue from GRC advisory work alongside technical testing.

---

## The GRC Triad

**Governance:** The policies, processes, and decision-making structures that guide how the organization manages security. Security governance answers "who is accountable for what?"

**Risk Management:** Identifying, assessing, and treating risks to information assets. The risk register is the core output — a prioritized list of risks with their likelihood, impact, treatment strategy, and residual risk.

**Compliance:** Demonstrating that the organization meets the requirements of applicable laws, regulations, and standards. Compliance is the floor, not the ceiling — being compliant doesn't mean being secure.

---

## ISO 27001 — Information Security Management System

ISO 27001 is the international standard for Information Security Management Systems (ISMS). It provides a framework for establishing, implementing, maintaining, and continually improving information security.

### Structure

**ISO 27001** (the main standard) defines:
- The ISMS requirements
- Clauses 4–10: context, leadership, planning, support, operations, evaluation, improvement

**ISO 27002** (the controls reference) provides guidance on 93 information security controls organized into 4 themes:
- People controls (8) — screening, training, HR security
- Organizational controls (37) — policies, risk management, incident management
- Technological controls (34) — access control, cryptography, vulnerability management
- Physical controls (14) — physical access, equipment protection

### Gap Assessment Methodology

A gap assessment compares the current state against ISO 27001 requirements:

```
Phase 1: Scoping
- Define the ISMS scope: which business units, locations, systems?
- Identify interested parties: customers, regulators, employees

Phase 2: Document Review
- Review existing security policies, procedures, records
- Check against ISO 27001 clause requirements (4-10)
- Map existing controls to Annex A controls

Phase 3: Interviews
- Interviews with CISO, IT manager, HR, legal, operations
- Assess awareness, training, incident management processes

Phase 4: Technical Assessment (if included)
- Validate that technical controls described in documents are implemented
- Sample testing of access controls, logging, patching

Phase 5: Gap Report
- For each ISO 27001 requirement: Conformant / Partially Conformant / Non-Conformant
- Prioritized remediation plan
- Estimated effort to close each gap
```

### Key ISO 27001 Controls to Know for Interviews

| Control Area | Common Gaps |
|-------------|-------------|
| A.5 — Policies | Policies outdated, not reviewed annually, not communicated |
| A.6 — Organization | No security roles defined, no supplier security |
| A.7 — People | No background checks, no security training, poor offboarding |
| A.8 — Asset Management | No asset inventory, no classification |
| A.9 — Access Control | Excessive privilege, shared accounts, no review |
| A.10 — Cryptography | No encryption policy, weak algorithms |
| A.12 — Operations | No change management, poor patch management |
| A.13 — Network Security | Flat networks, no monitoring |
| A.16 — Incident Management | No incident response plan, no post-incident review |
| A.17 — Business Continuity | No BCP/DR testing |
| A.18 — Compliance | No legal inventory, no compliance reviews |

---

## PCI-DSS — Payment Card Industry Data Security Standard

PCI-DSS applies to any organization that stores, processes, or transmits cardholder data (CHD). Version 4.0 is current (released 2022, mandatory from March 2024).

### PCI-DSS Scope

The key concept is **scope reduction** — minimize the systems that are in-scope for PCI by limiting which systems touch cardholder data.

Cardholder data includes:
- Primary Account Number (PAN) — the 16-digit card number
- Cardholder name, expiration date, service code (sensitive when stored with PAN)

Sensitive Authentication Data (SAD) — **must never be stored after authorization:**
- Full magnetic stripe / chip data
- CVV2/CVC2/CAV2 (the 3-4 digit security code)
- PIN / PIN block

### The 12 PCI-DSS Requirements

```
1.  Install and maintain network security controls
2.  Apply secure configurations to all system components
3.  Protect stored account data
4.  Protect cardholder data with strong cryptography during transmission
5.  Protect all systems against malware
6.  Develop and maintain secure systems and software
7.  Restrict access to system components and CHD by business need-to-know
8.  Identify users and authenticate access to system components
9.  Restrict physical access to cardholder data
10. Log and monitor all access to network resources and cardholder data
11. Test security of systems and networks regularly
12. Support information security with organizational policies and programs
```

### ASV Scanning (Requirement 11.3)

External vulnerability scans must be conducted quarterly by an Approved Scanning Vendor (ASV). The scan must cover all internet-facing IP addresses in scope. A "passing" scan requires no CVSS 4.0+ vulnerabilities without a documented exception.

**Key ASV scan rules:**
- Must be from an external network perspective
- Rescan required if initial scan fails
- ASVs must be on the PCI SSC approved list
- Results must be validated and documented

### PCI-DSS in Pentest Engagements

Requirement 11.4 mandates penetration testing at least annually and after significant changes:
- Must include both network and application layer testing
- Must cover the entire CDE perimeter and critical systems
- Must include segmentation validation testing
- Must follow a defined methodology (OWASP, PTES)

**Segmentation testing** — if the client claims their CDE is segmented from the rest of the network, you must verify this. Failure to properly test and document segmentation is a PCI audit finding.

---

## SOC 2 — Service Organization Control 2

SOC 2 is an auditing standard developed by the AICPA. It's relevant for service providers (SaaS, cloud services, managed services) that handle customer data. Not a certification — it's an auditor's opinion report.

### Trust Service Categories

| Category | What It Covers |
|----------|---------------|
| **Security** (required) | Protection against unauthorized access |
| Availability | System availability meets commitments |
| Processing Integrity | System processing is complete, valid, accurate, timely |
| Confidentiality | Confidential information protected as committed |
| Privacy | Personal information collected, used, retained per policy |

### SOC 2 Type I vs Type II

**Type I:** Point-in-time assessment. "Were the controls suitably designed as of this date?" Faster to obtain — typically 2-3 months.

**Type II:** Period-of-time assessment (typically 6-12 months). "Were the controls operating effectively throughout this period?" More valuable — demonstrates sustained operation, not just a snapshot.

### What Pentesters Need to Know

SOC 2 security requirements for testing context:
- **CC6.1:** Logical access controls — covered by access control assessments
- **CC6.6:** Restrict logical access from outside the entity's boundaries — perimeter security, EPT
- **CC7.1:** Detection of vulnerabilities — regular VA/PT requirement
- **CC7.2:** Monitor for anomalies — logging and monitoring

Many SOC 2 reports include an internal penetration test as evidence for CC7.1. The pentest report is attached as evidence in the SOC 2 audit.

---

## CERT-In — Indian Cybersecurity Regulations

The Indian Computer Emergency Response Team (CERT-In) issued the Information Technology (The Indian Computer Emergency Response Team and Manner of Performing Functions and Duties) Rules, 2013, and more recently the **CERT-In Directions 2022** — a landmark directive affecting all entities in India.

### CERT-In Directions 2022 — Key Requirements

**Mandatory incident reporting** (within 6 hours of detection):
- Data breaches and leakages
- Attacks on critical systems
- Ransomware attacks
- Compromise of critical networks/systems
- Unauthorized access to IT systems

**Log maintenance:**
- ICT infrastructure logs must be maintained for 180 days (6 months)
- Logs must be stored within India
- Must be provided to CERT-In on demand

**Time synchronization:**
- All systems must use NTP time synchronized to NTP server of NPTEL (National Physical Laboratory) or NPL

**KYC and identity verification:**
- Virtual Private Network (VPN) providers must register verified user information for 5 years

**Reporting mechanism:**
- Reports to be filed with CERT-In at incident@cert-in.org.in

### IT Act 2000 — Relevant Sections for Pentesters

As noted in Level 0, pentesters must operate under written authorization. Key sections:
- Section 43: Unauthorized access — civil liability
- Section 66: Unauthorized access with criminal intent — imprisonment up to 3 years
- Section 66C: Identity theft

Authorization must come from the **legal owner** of the systems, not just an IT administrator. The authorization document (Statement of Work) is your legal protection.

---

## Conducting a GRC Gap Assessment

### Engagement Structure

```
Week 1: Kick-off and document collection
- Kick-off meeting with stakeholders
- Collect: existing policies, procedures, previous audit reports, risk register
- Schedule interviews

Week 2-3: Interviews and observations
- CISO/ISSO — overall security program
- IT Operations — patching, monitoring, access management
- HR — background checks, training, onboarding/offboarding
- Legal/Compliance — regulatory inventory, data processing agreements
- Business units — data handling, third-party relationships

Week 3-4: Technical sampling (if included)
- Sample access control reviews
- Review firewall ruleset
- Check vulnerability management records
- Review patch status samples

Week 4: Analysis and reporting
- Map findings against framework
- Prioritize gaps by risk impact
- Draft recommendations
```

### Gap Assessment Report Structure

```
1. Executive Summary
   - Overall compliance posture (% conformant)
   - Critical gaps requiring immediate attention
   - Strategic roadmap overview

2. Scope and Methodology
   - Framework version assessed against
   - What was included/excluded
   - Assessment approach

3. Findings by Domain
   For each requirement:
   - Requirement description
   - Evidence reviewed
   - Finding: Conformant / Partially Conformant / Non-Conformant
   - Gap description (what's missing or inadequate)
   - Risk: High / Medium / Low
   - Recommendation

4. Remediation Roadmap
   - Immediate actions (0-30 days)
   - Short term (30-90 days)
   - Medium term (90-180 days)
   - Long term (180+ days / ongoing program)

5. Appendices
   - Evidence log
   - Interview records (anonymized)
   - Control mapping table
```

---

## Risk Management Basics

### Risk Formula

**Risk = Likelihood × Impact**

Where:
- **Likelihood** = probability that a threat will exploit a vulnerability
- **Impact** = consequence if the risk materializes (financial, operational, reputational, regulatory)

### Risk Treatment Options

**Accept:** Acknowledge the risk and choose not to take action. Appropriate when risk is below tolerance or treatment costs exceed benefit. Must be formally documented and approved.

**Mitigate (Reduce):** Implement controls to reduce likelihood or impact. The most common treatment — patch the vulnerability, implement access controls, add monitoring.

**Transfer:** Share the risk with a third party. Cyber insurance transfers financial impact. Outsourcing to an MSSP shares operational security risk. Note: ultimate accountability cannot be fully transferred.

**Avoid:** Eliminate the activity that creates the risk. Don't store cardholder data → PCI scope elimination. Don't collect unnecessary PII → reduced privacy risk.

### The Risk Register

Every mature security program maintains a risk register. For each identified risk:
```
Risk ID: R-001
Risk Description: Unpatched servers in production
Threat: External attacker exploiting known CVE
Vulnerability: Critical patches not applied within SLA
Asset: Production application servers
Likelihood: High (patches >90 days overdue)
Impact: High (production disruption, data breach)
Inherent Risk: Critical
Treatment: Mitigate — emergency patch deployment within 48 hours
Residual Risk: Medium (after patching, residual config risk remains)
Owner: IT Operations Manager
Target Date: 2024-03-31
Status: In Progress
```

---

## ISO 27001 Controls Reference — Annex A

ISO 27001:2022 organises 93 controls into 4 themes. Knowing these by theme and number signals real ISO expertise.

### Theme A — Organisational Controls (37 controls)

Key controls relevant to security assessments:

| Control | Name | What It Requires |
|---------|------|-----------------|
| A.5.1 | Policies for information security | Documented, approved, communicated security policy |
| A.5.2 | Information security roles and responsibilities | Clear ownership of security responsibilities |
| A.5.7 | Threat intelligence | Process for gathering and using threat intelligence |
| A.5.8 | Information security in project management | Security built into projects from start |
| A.5.15 | Access control | Policy governing who has access to what |
| A.5.16 | Identity management | Process for managing identities through lifecycle |
| A.5.17 | Authentication information | Management of passwords, keys, tokens |
| A.5.19 | Information security in supplier relationships | Third-party security requirements |
| A.5.23 | Information security for use of cloud services | Cloud security requirements |
| A.5.24 | Information security incident management planning | Documented IR process |
| A.5.25 | Assessment and decision on information security events | Classification and escalation process |
| A.5.36 | Compliance with policies, rules and standards | Audit process |
| A.5.37 | Documented operating procedures | Key processes documented |

### Theme B — People Controls (8 controls)

| Control | Name | What It Requires |
|---------|------|-----------------|
| A.6.1 | Screening | Background checks before employment |
| A.6.3 | Information security awareness, education and training | Regular security training for all staff |
| A.6.4 | Disciplinary process | Consequences for security policy violations |
| A.6.5 | Responsibilities after termination or change of employment | Secure offboarding |
| A.6.6 | Confidentiality or non-disclosure agreements | NDAs with employees and contractors |
| A.6.7 | Remote working | Security requirements for remote work |
| A.6.8 | Information security event reporting | Staff know how to report incidents |

### Theme C — Technological Controls (34 controls)

Most technical — most relevant to pentesters:

| Control | Name | What It Requires |
|---------|------|-----------------|
| A.8.1 | User endpoint devices | Endpoint security policy |
| A.8.2 | Privileged access rights | Management of admin accounts |
| A.8.3 | Information access restriction | Role-based access control |
| A.8.5 | Secure authentication | MFA requirements, password policy |
| A.8.6 | Capacity management | Monitoring and planning for capacity |
| A.8.7 | Protection against malware | Anti-malware controls |
| A.8.8 | Management of technical vulnerabilities | Patch management process |
| A.8.9 | Configuration management | Baseline configurations, change control |
| A.8.11 | Data masking | Masking of sensitive data |
| A.8.12 | Data leakage prevention | DLP controls |
| A.8.15 | Logging | Audit logging of events |
| A.8.16 | Monitoring activities | Log monitoring and alerting |
| A.8.20 | Networks security | Network security controls, segmentation |
| A.8.22 | Segregation of networks | Network segmentation |
| A.8.23 | Web filtering | Control access to external URLs |
| A.8.24 | Use of cryptography | Cryptography policy, key management |
| A.8.25 | Secure development life cycle | SDLC security requirements |
| A.8.26 | Application security requirements | Security requirements in development |
| A.8.28 | Secure coding | Secure coding practices |
| A.8.29 | Security testing in development and acceptance | Testing before release |

---

## PCI-DSS v4.0 Key Changes

PCI-DSS v4.0 became mandatory in March 2024. Key differences from v3.2.1 that interviewers and clients ask about:

**Customised Approach:** v4.0 introduces an alternative compliance pathway. Instead of meeting prescriptive requirements exactly, organisations can demonstrate that their controls achieve the security objective through alternative means. Requires documented risk assessment and approval from the organisation's executive management.

**Requirement 6 — Bespoke and custom software:**
Explicit requirements for web application firewalls (WAF) or web application security testing for public-facing web applications. Must be deployed as a security control by March 2025.

**Requirement 8 — Authentication:**
MFA is now required for ALL access to the cardholder data environment, not just remote administrative access. Includes all users (including developers and admins with local access). Phased requirement — must be met by March 2025.

**Requirement 10 — Log reviews:**
Automated log review mechanisms are now required (not manual daily log review). IDS/IPS and change detection logs must be reviewed promptly.

**Requirement 12.3 — Risk management:**
Documented risk assessments must be performed at least annually. Must cover all PCI requirements.

**Targeted Risk Analysis (TRA):**
Many requirements now allow frequency to be determined by the organisation's risk analysis rather than fixed schedules — but requires documented justification.

---

## CERT-In Incident Response — Detailed Requirements

CERT-In Directions 2022 set mandatory requirements for all Indian entities (government bodies, intermediaries, data centres, cloud service providers, VPN providers, and all organisations using IT infrastructure).

### Mandatory Incident Reporting Timeline

**6 hours from detection:**
```
Incidents requiring mandatory reporting:
- Data breach or data leak
- Attack on critical systems and infrastructure
- Unauthorised access to computer resource networks or systems
- Defacement of website or intrusion into website/application
- Scanning/probing that indicates preparation for attack
- Compromise of critical systems/information
- Ransomware attack
- Malicious code attacks
- Denial of Service (DoS) and Distributed Denial of Service (DDoS) attacks
- Attacks on Internet of Things (IoT) devices and associated systems
- Attacks on data centres and IT systems
- Attacks on critical infrastructure
- Attacks on public utility systems
- Attacks on smart city components
- Attacks on government digital payments systems
```

**Reporting format:**
```
Mandatory fields in incident report:
1. Name and address of the reporting organization
2. Contact details (name, designation, phone, email)
3. Nature of the incident (from the list above)
4. Date and time of incident discovery
5. Date and time of incident occurrence (if known)
6. Systems/applications affected
7. Country of origin (if known)
8. Number of affected users/systems
9. Description of the incident
10. Impact assessment
11. Actions taken so far
```

**Reporting method:** incident@cert-in.org.in with subject "Incident Report - [Organization Name] - [Date]"

### Log Retention Requirements

```
Mandatory: All ICT system logs must be retained for minimum 180 days

Applies to:
- All server logs (web, application, database, authentication)
- Network device logs (firewall, router, switch)
- Security device logs (IDS/IPS, WAF)
- Endpoint logs
- Email server logs
- VPN logs

Storage requirement: Logs must be stored within Indian jurisdiction
Format: Standard formats that can be provided on demand to CERT-In

Practical implication for assessments:
When reviewing Indian client environments, verify:
1. Log retention policy exists and specifies 180 days minimum
2. Centralised logging (SIEM) is in place
3. Logs are actually being stored for 180 days (check oldest log date)
4. NTP is synchronised to NTP server of NPTEL/NPL for log timestamp accuracy
```

### NTP Synchronisation Requirement

```
Mandatory: All systems must synchronise to:
- NTP server of National Physical Laboratory (NPL), CSIR
  Server: time.nplindia.in (stratum 1)
- Or NTP server of National Informatics Centre (NIC)
  Server: time.nic.in

Windows NTP configuration:
w32tm /config /manualpeerlist:"time.nplindia.in" /syncfromflags:manual /reliable:yes /update
w32tm /resync

Linux NTP configuration:
# /etc/chrony.conf or /etc/ntp.conf
server time.nplindia.in iburst
```

---

## Conducting a Compliance Gap Assessment — Interview Template

Senior security professionals are expected to describe their gap assessment methodology clearly. This is the model answer framework:

**Opening (scope definition):**
"Before starting any gap assessment, I spend 30-60 minutes with the client understanding their business context — their industry, regulatory obligations, what frameworks they're already partially implementing, and what triggered this assessment (audit, customer requirement, insurance, leadership mandate). This shapes which framework and which level of the framework is appropriate."

**Document review phase:**
"I request all existing security policies, procedures, and previous audit reports. I'm looking for two things: what exists on paper versus what's actually practiced, and where policies are absent entirely. Many organisations have a written policy but no evidence of implementation — that's a 'partially conformant' finding, not a pass."

**Technical validation:**
"For ISO 27001 or PCI, the documentation isn't sufficient — I need to verify that technical controls exist as described. If the patch management policy says critical patches within 7 days, I want to see patch scan reports that demonstrate this. If the password policy says 12 characters minimum, I want to see the Group Policy Object or LDAP configuration that enforces it. Unvalidated documentation is not evidence of control effectiveness."

**Gap prioritisation:**
"Not all gaps are equal. I prioritise by risk impact first, then by effort to remediate. A missing patch management process (high risk, moderate effort) gets elevated urgency over a missing clean desk policy (low risk, low effort). The remediation roadmap reflects this — immediate action for high-risk gaps, longer timelines for lower-risk items."

**Report structure:**
"My gap assessment reports use a traffic light system: Red = non-conformant (control absent or ineffective), Amber = partially conformant (control exists but gaps in implementation or documentation), Green = conformant. Every Red and Amber has a specific, actionable remediation recommendation — not 'improve your security' but 'implement automated vulnerability scanning with a 30-day critical patch SLA and produce monthly compliance reports.'"
