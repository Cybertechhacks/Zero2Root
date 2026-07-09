# Interview Q&A — Fresher Level

!!! tip "How to Use This Section"
    Every question here uses the three-layer format. Read all three layers — not just the model answer. Understanding *what's being tested* changes how you approach the entire conversation, not just that one question.

---

## Networking Questions

---

### Q1. Explain the TCP three-way handshake. How is it relevant to port scanning?

??? note "Concept Answer"
    TCP establishes a connection via three steps: the client sends a **SYN** (synchronize) packet with a random Initial Sequence Number (ISN). The server responds with **SYN-ACK**, acknowledging the client's ISN and including its own ISN. The client completes the handshake with **ACK**, acknowledging the server's ISN. After this, data transfer begins.

    Each SYN that a server receives creates a half-open connection entry in its SYN backlog queue, allocating resources before the connection is confirmed. This is the mechanism behind SYN flood attacks.

??? warning "What the Interviewer Is Testing"
    They want to see if you understand *why* the handshake exists (sequence number negotiation for reliable ordered delivery, bidirectional confirmation) rather than just the steps. They're also checking if you can connect the handshake mechanics to practical scanning knowledge. Follow-up questions: "What is a SYN scan and why is it stealthier than a connect scan?" and "What is a SYN flood and how is it mitigated?"

??? success "Model Answer to Give"
    "TCP's three-way handshake — SYN, SYN-ACK, ACK — establishes a reliable connection by negotiating sequence numbers that both sides use to order and acknowledge data. The SYN carries the client's starting sequence number, the SYN-ACK carries the server's, and the final ACK confirms both sides can transmit and receive.

    From a scanning perspective: Nmap's default SYN scan sends a SYN and, if it receives SYN-ACK, immediately sends RST to tear down the connection without completing the handshake. This is called a half-open or stealth scan — because the application layer never sees a completed connection, it typically doesn't log it. A TCP connect scan completes the full handshake and is logged by the application. The trade-off is that SYN scans require raw socket privileges (root/SYSTEM) while connect scans don't.

    For SYN floods: when a server receives a SYN, it allocates a half-open connection entry before the handshake completes. Flooding with SYNs from spoofed IPs exhausts this queue, preventing legitimate connections. SYN cookies mitigate this by encoding connection state into the SYN-ACK's sequence number rather than allocating a queue entry — no memory is consumed until the handshake completes."

---

### Q2. What is the difference between TCP and UDP? Give examples of when each is used.

??? note "Concept Answer"
    TCP (Transmission Control Protocol) is connection-oriented, reliable, ordered, and error-checked. It guarantees delivery through acknowledgments, retransmission, and flow control. UDP (User Datagram Protocol) is connectionless, unreliable, and unordered — it sends datagrams with no confirmation of delivery or ordering.

??? warning "What the Interviewer Is Testing"
    They're checking protocol fundamentals and whether you can connect protocol choice to real use cases. They also want to know the scanning implication — UDP scanning is harder than TCP because there's no guaranteed response from open ports.

??? success "Model Answer to Give"
    "TCP and UDP represent two different design philosophies. TCP trades speed for reliability — it establishes a connection, tracks sequence numbers for ordering, and retransmits lost packets. It's used for anything where data integrity matters: HTTP/S, SSH, SMTP, FTP, database connections.

    UDP is fire-and-forget — no connection, no acknowledgment, no ordering. It's used where speed matters more than reliability or where the application handles retransmission itself: DNS (53), DHCP (67/68), SNMP (161), NTP (123), VoIP and streaming. DNS uses UDP for queries because the overhead of a TCP handshake per lookup would be unacceptable — a single UDP query and response is much faster.

    Pentesting implication: UDP scanning is significantly harder than TCP. With TCP, a closed port returns RST — immediate feedback. With UDP, a closed port returns ICMP Port Unreachable, but an open port usually returns nothing. So no response could mean open or the packet was dropped. This makes UDP scans slow and unreliable, which is why many pentesters focus UDP scanning on specific high-value ports like 161 (SNMP) and 500 (IKE/VPN)."

---

### Q3. What happens when you type a URL in a browser and press Enter?

??? note "Concept Answer"
    This is a comprehensive question covering DNS resolution, TCP connection establishment, TLS handshake (for HTTPS), HTTP request/response, and browser rendering. It tests how well you can connect multiple networking concepts.

??? warning "What the Interviewer Is Testing"
    This is a classic systems design / networking question used to assess depth. They want to see how many layers of the stack you can walk through confidently. The more layers you cover and connect, the more impressed they are. Stopping at "DNS resolves the domain and you get the page" fails this question.

??? success "Model Answer to Give"
    "The full journey for `https://www.example.com`:

    First, DNS resolution: the browser checks its cache, then the OS cache, then `/etc/hosts`. If no cached result, it queries the configured recursive resolver (like 8.8.8.8). The resolver walks the hierarchy — root nameservers tell it which nameservers are authoritative for `.com`, the `.com` TLD nameservers tell it which nameservers are authoritative for `example.com`, and the authoritative nameserver returns the A record (IP address). This result is cached with its TTL.

    With the IP, the browser initiates a TCP three-way handshake to port 443 — SYN, SYN-ACK, ACK.

    Since it's HTTPS, a TLS handshake follows: the client sends ClientHello with supported TLS versions and cipher suites. The server responds with ServerHello selecting cipher suite, sends its certificate, and in TLS 1.3, both sides derive session keys from Diffie-Hellman key shares immediately. In TLS 1.2, additional round trips are needed.

    The browser validates the certificate — checks the CA signature, verifies the hostname matches, checks it isn't expired or revoked.

    Now HTTP: the browser sends a GET request with headers including Host, User-Agent, Accept, Cookie. The server processes it and returns an HTTP 200 response with the HTML body.

    The browser parses HTML, discovers additional resources (CSS, JavaScript, images), and fires additional requests for each. JavaScript may fire API calls as well. The page renders progressively as resources load.

    Security implications are everywhere: DNS can be poisoned, TLS can be stripped if HSTS isn't set, cookies without Secure flag travel over HTTP, unvalidated redirects can redirect to attacker sites."

