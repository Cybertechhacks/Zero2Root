# Networking Fundamentals

!!! info "Why This Matters in Interviews"
    Networking is the substrate of every pentest. You cannot understand port scanning without TCP, cannot exploit SSRF without HTTP, cannot intercept traffic without understanding ARP. Interviewers at every level probe networking because it reveals whether you understand *what your tools are doing* — or whether you're just running commands.

---

## The OSI Model — Not Just Names

The OSI (Open Systems Interconnection) model is a conceptual framework that divides network communication into seven layers. Most candidates can name the layers. Interviewers want to know *why the layering exists* and *what attacks target which layer*.

The layering principle is **separation of concerns** — each layer handles one job and hands its result to the layer above or below it. This is why a change at the physical layer (fiber vs Wi-Fi) doesn't require rewriting your HTTP application.

| Layer | Number | Name | Protocol Examples | Attack Surface |
|-------|--------|------|-------------------|----------------|
| Application | 7 | Application | HTTP, DNS, SMTP, FTP, SSH | SQLi, XSS, SSRF, command injection |
| Presentation | 6 | Presentation | SSL/TLS, encoding, compression | SSL stripping, encoding bypass |
| Session | 5 | Session | NetBIOS, RPC, session tokens | Session hijacking, token reuse |
| Transport | 4 | Transport | TCP, UDP | SYN flood, port scanning, TCP hijacking |
| Network | 3 | Network | IP, ICMP, OSPF, BGP | IP spoofing, routing attacks, ICMP tunneling |
| Data Link | 2 | Data Link | Ethernet, ARP, 802.11 (Wi-Fi) | ARP poisoning, MAC flooding, VLAN hopping |
| Physical | 1 | Physical | Cables, hubs, RF signals | Physical access, rogue AP, cable tapping |

The **TCP/IP model** (also called the Internet model) collapses OSI layers 5-7 into "Application" and layers 1-2 into "Network Access." In practice, you'll hear both models mentioned. Interviewers may ask you to map between them.

The key mental model: **when data travels down the stack on the sender's side, each layer adds a header (encapsulation). When it travels up the stack on the receiver's side, each layer strips its header (decapsulation).** An Ethernet frame contains an IP packet, which contains a TCP segment, which contains HTTP data.

---

## TCP — Transmission Control Protocol

TCP is a **connection-oriented, reliable, ordered, error-checked** transport protocol. Understanding its mechanics is essential because most application-layer protocols (HTTP, HTTPS, SSH, FTP, SMTP) run over TCP, and most scanning techniques exploit TCP behavior.

### The Three-Way Handshake

A TCP connection is established through three steps:

```
Client                          Server
  |                               |
  |--------- SYN ---------------→|   Client picks ISN_c, sends SYN
  |                               |   Server allocates half-open connection
  |←-------- SYN-ACK ------------|   Server picks ISN_s, ACKs ISN_c+1
  |                               |
  |--------- ACK ---------------→|   Client ACKs ISN_s+1
  |                               |   Full connection established
  |====== DATA TRANSFER =========|
```

**Initial Sequence Numbers (ISN):** Both sides independently pick a random 32-bit starting sequence number. Modern kernels use cryptographically random ISNs. Historically (early 1990s), ISNs were predictable, enabling TCP session hijacking — an attacker could forge packets with the correct sequence numbers. RFC 6528 mandates randomized ISNs.

**The SYN queue:** When a server receives a SYN, it allocates a half-open connection entry in its SYN backlog queue before the handshake completes. This is the mechanism exploited by **SYN flood attacks** — send millions of SYNs with spoofed source IPs, filling the queue, preventing legitimate connections. **SYN cookies** mitigate this by encoding connection state in the SYN-ACK's sequence number instead of allocating queue entries — no queue space is consumed until the handshake completes.

### TCP Flags

TCP uses 9 control flags in the header:

