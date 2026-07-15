# Segmentation Testing

!!! info "Why This Matters"
    Network segmentation is a primary defense control — it limits lateral movement and contains breaches. Segmentation testing verifies these controls actually work. A failed segmentation test is often a Critical finding because it means the entire network architecture assumption is invalid.

---

## What Is Segmentation Testing?

Segmentation testing validates that network zones are properly isolated — that a host in Zone A cannot reach hosts or services in Zone B unless explicitly permitted by design. This is distinct from a full penetration test — the goal is not to exploit vulnerabilities, but to verify that firewall rules, ACLs, and routing configurations enforce the intended segmentation.

**Common segmentation requirements:**
- **PCI-DSS:** The cardholder data environment (CDE) must be isolated from all other networks. Scope creep in PCI is a critical finding.

- **OT/ICS/SCADA:** Industrial control systems must be isolated from IT networks.

- **Management network:** Out-of-band management (IPMI, iDRAC, switch management) must be isolated.

- **DMZ:** Internet-facing systems in DMZ must not directly reach internal LAN.

- **Guest WiFi:** Guest network must not reach corporate network.

- **Development:** Dev/test environments isolated from production.

---

## Testing Methodology

### Pre-Test: Understand the Intended Design

Before testing, obtain:

- Network topology diagram