---

### Q4. What is ARP and how can it be exploited?

??? note "Concept Answer"
    ARP (Address Resolution Protocol) resolves IP addresses to MAC addresses at Layer 2. It's stateless and unauthenticated — any host can send unsolicited ARP replies, and receivers update their cache without verification.

??? warning "What the Interviewer Is Testing"
    They want to confirm you understand Layer 2 vs Layer 3 distinction, how ARP works fundamentally, and the practical exploit (ARP poisoning enabling MITM). They'll often follow up: "How would you detect ARP poisoning?" or "What tools do you use for ARP poisoning?"

??? success "Model Answer to Give"
    "ARP maps IP addresses to MAC addresses within a local subnet. When Host A wants to reach 192.168.1.1, it broadcasts 'Who has 192.168.1.1?' and the owner of that IP replies with its MAC address. Host A caches this mapping.

    The exploit is ARP poisoning: since ARP has no authentication, any host can send unsolicited ARP replies. An attacker sends a gratuitous ARP reply to the victim saying 'the gateway (192.168.1.1) is at MY MAC address' and simultaneously tells the gateway 'the victim's IP is at MY MAC address.' Both sides update their ARP caches with the attacker's MAC, so all traffic between victim and gateway flows through the attacker — a full MITM position. The attacker forwards traffic to avoid disruption while intercepting or modifying it.

    Tools I've used: bettercap or arpspoof. You also need to enable IP forwarding on the attacker machine so traffic isn't dropped: `echo 1 > /proc/sys/net/ipv4/ip_forward`.

    Detection: ARP monitoring tools like ArpWatch alert on IP-MAC mapping changes. Managed switches can run Dynamic ARP Inspection (DAI), which validates ARP packets against a trusted DHCP snooping binding table and drops unauthorized ARP replies."

---

### Q5. What is the difference between a stateful and stateless firewall?

??? note "Concept Answer"
    A stateless firewall inspects each packet independently against ACL rules (source IP, dest IP, ports, protocol) with no memory of previous packets. A stateful firewall tracks connection state in a state table — it knows whether a packet belongs to an established connection.

??? warning "What the Interviewer Is Testing"
    Practical scanning implications — specifically Nmap's ACK scan, which exploits the difference. They want to see if you know why firewalls matter for pentest technique selection.

??? success "Model Answer to Give"
    "A stateless firewall evaluates each packet in isolation against rules. It doesn't know whether an ACK packet is part of an established connection or an unsolicited probe. This means a rule like 'allow TCP port 80 inbound' allows *any* TCP packet on port 80 — including a port scanner sending ACK packets.

    A stateful firewall maintains a connection state table. When a SYN is allowed through, an entry is created. Subsequent packets are matched against this table — an ACK with no matching connection entry is dropped.

    From a scanning perspective, Nmap's ACK scan (`-sA`) exploits this difference: send ACK packets to various ports. If the port returns RST, the packet reached the host (passed the firewall). If nothing comes back, the firewall is stateful and dropped it. This doesn't tell you if a port is open or closed, but it maps which ports pass through the firewall — useful for understanding firewall rulesets during an external assessment.

    Application layer firewalls (WAFs) go further — they inspect HTTP payloads for attack patterns. They can block SQLi payloads, XSS, etc., but can often be bypassed through encoding, case manipulation, or parser confusion."

---

### Q6. What is DNS and what is a zone transfer? Why is it a security issue?

??? note "Concept Answer"
    DNS translates domain names to IP addresses. A zone transfer (AXFR) is a mechanism for secondary nameservers to copy an entire zone's records from the primary. Misconfigured nameservers allow zone transfers from any IP.

??? warning "What the Interviewer Is Testing"
    OSINT and reconnaissance fundamentals. Zone transfers are one of the first things tested during external recon. They want to see if you know the command and understand why it's a finding.

