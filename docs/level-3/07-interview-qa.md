# Interview Q&A — Senior Level (Additional)

!!! info "Reference"
    Core senior Q&As covering AD Advanced and engagement management are embedded in the [Engagement Management](06-engagement-management.md) module. This file covers additional technical and scenario-based questions.

---

### Q1. Explain how you'd approach testing a GraphQL API with no documentation.

??? success "Model Answer to Give"
    "GraphQL's introspection system is self-documenting, so documentation is rarely truly absent.

    First step: confirm whether introspection is enabled:
    ```
    POST /graphql
    {"query":"{ __schema { queryType { name } } }"}
    ```
    If this returns schema data, introspection is on — use InQL (Burp extension) or graphql-voyager to generate a complete visual schema. This gives me every query, mutation, subscription, type, and field — equivalent to full documentation.

    If introspection is disabled: Apollo and other frameworks often have field suggestion enabled — send a query with a typo:
    ```
    {"query":"{usr{name}}"}
    ```
    Response: 'Did you mean user?' — this leaks field names one at a time, allowing schema reconstruction without introspection.

    Second: test all discovered queries and mutations for BOLA — substitute IDs belonging to other users. Test mutations for mass assignment — add fields the schema exposes but the UI doesn't show. Test for nested query depth attacks (deeply nested queries that cause DoS). Test for batching abuse (many operations in one request to bypass rate limiting).

    Third: check for sensitive fields that should be restricted. A user type that includes `role`, `internal_notes`, `api_key`, `password_hash` in the schema when low-privileged users can query it is an excessive data exposure finding — even if those fields weren't listed in the UI.

    The combination of field suggestion enumeration + blind BOLA testing covers most GraphQL attack surface even without introspection."

---

### Q2. What's the difference between a Golden Ticket and a Silver Ticket, and when would you use each?

??? success "Model Answer to Give"
    "A Golden Ticket is a forged TGT (Ticket Granting Ticket) signed with the `krbtgt` account's hash. Because all TGTs in the domain are encrypted with `krbtgt`'s key, a valid `krbtgt` hash lets you forge a TGT for any user, with any group memberships, for any service. It's the master key to the entire domain.

    A Silver Ticket is a forged service ticket signed with a specific service account's or computer account's hash. It's scoped to that specific service only — but doesn't require `krbtgt`.

    When I'd use Golden Ticket:
    After DCSync — I have the `krbtgt` hash. I use it to create a persistent mechanism: forge a TGT with 10-year lifetime. Even if the compromise is discovered and all user passwords reset, the Golden Ticket continues working until `krbtgt` is rotated twice. I'd also use it for creating tickets with specific group memberships that don't exist for any real account.

    When I'd use Silver Ticket:
    When I have a service account or computer account hash but not `krbtgt`. If I've Kerberoasted a high-privilege service account and cracked it, I have its hash — I can forge service tickets to services that account is associated with, without needing to contact the KDC at all.

    The stealth difference: Golden Ticket abuse can be detected because the forged TGT doesn't appear in the KDC's ticket-granting logs (since the KDC never issued it). Silver Ticket abuse is even harder to detect — the service authenticates the ticket directly without contacting the KDC at all, so no KDC logs whatsoever. This is why Silver Tickets are favored in stealth-focused operations where the objective is targeted access to a specific service."

---

### Q3. How do you test for SSRF in a modern application where the URL parameter isn't obvious?

??? success "Model Answer to Give"
    "Modern applications rarely have parameters literally named 'url' — you have to find SSRF-triggerable input across less obvious vectors.

    My approach:

    Vector 1 — Webhook and integration features: Any feature that sends an HTTP callback to a user-specified endpoint. Payment systems (IPN webhooks), CI/CD systems (build notifications), monitoring tools, RSS feed imports. Test by pointing the webhook at Burp Collaborator and observing DNS and HTTP interactions.

    Vector 2 — Document/image generation: PDF generators, screenshot services, HTML-to-image converters. The server fetches a URL to render it. Test: can I include internal URLs? `<img src='http://169.254.169.254/latest/meta-data/'>`  in an HTML-to-PDF feature.

    Vector 3 — File import/export from URL: 'Import from URL', 'Connect to data source', 'Pull from feed' features. The server fetches the URL to retrieve content.

    Vector 4 — XML (XXE as SSRF): Any XML-parsing endpoint can be an SSRF vector via external entity declarations.

    Vector 5 — Header-based SSRF: Some applications fetch URLs from HTTP headers — `Referer`, `X-Forwarded-For`, custom headers. Less common but worth testing when behavior is unusual.

    Vector 6 — Blind SSRF detection: Use Burp Collaborator (or a simple DNS logger) as the target. Even if no response is returned to me, a DNS lookup or HTTP request to my collaborator domain confirms SSRF. Start with DNS (least likely to be blocked): `http://my-unique-id.burpcollaborator.net`.

    After confirming SSRF exists, escalate to: internal service discovery (scan common ports on internal RFC1918 ranges), cloud metadata access, SMB SSRF (trigger NTLM authentication toward my responder if SMB ports reachable internally)."

