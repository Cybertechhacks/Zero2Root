# Scanning Tools

---

## Nmap — Core Reference

Full Nmap documentation is in the [Scanning & Enumeration](../level-1/02-scanning-enumeration.md) module. Quick-reference card:

```bash
# Host discovery
nmap -sn 192.168.1.0/24              # Ping sweep
nmap -Pn target                       # Skip discovery, assume up

# Port scanning
nmap -sS target                       # SYN scan (stealth, root required)
nmap -sT target                       # TCP connect (no root needed)
nmap -sU -p 53,161,500 target        # UDP scan (specific ports)
nmap -p- --min-rate 5000 target      # All 65535 ports, fast
nmap -p 1-1024 target                # First 1024 ports
nmap --top-ports 100 target          # Most common 100 ports

# Detection
nmap -sV target                       # Service/version detection
nmap -O target                        # OS fingerprinting
nmap -sV -O -sC target               # Everything + default scripts

# NSE scripts
nmap -sC target                       # Default scripts
nmap --script vuln target             # Vulnerability scripts
nmap --script "http-*" target         # All HTTP scripts
nmap --script smb-vuln-ms17-010 target # Specific script

# Output
nmap -oA output target               # All formats (recommended)
nmap -oN output.txt target           # Normal
nmap -oX output.xml target           # XML
nmap -oG output.gnmap target         # Grepable

# Timing
nmap -T4 target                      # Fast (good for internal nets)
nmap -T2 target                      # Slow (for fragile targets)
```

---

## Masscan

Very fast port scanner — can scan the entire internet in under 6 minutes with appropriate rate. Use for large internal networks.

```bash
# Basic scan
masscan 192.168.0.0/16 -p80,443,22,445

# Fast rate (be careful — can overwhelm networks)
masscan 192.168.0.0/16 -p0-65535 --rate=10000

# Output
masscan 192.168.0.0/16 -p80,443 -oL results.txt

# Exclude ranges
masscan 0.0.0.0/0 -p80 --exclude 192.168.1.0/24
```

---

## Nessus / OpenVAS

**Nessus** (Tenable): Industry-standard commercial vulnerability scanner. Free tier (Nessus Essentials) allows scanning up to 16 hosts.

**OpenVAS** (Greenbone): Open-source alternative. Full feature set available for free.

**Key concepts for interviews:**
- Authenticated vs unauthenticated scanning — authenticated scans are dramatically more thorough (checks patch level, installed software versions, local config)

- Plugin families — Windows, Linux, Web Servers, Databases, SSL/TLS, etc.

- False positives — always validate Critical and High findings before reporting

- Scan policies — safe checks only vs intrusive checks (some plugins can crash services)

```bash
# OpenVAS CLI
gvm-cli socket --gvm-socket /var/run/gvmd/gvmd.sock --xml "<get_version/>"

# Nessus API (for automation)
curl -k -X POST https://localhost:8834/session \
  -d '{"username":"admin","password":"password"}' \
  -H "Content-Type: application/json"
```

---

## Nuclei

Template-based vulnerability scanner. Community maintains thousands of templates for CVEs, misconfigurations, and exposures.

```bash
# Update templates
nuclei -update-templates

# Scan with all templates
nuclei -u https://target.com

# Specific severity
nuclei -u https://target.com -severity critical,high

# Specific template categories
nuclei -u https://target.com -t cves/
nuclei -u https://target.com -t exposures/
nuclei -u https://target.com -t misconfiguration/
nuclei -u https://target.com -t technologies/

# Multiple targets
nuclei -l urls.txt -t cves/ -o results.txt

# Rate limiting
nuclei -u https://target.com -rate-limit 50 -c 10

# With authentication
nuclei -u https://target.com -H "Authorization: Bearer token123"
```

---

## testssl.sh

Tests TLS/SSL configuration comprehensively.

```bash
# Full scan
testssl.sh https://target.com

# Specific checks
testssl.sh --protocols target.com      # Protocol versions
testssl.sh --ciphers target.com        # Cipher suites
testssl.sh --headers target.com        # HTTP security headers
testssl.sh --vulnerabilities target.com # Known TLS vulns (POODLE, BEAST, etc.)

# JSON output for automation
testssl.sh --jsonfile results.json https://target.com

# Quick summary
testssl.sh --fast https://target.com
```

---

# Web Application Tools

---