??? success "Model Answer to Give"
    "DNS is the distributed system that resolves hostnames to IPs. The resolution walks a hierarchy: root nameservers know who manages .com, .com nameservers know who manages example.com, and example.com's authoritative nameserver knows all the specific records.

    A zone transfer is a complete copy of a DNS zone — meant for secondary nameservers to synchronize with the primary. The problem is when a nameserver is misconfigured to serve zone transfers to any requester, not just authorized secondary nameservers.

    ```bash
    dig axfr @ns1.example.com example.com
    ```

    If this succeeds, we receive every DNS record in the zone — every subdomain, internal hostname, mail server, and sometimes even commentary in TXT records. This is a critical finding in external pentests because it maps the entire DNS infrastructure: we can identify internal server names, development/staging subdomains, mail servers, and VPN gateways that wouldn't otherwise be visible. It compresses hours of subdomain enumeration into seconds.

    Even if the zone transfer fails, we still record the attempt — the fact that AXFR is disabled is noted, but we also check all nameservers (there may be secondary NS servers that are misconfigured even if the primary isn't)."

---

## OS and System Questions

---

### Q7. What is the difference between /etc/passwd and /etc/shadow in Linux? Why does the split exist?

??? note "Concept Answer"
    `/etc/passwd` contains user account information readable by all users. `/etc/shadow` contains password hashes and is readable only by root. The split exists because `/etc/passwd` must be world-readable (many programs use it to look up user information), but the password hashes should not be exposed.

??? warning "What the Interviewer Is Testing"
    Linux fundamentals and the reasoning behind security design decisions. They want to know if you'd recognize that grabbing `/etc/shadow` requires root — and that `/etc/passwd` still has useful reconnaissance value.

??? success "Model Answer to Give"
    "Before shadow passwords were introduced, all user info including password hashes lived in `/etc/passwd`, which needs to be world-readable because programs like `ls` use it to map UIDs to usernames. Once computing power made offline hash cracking feasible, that design became a liability.

    The fix was to split it. `/etc/passwd` retains user information (username, UID, GID, home directory, shell) but the password field is replaced with 'x' — a placeholder. The actual password hashes moved to `/etc/shadow`, owned by root with mode 640 or 000.

    During a pentest, `/etc/passwd` is still valuable even without root access — it gives us every username on the system, their home directories, and which shell they use. Shell set to `/usr/sbin/nologin` or `/bin/false` means the account shouldn't be able to log in interactively. UIDs help us identify service accounts vs human accounts.

    If we gain root (or use a SUID vulnerability), `/etc/shadow` is the target — those hashes can be cracked offline with hashcat or john, potentially giving us credentials that are reused elsewhere in the environment."

---

### Q8. What is SUID and how is it abused for privilege escalation?

??? note "Concept Answer"
    SUID (Set User ID) is a Linux permission bit that causes an executable to run with the file owner's effective UID rather than the executing user's UID. If root owns a SUID binary, any user who executes it gets a process with effective UID 0 (root).

??? warning "What the Interviewer Is Testing"
    Linux privilege escalation fundamentals — one of the most tested privesc techniques. They want to know how to find SUID binaries and how to abuse them, including GTFOBins awareness.

??? success "Model Answer to Give"
    "SUID causes a process to inherit the file owner's UID when executed. Legitimate uses include `passwd` (needs to write to `/etc/shadow` as root) and `ping` (needs raw socket access).

    The abuse: if a binary owned by root has SUID set, executing it gives root privileges for that process. Some binaries allow escaping to a shell or running arbitrary commands. For example:

    ```bash
    # Find SUID binaries owned by root
    find / -perm -4000 -user root -type f 2>/dev/null

    # If 'find' itself has SUID:
    find . -exec /bin/bash -p \; -quit
    # -p = privileged mode, preserves EUID=0

    # If 'vim' has SUID:
    vim -c ':!/bin/bash -p'

    # If 'python3' has SUID:
    python3 -c 'import os; os.setuid(0); os.system("/bin/bash")'
    ```

    GTFOBins (gtfobins.github.io) is the reference — it catalogs every Unix binary that can be abused under SUID, sudo, or other elevated permission scenarios.

    Capabilities are the modern, granular alternative — instead of full SUID, a binary might have `cap_setuid` or `cap_net_raw`. Same abuse potential:

    ```bash
    getcap -r / 2>/dev/null  # find files with capabilities
    ```"

---

### Q9. What is the Windows Registry and why does it matter in pentesting?

??? note "Concept Answer"
    The Windows Registry is a hierarchical database storing OS, application, hardware, and user configuration. It's organized into hives — HKLM (machine-wide), HKCU (current user), HKEY_USERS, HKCR, HKCC.

??? warning "What the Interviewer Is Testing"
    Windows fundamentals awareness. They want to know if you can point to specific registry locations relevant to post-exploitation — persistence mechanisms, credential storage, auto-run keys, service configuration.

??? success "Model Answer to Give"
    "The registry is essentially Windows's central configuration database. Everything from OS settings to application preferences to service definitions lives there.

    For pentesting, the most relevant locations are:

    **Persistence:** `HKLM\Software\Microsoft\Windows\CurrentVersion\Run` and the HKCU equivalent — any key here executes at login. Malware often plants persistence here.

    **Credentials:** `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon` — if autologon is configured, `DefaultUserName` and `DefaultPassword` may be stored here in cleartext.

    **Services:** `HKLM\SYSTEM\CurrentControlSet\Services\` — every service definition, including the binary path. If a low-privileged user can write the binary path key for a service running as SYSTEM, that's privilege escalation.

    **WDigest:** `HKLM\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest\UseLogonCredential` — if set to 1, LSASS caches credentials in cleartext. Attackers enable this for persistence after initial compromise to harvest future credentials.

    **AlwaysInstallElevated:** If both `HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer\AlwaysInstallElevated` and the HKCU equivalent are set to 1, any MSI package installs as SYSTEM — instant privilege escalation by crafting a malicious MSI.

    During post-exploitation I typically query the Run keys, check for AlwaysInstallElevated, look for saved credentials, and review service binary paths for writable paths."

---

### Q10. What is Pass-the-Hash?

??? note "Concept Answer"
    Pass-the-Hash (PtH) is an attack where an attacker uses a captured NTLM hash directly to authenticate without knowing the plaintext password. Because NTLM authentication uses the hash itself (not the plaintext) in the challenge-response, the hash is the credential.

??? warning "What the Interviewer Is Testing"
    Understanding of Windows authentication fundamentals and lateral movement. This is a mid-level concept being asked at entry level to gauge depth. If you know it thoroughly, you stand out.

??? success "Model Answer to Give"
    "NTLM authentication works as a challenge-response protocol where the server sends a challenge and the client responds with a function of the NT hash of their password applied to the challenge. Crucially, the NT hash itself is what's used — not the plaintext password.

    If an attacker extracts NT hashes from the SAM database or LSASS memory, they can use those hashes directly in NTLM authentication without ever cracking them to plaintext. This is Pass-the-Hash.

    For example, with Mimikatz:
    ```
    sekurlsa::logonpasswords  # dump hashes from LSASS
    ```

    Then with impacket:
    ```bash
    psexec.py -hashes :NThash DOMAIN/username@target-ip
    ```

    The colon before the hash means we're providing NT hash only (no LM hash).

    PtH works because NTLM never transmits or verifies the plaintext — the hash is the authentication credential. Mitigation: enforce Kerberos authentication where possible (Kerberos uses tickets, not hashes for authentication), restrict NTLM, implement Credential Guard to protect LSASS memory from dumping, and use Protected Users security group for privileged accounts."

---

## Security Concepts Questions

---

### Q11. What is the CIA triad? Give a real example of how a pentest finding maps to each component.

??? note "Concept Answer"
    CIA = Confidentiality (access restricted to authorized parties), Integrity (data is accurate and unmodified), Availability (systems accessible when needed). Almost every security control exists to protect one or more of these properties.

??? warning "What the Interviewer Is Testing"
    This is a fundamentals filter question. Beyond naming the three, they want a real-world mapping — ideally from your own experience or a credible scenario. The goal is to see if the framework is something you actually use, not just memorize.

??? success "Model Answer to Give"
    "Confidentiality, Integrity, and Availability.

    From a pentest perspective:

    **Confidentiality** — SQL injection in a login form that allows me to dump the users table directly maps to confidentiality. The database contained usernames, hashed passwords, email addresses, and PII that was accessible without authentication. Unauthorized access to data is a classic confidentiality failure.

    **Integrity** — SQL injection with write capability (`INSERT`, `UPDATE`, `DELETE`) or stored XSS where a low-privileged user injects a script that executes in an admin's browser (potentially modifying data on the admin's behalf) are integrity failures. The system can be altered in ways it shouldn't allow.

    **Availability** — If during a test I find a resource exhaustion vulnerability — say, an unauthenticated API endpoint that triggers an expensive operation and has no rate limiting — exploiting it could crash the server. Even though we typically don't execute DoS attacks, documenting the *potential* is an availability finding.

    In my reports I always map each finding to the CIA impact, which helps executives understand *why* a CVSS 7.5 vulnerability on an internal system might be less urgent than a CVSS 6.0 finding on a public-facing payment API."

---

### Q12. What is the difference between encryption and hashing? Why does it matter for password storage?

??? note "Concept Answer"
    Encryption is reversible with a key. Hashing is a one-way function — the output (digest) cannot be reversed to the input. For password storage, hashing is correct because the system never needs to "see" the original password again — it just hashes what the user provides at login and compares.

??? warning "What the Interviewer Is Testing"
    A critical concepts test that reveals whether you understand security fundamentals vs security theater. Candidates who say "passwords should be encrypted" immediately signal a gap. This is a common trap for people who've used security tools without understanding the underlying concepts.

??? success "Model Answer to Give"
    "Encryption is bidirectional — given the ciphertext and key, you can recover the plaintext. Hashing is one-way — given the hash, you cannot compute the input.

    For passwords, hashing is the correct approach because the system only needs to *verify* a password, never recover it. At login: take the input, hash it, compare to stored hash. If an attacker breaches the database, they get hashes — they have to crack them offline rather than immediately having plaintext.

    But not all hashing is equal for passwords:
    - MD5 and SHA-256 are designed to be fast — billions of hashes per second on a GPU, making brute force trivial.
    - Passwords must use slow, salted algorithms: bcrypt, scrypt, Argon2, or PBKDF2. These are intentionally expensive to compute — a bcrypt hash takes ~100ms to verify, making brute force attacks on a breached hash database orders of magnitude slower.
    - Salt — a random per-user value added before hashing — defeats precomputed rainbow tables.

    When I find a web app storing passwords in MD5 without salt, that's a critical finding — it means anyone who breaches the database effectively has immediate access to plaintext passwords, especially since most users reuse passwords across services. If the system can 'retrieve' your password (not just reset it), the passwords are encrypted, not hashed — also a critical finding.

    Encoding (Base64) is neither — it's a representation change anyone can reverse. Calling Base64 'encryption' is a red flag that indicates a developer has fundamentally misunderstood security."

---

### Q13. What is the difference between authentication and authorization? Give a vulnerability example for each.

??? note "Concept Answer"
    Authentication verifies identity ("who are you?"). Authorization verifies permissions ("what are you allowed to do?"). They are separate controls and can fail independently.

??? warning "What the Interviewer Is Testing"
    Many candidates conflate these. Interviewers want to confirm you understand them as distinct controls and can map specific vulnerability classes to each.

??? success "Model Answer to Give"
    "Authentication is the process of verifying identity — proving you are who you claim to be. Authorization is the process of verifying permissions — once I know who you are, what are you allowed to do?

    They fail independently:

    **Authentication bypass** — SQL injection in a login form: `username = admin'--`. This comments out the password check, so the query succeeds with any password. The system authenticates without verifying credentials. Another example: a JWT token where the algorithm can be changed to 'none' and the signature is not validated — the server accepts tokens without verification.

    **Authorization failure (broken access control)** — IDOR (Insecure Direct Object Reference): I'm authenticated as user_id=100 and I request `/api/profile?id=101`. If the application doesn't verify that user 100 is authorized to view user 101's profile, I get another user's data. I passed authentication (I have a valid session) but the authorization check is missing.

    In practice, authorization is more commonly broken than authentication in modern applications. Applications invest in strong login forms but then fail to check every API endpoint. This is why OWASP lists 'Broken Access Control' as A01 — the most critical web application vulnerability category.

    In my testing, after I find any authenticated endpoint, I systematically check: can I access other users' resources? Can I escalate to higher privilege endpoints (user → admin)? Can I perform actions the UI hides from me but the API doesn't restrict?"

---

### Q14. Explain symmetric vs asymmetric encryption. How are they used together in TLS?

??? note "Concept Answer"
    Symmetric: one key for encrypt/decrypt, fast, key distribution problem. Asymmetric: public/private key pair, slow, solves key distribution. TLS uses asymmetric to securely exchange a symmetric session key, then uses symmetric for all data transfer.

??? warning "What the Interviewer Is Testing"
    Protocol understanding depth. The combination question reveals whether you understand *why* TLS exists the way it does, not just what TLS is. The "why not just use asymmetric for everything?" follow-up is common.

??? success "Model Answer to Give"
    "Symmetric encryption uses a single shared key — the same key encrypts and decrypts. It's fast and efficient for bulk data, but the key distribution problem: how do two parties securely share a key over an insecure channel?

    Asymmetric encryption uses a mathematically related key pair — public key (share freely) and private key (keep secret). What you encrypt with one, only the other can decrypt. It solves key distribution — I can publish my public key anywhere. The downside is that it's computationally expensive, orders of magnitude slower than symmetric.

    TLS combines both to get the best of each:

    1. **Asymmetric phase (handshake):** Client and server use Diffie-Hellman key exchange (asymmetric) to establish a shared secret without ever sending that secret over the network. Both sides arrive at the same secret independently through the math of DH.

    2. **Symmetric phase (data transfer):** The shared secret from the DH exchange is used to derive symmetric session keys. All actual HTTP data is encrypted with AES-256-GCM — fast symmetric encryption.

    So: asymmetric solves the key distribution problem (no pre-shared secret needed), symmetric handles the bulk data efficiently. TLS 1.3 enforces Perfect Forward Secrecy (PFS) — each session uses ephemeral DH keys, so compromising the server's private key doesn't decrypt past sessions.

    In a pentest context: weak cipher suites, old TLS versions (1.0/1.1), missing HSTS, and certificate validation issues are all TLS-related findings I check with tools like `testssl.sh`."

---

### Q15. What is the principle of least privilege and why is it important?

??? note "Concept Answer"
    Least privilege means granting only the minimum access needed to perform a function. It limits the blast radius of a compromise — if a low-privileged account is compromised, the attacker has minimal access, not everything.

??? warning "What the Interviewer Is Testing"
    This comes up in both technical and conceptual interview rounds. They want to see if you apply this principle as a lens during assessments — not just state the definition.

??? success "Model Answer to Give"
    "Least privilege means every user, process, and system component should have only the minimum access necessary for its intended function — nothing more.

    Why it matters in practice: I regularly find violations of this principle during internal assessments.

    Common examples: a web application database account with DBA rights instead of just SELECT/INSERT on specific tables. A Windows service running as LocalSystem (which is essentially root) when it only needs network access. An AD user account that's a member of Domain Admins 'for convenience' even though they're a helpdesk analyst. A developer with production database write access.

    Each violation is a privilege escalation opportunity. If that web app is vulnerable to SQL injection and the DB account is DBA, an attacker gets `xp_cmdshell` — operating system command execution. If it were only SELECT, the same injection only reads data.

    My reporting always calls out least privilege violations even when they're not directly exploitable, because they're part of defense-in-depth. An account that has more privilege than it needs is a ticking bomb waiting for another vulnerability to amplify it.

    The corollary — need-to-know — applies to data access: just because someone can access a system doesn't mean they should access all data on it. Segmenting data access is as important as segmenting system access."

---

## Pentesting Concepts Questions

---

### Q16. What is the difference between a vulnerability assessment and a penetration test?

??? note "Concept Answer"
    VA identifies and classifies vulnerabilities without exploiting them. PT exploits vulnerabilities to demonstrate real-world impact. VA tells you what might be vulnerable; PT tells you what is actually exploitable and what an attacker could achieve.

??? warning "What the Interviewer Is Testing"
    This is scoping knowledge — fundamental for both client communication and interview differentiation. Many candidates blur the line. A clear, confident distinction with examples signals experience.

??? success "Model Answer to Give"
    "A vulnerability assessment is a systematic enumeration exercise — we run scanners, perform manual checks, identify weaknesses, score them by CVSS, and report them. We don't exploit anything. The output is: 'these vulnerabilities exist, here's their severity.'

    The limitation is that a VA can't distinguish between a vulnerability that's actually exploitable in this environment versus one that a scanner flagged but that doesn't apply due to compensating controls or configuration specifics. It also can't show the chained impact — an attacker rarely exploits a single critical vulnerability; they chain medium-severity issues to achieve high impact.

    A penetration test goes further — we exploit the vulnerabilities we find. If we confirm SQL injection, we demonstrate what data we can extract. If we find a foothold on an internal server, we pivot and show what we can reach from there. The deliverable isn't just 'these vulnerabilities exist' but 'an attacker exploiting these vulnerabilities could reach the finance database and extract customer payment records.'

    In my work, the distinction matters for scoping: a client asking for an ASV scan for PCI compliance needs a VA, not a PT. A client who wants to know if their new internal network design is actually secure needs a PT. The ROE is also different — a VA doesn't include exploitation authorization; a PT does."

---

### Q17. What is black box, white box, and grey box testing?

??? note "Concept Answer"
    Black box: no prior knowledge. White box: full knowledge (credentials, architecture, source). Grey box: partial knowledge (some credentials, some architecture). Each simulates a different threat model.

??? warning "What the Interviewer Is Testing"
    They want to see if you can articulate tradeoffs and recommend the right approach for different scenarios. This also reveals whether you've actually been in client conversations where this distinction matters.

??? success "Model Answer to Give"
    "The names refer to how much information the tester is given before starting.

    **Black box:** We know only the target's name or IP range. We simulate an external attacker with no insider advantage. This is the most realistic simulation of an external threat, but it's the least efficient use of budget — we spend significant time on reconnaissance that internal teams already know. Risk: we may miss significant internal vulnerabilities.

    **White box:** We receive full credentials, architecture diagrams, source code, infrastructure documentation. This maximizes coverage — we can test every component including those not reachable externally, review code, and focus testing time on actual vulnerabilities rather than information gathering. Source code review requires white box by definition.

    **Grey box:** We get partial information — often user-level credentials and some basic documentation. This is the most common in practice. It realistically simulates a compromised internal user (an attacker who's phished an employee, for example) while being more efficient than black box.

    My recommendation varies by client objective: if they want to know 'can an external attacker get in,' black box EPT is appropriate. If they want 'how much damage can an insider or compromised account do,' grey box IPT makes more sense. If they want 'find everything,' white box with source code review covers the most ground per dollar."

---

### Q18. What should you do if during a pentest you find evidence that the system is already compromised by a real attacker?

??? note "Concept Answer"
    Stop testing immediately. Document what you observed. Notify the client's point of contact immediately. Do not continue, do not investigate the other attacker — that's incident response, not pentest scope.

??? warning "What the Interviewer Is Testing"
    Professional judgment and ethics. This comes up because it actually happens, and the wrong answer (continue testing, investigate the attacker yourself, keep quiet until the report) reveals serious professional deficiencies.

??? success "Model Answer to Give"
    "Stop immediately and notify the client. This is non-negotiable.

    If I see active connections I didn't create, unfamiliar processes, recent file modifications I didn't make, or any artifact suggesting another actor — I document exactly what I observed with timestamps and screenshots, then call the designated emergency contact from the ROE immediately. Not email — phone call.

    I don't continue testing. Testing on a compromised system creates confusion about what the attacker did versus what I did, potentially destroying forensic evidence needed for the incident investigation. My authorization is for a pentest, not incident response — those are separate engagements with separate scope and legal implications.

    I also don't try to 'investigate' the other attacker. Even if I identify their C2 or methods, touching their infrastructure (out of scope by definition) could be criminal, and probing an active attacker's systems could alert them and cause them to accelerate or change behavior.

    Once I've notified the client, I wait for their direction. They may pause the engagement while IR is handled. The client decides whether to continue the pentest after the incident is contained.

    This situation is why ROE documents always include an emergency contact and a clear clause about what to do if an active incident is discovered — having that protocol established before testing starts means no one has to make judgment calls under pressure."

---

### Q19. What does CVSS stand for and how is the severity score calculated?

??? note "Concept Answer"
    CVSS = Common Vulnerability Scoring System. Version 3.1 uses a base score from 8 metrics across three groups: Exploitability (AV, AC, PR, UI), Scope (S), and Impact (C, I, A). Scores 0.0–10.0, mapped to None/Low/Medium/High/Critical.

??? warning "What the Interviewer Is Testing"
    Whether you understand that CVSS is a *base* score and doesn't tell the whole story — business context can change effective severity significantly. They also want to see you know the metric abbreviations if you use the term in interviews.

??? success "Model Answer to Give"
    "CVSS v3.1 calculates a base score from 8 metrics:

    **Exploitability metrics:**
    - **AV (Attack Vector):** How is the vulnerability accessed? Network (internet-reachable, highest risk) > Adjacent (same network/Bluetooth) > Local (requires local access) > Physical.
    - **AC (Attack Complexity):** Low (exploit is straightforward, repeatable) or High (specific conditions required, not always achievable).
    - **PR (Privileges Required):** None, Low, or High — how much access does the attacker already need?
    - **UI (User Interaction):** None (no victim action required) or Required (victim must click, open file, etc.).

    **Scope (S):** Has the impact changed from the vulnerable component to other components? Unchanged = impact limited to the vulnerable component. Changed = impact can extend to other components (e.g., a VM escape affecting the hypervisor).

    **Impact metrics:**
    - **C (Confidentiality Impact):** None / Low / High
    - **I (Integrity Impact):** None / Low / High
    - **A (Availability Impact):** None / Low / High

    Score ranges: 0.0 = None, 0.1–3.9 = Low, 4.0–6.9 = Medium, 7.0–8.9 = High, 9.0–10.0 = Critical.

    Importantly: CVSS base score doesn't reflect actual business risk. An unauthenticated RCE (CVSS 9.8) on an isolated internal dev server with no sensitive data may be lower *business* risk than a CVSS 5.0 authentication bypass on a customer-facing payment portal. In my reports I always include contextual severity — the base CVSS score plus the specific business impact given the environment."

---

### Q20. What is social engineering and what are the main categories?

??? note "Concept Answer"
    Social engineering manipulates humans rather than systems to achieve unauthorized access or information. Categories: phishing (email), spear phishing (targeted email), vishing (voice), smishing (SMS), pretexting, baiting (physical media), tailgating/piggybacking (physical access).

??? warning "What the Interviewer Is Testing"
    Breadth of security knowledge. Even as a technical pentester, you'll work with clients who need social engineering assessments, and you need to articulate each type clearly.

??? success "Model Answer to Give"
    "Social engineering targets the human element rather than technical controls. It's often the path of least resistance — it's easier to trick someone into handing over credentials than to exploit a hardened perimeter.

    The main categories:

    **Phishing:** Mass email campaigns impersonating trusted senders, directing recipients to fake login pages or malicious attachments. High volume, low targeting — designed to catch the small percentage who click.

    **Spear phishing:** Highly targeted phishing. The attacker researches the target specifically — LinkedIn, company website, recent press releases — to craft a convincing pretext. 'Hi [Name], this is [Name of real colleague] from [correct department]. Please review the attached Q3 report.' Much higher success rate.

    **Vishing (voice phishing):** Phone calls impersonating IT support, banks, government agencies. 'This is IT, we've detected suspicious activity on your account. Can you confirm your password so I can lock it down?'

    **Smishing:** SMS-based phishing. 'Your parcel delivery failed. Reschedule here: [malicious link].'

    **Pretexting:** Building a fabricated scenario (the pretext) to establish credibility. 'I'm from the auditing firm, here to review your financial systems' — followed by requesting system access.

    **Baiting:** Leaving malicious USB drives in parking lots, reception areas, etc., labeled 'Salary Information' or 'Confidential.' Curiosity drives victims to plug them in.

    **Tailgating/Piggybacking:** Physical access by following an authorized person through a secured door. 'My hands are full, could you hold the door?'

    In a pentest context, a phishing campaign is typically authorized separately from technical testing, with specific rules around which employees can be targeted and what actions are permitted."

---

### Q21. What is the difference between IDS and IPS?

??? note "Concept Answer"
    IDS (Intrusion Detection System) monitors traffic and generates alerts — it does not block. IPS (Intrusion Prevention System) is inline and actively blocks malicious traffic. IDS is passive, IPS is active.

??? warning "What the Interviewer Is Testing"
    Whether you understand detection vs prevention architecture, and whether you can connect this to why evasion techniques exist.

??? success "Model Answer to Give"
    "An IDS sits out-of-band — it receives a copy of traffic (via SPAN port or tap) and analyzes it. When it detects a signature match or anomaly, it generates an alert. It cannot block traffic because it's not in the traffic path.

    An IPS is inline — all traffic passes through it. When it detects malicious traffic, it can drop or modify the packets in real time. The tradeoff: if the IPS has a false positive or fails, it can block legitimate traffic or take down the network. IPS failures are why some organizations prefer IDS mode even when their hardware supports IPS.

    Detection methods:
    - **Signature-based:** Match traffic against known attack patterns. Fast and accurate for known attacks, blind to novel attacks.
    - **Anomaly-based:** Establish a baseline of normal behavior and alert on deviations. Catches novel attacks but generates high false positives.
    - **Behavioral:** Watch for sequences of actions that match attack patterns regardless of specific signatures.

    Pentesting implication: IDS/IPS evasion is a real skill. Common techniques include: fragmentation (split attack payload across fragments the IDS doesn't reassemble), encoding (URL encoding, Unicode encoding to bypass string-match signatures), traffic blending (use timing and packet sizes that match legitimate traffic patterns), and protocol-level evasion (exploit parser differences between what the IDS sees and what the target processes).

    During an engagement, detecting that an IDS is present changes technique selection — you move from noisy scans to slower, more surgical approaches."

---

### Q22. What is the purpose of network segmentation?

??? note "Concept Answer"
    Network segmentation divides a network into zones with controlled, restricted communication between them. Limits lateral movement — a compromise in one segment doesn't automatically give access to all other segments.

??? warning "What the Interviewer Is Testing"
    Defense-in-depth understanding and relevance to segmentation testing assessments. They want to see that you understand both the defensive purpose and the pentest objective.

??? success "Model Answer to Give"
    "Network segmentation creates security zones with firewall rules or ACLs controlling what can communicate with what. The goal is blast radius limitation — if an attacker compromises a host in the DMZ, they shouldn't be able to directly reach the core banking database.

    Common segmentation architectures:
    - **DMZ (Demilitarized Zone):** Public-facing servers (web servers, email) in a separate segment. DMZ can reach internet, cannot directly reach internal LAN.
    - **PCI segmentation:** Cardholder data environment (CDE) isolated from the rest of the corporate network. PCI-DSS requirement.
    - **OT/ICS segmentation:** Industrial control systems isolated from IT networks. A breach of the IT network shouldn't allow access to factory floor PLCs.
    - **Admin network:** Management interfaces (IPMI, IDRAC, switch management) on a separate out-of-band network.

    Segmentation testing validates these controls actually work — not just that firewall rules exist, but that you cannot route from segment A to segment B through any path. I've found environments where the 'segmented' PCI network was actually reachable from the corporate network via a misconfigured switch, or where an out-of-scope OT SCADA server was reachable from a compromised web server.

    Testing methodology: attempt connections from each in-scope segment to out-of-scope segments across all relevant ports. Document every path that succeeds. A 'segmentation failure' finding is typically critical — it undermines the entire network security architecture."

---

### Q23. What is a CVE? What is CVSS? How are they different?

??? note "Concept Answer"
    CVE is an identifier for a specific vulnerability. CVSS is a scoring system measuring severity. A CVE identifies what the vulnerability *is*; CVSS quantifies how severe it *is*.

??? warning "What the Interviewer Is Testing"
    Basic security vocabulary, surprisingly often confused. They're also checking if you know where to look these up (NVD, Mitre, vendor advisories).

??? success "Model Answer to Give"
    "CVE — Common Vulnerabilities and Exposures — is a unique identifier for a specific, publicly known vulnerability. For example, CVE-2021-44228 is Log4Shell (remote code execution in Apache Log4j). MITRE maintains the CVE program; once a vulnerability is reported and validated, it gets a CVE number. This standardizes how vulnerabilities are referenced across tools, reports, and discussions.

    CVSS — Common Vulnerability Scoring System — is a framework for rating the severity of vulnerabilities. It produces a score from 0.0 to 10.0 based on characteristics like attack vector, complexity, privileges required, and potential impact on CIA.

    The relationship: a CVE *has* a CVSS score. NVD (National Vulnerability Database, nvd.nist.gov) publishes CVSS scores for CVEs. Log4Shell (CVE-2021-44228) was scored CVSS 10.0 — maximum.

    In practice: when I find a vulnerability during a pentest, I check NVD to see if it has a CVE (meaning it's known and patched). If it does, I include the CVE in my report, and the CVSS base score. I then also include my own contextual assessment — because CVSS base scores don't account for the specific environment. A CVSS 10.0 in a completely isolated lab environment may be lower priority than a CVSS 7.5 in a payment card processing system."

---

### Q24. What is a firewall rule ordering problem?

??? note "Concept Answer"
    Firewall rules are evaluated top-to-bottom with first-match-wins semantics. A permissive rule placed before a restrictive rule can silently bypass the restriction, because the traffic matches the permissive rule first and is allowed before ever reaching the deny rule.

??? warning "What the Interviewer Is Testing"
    Config review and firewall analysis fundamentals. This is relevant when reviewing firewall configurations during assessments.

??? success "Model Answer to Give"
    "Most firewalls evaluate rules sequentially from top to bottom and apply the first matching rule. This means rule order matters critically.

    Classic problem: imagine these rules in order:
    ```
    1. ALLOW TCP from ANY to ANY port 443
    2. DENY TCP from untrusted_subnet to internal_server port 443
    ```

    Rule 2 never fires for traffic from untrusted_subnet to internal_server because Rule 1 matches first — it allows all TCP to port 443. The deny rule is shadowed.

    The correct order:
    ```
    1. DENY TCP from untrusted_subnet to internal_server port 443
    2. ALLOW TCP from ANY to ANY port 443
    ```

    Now the specific deny is checked before the broad allow.

    In config review engagements, I look for:
    - Overly broad ALLOW rules early in the chain
    - Shadowed DENY rules (deny rules that come after a broader allow rule they can never match)
    - Missing default-deny at the end (if no rule matches, the default should be DENY, not ALLOW)
    - Rules with ANY source or ANY destination that are too permissive

    I use tools like `nipper-ng` or manual analysis for firewall config reviews, and I specifically look for rules that allow traffic that should be blocked based on the intended segmentation design."

---

### Q25. What is the difference between a vulnerability, a threat, and a risk?

??? note "Concept Answer"
    Vulnerability = weakness. Threat = potential event that exploits the weakness. Risk = likelihood × impact of a threat exploiting a vulnerability. Risk is the combination of all three factors including asset value.

??? warning "What the Interviewer Is Testing"
    Conceptual precision. This is a GRC-leaning question but relevant for anyone who writes pentest reports — you need to correctly label findings.

??? success "Model Answer to Give"
    "These three terms are often conflated, especially in client conversations.

    **Vulnerability** is a weakness in a system, process, or control. An unpatched SQL injection vulnerability in a web form, a default password on a network device, a missing firewall rule.

    **Threat** is anything that could exploit a vulnerability and cause harm — an external hacker, a malicious insider, ransomware, a natural disaster, accidental user error. Threats are entities or events, not technical weaknesses.

    **Risk** is the intersection: what's the likelihood that a specific threat will exploit a specific vulnerability, and what's the impact if it does? Risk = Likelihood × Impact.

    Example: An unpatched authentication bypass in an internal HR system is a vulnerability. The threat is any employee (insider) or attacker who's gained internal network access. The risk depends on: how many people have internal network access? How attractive is the HR data (PII, salary info)? Are there compensating controls (SIEM alerts on unauthorized HR access)?

    In pentesting: I document vulnerabilities and demonstrate exploitability (confirming the vulnerability is real, not theoretical). I estimate business risk by combining CVSS base score, exploitability evidence, asset sensitivity, and the threat actors relevant to the client. A vuln with high exploitability and high-value target data = high business risk. The same vuln on a non-sensitive system with limited exposure = lower business risk."

---

!!! tip "Practice Tip"
    These 25 questions represent the most commonly asked Level 0 questions. Before your interview, practice answering each one out loud without reading the model answer. Stumbling means you need more internalization, not just more reading.

    Time yourself — each answer should be 90 seconds to 3 minutes. Too short means you're missing depth. Too long means you're rambling.