- Intended segmentation design (which zones exist, what's allowed between them)

- Firewall ruleset (if available — config review plus segmentation testing is more thorough)

Without the design document, you're testing blindly and can't verify what *should* be blocked.

### Step 1: Identify Your Position

```bash
# What network segment am I in?
ip a              # Linux
ipconfig /all     # Windows

# What can I reach at Layer 3?
ip route          # Linux routing table
route print       # Windows

# Gateway
ip route show default
```

### Step 2: Connectivity Testing

Test traffic from your source segment to each target segment across all relevant ports.

```bash
# Broad port scan from source to target network
nmap -sT -p- --min-rate 2000 [target_network] -oA segtest_[source_to_target]

# Targeted protocol-specific tests
# Can I reach the internal LAN from DMZ?
nmap -sT -p 22,23,80,443,445,3306,3389,8080 10.10.0.0/24

# Can guest WiFi reach corporate network?
# From guest WiFi IP, scan corporate subnet
nmap -sT -p 1-65535 192.168.1.0/24 --min-rate 3000

# Can PCI network reach non-PCI?
# Scan all company subnets from PCI host
for subnet in 10.0.0.0/24 10.1.0.0/24 192.168.0.0/24; do
    nmap -sT -p 1-1024 $subnet -oA pci_to_$(echo $subnet | tr /. __)
done
```

### Step 3: Protocol-Specific Tests

Beyond TCP port scanning, test other protocols that might bypass firewall rules:

```bash
# ICMP (ping) — often allowed even when other traffic is not
ping -c 3 [target_ip]

# UDP — often overlooked in firewall rules
nmap -sU -p 53,161,500,4500 [target_ip]

# ICMP tunneling test — can data be exfiltrated via ICMP?
# If ping works to an out-of-scope segment, data tunneling may be possible

# IPv6 — dual-stack environments often have weaker IPv6 rules
ping6 -c 3 [target_ipv6]
nmap -6 [target_ipv6_network]

# Check if VLAN hopping is possible (requires switch access)
# Use tools like yersinia, dtp-test
```

### Step 4: Application Layer Testing

Firewall may allow specific ports but block at application layer — test actual connectivity:

```bash
# Test web access from DMZ to internal
curl http://internal-server.corp.local
curl https://internal-server.corp.local

# Test database connectivity from DMZ to internal DB
# MySQL:
mysql -h internal-db.corp.local -u test -p -e "SELECT 1" 2>&1

# Test if web server in DMZ can reach internal API
curl http://10.10.1.50:8080/internal-api
```

### Step 5: Document Every Result

For each tested path, document:

```
Source: DMZ Web Server (192.168.10.50, VLAN 10)
Target: Internal Database (10.10.0.100, VLAN 100)
Port: TCP/3306 (MySQL)
Result: OPEN — connection established (FINDING: segmentation failure)
Expected: BLOCKED

Source: DMZ Web Server (192.168.10.50, VLAN 10)  
Target: Internal File Server (10.10.0.200, VLAN 100)
Port: TCP/445 (SMB)
Result: FILTERED — no response (PASS)
Expected: BLOCKED
```

---

## Common Segmentation Failures

| Failure | Root Cause | Impact |
|---------|-----------|--------|
| DMZ can reach internal LAN | Firewall misconfiguration, missing deny rule | Breach of DMZ → full internal access |
| Guest WiFi reaches corporate | VLAN misconfiguration on switch | Guest → corporate lateral movement |
| PCI scope creep | Firewall allows CDE to non-CDE | PCI-DSS scope violation, compliance failure |
| OT network reachable from IT | Missing firewall between IT and OT | IT breach → industrial control system access |
| Flat network (no segmentation) | No VLAN/firewall separation at all | Any compromised host = full network access |
| Management network accessible | Management VLAN not properly isolated | Access to all device management interfaces |
| IPv6 segmentation missing | Only IPv4 rules, IPv6 unfiltered | Bypass IPv4 firewall via IPv6 |

---

# Interview Q&A — Mid-Level

!!! tip "What Changes at This Level"
    Interviewers at mid-level expect you to have real engagement stories. "In a recent assessment, I found..." is expected, not impressive. What's impressive is the *depth* of your reasoning and your ability to chain findings, adapt techniques, and explain business impact precisely.

---

### Q1. You're performing an Android penetration test on a banking app with certificate pinning. Walk me through your bypass approach.

??? success "Model Answer to Give"
    "First I confirm pinning is actually implemented — I set up Burp as proxy on the device, and if the app throws a certificate error or just fails to load while my CA is installed on the device, that confirms pinning.

    My first attempt is always objection's built-in bypass: `android sslpinning disable`. This hooks the most common pinning implementations — OkHttp3 CertificatePinner, TrustManager, Conscrypt — and works probably 60% of the time without any additional work.

    If that fails, I look at the decompiled code to understand the specific implementation:
    ```bash
    jadx -d output/ app.apk
    grep -r 'CertificatePinner\|TrustManager\|checkServerTrusted\|hostnameVerifier' output/
    ```
    
    If it's a custom TrustManager, I write a targeted Frida script that hooks the specific class and method, replacing the implementation with one that always returns without throwing.

    For React Native or Flutter apps, the pinning lives in native code. I use Frida to hook the native SSL functions — `SSL_CTX_set_verify` or platform-specific APIs. There are community scripts for common frameworks.

    If the app detects Frida (some banking apps do), I use Magisk modules to hide root and Frida, or use a custom Frida gadget compiled into the app via APK repackaging.

    Last resort: APK modification — decompile with apktool, modify the `network_security_config.xml` to trust user CAs, repackage and sign. This works for apps using Android's built-in pinning via network security config, though it requires bypass of any APK tampering detection as well.

    In my report, the absence of pinning is a Medium finding — it doesn't directly enable data theft, but it makes MITM attacks easier and removes a layer of defense."

---

### Q2. Explain how Kerberoasting works and what makes an account vulnerable.

??? success "Model Answer to Give"
    "Kerberoasting exploits the Kerberos ticket-granting process. In AD, any authenticated domain user can request a service ticket for any Service Principal Name (SPN). The KDC doesn't check authorization — it just validates that the requestor has a valid TGT. The service ticket is encrypted with the service account's NTLM hash.

    The attack: request the service ticket, extract it from memory, and crack it offline.

    ```bash
    # Enumerate accounts with SPNs
    GetUserSPNs.py -dc-ip 192.168.1.10 corp.local/user:password
    
    # Request the tickets
    GetUserSPNs.py -dc-ip 192.168.1.10 corp.local/user:password -request -outputfile kerberoast.txt
    
    # Crack
    hashcat -m 13100 kerberoast.txt /wordlists/rockyou.txt
    ```

    What makes an account vulnerable: it must have an SPN set — which marks it as a service account (SQL service, web service, custom applications). The vulnerability is the combination of SPN + weak password.

    Severity factors: service accounts often have high privileges — some are Domain Admins 'for convenience.' Even if they're not, service accounts often have service-level access that enables lateral movement. And service account passwords often don't expire and aren't changed frequently.

    Mitigation: use Managed Service Accounts (gMSA) — AD automatically manages passwords (240-character random) and rotates them. For accounts that must have SPNs, enforce long random passwords (25+ characters) and monitor for unusual TGS requests (many SPNs enumerated from one account in a short time window)."

---

### Q3. What is the difference between BOLA and BFLA in API security?

??? success "Model Answer to Give"
    "Both are access control failures but at different levels.

    BOLA — Broken Object Level Authorization — is a horizontal access control failure. You're authorized to access an object type, but you can access individual objects belonging to other users.
    ```
    GET /api/orders/10042    ← Your order
    GET /api/orders/10043    ← Another user's order (BOLA if you can read it)
    ```
    The authorization check is missing for the specific object — the API doesn't verify 'does this user own order 10043?'

    BFLA — Broken Function Level Authorization — is a vertical access control failure. You can access functions/endpoints that require a higher privilege level than you have.
    ```
    DELETE /api/admin/users/42    ← Admin-only endpoint
    POST /api/users/42/ban        ← Admin-only action
    GET /api/internal/analytics   ← Internal-only endpoint
    ```
    As a regular user, you shouldn't be able to call these at all. The API doesn't check your role before executing the function.

    In testing, I treat them as separate attack categories:

    For BOLA: create two accounts, access each other's resources by modifying IDs, examine full JSON responses for object references to other users.

    For BFLA: enumerate all endpoints (Swagger docs, JS source, traffic capture), then call each with a low-privilege token. Also try HTTP method switching — GET might be accessible but DELETE or POST might expose admin functions.

    Both are in the OWASP API Security Top 10 because authorization in APIs is typically far weaker than authentication. The API correctly rejects unauthenticated requests but then provides zero object-level or function-level access control."

---

### Q4. You find a Responder capture with an NTLMv2 hash. What do you do next?

??? success "Model Answer to Give"
    "Two tracks in parallel.

    Track 1 — Offline cracking:
    ```bash
    hashcat -m 5600 ntlmv2_hash.txt /wordlists/rockyou.txt
    hashcat -m 5600 ntlmv2_hash.txt /wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule
    ```
    If the password is in rockyou with rules, this cracks within minutes to hours. If not, I move to larger wordlists and more complex rule sets.

    Track 2 — Relay without cracking (parallel, doesn't require knowing the password):
    NTLMv2 hashes can't be relayed directly, but if I reconfigure to capture and relay authentication attempts in real time, I can relay to hosts where SMB signing is disabled.

    First check which hosts have SMB signing disabled:
    ```bash
    cme smb 192.168.1.0/24 --gen-relay-list targets.txt
    ```
    
    Then configure Responder to not handle SMB/HTTP (so relay tool handles it instead), and run ntlmrelayx:
    ```bash
    ntlmrelayx.py -tf targets.txt -smb2support
    ```

    When the next authentication attempt is captured, it's relayed to all targets. If the user is a local admin on any target, I get SAM dump and potentially a shell — no cracking required.

    In my report: capturing NTLMv2 hashes is a High finding (the LLMNR/NBT-NS poisoning that enabled it), relay is Critical if it leads to lateral movement, and cracking it demonstrates weak password policy."

---

### Q5. Explain how you would approach a source code review for a Node.js Express application.

??? success "Model Answer to Give"
    "I start by understanding the codebase structure before looking at any code.

    ```bash
    # What dependencies are in use?
    cat package.json | jq '.dependencies'
    # Known vulnerable packages? Run:
    npm audit
    
    # File structure
    find . -name '*.js' -not -path '*/node_modules/*' | head -50
    
    # Find routes (entry points)
    grep -r 'app\.\(get\|post\|put\|delete\|patch\|use\)' . --include='*.js'
    grep -r 'router\.\(get\|post\|put\|delete\|patch\)' . --include='*.js'
    ```

    Then I systematically review by vulnerability category.

    **Injection:** Look for query construction with user input:
    ```bash
    grep -r 'req\.\(body\|params\|query\)' . --include='*.js' | grep -v 'node_modules'
    ```
    Trace each usage — does it reach a database call, OS command, or eval?

    **Authentication/Authorization:** Find the auth middleware and verify it's applied to all sensitive routes. Check JWT validation — is the algorithm verified? Is the secret strong? Is expiry checked?

    **SSRF:** Search for HTTP requests made by the server:
    ```bash
    grep -r 'axios\|fetch\|request\|http\.get\|https\.get' . --include='*.js' | grep -v 'node_modules'
    ```
    Do any of these use user-supplied URLs?

    **Path traversal:**
    ```bash
    grep -r 'readFile\|createReadStream\|sendFile' . --include='*.js'
    ```
    Is the path sanitized? Is `path.join()` used but then not validated to stay within expected directory?

    **Prototype pollution:**
    ```bash
    grep -r 'assign\|merge\|extend\|defaults' . --include='*.js'
    ```
    Custom merge functions without prototype checks are vulnerable.

    **Crypto:**
    ```bash
    grep -r 'MD5\|SHA1\|createCipher\b\|Math\.random' . --include='*.js'
    ```
    `createCipher` (without IV) is deprecated. `Math.random()` is not cryptographically secure.

    I document every finding with file:line reference, code snippet showing source and sink, and a severity rating. The code review findings go into the report as separate findings from any dynamic testing findings — even if the same vulnerability was found dynamically, the code review finding confirms it and provides root cause."

---

### Q6. What is the difference between stored XSS and DOM-based XSS, and which is harder to find with automated scanners?

??? success "Model Answer to Give"
    "Stored XSS: payload is saved to the database (comment, profile, message field) and reflects back to other users who view that content. The attack flow goes through the server — attacker submits to server, server stores, server returns to victim.

    DOM-based XSS: the vulnerability exists entirely in client-side JavaScript. The payload in the URL or local storage is read by JavaScript and written to the DOM via a dangerous sink — `innerHTML`, `document.write`, `eval`. The server never sees the malicious payload — it only serves the vulnerable JavaScript.

    Example:
    ```javascript
    // Vulnerable client-side code:
    var search = decodeURIComponent(location.hash.substring(1));
    document.getElementById('result').innerHTML = search;
    
    // Attack URL:
    https://target.com/page#<img src=x onerror=alert(document.cookie)>
    ```
    The hash fragment is never sent to the server in HTTP requests — so server-side WAFs and scanners never see it.

    DOM-based XSS is dramatically harder for automated scanners to find because:
    1. The payload never appears in HTTP responses — scanners that inject and look for reflection in responses miss it entirely
    2. The execution context is the browser's JavaScript engine, not the server
    3. Finding it requires understanding which sources (location.hash, location.search, document.referrer, postMessage) feed which sinks

    Tools for DOM XSS:
    - DOM Invader (Burp Suite Pro) — instruments the browser to track sources to sinks
    - Semgrep with JavaScript rules — static analysis of sink patterns
    - Manual JavaScript review — grep for innerHTML, document.write, eval, and trace back to sources

    In my testing, I always manually review JavaScript source for DOM XSS in addition to automated scanning, specifically because automated tools have low detection rates for it."

---

!!! tip "At This Level"
    Mid-level interviews often include a live exercise — "here's a web app, find vulnerabilities" or "here's a piece of code, review it." Practice on HackTheBox, PortSwigger Web Academy (all labs), and do at least one source code review on a vulnerable app (DVWA, WebGoat) documenting findings in full report format.
