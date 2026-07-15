# Reconnaissance

!!! info "Why This Matters"
    Reconnaissance determines the quality of everything that follows. The more you know about your target — its technologies, its people, its infrastructure — the more precisely you can attack. A thorough recon phase means you test what actually matters, not what you assume is there.

---

## Passive vs Active Reconnaissance

The fundamental distinction in reconnaissance is whether your activities generate traffic that the target can observe.

### Passive Reconnaissance

You gather information without directly interacting with the target's systems. All queries go to third-party sources — DNS registries, Google, Shodan, LinkedIn, archived data. The target cannot detect passive reconnaissance in their logs because you never touch their infrastructure.

**When to use:** Always — do passive recon before active. Even in black-box external pentests, passive recon gives you a map of the attack surface before you generate any traffic the target might detect.

**Sources:**
- WHOIS databases

- DNS records (public)

- Search engines (Google, Bing, DuckDuckGo)

- Certificate Transparency logs

- Shodan, Censys, FOFA

- Social media and LinkedIn

- Job postings (reveal technology stack)

- Public code repositories (GitHub, GitLab)

- Web archives (Wayback Machine)

- Google Dorks

### Active Reconnaissance

You directly interact with the target's infrastructure — scanning, banner grabbing, sending requests. The target can potentially detect and log this activity.

**When to use:** After passive recon has identified the attack surface. More targeted active recon is less noisy than blind scanning.

---

## WHOIS

WHOIS is a query protocol for looking up domain registration information. It reveals the registrant's name, organization, email, address, nameservers, registration date, and expiry date.

```bash
whois example.com
whois 198.51.100.5      # Reverse WHOIS on an IP
```

**What to look for:**
- Registrant organization and contact details (useful for spear phishing pretexts)

- Nameservers (identify DNS provider)

- Registration date (new domains may indicate phishing campaigns against your client)

- Expiry date (expiring domains can be snatched for subdomain takeover)

