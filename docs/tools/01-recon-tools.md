# Recon Tools

Quick reference for the reconnaissance phase — passive and active information gathering.

---

## theHarvester

**Purpose:** Gathers email addresses, subdomains, IPs, and URLs from public sources.

```bash
# Search across all sources
theHarvester -d example.com -b all

# Search specific sources
theHarvester -d example.com -b google,bing,linkedin,yahoo

# Output to file
theHarvester -d example.com -b all -f results.html

# Common sources: google, bing, baidu, yahoo, hunter, linkedin, twitter, github, shodan
```

**Interview relevance:** Know what sources it queries, that it's passive reconnaissance (no direct contact with target), and what the typical output is used for (email lists for phishing simulation, subdomain list for further testing).

---

## Amass

**Purpose:** Comprehensive subdomain enumeration using DNS, scraping, APIs, and brute force.

```bash
# Passive enumeration only
amass enum -passive -d example.com

# Active + passive (DNS brute force included)
amass enum -d example.com

# Use API keys for additional sources
amass enum -d example.com -config ~/.config/amass/config.ini

# Output to file
amass enum -d example.com -o subdomains.txt

# Intel mode — find related domains
amass intel -d example.com -whois
```

**Interview relevance:** Understanding passive vs active mode, and that amass uses multiple techniques (DNS, CT logs, scraping, APIs) making it more comprehensive than single-technique tools.

---

## Subfinder

**Purpose:** Fast passive subdomain discovery using multiple APIs.

```bash
# Basic usage
subfinder -d example.com

# Output list of subdomains
subfinder -d example.com -o subdomains.txt

# Silent mode (output only)
subfinder -d example.com -silent

# Use with other tools (pipe)
subfinder -d example.com | httpx | nuclei -t technologies/
```

---

## Certificate Transparency — crt.sh

Every certificate issued for a domain is publicly logged in CT logs. Often reveals subdomains that aren't in DNS.

```bash
# Command line query
curl -s "https://crt.sh/?q=%.example.com&output=json" | jq '.[].name_value' | sort -u

# Alternative: grep out unique subdomains
curl -s "https://crt.sh/?q=%.example.com&output=json" | \
  python3 -c "import sys,json; [print(v) for x in json.load(sys.stdin) for v in x['name_value'].split('\n')]" | \
  sort -u
```

---

## Shodan CLI

```bash
# Install
pip install shodan
shodan init YOUR_API_KEY

# Basic search
shodan search hostname:example.com

# Search with specific port
shodan search hostname:example.com port:443

# Get IP information
shodan host 198.51.100.1

# Count results without downloading
shodan count hostname:example.com

# Download results
shodan download results hostname:example.com
shodan parse results.json.gz

# Monitor (alerts when new services appear)
shodan alert create "Example Corp" 198.51.100.0/24

# Stats
shodan stats --facets port hostname:example.com
```

---

## Recon-ng

**Purpose:** Full-featured OSINT framework with modular architecture. Similar concept to Metasploit but for reconnaissance.

```bash
# Start
recon-ng

# Inside recon-ng:
> marketplace install all              # Install all modules
> workspaces create example            # Create workspace
> db insert domains domains=example.com

# Use a module
> modules load recon/domains-hosts/hackertarget
> run

# Search for modules
> marketplace search github

# Common modules:
# recon/domains-hosts/brute_hosts      — DNS brute force
# recon/hosts-hosts/shodan_hostname    — Shodan lookup
# recon/domains-contacts/whois_pocs   — WHOIS contacts
# recon/contacts-credentials/hibp      — Have I Been Pwned lookup
```

---

## WHOIS Lookup

```bash
# Domain WHOIS
whois example.com

# IP range WHOIS
whois 198.51.100.1

# ASN lookup (find all IP ranges for an org)
whois -h whois.radb.net -- '-i origin AS12345'

# Online tools:
# https://whois.domaintools.com/
# https://bgp.he.net/
# https://search.arin.net/rdap/ (ARIN for North America)
# https://rdap.db.ripe.net/ (RIPE for Europe)
# https://rdap.apnic.net/ (APNIC for Asia-Pacific including India)
```

---