## Burp Suite

The central tool for web application testing. Every web pentester must know this.

**Key features:**

**Proxy:** Intercepts all browser traffic. Configure browser to use 127.0.0.1:8080 as proxy. Install Burp's CA certificate in browser.

**Repeater:** Resend and modify individual requests manually. Core workflow tool.

**Intruder:** Automated fuzzing. Four attack types:

- Sniper: One payload, one position

- Battering Ram: Same payload, multiple positions

- Pitchfork: Multiple payloads, one-to-one pairing

- Cluster Bomb: Multiple payloads, all combinations (most thorough)

**Scanner (Pro):** Active and passive vulnerability scanning. Passive = analysis of traffic already captured. Active = sends additional requests to probe for vulnerabilities.

**Decoder:** Encode/decode Base64, URL encoding, HTML entities, hex.

**Comparer:** Diff two responses — useful for identifying subtle differences indicating blind injection or access control changes.

**Extensions (BApp Store):**
- Autorize: Tests access control by replaying requests with different session tokens

- Logger++: Advanced request logging

- InQL: GraphQL introspection and testing

- JWT Editor: JWT manipulation

- JS Link Finder: Extracts endpoints from JavaScript files

- Param Miner: Discovers hidden parameters

```
# Essential keyboard shortcuts:
Ctrl+R = Send to Repeater
Ctrl+I = Send to Intruder
Ctrl+U = URL encode selection
Ctrl+Shift+U = URL decode selection
```

---

## Gobuster / Feroxbuster / ffuf

**Gobuster:** Directory and DNS brute force.

```bash
# Directory/file brute force
gobuster dir -u http://target.com -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
gobuster dir -u http://target.com -w wordlist.txt -x php,html,txt,js
gobuster dir -u http://target.com -w wordlist.txt -t 50  # 50 threads

# DNS subdomain brute force
gobuster dns -d example.com -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt

# VHost brute force
gobuster vhost -u http://target.com -w subdomains.txt
```

**ffuf** (Fuzz Faster U Fool): More flexible, supports request templates.

```bash
# Directory fuzzing
ffuf -u http://target.com/FUZZ -w wordlist.txt

# Parameter fuzzing
ffuf -u "http://target.com/page?FUZZ=value" -w params.txt

# POST body fuzzing
ffuf -u http://target.com/login -X POST -d "user=FUZZ&pass=test" -w users.txt

# Filter by status code
ffuf -u http://target.com/FUZZ -w wordlist.txt -mc 200,201,301,302

# Match by word/line count (filter false positives)
ffuf -u http://target.com/FUZZ -w wordlist.txt -fw 10  # Filter 10-word responses
```

---

## SQLMap

Automated SQL injection detection and exploitation.

```bash
# Basic test
sqlmap -u "http://target.com/page?id=1"

# POST request
sqlmap -u "http://target.com/login" --data="user=admin&pass=test"

# With session cookie
sqlmap -u "http://target.com/profile" --cookie="session=abc123"

# From Burp request file
sqlmap -r request.txt

# Enumerate
sqlmap -u "http://target.com/page?id=1" --dbs        # Databases
sqlmap -u "http://target.com/page?id=1" -D mydb --tables
sqlmap -u "http://target.com/page?id=1" -D mydb -T users --dump

# WAF bypass
sqlmap -u "http://target.com/page?id=1" --tamper=space2comment,between,randomcase
sqlmap -u "http://target.com/page?id=1" --random-agent --delay=2 --level=5 --risk=3
```

**Interview note:** Always explain that sqlmap is used to confirm and demonstrate findings, and should be run with appropriate parameters to avoid overwhelming the target (use `--delay` and `--level=1` for initial testing, increase if needed).

---

## Nikto

Web server misconfiguration scanner. Fast, noisy — use for quick misconfiguration checks.

```bash
# Basic scan
nikto -h http://target.com

# HTTPS
nikto -h https://target.com -ssl

# Specific port
nikto -h http://target.com:8080

# Output
nikto -h http://target.com -o results.txt -Format txt
nikto -h http://target.com -o results.html -Format html

# Tuning (limit check types to reduce noise)
nikto -h http://target.com -Tuning 1234     # Specific check categories
```

---

# Network & Infrastructure Tools

---

## Wireshark / tcpdump

**Wireshark:** GUI packet analyzer. Essential for understanding traffic, capturing credentials over cleartext protocols, and debugging.