---

### Q4. Describe your process for privilege escalation on a Linux machine where you have a low-privilege shell.

??? success "Model Answer to Give"
    "I have a structured process, and I follow it every time rather than jumping around.

    First 60 seconds — context:
    ```bash
    id && whoami            # Who am I? Groups?
    hostname && uname -a    # OS version, kernel
    ip a                    # Network interfaces — am I a pivot point?
    ss -tulpn               # Locally listening services
    ```

    Automated enumeration while I do manual checks:
    Transfer and run linPEAS — it's comprehensive and highlights the most interesting findings in red.

    Manual checks in priority order:

    1. Sudo rights first — highest probability of quick win:
    ```bash
    sudo -l
    ```
    Any NOPASSWD entry, any unusual binary → GTFOBins immediately.

    2. SUID binaries:
    ```bash
    find / -perm -4000 -user root -type f 2>/dev/null
    ```
    Compare against expected list (passwd, ping, su). Unexpected SUID binaries → GTFOBins.

    3. Writable cron jobs:
    ```bash
    cat /etc/crontab && ls /etc/cron.d/
    pspy64  # Monitor for cron execution if unsure of schedule
    ```
    Cron script writable by my user → inject reverse shell payload.

    4. Service running as root with writable config/binary:
    ```bash
    ps aux | grep root
    find / -writable -name "*.service" 2>/dev/null
    ```

    5. Capabilities:
    ```bash
    getcap -r / 2>/dev/null
    ```
    `cap_setuid` or `cap_sys_admin` on any binary → immediate escalation path.

    6. Passwords in files:
    ```bash
    find / -name '*.conf' 2>/dev/null | xargs grep -l 'password' 2>/dev/null
    cat ~/.bash_history
    find / -name '.env' 2>/dev/null
    ```

    7. Kernel exploits — last resort (risky, can crash the system):
    ```bash
    uname -r
    # Check CVEs against kernel version
    # Use only in test environments or with explicit client authorization for exploitation
    ```

    I document every step and what I found at each step. During a real engagement I'm very careful with kernel exploits — I identify the vulnerability and report it, but only execute with explicit client authorization for exploitation."

---

### Q5. What's your experience with adversary simulation frameworks and how do they differ from standard pentesting tools?

??? success "Model Answer to Give"
    "The fundamental difference is in philosophy and architecture.

    Standard pentesting tools (Nmap, Metasploit, Burp Suite) are modular — you choose the right tool for each phase and chain them manually. They're designed for thoroughness and reproducibility of findings. Metasploit's Meterpreter is a capable post-exploitation shell, but it's not designed for long-term stealth — it's detected by most EDR solutions.

    Adversary simulation frameworks like Cobalt Strike, Havoc, or Sliver are designed around the red team operational model: establishing long-term, stealthy persistence and blending with legitimate traffic. They have:

    **C2 malleability:** Cobalt Strike's Malleable C2 profiles configure the beacon's network traffic to look like any legitimate protocol or application — Bing search requests, Amazon S3 API calls. This blends into normal corporate traffic and evades signature-based detection.

    **Sleep discipline:** Beacons sleep for configurable intervals (5 minutes, 1 hour) with jitter — they don't constantly communicate. This makes behavioral detection harder.

    **In-memory execution:** Most operations are performed in memory, minimizing on-disk artifacts. Operators use BOFs (Beacon Object Files) to execute code directly in the beacon process.

    **Team collaboration:** Multiple operators can work through the same team server, see each other's sessions, and hand off access.

    **MITRE ATT&CK alignment:** The framework logs every action with ATT&CK technique mappings, making report writing and detection gap analysis much easier.

    In a red team engagement, the framework is the persistent presence — initial access might come from a custom phisher, but the ongoing C2 channel uses the red team framework for the weeks or months of the engagement."

---