| Flag | Bit | Meaning | Pentesting Significance |
|------|-----|---------|------------------------|
| SYN | 0x002 | Synchronize — initiate connection | Basis of port scanning |
| ACK | 0x010 | Acknowledge received data | Present in all packets after handshake |
| FIN | 0x001 | Finish — graceful close | Used in FIN scans for firewall evasion |
| RST | 0x004 | Reset — abrupt close | Closed port response; RST scan technique |
| PSH | 0x008 | Push data immediately to application | Often combined with ACK in data packets |
| URG | 0x020 | Urgent data present | Rarely used legitimately; firewall bypass attempts |
| ECE | 0x040 | ECN-Echo (congestion control) | |
| CWR | 0x080 | Congestion Window Reduced | |
| NS  | 0x100 | Nonce Sum (experimental) | |

**Pentesting relevance of flag combinations:**
- `SYN` only → beginning of connection attempt
- `SYN + ACK` → server accepting connection
- `RST + ACK` → port is closed (immediate rejection)
- `FIN + ACK` → graceful connection close
- `FIN` only (no ACK) → FIN scan technique — RFC says closed ports must RST, open ports should ignore; some firewalls pass FIN packets that would block SYNs
- `ACK` only → ACK scan — maps stateful firewall rules; ports behind stateful firewalls return RST whether open or closed, but ACKs may pass through packet-filter firewalls
- Xmas scan: `FIN + PSH + URG` — so-named because the flags "light up the tree"

### TCP Connection Teardown

Graceful close uses a four-way exchange (each side sends FIN and receives ACK independently). `TIME_WAIT` state keeps the connection entry for 2×MSL (Maximum Segment Lifetime, typically 60 seconds) to absorb any delayed duplicate packets.

### Why Nmap SYN Scan Is "Stealthy"

A TCP connect scan (`nmap -sT`) completes the full three-way handshake, so the target's application layer logs a completed connection. A SYN scan (`nmap -sS`) sends SYN, receives SYN-ACK from open ports, then sends RST — the handshake never completes, so the application layer never sees the connection. Only kernel-level logs may record it. This is why `-sS` is called a "half-open" or "stealth" scan — though modern IDS/IPS systems detect SYN scans trivially.

---

## UDP — User Datagram Protocol

UDP is **connectionless, unreliable, and unordered.** No handshake, no sequence numbers, no acknowledgment. Each datagram is independent.

**Use cases:** DNS (53), DHCP (67/68), SNMP (161), NTP (123), TFTP (69), RADIUS (1812), VoIP (RTP), gaming, streaming — anything where speed matters more than reliability or where the application handles retransmission itself.

**UDP scanning challenge:** Unlike TCP (which gives RST for closed ports), UDP gives no response for open ports in most cases. A closed UDP port triggers an ICMP Port Unreachable message. This makes UDP scanning slow and unreliable:
- No response = port might be open OR packet was dropped
- ICMP Port Unreachable = port is closed
- Many hosts rate-limit ICMP responses, making UDP scans slower than TCP

```bash
# Nmap UDP scan (slow, requires root)
nmap -sU -p 53,67,68,69,161,500 target

# Focus on common UDP services
nmap -sU --top-ports 20 target
```

---

## IP Addressing

### IPv4

IPv4 addresses are 32 bits, written in dotted-decimal notation (four octets). `192.168.1.100` = `11000000.10101000.00000001.01100100`.

**Private ranges (RFC 1918):**
- `10.0.0.0/8` — 10.0.0.0 to 10.255.255.255 (16,777,216 addresses)
- `172.16.0.0/12` — 172.16.0.0 to 172.31.255.255 (1,048,576 addresses)
- `192.168.0.0/16` — 192.168.0.0 to 192.168.255.255 (65,536 addresses)

**Other special ranges:**
- `127.0.0.0/8` — Loopback (127.0.0.1 = localhost)
- `169.254.0.0/16` — APIPA (Automatic Private IP Addressing) — assigned when DHCP fails
- `0.0.0.0` — "This network" / "any address" — used in routing and listen statements
- `255.255.255.255` — Limited broadcast
- `224.0.0.0/4` — Multicast

**Subnetting:** A subnet mask defines how many bits are the network portion. `/24` means 24 bits for network, 8 bits for host — 256 addresses (254 usable, minus network address and broadcast).

Quick mental math: `/24` = 256 hosts, `/25` = 128, `/26` = 64, `/27` = 32, `/28` = 16.