## Google Dorks — Quick Reference

```
# Restrict to domain
site:example.com

# Find specific file types
site:example.com filetype:pdf
site:example.com ext:xlsx ext:docx

# Find admin panels
inurl:admin site:example.com
inurl:login site:example.com
intitle:"admin panel" site:example.com

# Find exposed configs
site:example.com ext:conf
site:example.com ext:env
site:example.com ext:ini ext:cfg

# Find exposed credentials
site:example.com intext:"password"
site:example.com intext:"api_key"

# Directory listings
intitle:"index of" site:example.com

# Error messages revealing tech stack
intext:"SQL syntax" site:example.com
intext:"Warning: mysql" site:example.com
intext:"Fatal error" site:example.com

# Backup files
site:example.com ext:bak ext:backup ext:old
```

---

## DNS Enumeration Quick Reference

```bash
# Zone transfer attempt
dig axfr @ns1.example.com example.com

# All DNS record types
dig ANY example.com
dig A example.com
dig AAAA example.com
dig MX example.com
dig NS example.com
dig TXT example.com
dig SOA example.com
dig CNAME www.example.com

# Reverse DNS
dig -x 198.51.100.1

# Using dnsrecon
dnsrecon -d example.com -t axfr         # Zone transfer
dnsrecon -d example.com -t brt          # Brute force
dnsrecon -d example.com -t std          # Standard enumeration
dnsrecon -r 198.51.100.0/24 -t rvl     # Reverse lookup of IP range

# Using dnsenum
dnsenum example.com
dnsenum --threads 10 -f /usr/share/wordlists/dns/subdomains.txt example.com
```

---

## Maltego — Visual Link Analysis

Maltego creates visual relationship graphs connecting entities (people, organizations, domains, IPs, email addresses). Particularly powerful for investigating relationships across multiple data sources simultaneously.

```
Setup:
1. Register at maltego.com (free community edition available)
2. Download and install Maltego
3. Add Transform Hubs (data source integrations)

Core entities:
- Domain, DNS name, URL
- IP address, AS number, netblock
- Person, email address, phone number
- Organization, location

Key transforms:
Domain → DNS Names (subdomains)
Domain → MX records (mail servers)
Domain → Whois (registrant info)
Email → Person (social media profiles)
IP → AS number → Netblock (find related IPs)
Domain → Shodan results

Workflow:
1. Start with target domain
2. Run "All DNS" transform — discovers subdomains, mail servers, nameservers
3. Run WHOIS transform on domain — gets registrant details
4. Run "To IP Address" on discovered hostnames
5. Run Shodan transforms on IP addresses
6. Build relationship map visually

Community vs Commercial:
Community: 12 entities per graph, limited transforms
Professional/Enterprise: Unlimited, full transform library including Shodan, VirusTotal, etc.
```

---

## Wayback Machine / Web Archives

Historical website content reveals removed endpoints, old application versions, and content that developers thought was gone.

```bash
# Command-line tools for Wayback Machine

# waybackurls — get all URLs ever crawled for a domain
go install github.com/tomnomnom/waybackurls@latest
waybackurls example.com

# Filter for interesting file types
waybackurls example.com | grep -E "\.(php|asp|aspx|jsp|cfm|cgi)"
waybackurls example.com | grep -E "\.(json|xml|yaml|config|env|bak|old|backup)"
waybackurls example.com | grep "admin\|login\|api\|internal"

# gau — get all URLs from multiple sources (Wayback, CommonCrawl, OTX, URLScan)
go install github.com/lc/gau/v2/cmd/gau@latest
gau example.com
gau --blacklist png,jpg,gif,svg example.com  # Skip image URLs

# Katana — active web crawler
go install github.com/projectdiscovery/katana/cmd/katana@latest
katana -u https://example.com
katana -u https://example.com -jc  # Execute JavaScript (finds dynamic endpoints)

# Combine tools
gau example.com | sort -u | grep -E "\.(php|asp|cfm|jsp)" > old_endpoints.txt
```

**What to look for in historical content:**
- Old API endpoints that may still be active
- Removed admin panels that weren't properly access-controlled
- Old versions of applications with known CVEs
- Configuration files that were briefly indexed
- Employee names and email addresses from old "about" pages
- Forgotten subdomains from acquisitions or deprecated projects