!!! tip "Before Your Senior Interview"
    Prepare for a whiteboard session. Senior interviews often include: draw out an AD attack chain from initial access to DA, explain a specific technique at the protocol level, or walk through how you'd approach a novel scenario you haven't seen before. The ability to reason through new problems live is what they're evaluating — not just whether you've memorized techniques.

---

### Q6. Explain how you'd test for NTLM relay vulnerabilities during an internal assessment.

??? success "Model Answer to Give"
    "NTLM relay exploits the Windows authentication protocol where a captured authentication attempt can be forwarded to another service to gain access — without ever cracking the password.

    The prerequisite check first: I identify which hosts have SMB signing disabled. SMB signing prevents relay because the server and client cryptographically verify message integrity.
    
    ```bash
    nxc smb 192.168.1.0/24 --gen-relay-list targets.txt
    # Shows all hosts where SMB signing is NOT required
    ```

    Then I configure Responder to capture but not answer SMB and HTTP, allowing ntlmrelayx to handle those:
    ```
    # In Responder.conf: SMB = Off, HTTP = Off
    responder -I eth0 -rdwv              # Poison LLMNR/NBT-NS
    ntlmrelayx.py -tf targets.txt -smb2support  # Relay to targets
    ```

    When any Windows host on the network tries to resolve a hostname via LLMNR or NBT-NS — for example, a user mistyping a UNC path — Responder answers and the authentication is relayed to all targets. If the authenticating user is a local admin on any target, we get a SAM hash dump automatically.

    For environments where SMB signing IS enforced, I look at alternative relay paths: WebDAV relay to LDAP (requires coercing HTTP authentication instead of SMB), or mitm6 (IPv6 DHCPv6 poisoning triggers HTTP authentication which can be relayed to LDAP).

    In reporting: if I find hosts without SMB signing, that's a High finding even without demonstrating the relay, because the fix is simple (a Group Policy change) and the risk is clear. If I demonstrate the relay to the point of credential extraction, it becomes Critical."

---

### Q7. How do you approach scoping a mobile application penetration test? What information do you need before starting?

??? success "Model Answer to Give"
    "Mobile assessment scoping requires more specificity than web assessments because the technical setup is complex and varies significantly between platforms.

    **Platform and version:**
    iOS and Android require completely different tooling, setup, and methodology. I need to know both platforms if both exist, and specifically which OS versions to test against — older versions may have different security models.

    **App version and delivery method:**
    The client should provide the specific build to test. For Android: the APK file directly (not from Play Store — store builds have different properties). For iOS: either an IPA file for sideloading or TestFlight access. Production store builds are often harder to analyze due to certificate requirements and device restrictions.

    **Backend API scope:**
    Mobile apps are mostly frontends to APIs. The backend is often the higher-risk surface. Confirm whether the API is in scope alongside the app — most of my significant mobile findings are actually in the API, not the app itself.

    **Authentication mechanisms:**
    Biometric auth, certificate pinning, jailbreak/root detection — I need to know what's implemented so I can plan bypass approaches before the engagement starts, not discover them on Day 1.

    **Testing environment:**
    Does the client have a staging environment for the backend API? Testing dynamic analysis against production can cause real user data to be exposed or transactions to process. A staging environment is strongly preferred.

    **Third-party SDKs:**
    Analytics, crash reporting, payment SDKs are in scope or out? If Stripe or Braintree SDKs are in use, those are third-party components with their own scope considerations.

    **Minimum I need before starting:**
    - APK or IPA file for the build to test
    - Test account credentials (ideally multiple accounts for IDOR testing)
    - API base URL and documentation (if available)
    - Confirmation of whether backend API is in scope
    - Staging environment access"

---

### Q8. Walk me through how ADCS ESC1 works from low-privilege domain user to Domain Admin.