**Key filters:**
```
# Protocol filters
http
https or ssl
smb or smb2
dns
ftp
telnet

# IP filters
ip.addr == 192.168.1.100
ip.src == 192.168.1.100
ip.dst == 192.168.1.100

# Port filters
tcp.port == 80
tcp.port == 445

# Credential hunting
http.request.method == "POST"
ftp.request.command == "PASS"
smtp.auth

# Follow TCP stream: right-click packet → Follow → TCP Stream
```

**tcpdump (CLI):**
```bash
# Capture all traffic
tcpdump -i eth0

# Save to file
tcpdump -i eth0 -w capture.pcap

# Read file
tcpdump -r capture.pcap

# Filters
tcpdump -i eth0 port 80
tcpdump -i eth0 host 192.168.1.100
tcpdump -i eth0 'tcp port 80 and host 192.168.1.100'
tcpdump -i eth0 not arp          # Exclude ARP
```

---

## Netcat / Ncat

```bash
# Listen for incoming connection
nc -lvnp 4444                    # Listener
ncat -lvnp 4444 --ssl           # Encrypted listener

# Connect
nc target 4444

# File transfer
nc -lvnp 9999 > received_file   # Receiver
nc target 9999 < file_to_send   # Sender

# Port scanning (basic)
nc -zv target 20-100

# Banner grabbing
echo "" | nc -nv target 22
```

---

## CrackMapExec (CME)

Swiss army knife for Windows/AD network testing.

```bash
# Enumerate hosts
cme smb 192.168.1.0/24

# Test credentials
cme smb target -u admin -p 'Password123'
cme smb target -u admin -H NTLMhash          # Pass-the-Hash
cme smb target -u users.txt -p passwords.txt  # Credential spraying

# Enumerate shares
cme smb target -u user -p pass --shares

# Enumerate users
cme smb dc -u user -p pass --users

# Check for SMB signing
cme smb 192.168.1.0/24 --gen-relay-list targets.txt

# Execute commands (if admin)
cme smb target -u admin -p pass -x "whoami"
cme smb target -u admin -p pass -X "Get-Process"  # PowerShell

# Target multiple protocols
cme winrm target -u admin -p pass -x "whoami"
cme ldap dc -u admin -p pass --users
cme mssql target -u sa -p pass --query "SELECT @@version"
```

---

## Enum4linux-ng

Linux host enumeration via SMB/RPC/LDAP.

```bash
# Full enumeration
enum4linux-ng -A target

# Specific enumeration
enum4linux-ng -U target    # Users
enum4linux-ng -G target    # Groups
enum4linux-ng -S target    # Shares
enum4linux-ng -P target    # Password policy
enum4linux-ng -N target    # RID cycling (user enumeration via RID)
```

---

## Impacket Suite

Python implementation of Windows networking protocols. Essential for AD testing from Linux.

```bash
# Authentication testing
smbclient.py corp.local/user:pass@target      # SMB client
psexec.py corp.local/user:pass@target         # Remote shell via SMB
wmiexec.py corp.local/user:pass@target        # Remote shell via WMI
smbexec.py corp.local/user:pass@target        # Remote shell via service

# Pass-the-Hash (use NT hash instead of password)
psexec.py -hashes :NThash corp.local/user@target

# Kerberos tickets
GetUserSPNs.py -dc-ip dc_ip corp.local/user:pass   # Kerberoast
GetNPUsers.py corp.local/ -usersfile users.txt -no-pass  # AS-REP roast

# Credential dumping
secretsdump.py corp.local/admin:pass@target   # Remote dump
secretsdump.py -sam sam.hive -system system.hive LOCAL  # Offline dump

# NTLM relay
ntlmrelayx.py -tf targets.txt -smb2support

# Kerberos ticket operations
ticketer.py -nthash krbtgt_hash -domain-sid S-1-5-21-... -domain corp.local admin
```

---

## BloodHound / SharpHound

Active Directory attack path visualization.

```bash
# Collect AD data from Linux
bloodhound-python -d corp.local -u user -p pass -c All -ns dc_ip

# Collect from Windows (SharpHound)
SharpHound.exe -c All --zipfilename output.zip

# Import to BloodHound
# GUI: Drag and drop the ZIP file

# Key queries in BloodHound:
# "Find Shortest Paths to Domain Admins"
# "Find All Domain Admins"
# "Find Kerberoastable Users"
# "Find AS-REP Roastable Users"
# "Find Computers where Domain Users are Local Admin"
# "Find Principals with DCSync Rights"
# "Shortest Paths to Unconstrained Delegation Systems"
```