---

## GitHub and Code Repository Recon

Developers routinely commit sensitive information — API keys, database credentials, internal hostnames — to public repositories.

```bash
# Manual GitHub search (web browser)
# https://github.com/search?q=example.com+password&type=code
# https://github.com/search?q=example.com+api_key&type=code
# https://github.com/search?q=example.com+secret&type=code
# https://github.com/search?q=example.com+token&type=code
# https://github.com/search?q=example.com+aws_access_key&type=code
# https://github.com/search?q=org:example-corp+password&type=code

# trufflehog — scan git history for secrets
pip install trufflehog
trufflehog github --org example-corp
trufflehog github --repo https://github.com/example-corp/repo
trufflehog git file:///path/to/local/repo

# gitleaks — find secrets in repositories
go install github.com/gitleaks/gitleaks/v8@latest
gitleaks detect --source /path/to/repo
gitleaks detect --source /path/to/repo --report-format json --report-path results.json

# Scan entire GitHub organization
gitleaks detect --source . -c gitleaks.toml

# gitrob — scan GitHub organizations for sensitive files
go install github.com/michenriksen/gitrob@latest
gitrob analyze example-corp

# GitHub dorking with gh CLI
gh search code "example.com password" --limit 100
gh search code "org:example-corp api_key" --limit 100
```

**High-value targets in GitHub:**
```
# Files that commonly contain credentials
.env, .env.local, .env.production
config.yml, config.json, settings.py
*.pem, *.key, *.p12, *.pfx
docker-compose.yml (often has DB passwords)
.travis.yml, .circleci/config.yml (CI/CD env vars)
Dockerfile (ENV statements)
terraform.tfvars (cloud credentials)
kubeconfig (Kubernetes cluster access)

# Search operators for GitHub
filename:.env secret
filename:config.yml password
extension:pem private
path:/.aws credentials
```

---

## Shodan Dorking — Advanced Usage

```bash
# Find specific vulnerable software versions
product:"Apache httpd" version:"2.4.49"   # CVE-2021-41773
product:"GitLab" version:"13.10.0"        # Known vulnerable version
product:"Confluence" port:8090

# Find internet-exposed services that shouldn't be
port:27017 country:IN                     # MongoDB in India
port:9200 product:Elasticsearch           # Elasticsearch (often unauthenticated)
port:6379 product:Redis                   # Redis (often unauthenticated)
port:5432 PostgreSQL country:US           # Postgres

# Find organization infrastructure
org:"Example Corporation" port:22
org:"Example Corporation" http.title:"admin"
org:"Example Corporation" ssl.cert.subject.cn:"*.example.com"

# Find exposed control panels
http.title:"Jenkins" port:8080
http.title:"Kibana" port:5601
http.title:"Jupyter" port:8888 country:IN
http.title:"phpMyAdmin"
http.component:"Laravel"

# Find default credentials
"default password" org:"Example Corp"
http.html:"admin/admin"

# ICS/SCADA (useful context for OT security assessments)
port:102 product:"Siemens S7"             # Siemens PLCs
port:20000 product:DNP3                   # DNP3 industrial protocol
"Schneider Electric" port:80

# Using Shodan API
shodan search --fields ip_str,port,org,product "hostname:example.com" --limit 100
shodan scan submit --filename targets.txt  # Scan specific IPs/ranges
shodan alert create "example monitoring" "org:\"Example Corp\""  # Monitor for changes
```

---

## Hunter.io and Email Pattern Discovery

Before running phishing simulations or credential spraying, identify the email format used by the target organization.