??? success "Model Answer to Give"
    "ESC1 exploits a certificate template misconfiguration in Active Directory Certificate Services. The attack chain requires three conditions to be met simultaneously on a template: the template allows enrollment by low-privileged groups (like Domain Users), the template has the CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT flag set (meaning the enrollee can specify any Subject Alternative Name), and the template's Extended Key Usage includes Client Authentication.

    When all three are present, any domain user can request a certificate that claims to be any other user — including Domain Admin — because the CA issues the certificate based on what the requester claims rather than verifying identity.

    Step by step:

    Step 1 — Find vulnerable templates:
    ```bash
    certipy find -u user@corp.local -p password -dc-ip dc_ip -vulnerable
    ```
    This shows templates meeting the ESC1 criteria.

    Step 2 — Request a certificate claiming to be Domain Administrator:
    ```bash
    certipy req -u user@corp.local -p password \
      -dc-ip dc_ip -target ca.corp.local \
      -ca 'Corp-CA' -template VulnTemplate \
      -upn administrator@corp.local
    ```
    The `-upn` flag is the key — we're telling the CA to include `administrator@corp.local` in the Subject Alternative Name. The CA issues a legitimate certificate with the Domain Admin's UPN because the template permits this.

    Step 3 — Authenticate with the certificate using PKINIT:
    ```bash
    certipy auth -pfx administrator.pfx -dc-ip dc_ip
    ```
    PKINIT is Kerberos public key authentication — the DC accepts the certificate and returns a TGT plus the NT hash for the administrator account.

    Step 4 — Use the NT hash for Pass-the-Hash or the TGT for further operations.

    The business impact: a low-privilege domain user account achieves Domain Admin in under 5 minutes without cracking any password, without exploiting any software vulnerability, and using only legitimate AD certificate infrastructure. The fix is disabling CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT on templates not requiring it, or restricting enrollment to administrators only."

---

### Q9. What's the difference between a red team report and a penetration test report?

??? success "Model Answer to Give"
    "The structure, audience, and purpose are fundamentally different.

    A pentest report is a vulnerability catalog — here are all the weaknesses we found, ranked by severity, with remediation guidance. The primary audience is the technical team that will fix things. Executive summary exists but the bulk of the value is in the finding details.

    A red team report tells an attack story — here is the path a real threat actor would take, here are the decisions made at each stage, here is what your security controls caught and what they missed. The primary audience is the CISO and executive leadership who need to understand the program's effectiveness, not just a list of fixes.

    Structural differences:

    **Pentest report:** Sorted by severity. Critical findings first. Each finding is standalone — it describes a vulnerability in isolation. Remediation is specific and technical.

    **Red team report:** Sorted chronologically by attack phase (initial access → lateral movement → privilege escalation → objectives). Findings exist to support the narrative, not as standalone items. The detection analysis section — what the SOC caught vs missed, with MTTD and MTTR metrics — is as important as the technical findings.

    **MITRE ATT&CK mapping:** Optional in pentest reports, often included but not central. Mandatory in red team reports — every action maps to a technique ID, and the coverage heat map shows which ATT&CK tactics and techniques were tested and which were detected.

    **Tone:** Pentest report: 'we found X, fix it with Y.' Red team report: 'an attacker with these goals, using these techniques, achieved these objectives — here's the evidence, here's what worked in your defense, here's the gap.'

    In practice: clients who haven't done a pentest shouldn't be doing red team exercises. The red team assumes basic hygiene exists and tests the detection and response layer on top. A client with 200 unpatched critical vulnerabilities needs a pentest, not a red team."

---

### Q10. How do you handle a situation where the client's blue team detects your red team activity and responds?

??? success "Model Answer to Give"
    "This is the best possible outcome for the engagement — it means their detection is working.

    The first decision: do we acknowledge or continue operating?

    Most red team engagements have a pre-agreed deconfliction process. If the IR team contacts us directly (sometimes they find our infrastructure and reach out), we use the pre-agreed code word to identify ourselves. If they escalate through internal channels and haven't found us yet, we may choose to continue operating (they detected some activity but not our full presence) — this is a judgment call based on the ROE.

    What I don't do: panic. Getting detected is data. I note precisely what we were doing when detection occurred, what the timeline was, and document it for the report.

    If the IR team initiates a full response and it's clear they're actively hunting:
    Options depending on ROE:
    1. Acknowledge — notify the CISO or designated red team liaison, deconflict, shift to purple team mode where we discuss in real time what they found and what they missed
    2. Go quieter — reduce activity tempo, switch C2 channels, see if they can sustain detection at reduced footprint (this is valuable data too)

    What to document:
    - What technique triggered detection (e.g., Mimikatz execution at 14:32)
    - How long until alert fired (MTTD)
    - How quickly IR mobilized (MTTR)
    - What containment action they took (blocked IP, quarantined host, disabled account)
    - Whether our backdoors survived containment (if persistence was tested)

    For the report: partial detection is often more interesting than no detection or full detection. 'Blue team caught the Mimikatz execution in 3 minutes but didn't detect the DCSync that happened 2 hours earlier' — that's specific, actionable intelligence for improving detection coverage."