**CIDR notation:** `192.168.1.0/24` means the network is `192.168.1.0` with a mask of `255.255.255.0`. The broadcast is `192.168.1.255`. Usable hosts: `192.168.1.1` to `192.168.1.254`.

**Pentesting implication:** When scoping an engagement, the target provides IP ranges in CIDR notation. Understanding subnetting lets you calculate exactly how many hosts you're scanning. `10.0.0.0/8` is 16 million addresses — you need to narrow scope before blindly scanning.

### IPv6

IPv6 uses 128-bit addresses in hexadecimal. `::1` is loopback. `fe80::/10` is link-local (equivalent to APIPA). Many pentesters overlook IPv6 — which is a mistake, because dual-stack environments may have IPv6 firewall rules that are far more permissive than IPv4 rules.

---

## DNS — Domain Name System

DNS translates human-readable domain names into IP addresses. Understanding DNS deeply is critical because DNS is exploited in SSRF, subdomain enumeration, zone transfers, and more.

### DNS Resolution — Step by Step

When your browser requests `www.example.com`:

```
Browser → OS DNS resolver (checks local cache)
       → /etc/hosts (or C:\Windows\System32\drivers\etc\hosts)
       → Recursive resolver (configured DNS server, e.g., 8.8.8.8)
         → Root nameservers (13 sets: a.root-servers.net through m.root-servers.net)
             → TLD nameservers (.com, .org, .in, etc.)
                 → Authoritative nameserver for example.com
                     → Returns A record (IP address)
       → Recursive resolver caches result for TTL duration
Browser receives IP → makes TCP connection
```

The root nameservers don't know the answer — they know who to ask next. This hierarchical delegation is why DNS is distributed and resilient.

### DNS Record Types

| Record | Purpose | Pentesting Relevance |
|--------|---------|---------------------|
| A | IPv4 address for hostname | Primary target resolution |
| AAAA | IPv6 address for hostname | Often overlooked, may reveal internal hosts |
| CNAME | Canonical name (alias) | Subdomain takeover if target CNAME points to unclaimed service |
| MX | Mail exchange server | Identifies mail infrastructure; phishing campaign target selection |
| NS | Nameserver for the zone | Zone transfer attempts |
| PTR | Reverse DNS (IP → hostname) | Identify hosts during internal assessments, map IP ranges to names |
| TXT | Arbitrary text | SPF, DKIM, DMARC records; sometimes reveals internal info, verification tokens |
| SOA | Start of authority | Zone transfer check; contains primary NS and admin email |
| SRV | Service location | Active Directory uses SRV records extensively; reveals AD infrastructure |
| CAA | Certification Authority Authorization | Which CAs can issue certs for the domain |

### DNS Zone Transfer

A zone transfer (AXFR query) requests a complete copy of a DNS zone — intended for secondary nameservers to synchronize with primaries. Misconfigured nameservers allow AXFR from any IP, revealing every subdomain and internal hostname.

```bash
# Attempt zone transfer
dig axfr @ns1.example.com example.com

# Using dnsrecon
dnsrecon -d example.com -t axfr

# Using dnsenum
dnsenum example.com
```

A successful zone transfer is a critical finding — it exposes the entire DNS structure of the target.

### DNS Security Issues

**DNS Cache Poisoning (Kaminsky Attack):** If an attacker can inject a forged DNS response into a recursive resolver's cache before the legitimate response arrives, all clients using that resolver get poisoned results. The Kaminsky attack (2008) revealed that predictable transaction IDs made this practical at scale. Mitigations: randomized source ports (each query from a different port), DNSSEC.

**DNSSEC:** Signs DNS records with cryptographic signatures. Allows resolvers to verify responses haven't been tampered with. Not universally deployed — many domains don't implement it.

**DNS Tunneling:** Encodes arbitrary data inside DNS queries and responses to exfiltrate data or tunnel C2 traffic through DNS, which is rarely blocked by egress filters. Tools: dnscat2, iodine. Detection: unusually long or high-frequency DNS queries, queries for non-existent domains, base64/hex patterns in hostnames.

---

## HTTP and HTTPS

HTTP (HyperText Transfer Protocol) is a **stateless, application-layer, request-response protocol**. Every web pentest lives at this layer.

### HTTP Request Structure

