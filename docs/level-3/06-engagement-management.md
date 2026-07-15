# Engagement Management

!!! info "Why This Matters"
    Technical excellence is necessary but not sufficient at senior level. Engagement management is what keeps clients, builds long-term relationships, and protects your firm legally. Poor engagement management has ended careers and firms even when the technical work was excellent.

---

## Writing a Statement of Work

The SOW is the legal contract defining what you're doing, for whom, at what cost, and under what terms. Every point that's ambiguous in the SOW will cause problems during the engagement.

### SOW Core Components

**Engagement Overview:** One paragraph description of the engagement type, objectives, and approach.

**Scope:** The most critical section.
```
In Scope:

- Production web application: https://app.example.com and all subdomains

- Associated REST APIs

- Mobile applications: iOS v2.3.1 and Android v2.4.0 (builds to be provided)

Out of Scope:

- Third-party services (Stripe, Salesforce, AWS infrastructure)

- Physical security testing

- Social engineering of employees

- Denial-of-service testing

- Production database servers (identify vulnerabilities but do not exploit)
```

**Methodology:** Reference frameworks (OWASP, PTES, OWASP MASTG for mobile).

**Timeline:** Start and end dates, deliverable due dates, testing windows.

**Deliverables:** Report format, severity classification system, executive summary, detailed findings, raw tool output as appendices.

**Assumptions and Dependencies:** "Client will provide VPN access by [date]", "Client will provide test accounts by [date]", "Testing window is 09:00–18:00 IST".

**Contacts:**
```
Client Technical Contact: [Name, Phone, Email]  — for day-to-day questions
Client Emergency Contact: [Name, Phone, Email]  — 24/7 for critical findings
Client Authorization Signatory: [Name, Title]   — legal authority
Tester: [Name, Firm, Phone]
```

**Limitation of Liability:** Standard legal protection for both parties.

**Confidentiality:** Testing data handling, retention periods, destruction policy.

---

## Communicating Critical Findings During an Engagement

**The first call scenario:** You find unauthenticated RCE on a customer-facing payment server at 14:30 on a Tuesday.

Do:

- Stop exploiting it (you've confirmed the impact, no need to go further)

- Document the finding with timestamp, evidence, and reproduction steps

- Call the technical contact immediately — don't email

- State clearly: "I need to inform you of a critical finding. We found unauthenticated remote code execution on [server]. I recommend discussing before I continue testing."

- Let the client decide next steps

- Follow up the call with a written summary within the hour

Don't:

- Continue exploiting to "show more impact"

- Wait until the end of the day or week

- Send an email and assume they'll see it

- Make decisions about what to do with the vulnerability on the client's behalf

**Why this matters in interviews:** Interviewers will ask about this scenario explicitly. The wrong answer is any version of "I'd keep testing to gather more evidence." The right answer prioritizes client communication and professional responsibility over thoroughness.

---

## Managing Difficult Situations

**Accidental service disruption:**
1. Stop testing immediately
2. Call the emergency contact — don't wait to understand the full impact
3. Provide exact timing and what you were doing when the disruption occurred
4. Assist with recovery if asked and if you can help
5. Document everything meticulously for the post-incident review
6. Include a lesson learned in the engagement report

**Finding evidence of an existing breach:**
1. Stop all testing immediately
2. Call the emergency contact
3. Do not investigate the breach yourself — that's incident response, not pentest scope
4. Do not access the attacker's infrastructure (even to understand it)
5. Preserve all evidence you've already observed — document times and observations
6. Wait for client direction

**Client wants to expand scope mid-engagement:**
1. Never expand scope verbally — scope changes require written authorization
2. Draft a scope change amendment with the new in-scope items
3. Get signature from the appropriate authority (not just a verbal OK from the IT contact)
4. Only test the expanded scope after receiving signed amendment

**Client disagrees with your severity rating:**
Present your reasoning clearly. Explain the CVSS metrics and why you assigned each value. Explain the contextual risk in their specific environment. But — be open to information you didn't have. If the client explains that the system is isolated and contains no sensitive data, adjusting the contextual severity down is appropriate. Don't inflate severity as a scare tactic; don't deflate it to avoid difficult conversations.

---

## Report Delivery

**The readout call:** Most engagements end with a readout — a presentation of findings to the client team before or alongside report delivery. Senior pentesters own this call.

Structure:
1. Engagement overview (5 minutes) — what you tested, how
2. Overall risk posture (2 minutes) — one honest sentence about the state of security
3. Critical and high findings (15-20 minutes) — walk through each, show the evidence, explain business impact
4. Medium and lower findings (5 minutes) — brief overview
5. Strategic recommendations (5 minutes)
6. Q&A

Tips:

- Prepare for technical questions (developer will ask "but we sanitize input with X" — know your answer)

- Prepare for pushback on severity (executive will say "but this is very unlikely" — have CVSS justification ready)

- The audience is mixed — technical and executive. Adjust in real time.

---

# Interview Q&A — Senior Level

!!! tip "Senior Level Reality"
    Senior interviews assess judgment, communication, and depth simultaneously. Prepare stories from real engagements — what was challenging, what decision you had to make, what the outcome was. STAR format (Situation, Task, Action, Result) is your friend for behavioral questions, but technical questions still dominate.

---

### Q1. Explain the difference between unconstrained, constrained, and resource-based constrained delegation. Which is the most dangerous misconfiguration to find?

??? success "Model Answer to Give"
    "All three are Kerberos delegation configurations that allow a service to impersonate users when accessing other services — but they differ significantly in scope and in what rights are granted.

    Unconstrained delegation is the most dangerous. When a machine or service account has unconstrained delegation enabled, incoming service tickets from authenticating users contain a copy of that user's full TGT — the service can impersonate the user to any service in the domain. In an engagement, if I control a machine with unconstrained delegation, I can trigger any high-privilege user (including Domain Controllers) to authenticate to my machine — using techniques like SpoolSample or PetitPotam to coerce authentication from the DC. When the DC authenticates, its TGT arrives on my machine, and I can use it to DCSync. The path from 'local admin on an unconstrained delegation server' to 'Domain Admin' can be very short.

    Constrained delegation is more limited — the service can only impersonate users to specific target services listed in the `msDS-AllowedToDelegateTo` attribute. But if you control an account with constrained delegation, you can still impersonate any user (including Domain Admin) to the configured target service — you don't need the user's password or current TGT. So constrained delegation on a service account that can delegate to `cifs/fileserver` means you can impersonate Domain Admin to that file server.

    Resource-based constrained delegation (RBCD) reverses the model — the target resource defines who can delegate to it via `msDS-AllowedToActOnBehalfOfOtherIdentity`. The exploitation path requires write access to a computer object. If I have GenericWrite on Computer A, I can configure RBCD to allow an attacker-controlled computer account to delegate to Computer A — then impersonate Domain Admin to services on Computer A.

    Most dangerous to find: unconstrained delegation. The blast radius is domain-wide and the exploitation is relatively straightforward if you can trigger coerced authentication."

---

### Q2. A client says 'we don't care about insider threats, just test our external perimeter.' How do you handle this?

??? success "Model Answer to Give"
    "I'd address it directly in the pre-engagement conversation, not just accept it.

    I'd acknowledge their priority and confirm that we'll test the external perimeter thoroughly. But I'd also explain the business risk of excluding insider threat testing: the majority of significant breaches start with a phishing email or compromised credential that gives attacker 'insider' access. Testing only the external perimeter tells you how hard it is to get in — but not what happens to the business when an attacker does get in. If the answer is 'everything is flat network and the attacker has Domain Admin in 30 minutes,' that's a critical risk the business should understand.

    I'd suggest framing it as two assessments: an external penetration test (their stated priority) plus an assumed-breach scenario — 'assume an attacker has compromised one employee workstation, assess the blast radius.' The assumed-breach scenario often produces the most impactful findings for client security investment decisions.

    If after this conversation they still only want external testing, I accept it professionally and execute it excellently. I document their decision in the SOW as an explicit client choice. In the executive summary, I'd note that internal threat simulation was explicitly excluded from scope, and I might include a brief section on what assumed-breach testing could add.

    What I won't do: simply agree, skip the conversation, and later include criticism of their security posture in areas they didn't authorize me to test."

---

### Q3. What is DCSync and what rights are required to execute it?

??? success "Model Answer to Give"
    "DCSync abuses the Active Directory replication protocol. Domain Controllers synchronize with each other using `IDL_DRSGetNCChanges` — a replication request that returns account objects including their NTLM hashes, Kerberos keys, and historical passwords.

    Any principal that has these three directory rights on the domain object can issue this replication request without being a Domain Controller:
    - `DS-Replication-Get-Changes`
    - `DS-Replication-Get-Changes-All`
    - `DS-Replication-Get-Changes-In-Filtered-Set` (optional, for RODC-filtered attributes)

    By default, only Domain Admins, Enterprise Admins, and Domain Controllers have these rights. Any non-DC account with these rights is immediately a Critical finding — it's an account that can extract every credential in the domain from the network without ever touching a DC directly.

    In execution:
    ```bash
    secretsdump.py corp.local/syncuser:password@dc.corp.local
    ```
    This returns every user's NTLM hash, historical hashes, and Kerberos keys — including `krbtgt`, which enables Golden Ticket attacks.

    For detection: Windows Event ID 4662 logs when an object with Replication rights is accessed. A SIEM rule alerting on `DS-Replication-Get-Changes-All` from non-DC IP addresses is the primary detection. Microsoft's Defender for Identity (formerly ATA) includes DCSync detection as a built-in alert.

    For mitigation: audit and remove unnecessary replication rights, implement Privileged Identity Management (PIM) for any account that legitimately needs replication rights, and enable Protected Users group for Domain Admins."

---

### Q4. You find an ADCS ESC1 vulnerability. Walk me through the attack chain from low-privilege user to Domain Admin.

??? success "Model Answer to Give"
    "ESC1 requires a certificate template where: enrollment is open to Domain Users (or a broader group), the CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT flag is set (meaning the enrollee can specify any Subject Alternative Name), and the EKU includes Client Authentication.

    The chain:

    Step 1 — Identify the vulnerable template:
    ```bash
    certipy find -u user@corp.local -p password -dc-ip dc_ip -vulnerable
    ```
    This shows vulnerable templates with their enrollment rights.

    Step 2 — Enroll for a certificate claiming to be Domain Administrator:
    ```bash
    certipy req -u user@corp.local -p password \
      -dc-ip dc_ip -target ca.corp.local \
      -ca 'Corp-CA' -template VulnerableTemplate \
      -upn administrator@corp.local
    ```
    Because CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT is set, we supply `administrator@corp.local` as the UPN in the SAN. The CA issues a legitimate certificate for that identity.

    Step 3 — Authenticate using the certificate to get the administrator's NTLM hash:
    ```bash
    certipy auth -pfx administrator.pfx -dc-ip dc_ip
    ```
    This uses PKINIT (public key Kerberos) to authenticate as administrator and returns their NTLM hash and a TGT.

    Step 4 — Pass-the-Hash or use the TGT for Domain Admin access.

    The business impact: this entire chain is executed without knowing the administrator's password, without cracking anything, and with only a low-privilege domain user account. The certificate is issued by the trusted enterprise CA — it's legitimate infrastructure working exactly as designed, just misconfigured.

    Mitigation: disable CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT on templates used for user authentication, or require CA manager approval for enrollment. The 'Certified Pre-owned' whitepaper from SpecterOps documents this and all ESC attack paths in detail — recommend it to clients' AD teams."

---

### Q5. What's your approach to scoping a red team engagement?

??? success "Model Answer to Give"
    "Red team scoping is more complex than pentest scoping because the objectives are behavioral — you're testing people and processes, not just technology. I approach it in four conversations.

    First conversation — objectives: What does success look like? The objectives must be specific and measurable. 'Test our security' is not an objective. 'Determine whether our SOC can detect and respond to a simulated ransomware operator gaining persistent access to the finance subnet within 72 hours' is. Common objective categories: data exfiltration (can we reach and extract sensitive data?), operational disruption (can we affect production systems?), credential compromise (can we obtain executive credentials?), detection effectiveness (what percentage of our TTPs trigger alerts?).

    Second conversation — rules of engagement constraints: What's absolutely off-limits? Production systems with zero tolerance for disruption? Key executives who must not be phished? Any systems where a brief outage would have regulatory implications? These become explicit exclusions.

    Third conversation — threat model: Which threat actors are most relevant to this organization? For a bank, it's likely financially motivated groups — their TTPs (Cobalt Strike usage, specific initial access vectors, specific lateral movement patterns) should guide the red team's approach. This is where threat intelligence feeds the technical execution.

    Fourth conversation — detection and response team awareness: In a classic red team, the blue team is completely unaware. In some engagements (especially first-time red teams), a 'purple team' model is more appropriate — red team executes, blue team watches, everyone discusses detection immediately. This is more educational but less realistic.

    SOW for red team needs all of the above plus: specific IP ranges for C2 infrastructure that can be whitelisted if needed for emergency stop, defined 'get-out-of-jail' process if the red team triggers an actual IR response, and clear deconfliction process."

---

### Q6. How do you stay current with new attack techniques?

??? success "Model Answer to Give"
    "I treat staying current as a professional obligation, not an optional extra. My approach has a few components:

    Primary research sources: I follow SpecterOps (BloodHound, Certified Pre-owned research, their blog), Synacktiv, Crowdstrike research, and Google Project Zero. These produce high-quality original research rather than just aggregating others' work. I read new whitepapers when they come out.

    Lab environment: I maintain a small home lab with a Windows AD environment, a few Linux VMs, and AWS free tier. New techniques get tested in the lab before I'd ever reference them confidently in an engagement. Reading about Kerberos delegation is different from executing the attack chain and debugging it.

    Community: DEFCON/Black Hat talks (the papers are all free after the conference). The relevant Discord communities — OffSec Community, BadBlood, BloodHound Slack. Twitter/X security research community — though signal-to-noise is challenging there.

    Practice platforms: HackTheBox regularly (new machines drop weekly). PortSwigger Web Academy updates their labs with new techniques. CloudGoat for cloud attack paths.

    Certifications as forcing functions: I've found that certifications with practical exams (OSCP, CRTO, CRTE) force deep engagement with specific technique domains. Even if I know the content, the exam forces me to execute it reliably under time pressure — which is different from having read about it.

    The honest answer to what I've done recently: [specific technique from last month or last few months — be concrete]. Generic answers about 'keeping up with the industry' don't land as well as specific examples."

---

!!! tip "For Senior Interviews"
    Prepare 3-4 detailed stories from real engagements using STAR format. Each story should demonstrate: a technical challenge that required creativity, a professional judgment call under uncertainty, or a situation where you led a team or client conversation. Senior hiring is as much about 'can I trust this person with our clients' as it is about technical depth.