---

# Mobile Testing Tools

---

## ADB (Android Debug Bridge)

```bash
# Device management
adb devices                           # List connected devices
adb shell                             # Shell on device
adb install app.apk                   # Install APK
adb pull /path/on/device ./local      # Pull file from device
adb push ./local /path/on/device      # Push file to device

# App management
adb shell pm list packages            # List installed packages
adb shell pm path com.example.app     # Find APK path
adb shell run-as com.example.app ls   # Access app data (non-root)

# Logging
adb logcat                            # All logs
adb logcat -s tag                     # Filter by tag
adb logcat | grep -iE "password|token|key"

# Backup
adb backup -noapk -f backup.ab com.example.app

# Port forwarding
adb forward tcp:8080 tcp:8080         # Forward device port to host
adb reverse tcp:9090 tcp:9090         # Forward host port to device

# Proxy setup
adb shell settings put global http_proxy host:port
adb shell settings delete global http_proxy
```

---

## apktool

Decodes and rebuilds Android APKs.

```bash
# Decompile APK
apktool d app.apk -o output_dir/
apktool d app.apk -o output_dir/ --no-res  # Skip resource decoding

# Rebuild APK (after modification)
apktool b output_dir/ -o app_modified.apk

# Sign rebuilt APK
keytool -genkeypair -v -keystore test.jks -alias testkey -keyalg RSA -keysize 2048 -validity 365
apksigner sign --ks test.jks --out app_signed.apk app_modified.apk

# Install and test
adb install -r app_signed.apk
```

---

## jadx

Decompiles APK to readable Java code. Better than apktool for code analysis.

```bash
# Command line decompile
jadx -d output_dir/ app.apk

# GUI (recommended for navigating large codebases)
jadx-gui app.apk

# Show original bytecode comments
jadx -d output_dir/ --show-bad-code app.apk

# After decompilation, search for sensitive patterns:
grep -r "api_key\|password\|secret\|token" output_dir/ --include="*.java"
grep -r "http://" output_dir/ --include="*.java"
grep -r "Log\.\(d\|v\|i\|e\)" output_dir/ --include="*.java"
```

---

## MobSF (Mobile Security Framework)

Automated static and dynamic analysis for Android and iOS.

```bash
# Docker setup
docker run -it --rm -p 8000:8000 opensecurity/mobile-security-framework-mobsf:latest

# Access: http://localhost:8000
# Upload APK or IPA for automated analysis

# Key sections in MobSF report:
# - Android Manifest Analysis (permissions, exported components)
# - Security Analysis (insecure code patterns, dangerous APIs)
# - File Analysis (interesting files in APK)
# - Strings Analysis (hardcoded secrets)
# - Permissions Analysis
# - Network Security Analysis
```

---

## Frida

Dynamic instrumentation framework for hooking and modifying app behavior at runtime.

```bash
# Install frida-tools
pip install frida-tools

# Push frida-server to Android device
adb push frida-server /data/local/tmp/
adb shell "chmod 755 /data/local/tmp/frida-server && /data/local/tmp/frida-server &"

# List running apps
frida-ps -U

# Attach to running app
frida -U -n "com.example.app" -l script.js

# Spawn and attach
frida -U -f com.example.app -l script.js --no-pause

# Use Codeshare scripts
frida -U -f com.example.app --codeshare pcipolloni/universal-android-ssl-pinning-bypass-with-frida
```

---

## Objection

Frida-based automated mobile testing framework.

```bash
# Launch with objection
objection -g com.example.app explore

# Key commands inside objection:

# Android:
android info list                    # App details
android hooking list activities      # All activities
android hooking list classes         # Loaded classes
android keystore list                # Keystore contents
android sslpinning disable          # Bypass SSL pinning
android root disable                 # Bypass root detection
memory dump all /tmp/memdump        # Dump process memory
android sqlite list                  # List databases
android sqlite execute "SELECT * FROM users"

# iOS:
ios info list
ios keychain dump                   # Dump iOS keychain
ios sslpinning disable             # Bypass SSL pinning
ios hooking list classes
ios pasteboard monitor
```