```
GET /api/v1/users/123 HTTP/1.1
Host: api.example.com
User-Agent: Mozilla/5.0 ...
Accept: application/json
Authorization: Bearer eyJhbGc...
Cookie: session=abc123; CSRF=xyz789
Connection: keep-alive

[Request body — present for POST, PUT, PATCH]
```

Key headers relevant to pentesting:
- `Host`: Virtual host routing — changing this can reach different vhosts on the same IP
- `Authorization`: Bearer tokens, Basic auth, API keys
- `Cookie`: Session management
- `Referer`: Can leak sensitive URLs
- `X-Forwarded-For`: IP forwarding header — can be spoofed to bypass IP-based controls
- `Content-Type`: Changing this (e.g., `application/json` → `application/xml`) can trigger parsing differences
- `Origin`: Cross-origin request origin — relevant to CORS

### HTTP Methods

| Method | Purpose | Security Implication |
|--------|---------|---------------------|
| GET | Retrieve resource | Parameters in URL — logged in server logs, browser history, Referer header |
| POST | Submit data | Body parameters — not in URL, but equally vulnerable to injection |
| PUT | Replace resource | Often used in REST APIs; may allow file upload/overwrite |
| PATCH | Partial update | Mass assignment risk |
| DELETE | Remove resource | Broken access control — can user delete other users' resources? |
| OPTIONS | List allowed methods | Use to enumerate what HTTP methods server accepts |
| HEAD | GET without body | Used in recon to check if resource exists without downloading content |
| TRACE | Echo request back | XST (Cross-Site Tracing) — mostly mitigated in modern browsers |
| CONNECT | Tunnel through proxy | Used for HTTPS through HTTP proxies |

### HTTP Status Codes

| Range | Meaning | Pentesting Use |
|-------|---------|---------------|
| 200 OK | Success | Resource exists, request worked |
| 201 Created | Resource created | POST/PUT succeeded |
| 301/302 | Redirect | May leak internal URLs; open redirect potential |
| 400 Bad Request | Malformed request | Boundary of what server accepts |
| 401 Unauthorized | Authentication required | No token provided |
| 403 Forbidden | Authenticated but not authorized | Access control boundary |
| 404 Not Found | Resource doesn't exist | Compare with 403 — 403 proves existence |
| 405 Method Not Allowed | HTTP method not allowed | Probe which methods work |
| 429 Too Many Requests | Rate limiting | Rate limit detection |
| 500 Internal Server Error | Server-side error | May reveal framework, stack traces, error messages |
| 502/503/504 | Gateway/service errors | Load balancer or upstream service issues |

**403 vs 404 distinction:** If you request `/admin` and get 403, the endpoint *exists* but you're blocked. If you get 404, it (apparently) doesn't exist. This distinction matters for mapping attack surface.

### Cookies and Security Attributes

Cookies carry session state in a stateless protocol. Security-relevant cookie attributes:

- **Secure:** Cookie only sent over HTTPS. Without this, cookies travel over HTTP and can be intercepted.
- **HttpOnly:** JavaScript cannot access the cookie via `document.cookie`. Mitigates XSS-based session theft (but not all XSS impact).
- **SameSite:** Controls cross-site sending. `Strict` = never sent cross-site; `Lax` = sent for top-level GET navigation; `None` = always sent (must also set Secure). `None` without `SameSite=Strict/Lax` enables CSRF.
- **Domain:** Specifies which (sub)domains receive the cookie. A broad setting (e.g., `.example.com`) shares the cookie across all subdomains — a subdomain takeover would receive session cookies.
- **Path:** Cookie only sent for URLs matching this path.
- **Expires/Max-Age:** Session cookie (no expiry) vs persistent cookie.

---

## TLS and HTTPS

TLS (Transport Layer Security) provides confidentiality, integrity, and authentication for application-layer protocols. HTTPS = HTTP over TLS.

### TLS Handshake (TLS 1.3 Simplified)

