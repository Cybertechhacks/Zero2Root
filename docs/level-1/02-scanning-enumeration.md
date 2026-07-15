# Scanning & Enumeration

!!! info "Why This Matters"
    Scanning is where passive reconnaissance becomes active engagement. You're now generating traffic that the target can detect. Precision matters — a noisy, undirected scan misses things and announces your presence. This module covers Nmap at a depth that lets you answer any interview question about it, plus service-specific enumeration that forms the backbone of internal network pentests.

---

## Nmap — In-Depth

Nmap (Network Mapper) is the most important scanning tool in a pentester's arsenal. Interviewers ask about it at every level. Know it beyond "I run Nmap to find open ports."

### Scan Types

#### TCP SYN Scan (`-sS`) — Default for Root

The default scan when run as root. Sends SYN, receives SYN-ACK (open) or RST (closed). Immediately sends RST — never completes the handshake. This is why it's called "stealth" or "half-open" — the application layer sees no completed connection.

```bash
nmap -sS target          # Requires root/Administrator
```

**Port state determination:**
- SYN-ACK received → **open** (port accepting connections)

- RST received → **closed** (port reachable, no service listening)

- No response / ICMP unreachable → **filtered** (firewall dropping packets)

- SYN-ACK then immediate RST from our RST → **open** (we RST'd it)

#### TCP Connect Scan (`-sT`) — No Privileges Required

Uses the OS TCP stack to complete a full three-way handshake. Does not require raw socket privileges — works without root. The connection is logged by the application layer.

```bash
nmap -sT target          # Works without root
```

Use when: you can't get root on the scanning machine, or the target is on a network that requires full connections (some load balancers reset half-open connections immediately).

#### UDP Scan (`-sU`) — Slow and Important

Sends UDP packets. No response = open|filtered. ICMP Port Unreachable = closed. Some services respond with application-layer data.

```bash
nmap -sU -p 53,67,68,69,123,161,162,500 target   # Key UDP ports
nmap -sU --top-ports 20 target                     # Most common UDP ports
```

**Why UDP scanning is slow:** Linux rate-limits ICMP outgoing packets to ~1000/second by default. Nmap respects this, making UDP scans for large ranges take hours. Combine `--min-rate` carefully.

#### Other Scan Types

```bash
# ACK scan — map firewall rules (stateful vs stateless)
# RST = port passed firewall; no response = filtered
nmap -sA target

# FIN scan — works through some packet-filter firewalls
# RFC: closed ports RST, open ports ignore FIN
nmap -sF target

# Xmas scan — FIN+PSH+URG set
nmap -sX target

# NULL scan — no flags set
nmap -sN target

# Window scan — like ACK but uses TCP window size
nmap -sW target

# Maimon scan — FIN+ACK
nmap -sM target

# IP protocol scan — which IP protocols are supported (not TCP/UDP ports)
nmap -sO target

# SCTP INIT scan
nmap -sY target
```

**Note:** FIN/Xmas/NULL scans don't work reliably against Windows — Windows always responds with RST regardless of port state, making all ports appear closed.

### Service Version Detection (`-sV`)

Probes open ports to determine the exact service and version running. Nmap sends protocol-specific probes and matches responses against the `nmap-service-probes` database.

```bash
nmap -sV target                    # Basic version detection
nmap -sV --version-intensity 9 target   # Maximum probe intensity (slower)
nmap -sV --version-light target    # Fewer probes (faster, less accurate)
```

**What `-sV` does under the hood:** After identifying open ports, Nmap sends a series of probes (TCP connect, then service-specific banners like HTTP GET, FTP commands, SSL ClientHello, etc.). The response is matched against regex patterns in nmap-service-probes. This is why `-sV` is significantly slower than a basic SYN scan.

### OS Detection (`-O`)

Sends a series of specially crafted packets and analyzes TCP/IP stack behavior (window size, TTL, TCP options, IPID sequence patterns) to fingerprint the OS. Requires at least one open and one closed port, and root/Administrator privileges.

```bash
nmap -O target
nmap -O --osscan-guess target      # More aggressive guessing
```

### NSE — Nmap Scripting Engine

NSE scripts extend Nmap functionality dramatically. Scripts are written in Lua and live in `/usr/share/nmap/scripts/`.

```bash
# List all scripts
ls /usr/share/nmap/scripts/
nmap --script-help all

# Script categories
nmap --script default target       # Safe, informational scripts (default = -sC)
nmap --script safe target
nmap --script intrusive target     # May crash services or cause harm
nmap --script exploit target       # Actual exploitation attempts
nmap --script vuln target          # Vulnerability detection scripts
nmap --script auth target          # Authentication testing (default creds, etc.)
nmap --script discovery target     # Service and network discovery
nmap --script brute target         # Brute force authentication

# Run specific scripts
nmap --script http-title target
nmap --script smb-vuln-ms17-010 target    # EternalBlue check
nmap --script ssl-cert,ssl-enum-ciphers target   # TLS analysis
nmap --script ftp-anon target      # Anonymous FTP check
nmap --script ldap-rootdse target  # LDAP base info

# Pass script arguments
nmap --script http-brute --script-args http-brute.path=/admin target
nmap --script smb-brute --script-args smbuser=admin,smbpass=password target
```

### Timing Templates (`-T`)

Controls timing aggressiveness. Higher = faster but louder and more likely to trigger IDS or overwhelm unstable targets.

| Template | Name | Description |
|----------|------|-------------|
| `-T0` | Paranoid | 5 minute delay between probes — IDS evasion |
| `-T1` | Sneaky | 15 second delay — IDS evasion |
| `-T2` | Polite | 0.4 second delay — reduces bandwidth |
| `-T3` | Normal | Default |
| `-T4` | Aggressive | Assumes fast, reliable network |
| `-T5` | Insane | Very fast, may miss results on unstable networks |

```bash
nmap -T4 target         # Fast scan — good for internal networks
nmap -T2 target         # Slow scan — for stealth or fragile targets
```

### Port Specification

```bash
nmap -p 22,80,443 target           # Specific ports
nmap -p 1-1024 target              # Port range
nmap -p- target                    # All 65535 ports (slow but thorough)
nmap -p- --min-rate 5000 target    # All ports, faster with min-rate
nmap --top-ports 1000 target       # Most commonly open 1000 ports
nmap --top-ports 100 target        # Top 100 — quick initial sweep
nmap -F target                     # Fast scan (top 100 ports)
nmap -p U:53,111,137,T:21-25,80,139,443 target  # Mix of UDP and TCP
```

### Output Formats

```bash
nmap -oN output.txt target         # Normal output
nmap -oX output.xml target         # XML (parseable by tools like Metasploit)
nmap -oG output.gnmap target       # Grepable output
nmap -oA output target             # All three formats simultaneously (recommended)
nmap -oJ output.json target        # JSON (newer versions)
```

**Always use `-oA`** in real engagements. You'll want to grep the results later and parse them in tools.

### Scanning Through Proxies

```bash
# Scan through a SOCKS proxy (useful when pivoting)
nmap --proxies socks4://127.0.0.1:1080 target

# Via proxychains
proxychains nmap -sT -p 22,80,443,445 target
# Note: SYN scan doesn't work through proxychains — use -sT
```

### Complete Recommended Scan Sequence for Internal Networks

```bash
# Phase 1: Fast host discovery
nmap -sn 192.168.1.0/24 -oA phase1_hosts

# Phase 2: Full port scan on live hosts (all 65535 ports)
nmap -p- --min-rate 5000 -T4 -iL live_hosts.txt -oA phase2_allports

# Phase 3: Service and version detection on open ports
# (Extract open ports from phase 2 first with grep/awk)
nmap -sV -sC -p <ports> -iL live_hosts.txt -oA phase3_services

# Phase 4: Targeted vulnerability scripts on services found
nmap --script vuln -p <ports> -iL live_hosts.txt -oA phase4_vulns
```

---

## Host Discovery

Before scanning ports, determine which hosts are alive.

```bash
# Ping sweep (ICMP echo request)
nmap -sn 192.168.1.0/24

# ARP scan (most reliable on local segment, requires root)
nmap -PR -sn 192.168.1.0/24
arp-scan -l                        # Local network ARP scan
arp-scan 192.168.1.0/24

# TCP SYN to common ports (when ICMP is blocked)
nmap -PS22,80,443,445 -sn 192.168.1.0/24

# TCP ACK to bypass stateful firewalls
nmap -PA80,443 -sn 192.168.1.0/24

# UDP ping
nmap -PU53 -sn 192.168.1.0/24

# No host discovery (treat all hosts as up) — useful when ICMP is blocked
nmap -Pn 192.168.1.0/24
```

---

## SMB Enumeration

SMB (Server Message Block) runs on port 445 (and legacy 139 for NetBIOS). In internal Windows environments, SMB is one of the most important enumeration targets — it reveals hostnames, domain information, shares, user accounts, and often allows authentication.

```bash
# Basic SMB scan
nmap -p 139,445 --script=smb-enum-shares,smb-enum-users,smb-os-discovery target

# List shares
smbclient -L //target -N              # Null session
smbclient -L //target -U username%password

# Connect to a share
smbclient //target/sharename -N
smbclient //target/C$ -U administrator%password

# Enumerate everything with enum4linux (older but comprehensive)
enum4linux -a target

# Enumerate with enum4linux-ng (modern rewrite)
enum4linux-ng -A target

# rpcclient — RPC over SMB for AD enumeration
rpcclient -U "" target -N             # Null session
rpcclient> enumdomusers               # List domain users
rpcclient> enumdomgroups              # List domain groups
rpcclient> querydominfo               # Domain information
rpcclient> getdompwinfo               # Password policy
rpcclient> enumalsgroups domain       # Local groups
rpcclient> lookupnames administrator  # Get SID for user

# smbmap — map shares and permissions
smbmap -H target                      # Anonymous
smbmap -H target -u username -p password
smbmap -H target -u username -p password -R  # Recursive file listing

# crackmapexec — modern, feature-rich SMB tool
cme smb target
cme smb target -u '' -p ''                        # Null session
cme smb target -u users.txt -p passwords.txt      # Credential spraying
cme smb target -u user -p pass --shares           # List shares
cme smb target -u user -p pass --users            # List users
cme smb target -u user -p pass --groups           # List groups
cme smb target -u user -p pass -M spider_plus     # Spider shares for files
```

**EternalBlue check (MS17-010):**
```bash
nmap --script smb-vuln-ms17-010 -p 445 target
```

---

## FTP Enumeration

FTP runs on port 21. Primary checks: anonymous authentication, version-based vulnerabilities, cleartext credentials.

```bash
# Basic connection
ftp target
# Username: anonymous, Password: (any email)

# Nmap NSE
nmap --script ftp-anon,ftp-bounce,ftp-libopie,ftp-proftpd-backdoor,ftp-vsftpd-backdoor,ftp-vuln-cve2010-4221 -p 21 target

# Check for anonymous FTP
nmap --script ftp-anon -p 21 target

# Manual enumeration
ftp target
ftp> ls -la       # List all files including hidden
ftp> get file.txt # Download a file
ftp> put file.txt # Upload a file

# Active vs Passive FTP matters for firewall traversal:
ftp> passive   # Toggle passive mode
```

**vsftpd 2.3.4 backdoor (classic lab vulnerability):**
A backdoor was introduced into vsftpd 2.3.4 source code. Connecting with a username containing `:)` triggers a bind shell on port 6200.
```bash
nmap --script ftp-vsftpd-backdoor -p 21 target
```

---

## SNMP Enumeration

SNMP (Simple Network Management Protocol) runs on UDP/161. Version 1 and 2c use community strings as authentication — "public" and "private" are the default strings. If devices still use these defaults, SNMP exposes significant information.

```bash
# Basic SNMP walk (requires community string)
snmpwalk -v2c -c public target                    # Walk all MIB
snmpwalk -v2c -c public target 1.3.6.1.2.1.1     # System info
snmpwalk -v2c -c public target 1.3.6.1.2.1.25.4.2 # Running processes
snmpwalk -v2c -c public target 1.3.6.1.2.1.25.6.3 # Installed software
snmpwalk -v2c -c public target 1.3.6.1.2.1.4.20  # IP addresses
snmpwalk -v2c -c public target 1.3.6.1.4.1.77.1.2.25 # Windows user list

# snmp-check — more readable output
snmp-check target
snmp-check -c private target

# Brute force community strings
onesixtyone -c /usr/share/metasploit-framework/data/wordlists/snmp_default_pass.txt target
hydra -P /wordlists/community_strings.txt target snmp

# Nmap SNMP scripts
nmap --script snmp-brute,snmp-info,snmp-interfaces,snmp-processes,snmp-sysdescr,snmp-win32-services,snmp-win32-shares,snmp-win32-software,snmp-win32-users -p U:161 target
```

**Common SNMP OIDs to know:**

| OID | Description |
|-----|-------------|
| 1.3.6.1.2.1.1.5 | System hostname |
| 1.3.6.1.2.1.1.6 | System location |
| 1.3.6.1.2.1.1.1 | System description (OS, version) |
| 1.3.6.1.2.1.25.4.2.1.2 | Running processes |
| 1.3.6.1.2.1.25.6.3.1.2 | Installed software |
| 1.3.6.1.2.1.4.20.1.1 | IP addresses configured on interfaces |
| 1.3.6.1.4.1.77.1.2.25 | Windows user list |

**SNMPv3** uses proper authentication (MD5/SHA) and optionally encryption. If SNMPv3 is in use, brute force community strings don't apply, but version 3 username enumeration can still be possible with some implementations.

---

## LDAP Enumeration

LDAP (Lightweight Directory Access Protocol) runs on port 389 (636 for LDAPS). In Active Directory environments, LDAP is the query protocol for everything — users, groups, computers, GPOs, trusts.

```bash
# ldapsearch — basic queries
# Unauthenticated (null bind) — may reveal base info
ldapsearch -x -H ldap://target -s base

# List naming contexts
ldapsearch -x -H ldap://target -s base namingcontexts

# Enumerate users (with credentials)
ldapsearch -x -H ldap://target -D "CN=user,DC=example,DC=com" -w password \
  -b "DC=example,DC=com" "(objectClass=user)" cn sAMAccountName

# Enumerate all objects
ldapsearch -x -H ldap://target -D "user@example.com" -w password \
  -b "DC=example,DC=com" "(objectClass=*)"

# Nmap LDAP scripts
nmap --script ldap-rootdse -p 389 target
nmap --script ldap-search --script-args ldap.base='"dc=example,dc=com"' -p 389 target

# ldapdomaindump — comprehensive AD enumeration to HTML/JSON
ldapdomaindump -u 'DOMAIN\user' -p password ldap://target

# With CrackMapExec
cme ldap target -u user -p password --users
cme ldap target -u user -p password --groups
cme ldap target -u user -p password --computers
cme ldap target -u user -p password -M get-desc-users  # Users with password in description
```

---

## Banner Grabbing

Banner grabbing extracts the service banner — the string a service sends when you connect. Banners often reveal software name, version, and sometimes OS details.

```bash
# Netcat
nc target 22    # SSH banner
nc target 21    # FTP banner
nc target 25    # SMTP banner

# Telnet
telnet target 80
GET / HTTP/1.0

# curl
curl -I http://target    # HTTP headers only
curl -v http://target    # Full request/response

# Nmap (banner script)
nmap --script banner -p 21,22,25,80,443 target

# netcat one-liner
echo "" | nc -nv -w1 target 22

# Python banner grabber
python3 -c "import socket; s=socket.socket(); s.connect(('target', 22)); print(s.recv(1024).decode())"
```

**Information to extract from banners:**
- Software and exact version → search CVE databases

- Operating system clues (e.g., SSH banners often include Ubuntu/Debian/CentOS/Red Hat)

- Application server names and versions

- Custom error pages revealing internal hostnames or paths

---

## Common Scanning Mistakes to Avoid

**1. Scanning out of scope:** Always verify the target IP/domain is in scope before scanning. Check the scope document.

**2. Running intrusive scripts without authorization:** `--script exploit` or specific exploit NSE scripts can crash services. Never run these without explicit authorization.

**3. Assuming ICMP blockers mean no hosts:** Many networks block ping. Use `-Pn` or TCP-based host discovery.

**4. Missing UDP:** Everyone scans TCP. UDP often has critical services (SNMP, DNS, DHCP, TFTP) exposed. Always include targeted UDP scanning.

**5. Not saving output:** Always use `-oA`. You'll grep for ports, services, and hostnames throughout the engagement and during report writing.

**6. Scanning too fast on unstable networks:** `-T5` on a VPN or slow network misses open ports. `-T4` is usually the right balance.

**7. Forgetting IPv6:** Dual-stack environments have IPv6 addresses too. `nmap -6 target` or `nmap -6 2001:db8::/32`.

**8. Not re-scanning after finding footholds:** After pivoting into a new network segment, re-scan from the new position. You may see services blocked from the external position.