- Registrar abuse contacts (useful if you're on a bug bounty and need to report infra abuse)

**WHOIS privacy protection:** Many registrants use WHOIS privacy services (Domains by Proxy, etc.) that substitute their real contact details with proxy contact details. This limits WHOIS usefulness but is itself useful information — intentional privacy measures suggest security awareness.

**ARIN/RIPE/APNIC for IP ranges:** WHOIS also covers IP address allocation. Querying an IP tells you which organization owns the range, enabling you to discover all IP ranges assigned to a target:

```bash
whois 198.51.100.0
# Returns: CIDR range, organization, ASN, abuse contact
```

---

## DNS Enumeration

DNS is a goldmine during reconnaissance. Beyond the A record for the main domain, DNS reveals subdomains (potential attack surface), mail servers (phishing targets), nameservers (zone transfer opportunities), and sometimes internal information in TXT records.

### Basic DNS Queries

```bash
# A record (IPv4)
dig A example.com
nslookup example.com

# All record types
dig ANY example.com

# MX records (mail servers)
dig MX example.com

# NS records (nameservers)
dig NS example.com

# TXT records (SPF, DKIM, DMARC, verification tokens)
dig TXT example.com

# SOA record (primary NS, admin email, zone serial)
dig SOA example.com

# PTR record (reverse DNS — IP to hostname)
dig -x 198.51.100.5

# Using a specific nameserver
dig @ns1.example.com example.com
```

### Zone Transfer Attempt

Always attempt zone transfer against all nameservers. One may be misconfigured even if the primary isn't.

```bash
# Get nameservers first
dig NS example.com

# Attempt zone transfer from each
dig axfr @ns1.example.com example.com
dig axfr @ns2.example.com example.com

# With host command
host -t axfr example.com ns1.example.com

# With dnsrecon
dnsrecon -d example.com -t axfr

# With dnsenum
dnsenum example.com
```

A successful zone transfer returns every record in the zone — subdomains, mail servers, internal hostnames — and is a critical finding.

### Subdomain Enumeration

If zone transfer fails, enumerate subdomains through other means:

**Brute force with wordlists:**
```bash
# gobuster dns mode
gobuster dns -d example.com -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-5000.txt

# amass (comprehensive, uses multiple sources)
amass enum -d example.com

# subfinder (passive, multiple sources)
subfinder -d example.com

# dnsrecon brute force
dnsrecon -d example.com -t brt -D /usr/share/wordlists/dnsmap.txt
```

**Certificate Transparency logs:**
Every certificate issued for a domain is logged publicly in Certificate Transparency (CT) logs. This reveals subdomains that may not be in DNS anymore but had certificates issued.

```bash
# curl the crt.sh API
curl -s "https://crt.sh/?q=%.example.com&output=json" | jq '.[].name_value' | sort -u

# Or browse to: https://crt.sh/?q=%25.example.com
```

**Reverse DNS scanning:**
If you know the IP range, reverse DNS lookups can reveal hostnames:
```bash
dnsrecon -r 198.51.100.0/24 -t rvl   # Reverse lookup entire range
```

---

## Google Dorking

Google dorking uses advanced search operators to find sensitive information indexed by Google. This is pure passive reconnaissance — you're querying Google, not the target.

### Core Operators

| Operator | Function | Example |
|----------|----------|---------|
| `site:` | Limit to specific domain | `site:example.com` |
| `inurl:` | String in URL | `inurl:admin site:example.com` |
| `intitle:` | String in page title | `intitle:"index of" site:example.com` |
| `intext:` | String in page body | `intext:"password" site:example.com` |
| `filetype:` | File extension | `filetype:pdf site:example.com` |
| `ext:` | File extension (alternative) | `ext:sql site:example.com` |
| `cache:` | Google's cached version | `cache:example.com` |
| `link:` | Pages linking to URL | `link:example.com` |
| `related:` | Similar sites | `related:example.com` |
| `-` | Exclude results | `site:example.com -www` |
| `"..."` | Exact phrase | `"confidential" site:example.com` |
| `OR` | Either term | `admin OR administrator site:example.com` |
| `*` | Wildcard | `"password *" site:example.com` |

### Useful Dork Combinations

```
# Directory listings (exposed file indexes)
intitle:"index of" site:example.com

# Login panels
inurl:login site:example.com
inurl:admin site:example.com
intitle:"login" site:example.com

# Configuration files
ext:xml site:example.com
ext:conf site:example.com
ext:env site:example.com
filetype:yaml site:example.com

# Database files
ext:sql site:example.com
ext:db site:example.com
ext:sqlite site:example.com

# Log files
ext:log site:example.com
intitle:"index of" "access.log" site:example.com

# Backup files
ext:bak site:example.com
ext:old site:example.com
ext:backup site:example.com

# Exposed credentials
intext:"password" ext:txt site:example.com
intext:"api_key" site:example.com

# Error messages (reveal stack info)
intext:"Fatal error" site:example.com
intext:"Warning: mysql" site:example.com

# Specific technologies
inurl:".php?id=" site:example.com     # Potential SQLi parameter
intitle:"phpMyAdmin" site:example.com  # Database admin panel
inurl:"/wp-admin" site:example.com     # WordPress admin
```

**GHDB:** The Google Hacking Database (exploit-db.com/google-hacking-database) maintains thousands of categorized dorks. Always check it before manual dorking — someone may have already built the exact dork you need.

---

## Shodan

Shodan is a search engine for internet-connected devices. It continuously scans the internet and indexes banner information from ports. Unlike Google (which indexes web pages), Shodan indexes open ports and their banners across all protocols.

### Key Shodan Filters

```
# Search by hostname
hostname:example.com

# Search by IP or CIDR
ip:198.51.100.0/24

# Search by organization (ASN registrant name)
org:"Example Corporation"

# Search by autonomous system number
asn:AS12345

# Search by country
country:IN        # India
country:US

# Search by product/software
product:"Apache httpd"
product:"nginx"
product:Elasticsearch

# Search by port
port:22
port:3306
port:6379           # Redis

# Combine filters
org:"Example Corp" port:3306
hostname:example.com product:nginx

# Search for default credentials
"default password" hostname:example.com

# Search for specific response strings
"MongoDB Server Information" hostname:example.com
"X-Powered-By: PHP" hostname:example.com

# Find printers, cameras, etc.
product:"HP LaserJet" org:"Example Corp"
"Server: IP Webcam" country:IN
```

### Shodan for Pentesting

```bash
# Shodan CLI (after registering and installing)
shodan search hostname:example.com

# Get all IPs for an organization
shodan search org:"Example Corp" --fields ip_str,port,data

# Alert on new open ports for a domain
shodan alert create example.com 198.51.100.0/24

# Download results for offline processing
shodan download results hostname:example.com
shodan parse results.json.gz
```

**What to look for on Shodan during recon:**
- Open RDP (3389), SSH (22), Telnet (23) — remote access services

- Exposed databases (MongoDB 27017, Redis 6379, Elasticsearch 9200, MySQL 3306)

- Default banners revealing software versions → search CVEs

- Admin panels (Tomcat manager, phpmyadmin, Jenkins)

- Unusual ports that shouldn't be internet-facing

- IoT devices (printers, cameras, industrial equipment)

**Censys** is an alternative to Shodan with different coverage and query syntax. Use both for comprehensive coverage.

---

## Web Technology Fingerprinting

Identifying the technology stack before testing focuses your efforts on relevant vulnerabilities.

### Passive Fingerprinting

**HTTP Headers:** Reveal web server, framework, cookies:
```
Server: nginx/1.18.0
X-Powered-By: PHP/7.4.3
X-Generator: Drupal 8 (https://www.drupal.org)
Set-Cookie: PHPSESSID=...; path=/     # PHP
Set-Cookie: JSESSIONID=...             # Java
Set-Cookie: ASP.NET_SessionId=...      # ASP.NET
```

**HTML source code:** Comment blocks often contain version info, internal paths, developer notes. Framework-specific paths (e.g., `/wp-content/` for WordPress).

**JavaScript files:** Framework names and versions often appear in libraries.

**`robots.txt`:** Lists directories the webmaster doesn't want crawled — which often means interesting directories. Always check.

**`sitemap.xml`:** Lists URLs for SEO purposes — maps the full application structure.

**`/.well-known/`:** Various discovery files — `security.txt` (bug bounty contact), `openid-configuration` (OAuth discovery).

### Active Fingerprinting

```bash
# whatweb — technology stack identification
whatweb http://example.com -v

# Wappalyzer (browser extension) — passive while browsing

# nmap service and version detection
nmap -sV -p 80,443,8080,8443 example.com

# curl to inspect headers
curl -I http://example.com
curl -v http://example.com 2>&1 | grep -E "^[<>]"

# Check for specific CMS
curl http://example.com/wp-login.php        # WordPress
curl http://example.com/administrator/      # Joomla
curl http://example.com/user/login          # Drupal
```

---

## GitHub and Code Repository Recon

Developers push sensitive information to public repositories more often than they should. This is one of the highest-yield passive recon activities.

```bash
# Search GitHub for target domain
# https://github.com/search?q=example.com&type=code

# Search for API keys, passwords
# https://github.com/search?q=example.com+password&type=code
# https://github.com/search?q=example.com+api_key&type=code
# https://github.com/search?q=example.com+secret&type=code

# Tools for automated GitHub recon
# trufflehog — searches for secrets in git history
trufflehog github --org=example-corp

# gitleaks — find secrets in repos
gitleaks detect --source /path/to/cloned/repo

# gitrob — find sensitive files in GitHub organizations
gitrob analyze example-corp
```

**What to look for in repos:**
- Hardcoded API keys, database credentials, OAuth tokens

- Internal IP addresses or hostnames

- AWS/GCP/Azure credentials (`.env` files, config files)

- Private SSH keys

- JWT secrets

- Database connection strings

Even if developers notice and remove the file, `git log` still contains the history. Secrets in git history require a force-push to purge properly — many teams don't know this.

---

## Email Harvesting

Collecting email addresses of target organization employees enables spear phishing and credential stuffing.

```bash
# theHarvester — searches multiple public sources
theHarvester -d example.com -b all
theHarvester -d example.com -b google,linkedin,bing

# hunter.io — finds email patterns
# Visit hunter.io/search/example.com
# Reveals email pattern (firstname.lastname@example.com) and specific addresses

# LinkedIn search
# Search for employees at the target company
# LinkedIn Sales Navigator (paid) gives full access
# Free: search "site:linkedin.com/in/ example.com" in Google

# Phonebook.cz, EmailFormat.com — email pattern databases
```

**From email addresses, derive:**
- Email format (first.last vs flast vs first_last) — use to construct addresses for other employees

- Employee names → spear phishing targets

- Job roles and departments → targeted pretexting scenarios

---

## Job Postings as Intelligence

A company's job postings reveal their technology stack, current projects, and gaps in their security posture:

```
"Experience with AWS EKS, Kubernetes, Terraform required"
→ Cloud-native infrastructure, likely container-based

"Must have experience with PAN-OS firewall management"
→ Palo Alto Networks is their firewall vendor

"Familiarity with Splunk SIEM preferred"
→ Their SIEM platform

"Currently hiring: SAP BASIS administrator"
→ SAP ERP in use

"Help Desk Technician — will support 2000 Windows 10 endpoints"
→ Scale and OS version of endpoint environment

"We are migrating from on-prem to Azure"
→ Hybrid environment, migration in progress (often security gaps during transitions)
```

Expired job postings (archive.org) can reveal past technology choices and projects.

---

## Wayback Machine

The Internet Archive's Wayback Machine (web.archive.org) stores historical snapshots of websites. Useful for:

- Finding old application versions with known vulnerabilities that may still be running internally

- Discovering hidden/removed endpoints that might still exist

- Understanding application structure before a major redesign

- Finding old credentials or configuration data that was later removed

```bash
# Manual browsing: https://web.archive.org/web/*/example.com/*

# Using waybackurls tool
waybackurls example.com | sort -u | grep -E "\.(php|asp|aspx|jsp|cfm)"

# Using gau (Get All URLs) — combines multiple sources
gau example.com | sort -u
```

---

## Reconnaissance Workflow Summary

A systematic recon workflow for an external engagement:

```
1. WHOIS — registrant, nameservers, IP ranges
2. ASN lookup — all IP ranges owned by the organization
3. DNS — all records, zone transfer attempt, subdomain enum (brute + CT logs)
4. Shodan/Censys — what's exposed on discovered IPs
5. Google Dorks — sensitive files, exposed panels, error messages
6. Web fingerprinting — technology stack per application
7. GitHub recon — secrets, internal info in public repos
8. Email harvesting — employee addresses, email format
9. Job postings — technology stack and projects
10. Wayback Machine — historical endpoints, old versions
```

Document everything in a structured format as you go. The recon phase output becomes the roadmap for scanning and testing phases.