```
Client                              Server
  |                                   |
  |-- ClientHello (supported TLS,  -->|  Supported TLS versions, cipher suites,
  |   cipher suites, random nonce)    |  key share (Diffie-Hellman parameters)
  |                                   |
  |<-- ServerHello (chosen version, --|  Selects cipher suite, sends its key share
  |    cipher, key share)             |  and certificate
  |    Certificate                    |
  |    CertificateVerify              |
  |    Finished                       |
  |                                   |
  |-- Finished ---------------------->|  Both sides derive session keys
  |                                   |
  |====== Encrypted Application Data =|
```

Key concepts:
- **Certificate:** Contains the server's public key, signed by a Certificate Authority (CA). The client verifies the certificate is signed by a trusted CA and that the hostname matches.
- **Certificate chain:** Server cert → Intermediate CA cert → Root CA cert. The root CA must be in the client's trust store.
- **HSTS (HTTP Strict Transport Security):** `Strict-Transport-Security: max-age=31536000; includeSubDomains` — tells browsers to *only* connect via HTTPS for the specified duration. Prevents SSL stripping attacks.
- **Certificate Pinning:** Application hardcodes expected certificate/public key. Prevents MITM even with a trusted CA-issued certificate. Common in mobile apps — bypass is a core skill (MASTG).

### TLS Vulnerabilities to Know

| Vulnerability | Description | Affected Versions |
|---------------|-------------|-------------------|
| POODLE | Padding oracle on SSLv3 CBC | SSLv3 (deprecated) |
| BEAST | Chosen-plaintext attack on CBC | TLS 1.0 (mitigated) |
| CRIME/BREACH | Compression side-channel attacks | TLS compression enabled |
| Heartbleed | Buffer over-read in OpenSSL's heartbeat | OpenSSL 1.0.1 – 1.0.1f |
| SWEET32 | Birthday attack on 64-bit block ciphers | 3DES, Blowfish |
| DROWN | Downgrade via SSLv2 on same key | SSLv2 still enabled |
| ROBOT | Return Of Bleichenbacher's Oracle Threat | PKCS#1 v1.5 RSA |

When testing TLS: use `testssl.sh` or `sslscan` or `sslyze`. Look for: SSLv3/TLS 1.0/1.1 still enabled, weak cipher suites (RC4, 3DES, DES, NULL), self-signed or expired certificates, missing HSTS, missing HPKP (deprecated but still seen).

---

## Essential Protocols — Port, Purpose, Attack Surface

Every pentester must know these by heart:

| Port | Protocol | Purpose | Attack Surface |
|------|----------|---------|---------------|
| 21 | FTP | File transfer | Anonymous auth, cleartext creds, bounce attacks, FTPS misconfig |
| 22 | SSH | Secure shell | Weak keys, old versions (ShellShock), password auth enabled |
| 23 | Telnet | Legacy remote access | Cleartext protocol — capture credentials with Wireshark/Responder |
| 25 | SMTP | Mail sending | Open relay, VRFY/EXPN user enum, spoofing without SPF/DMARC |
| 53 | DNS | Name resolution | Zone transfer, cache poisoning, DNS tunneling |
| 67/68 | DHCP | IP assignment | Rogue DHCP, DHCP starvation |
| 69 | TFTP | Trivial file transfer | No auth, UDP, used in network device boot — may expose configs |
| 80 | HTTP | Web traffic | All web vulns |
| 88 | Kerberos | AD authentication | Kerberoasting, AS-REP roasting, ticket attacks |
| 110 | POP3 | Email retrieval (old) | Cleartext credentials |
| 111 | RPC | Remote procedure calls | NFS enumeration, RPC service list |
| 135 | MSRPC | Windows RPC | DCOM exploitation, remote WMI |
| 137-139 | NetBIOS | Legacy Windows networking | NBT-NS poisoning (Responder), null sessions |
| 143 | IMAP | Email retrieval | Credential brute force |
| 161/162 | SNMP | Network device management | Community string = password (often "public"/"private"), walk MIB for device info, v1/v2c cleartext |
| 389 | LDAP | Directory services | Unauthenticated enumeration, LDAP injection |
| 443 | HTTPS | Secure web | All web vulns + TLS misconfig |
| 445 | SMB | Windows file sharing | EternalBlue, PsExec, relay attacks, null sessions, share enumeration |
| 500 | IKE/ISAKMP | IPsec VPN | Aggressive mode PSK cracking |
| 512-514 | rsh/rexec/rlogin | Legacy Unix remote | Often misconfigured to trust any host (.rhosts) |
| 636 | LDAPS | LDAP over TLS | Same as LDAP but encrypted |
| 873 | rsync | File sync | Unauthenticated access to module lists |
| 993/995 | IMAPS/POP3S | Secure email | TLS misconfig |
| 1433 | MSSQL | Microsoft SQL Server | SA account, xp_cmdshell, linked servers |
| 1521 | Oracle DB | Oracle Database | TNS listener attacks |
| 2049 | NFS | Network File System | Exports without auth, root squash misconfig |
| 3306 | MySQL | MySQL Database | Weak credentials, UDF injection |
| 3389 | RDP | Remote Desktop | BlueKeep, DejaBlue, credential spraying, NLA bypass |
| 4444/4445 | Metasploit default | C2/shells | |
| 5432 | PostgreSQL | PostgreSQL Database | Weak credentials, COPY TO/FROM for file read/write |
| 5900 | VNC | Remote desktop | No auth, weak password, screenshot capture |
| 6379 | Redis | In-memory DB | Unauthenticated access (common!), SSRF to Redis |
| 8080/8443 | HTTP/HTTPS alt | Web apps, admin panels | Same as 80/443 — often less hardened admin interfaces |
| 8888 | Jupyter Notebook | Data science tool | Often exposed without auth — direct code execution |
| 27017 | MongoDB | NoSQL database | No auth by default in older versions |