```
# Manual: https://hunter.io/search/example.com
# Shows: email format (firstname.lastname@example.com) + verified addresses

# Email format patterns (common):
{first}.{last}@example.com     → john.smith@example.com
{f}{last}@example.com          → jsmith@example.com
{first}@example.com            → john@example.com
{first}{last}@example.com      → johnsmith@example.com
{first}_{last}@example.com     → john_smith@example.com

# Once format known, generate email list from LinkedIn employee names
# LinkedIn → search employees → export names → Python script to format

# EmailFormat.com — another pattern database
# https://www.email-format.com/i/search/?q=example.com

# Verify emails without sending (SMTP verification)
# Tools: email-verifier, verify-email
python3 -c "
import smtplib
smtp = smtplib.SMTP('mail.example.com')
smtp.ehlo()
smtp.mail('')
code, msg = smtp.rcpt('test@example.com')
print(f'Code: {code}')  # 250 = valid, 550 = invalid
"
```

---

## Passive DNS and IP History

Historical DNS records reveal infrastructure that changed — previous hosting, moved services, internal IP leakage.

```bash
# SecurityTrails (web UI + API)
# https://securitytrails.com/domain/example.com/history/a
# Shows historical A, MX, NS, CNAME records with dates

# RiskIQ PassiveTotal (now Microsoft Defender TI)
# Historical DNS, WHOIS, malware associations

# CIRCL passive DNS
# https://www.circl.lu/services/passive-dns/

# VirusTotal for domain/IP history
curl -s "https://www.virustotal.com/api/v3/domains/example.com" \
  -H "x-apikey: YOUR_API_KEY" | jq '.data.attributes.last_dns_records'

# DNSDumpster (web) — visual DNS map
# https://dnsdumpster.com/

# What IP history reveals:
# - Previous hosting provider (may still have old version running)
# - Internal IPs leaked in DNS (dev environments)
# - Relationship between domains (shared hosting = shared IP = related company)
# - CDN vs origin IP (bypass CDN/WAF to reach origin directly)
```

---

## Recon Automation — Full Pipeline

For external engagements, a repeatable automated recon pipeline saves time and ensures nothing is missed.

```bash
#!/bin/bash
# Basic recon automation script
TARGET=$1
OUTPUT_DIR="recon_$TARGET"
mkdir -p $OUTPUT_DIR

echo "[*] Starting recon for $TARGET"

# 1. Subdomain enumeration
echo "[*] Subdomain enumeration..."
subfinder -d $TARGET -silent -o $OUTPUT_DIR/subdomains_subfinder.txt
amass enum -passive -d $TARGET -o $OUTPUT_DIR/subdomains_amass.txt
curl -s "https://crt.sh/?q=%.${TARGET}&output=json" | \
  jq -r '.[].name_value' | sort -u > $OUTPUT_DIR/subdomains_crt.txt

# Combine and deduplicate
cat $OUTPUT_DIR/subdomains_*.txt | sort -u > $OUTPUT_DIR/all_subdomains.txt
echo "[*] Found $(wc -l < $OUTPUT_DIR/all_subdomains.txt) unique subdomains"

# 2. DNS resolution — find live hosts
echo "[*] Resolving live hosts..."
cat $OUTPUT_DIR/all_subdomains.txt | \
  dnsx -silent -a -resp-only > $OUTPUT_DIR/live_ips.txt

# 3. HTTP probing — find web servers
echo "[*] Probing for web servers..."
cat $OUTPUT_DIR/all_subdomains.txt | \
  httpx -silent -status-code -title -tech-detect > $OUTPUT_DIR/web_servers.txt

# 4. Screenshot all web servers (gowitness)
echo "[*] Taking screenshots..."
cat $OUTPUT_DIR/web_servers.txt | cut -d' ' -f1 | \
  gowitness file -f - --destination $OUTPUT_DIR/screenshots/

# 5. Nuclei scanning
echo "[*] Running nuclei..."
cat $OUTPUT_DIR/web_servers.txt | cut -d' ' -f1 | \
  nuclei -t exposures/ -t misconfiguration/ -severity high,critical \
  -o $OUTPUT_DIR/nuclei_findings.txt

# 6. Port scan live IPs
echo "[*] Port scanning..."
nmap -iL $OUTPUT_DIR/live_ips.txt -p- --min-rate 5000 \
  -oA $OUTPUT_DIR/nmap_portscan

echo "[*] Recon complete. Results in $OUTPUT_DIR/"
```

**Tools used in the pipeline above (install all):**
```bash
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/owasp-amass/amass/v4/...@master
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/sensepost/gowitness@latest
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
```