---

## ARP — Address Resolution Protocol

ARP operates at Layer 2. When Host A needs to send a packet to Host B on the same subnet, it knows Host B's IP but not its MAC address. ARP resolves IP → MAC.

```
Host A broadcasts: "Who has 192.168.1.100? Tell 192.168.1.50"
Host B replies unicast: "192.168.1.100 is at aa:bb:cc:dd:ee:ff"
Host A caches this mapping (ARP cache) and sends the frame to that MAC.
```

**The critical flaw:** ARP is stateless and has no authentication. Any host on the segment can send unsolicited ARP replies, and receivers will update their cache. This enables ARP poisoning/spoofing.

**ARP Poisoning / ARP Spoofing:**

```
Attacker → Host A: "192.168.1.1 (gateway) is at attacker's MAC"
Attacker → Router: "192.168.1.50 (Host A) is at attacker's MAC"
```

Both Host A and the router now send traffic through the attacker — a classic man-in-the-middle position. The attacker forwards the traffic (so both sides don't notice) while capturing or modifying it.

**Tools:** `arpspoof`, `ettercap`, `bettercap`
```bash
# Enable IP forwarding (so traffic flows through you)
echo 1 > /proc/sys/net/ipv4/ip_forward

# ARP spoof both directions
arpspoof -i eth0 -t 192.168.1.100 192.168.1.1   # Tell victim the gateway is us
arpspoof -i eth0 -t 192.168.1.1 192.168.1.100   # Tell gateway the victim is us
```

**Detections and mitigations:** Dynamic ARP Inspection (DAI) on managed switches; static ARP entries; XDR/EDR ARP monitoring; ArpWatch.

---

## VLANs and VLAN Hopping

A VLAN (Virtual LAN) logically segments a physical network. Hosts in VLAN 10 cannot communicate with hosts in VLAN 20 without going through a router or Layer 3 switch — even if they're on the same physical switch. This is a critical segmentation control.

**VLAN tagging (802.1Q):** Switches add a 4-byte 802.1Q tag to frames, including a 12-bit VLAN ID, when transporting frames over trunk links (links between switches or between switch and router).

**Access port vs trunk port:**
- **Access port:** Belongs to one VLAN; 802.1Q tags are stripped when frames leave toward the end device. End devices (PCs, servers) connect to access ports and are unaware of VLAN tagging.
- **Trunk port:** Carries frames from multiple VLANs; 802.1Q tags are preserved. Switch-to-switch and switch-to-router links are trunks.

**VLAN Hopping Attack 1 — Switch Spoofing:**
Many switches auto-negotiate trunk mode with connected devices (DTP — Dynamic Trunking Protocol). An attacker configures their NIC to act as a trunk port and negotiate DTP with the switch. Once trunking is established, the attacker receives frames from all VLANs on the trunk and can inject 802.1Q tagged frames into any VLAN.

*Mitigation:* Disable DTP on all access ports (`switchport nonegotiate`), manually configure all ports as access or trunk — never auto.

**VLAN Hopping Attack 2 — Double Tagging:**
Requires the attacker's access port to be in the native VLAN (the VLAN that frames are assigned to on a trunk when there's no 802.1Q tag — often VLAN 1 by default). The attacker sends a frame with two 802.1Q tags: the outer tag is the native VLAN, the inner tag is the target VLAN. When the switch strips the outer tag (because it matches the native VLAN), the inner tag is revealed and the frame is forwarded to the target VLAN.

*Limitation:* Only works one-way (attacker can send to target VLAN but responses go back to the attacker's original VLAN unless ARP poisoning is also used).

*Mitigation:* Change native VLAN away from VLAN 1; explicitly tag all native VLAN traffic.

---

## Firewalls

Firewalls control traffic flow based on rules. Understanding firewall types is critical for both assessment scoping and for choosing bypass techniques.

### Stateless (Packet Filtering) Firewalls

Inspect each packet independently against a rule set (source IP, destination IP, source port, destination port, protocol). No concept of connection state.

**Limitation:** Cannot distinguish a SYN (new connection) from an ACK (existing connection). A rule allowing TCP port 80 inbound also allows an attacker to send arbitrary TCP ACK packets on port 80. Nmap ACK scans (`-sA`) can exploit this to map which ports have stateless firewall rules.

### Stateful Firewalls

Track connection state in a state table. A packet is allowed only if it matches an established connection entry or matches a rule permitting new connections. An unsolicited ACK with no matching SYN in the state table is dropped.

**Fragmentation bypass:** Very old stateful firewalls reassemble fragments only partially or not at all, allowing attackers to split attack payloads across fragments that pass individually but form malicious content when reassembled at the destination.

### Application Layer Firewalls / WAFs

Inspect application-layer content (HTTP body, headers, cookies). Can block SQL injection, XSS, etc. Often bypassable through encoding, case variation, comment insertion, or exploiting parser differences between WAF and backend.

### Firewall Rule Order

Rules are processed top-to-bottom (most firewalls). The first matching rule wins. An explicit `deny` rule at the end catches everything not explicitly permitted (default-deny). Understanding this matters when you're analyzing firewall configs during config review engagements.

---

## Key Networking Concepts for Pentests

**NAT (Network Address Translation):** Routers translate private IPs to a public IP for internet traffic. Complicates external-to-internal exploitation because the internal IP is hidden. PAT (Port Address Translation) allows multiple internal hosts to share one public IP by using different source ports.

**Proxy servers:** Intermediate servers that make requests on behalf of clients. Can be transparent (client unaware) or explicit. Relevant to SSRF (the server makes requests through its proxy), and to intercepting traffic during web assessments (Burp Suite as an intercepting proxy).

**Port forwarding:** Redirecting traffic arriving on one port/IP to another port/IP. SSH port forwarding (`ssh -L`, `-R`, `-D`) is essential for pivoting:
```bash
# Local forward: traffic to localhost:8080 is forwarded through SSH to target:80
ssh -L 8080:internal-server:80 pivot-host

# Dynamic (SOCKS proxy): all traffic through localhost:1080 is proxied via pivot-host
ssh -D 1080 pivot-host
```

**Routing:** Routers maintain routing tables to decide where to forward packets. In an internal assessment, understanding the network topology (which subnets can reach which) is essential for planning pivot paths.

---

## Summary: What to Memorize Cold

- OSI 7 layers and what attacks target each
- TCP three-way handshake mechanics and SYN flood/SYN cookie relationship
- TCP flags and what each means in a scan context
- Private IP ranges
- DNS record types and what zone transfer reveals
- HTTP methods and status codes (200, 301, 400, 401, 403, 404, 500)
- Cookie security attributes (Secure, HttpOnly, SameSite)
- TLS handshake sequence
- Port numbers for all 30+ essential services
- ARP poisoning mechanism
- VLAN hopping techniques
- Stateful vs stateless firewall differences
