# Web Application Tools

!!! info "Purpose"
    Deep reference for every major web application testing tool. Each section covers setup, core usage patterns, interview-relevant depth, and real workflow examples.

---

## Burp Suite — Complete Reference

Burp Suite is the central tool for web application penetration testing. Know it deeply — interviewers at every level ask about it.

### Setup and Configuration

```bash
# Start Burp Suite (Community or Pro)
java -jar burpsuite_community.jar
# or use the installed launcher

# Configure browser proxy:
# Firefox: Settings → Network Settings → Manual proxy
# HTTP Proxy: 127.0.0.1  Port: 8080
# Also proxy HTTPS: same settings

# Install Burp CA Certificate:
# Navigate to http://burpsuite in browser while proxy is active
# Download CA → Import into browser certificate store
# Firefox: Settings → Privacy → View Certificates → Import

# For mobile devices: configure device Wi-Fi proxy to attacker IP:8080
```

### Proxy — Core Interception

```
Key controls:
- Intercept ON/OFF toggle (hotkey: I)
- Forward: send intercepted request (hotkey: F)
- Drop: discard intercepted request
- Action → Send to Repeater/Intruder/Scanner

Proxy history:
- Filter by host, method, status, MIME type, search string
- Right-click any request → Send to tool
- Ctrl+R = Send to Repeater
- Ctrl+I = Send to Intruder

Match and Replace (under Proxy Options):
- Auto-replace headers, cookies, or body content on every request
- Useful: replace User-Agent, add/modify auth headers globally
```

### Repeater — Manual Testing

The most-used Burp tool. Send a request here, modify it, resend.

```
Workflow:
1. Intercept request in Proxy
2. Ctrl+R to send to Repeater
3. Modify request manually
4. Ctrl+Space or click Send
5. Inspect response
6. Repeat with modifications

Useful features:
- Inspector panel: parse and modify parameters visually
- Response rendering: switch between Raw/Pretty/Rendered/Hex
- Search in response: Ctrl+F
- History of all sends within the tab
- Save requests/responses for report evidence
```

### Intruder — Fuzzing and Brute Force

```
Attack types:
- Sniper:       One wordlist, one payload position (most common)
- Battering Ram: Same payload in all positions simultaneously
- Pitchfork:    Multiple wordlists, one-to-one (usernames + passwords)
- Cluster Bomb: All combinations of all wordlists (exhaustive)

Setup:
1. Send request to Intruder (Ctrl+I)
2. Positions tab: mark payload positions with §markers§
3. Payloads tab: load wordlist or set payload type
4. Options tab: set threads, grep for strings, configure redirects
5. Start Attack

Payload types:
- Simple list: load wordlist file
- Runtime file: read line-by-line during attack
- Numbers: numeric ranges (for ID enumeration)
- Dates: date ranges
- Brute forcer: character set + length (for PIN brute force)
- Null payload: repeat same request N times (race conditions)

Grep Match (Options tab):
- Flag responses containing specific strings
- "Invalid password" vs "Welcome" — identifies successes

Rate limiting (Community Edition throttle):
- Intruder is rate-limited in Community to ~1 req/sec
- Use Turbo Intruder extension for high-speed fuzzing
```

### Scanner (Pro Only)

```
Passive scanning: always on — analyzes traffic passing through proxy
Active scanning: sends additional probes to find vulnerabilities

Active scan options:
- Right-click request → Scan
- Or use Dashboard → New Scan → enter scope
- Configure scan speed vs thoroughness tradeoff
- Review issues in Dashboard → Issues panel

Issue severity and confidence:
- High/Medium/Low severity
- Certain/Firm/Tentative confidence
- Always manually verify before reporting
```

### Decoder

```
Functions:
- Decode/Encode: Base64, URL, HTML, Hex, Binary, Gzip, Zlib
- Hash: MD5, SHA-1, SHA-256, SHA-512

Workflow:
1. Highlight text in any Burp tool
2. Right-click → Send to Decoder
3. Select decode/encode operation
4. Chain multiple operations

Useful patterns:
- Double URL decode: detect double-encoding bypass attempts
- Base64 → JSON: decode JWT payload without external tools
```

### Comparer

```
Use case: identify differences between two responses
- Compare response to authorized vs unauthorized request (access control)
- Compare error vs success response (timing/content differences)
- Compare original vs modified request responses

Method:
1. Right-click response → Send to Comparer
2. Send second item to Comparer
3. Click Compare → Words or Bytes
4. Highlighted differences shown
```

### Target — Scope and Site Map

```
Scope management:
- Target → Scope tab → Add in-scope items
- Use regex for flexible scope: https://app\.example\.com/.*
- All other Burp tools respect scope settings

Site map:
- Builds automatically from proxy traffic
- Right-click host → Spider (crawl all discovered links)
- Filter by status code, MIME type, parameters
- Export for documentation
```

### Key Burp Extensions (BApp Store)

```
Essential extensions every web tester should have:

Autorize
  Purpose: Automated access control testing
  How: Define a low-privilege session token; Autorize replays every 
       request through that token; flags when response differs from 
       high-privilege version (potential BOLA/BFLA)
  Install: BApp Store → Autorize

Logger++
  Purpose: Advanced request/response logging with filters
  How: Logs all traffic with timestamps; filterable by any field;
       export to CSV; essential for large engagements
  
JWT Editor
  Purpose: JWT manipulation without external tools
  How: Intercepts JWTs; decode/modify/re-sign in Burp; 
       supports none algorithm, key confusion attacks, embedded JWK
       
InQL
  Purpose: GraphQL testing
  How: Automatic introspection; generates queries for all types;
       visual schema browser; integrates with Repeater/Intruder

JS Link Finder
  Purpose: Extract API endpoints from JavaScript files
  How: Scans all JS responses; extracts URLs and paths;
       pastes into target scope for further testing

Param Miner
  Purpose: Discover hidden HTTP parameters
  How: Sends requests with guessed parameters; identifies 
       parameters affecting response (cache poisoning, hidden functionality)

Turbo Intruder
  Purpose: High-speed fuzzing (bypasses Community rate limit)
  How: Python-scriptable request engine; 
       1000s of requests/second; essential for race condition testing

HTTP Request Smuggler
  Purpose: Detect CL.TE and TE.CL request smuggling
  How: Sends timing-based and response-based detection probes;
       automates what's tedious to do manually

HUNT
  Purpose: Highlight parameters likely vulnerable to specific classes
  How: Marks parameters named "id", "file", "url", "redirect" etc.
       in the Proxy history; guides manual testing prioritization

ActiveScan++
  Purpose: Extends active scanner with additional checks
  How: Adds SSRF, SSTI, DNS rebinding, and other checks 
       the built-in scanner misses

Retire.js
  Purpose: Identify known-vulnerable JavaScript libraries
  How: Scans JS files against CVE database; flags outdated jQuery,
       Angular, React, etc.
```

---

## OWASP ZAP — Open Source Alternative

ZAP (Zed Attack Proxy) is a free, open-source web application scanner. Less powerful than Burp Pro but fully free and useful for automated scanning.

```bash
# Start ZAP
zaproxy
# or: owasp-zap

# CLI mode for automation
zap.sh -daemon -port 8080 -host 0.0.0.0 -config api.key=yourkey

# Spider and scan
zap-cli --api-key yourkey spider http://target.com
zap-cli --api-key yourkey active-scan http://target.com
zap-cli --api-key yourkey report -o report.html -f html

# Docker (CI/CD integration)
docker run -t owasp/zap2docker-stable zap-baseline.py -t http://target.com
docker run -t owasp/zap2docker-stable zap-full-scan.py -t http://target.com
```

**Key ZAP features:**
- HUD (Heads Up Display): overlay in browser showing live alerts while browsing
- Active scanner: automatically tests all discovered endpoints
- Fuzzer: similar to Burp Intruder
- Ajax Spider: crawls JavaScript-heavy SPAs (handles dynamic content better than basic spider)
- OpenAPI/Swagger import: import API definition for structured scanning
- Automation Framework: YAML-based automation pipeline integration

---

## gobuster — Directory and DNS Brute Force

```bash
# Directory/file discovery
gobuster dir -u http://target.com \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt

# With file extensions
gobuster dir -u http://target.com \
  -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt \
  -x php,html,txt,js,json,xml,bak,old,backup

# Ignore SSL errors (for self-signed certs)
gobuster dir -u https://target.com -w wordlist.txt -k

# Custom headers (with auth token)
gobuster dir -u http://target.com -w wordlist.txt \
  -H "Authorization: Bearer token123" \
  -H "Cookie: session=abc123"

# Increase threads (default 10)
gobuster dir -u http://target.com -w wordlist.txt -t 50

# Status code filtering (default shows 200,204,301,302,307,401,403,405)
gobuster dir -u http://target.com -w wordlist.txt -s "200,204,403"

# DNS subdomain brute force
gobuster dns -d example.com \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt

# VHost enumeration
gobuster vhost -u http://target.com \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  --append-domain  # appends .target.com to each word

# Output results
gobuster dir -u http://target.com -w wordlist.txt -o results.txt
```

**Good wordlists by scenario:**
```
Quick initial scan:      /usr/share/seclists/Discovery/Web-Content/common.txt
Medium depth:            /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
API endpoint discovery:  /usr/share/seclists/Discovery/Web-Content/api/api-endpoints.txt
PHP applications:        /usr/share/seclists/Discovery/Web-Content/PHP.fuzz.txt
Parameters:              /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt
```

---

## ffuf — Fast Web Fuzzer

More flexible than gobuster — supports full request templating.

```bash
# Basic directory fuzzing
ffuf -u http://target.com/FUZZ -w wordlist.txt

# With extensions
ffuf -u http://target.com/FUZZ -w wordlist.txt -e .php,.html,.txt,.bak

# Parameter fuzzing (GET)
ffuf -u "http://target.com/page?FUZZ=value" -w params.txt

# Parameter value fuzzing
ffuf -u "http://target.com/page?id=FUZZ" -w /usr/share/seclists/Fuzzing/number-list-100.txt

# POST body fuzzing
ffuf -u http://target.com/login \
  -X POST \
  -d "user=FUZZ&pass=test" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -w usernames.txt

# JSON POST fuzzing
ffuf -u http://target.com/api/login \
  -X POST \
  -d '{"user":"FUZZ","pass":"test"}' \
  -H "Content-Type: application/json" \
  -w usernames.txt

# Multiple positions (pitchfork mode)
ffuf -u http://target.com/login \
  -X POST \
  -d "user=W1&pass=W2" \
  -w usernames.txt:W1 \
  -w passwords.txt:W2 \
  -mode pitchfork

# Filtering responses (critical for reducing noise)
ffuf -u http://target.com/FUZZ -w wordlist.txt \
  -fc 404             # Filter HTTP 404
  -fs 1234            # Filter responses with exactly 1234 bytes
  -fw 10              # Filter responses with exactly 10 words
  -fl 20              # Filter responses with exactly 20 lines
  -ft "Not Found"     # Filter responses containing this string

# Match specific codes only
ffuf -u http://target.com/FUZZ -w wordlist.txt -mc 200,201,301,302,403

# VHost fuzzing
ffuf -u http://target.com/ \
  -H "Host: FUZZ.target.com" \
  -w subdomains.txt \
  -fs 1234  # Filter default response size

# Recursive fuzzing
ffuf -u http://target.com/FUZZ -w wordlist.txt -recursion -recursion-depth 2

# Output
ffuf -u http://target.com/FUZZ -w wordlist.txt -o results.json -of json
```

---

## sqlmap — SQL Injection Testing

```bash
# Basic detection
sqlmap -u "http://target.com/page?id=1"

# Specify injection parameter
sqlmap -u "http://target.com/page?id=1&name=test" -p id

# POST request
sqlmap -u "http://target.com/login" \
  --data="username=admin&password=test"

# JSON POST
sqlmap -u "http://target.com/api/users" \
  --data='{"id":1}' \
  -H "Content-Type: application/json"

# From Burp request file (most reliable method)
# In Burp: right-click request → Save item
sqlmap -r request.txt

# With session cookie (authenticated testing)
sqlmap -u "http://target.com/profile?id=1" \
  --cookie="session=abc123; csrf=xyz"

# Database enumeration
sqlmap -u "http://target.com/page?id=1" --dbs                   # List databases
sqlmap -u "http://target.com/page?id=1" -D target_db --tables   # List tables
sqlmap -u "http://target.com/page?id=1" -D target_db -T users --columns
sqlmap -u "http://target.com/page?id=1" -D target_db -T users --dump

# Dump with specific columns
sqlmap -u "http://target.com/page?id=1" \
  -D target_db -T users \
  -C username,password,email --dump

# Specify DBMS (faster, avoids guessing)
sqlmap -u "http://target.com/page?id=1" --dbms=mysql
sqlmap -u "http://target.com/page?id=1" --dbms=mssql
sqlmap -u "http://target.com/page?id=1" --dbms=postgresql
sqlmap -u "http://target.com/page?id=1" --dbms=oracle

# Injection technique selection
sqlmap -u "http://target.com/page?id=1" --technique=BEUSTQ
# B=Boolean, E=Error, U=UNION, S=Stacked, T=Time, Q=Inline

# WAF bypass with tamper scripts
sqlmap -u "http://target.com/page?id=1" \
  --tamper=space2comment,between,randomcase,charunicodeencode

# Multiple tamper scripts (combine for better bypass)
sqlmap -u "http://target.com/page?id=1" \
  --tamper="apostrophemask,apostrophenullencode,base64encode,between,chardoubleencode,charencode,charunicodeencode,equaltolike,greatest,ifnull2ifisnull,multiplespaces,randomcase,space2comment,space2plus,space2randomblank,unionalltounion,unmagicquotes"

# Stealth options
sqlmap -u "http://target.com/page?id=1" \
  --random-agent \     # Random User-Agent
  --delay=2 \          # 2-second delay between requests
  --level=1 \          # Minimal tests (1-5, default 1)
  --risk=1             # Minimal risk (1-3, default 1)

# OS interaction (if FILE or SYSTEM privilege)
sqlmap -u "http://target.com/page?id=1" --file-read="/etc/passwd"
sqlmap -u "http://target.com/page?id=1" --file-write="shell.php" --file-dest="/var/www/html/shell.php"
sqlmap -u "http://target.com/page?id=1" --os-shell   # Interactive OS shell
sqlmap -u "http://target.com/page?id=1" --os-pwn    # Meterpreter shell via SQLMap

# Second-order injection
sqlmap -u "http://target.com/profile" \
  --second-url="http://target.com/display_profile"
```

**Common tamper scripts explained:**
```
space2comment     → SELECT/**/username  (bypass space filters)
between           → a BETWEEN b AND b  (bypass = operator filters)
randomcase        → SeLeCt  (bypass case-sensitive keyword filters)
charunicodeencode → Unicode encoding of characters
base64encode      → Encodes payload in Base64
equaltolike       → = becomes LIKE (bypass = filters)
```

---

## Nikto — Web Server Scanner

```bash
# Basic scan
nikto -h http://target.com

# HTTPS
nikto -h https://target.com -ssl

# Specific port
nikto -h http://target.com -port 8080

# With authentication
nikto -h http://target.com -id admin:password        # HTTP Basic
nikto -h http://target.com -C "session=abc123"       # Cookie

# Scan specific directory
nikto -h http://target.com/app

# Tuning (select check categories)
nikto -h http://target.com -Tuning 1    # Interesting files
nikto -h http://target.com -Tuning 2    # Misconfiguration
nikto -h http://target.com -Tuning 3    # Information disclosure
nikto -h http://target.com -Tuning 4    # XSS
nikto -h http://target.com -Tuning 8    # Command injection
nikto -h http://target.com -Tuning 9    # SQL injection
nikto -h http://target.com -Tuning b    # Software identification

# Output formats
nikto -h http://target.com -o results.html -Format htm
nikto -h http://target.com -o results.xml -Format xml
nikto -h http://target.com -o results.txt -Format txt
nikto -h http://target.com -o results.csv -Format csv

# Multiple hosts
nikto -h hosts.txt

# Via proxy (through Burp)
nikto -h http://target.com -useproxy http://127.0.0.1:8080
```

**What Nikto checks:**
- Outdated server software versions
- Default files and installation scripts
- CGI vulnerabilities
- SSL/TLS configuration issues
- HTTP methods (PUT, DELETE, TRACE enabled)
- Directory indexing enabled
- Misconfigured robots.txt
- Backup and config files (`.bak`, `.old`, `config.php~`)
- Default credentials on common applications

---

## Nuclei — Template-Based Scanning

```bash
# Install / update
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
nuclei -update
nuclei -update-templates

# Scan with all templates (broad but slow)
nuclei -u https://target.com

# Specific severity
nuclei -u https://target.com -severity critical,high

# Specific template categories
nuclei -u https://target.com -t cves/                    # CVE checks
nuclei -u https://target.com -t exposures/               # Exposed files/configs
nuclei -u https://target.com -t misconfiguration/        # Misconfigs
nuclei -u https://target.com -t technologies/            # Tech fingerprinting
nuclei -u https://target.com -t vulnerabilities/         # Vulnerability checks
nuclei -u https://target.com -t default-logins/          # Default credentials
nuclei -u https://target.com -t exposed-panels/          # Admin panels

# Multiple targets
nuclei -l urls.txt -t cves/ -severity critical

# With authentication
nuclei -u https://target.com \
  -H "Authorization: Bearer token123" \
  -H "Cookie: session=abc123"

# Rate limiting (be responsible)
nuclei -u https://target.com -rate-limit 50 -concurrency 10

# Output
nuclei -u https://target.com -o results.txt
nuclei -u https://target.com -json -o results.json

# Custom template example (YAML):
cat > custom_check.yaml << 'EOF'
id: custom-api-key-exposure
info:
  name: API Key Exposed in Response
  severity: high
  tags: exposure,apikey

requests:
  - method: GET
    path:
      - "{{BaseURL}}/config"
      - "{{BaseURL}}/api/config"
      - "{{BaseURL}}/.env"
    matchers:
      - type: regex
        regex:
          - "api[_-]?key['\"]?\s*[:=]\s*['\"]?[a-zA-Z0-9]{20,}"
        part: body
EOF
nuclei -u https://target.com -t custom_check.yaml
```

---

## wfuzz — Web Fuzzer

Older tool but still useful, especially for complex fuzzing scenarios.

```bash
# Basic directory fuzzing
wfuzz -c -z file,/usr/share/wordlists/dirb/common.txt \
  http://target.com/FUZZ

# Filter 404s
wfuzz -c -z file,wordlist.txt --hc 404 http://target.com/FUZZ

# POST fuzzing
wfuzz -c -z file,usernames.txt \
  -d "username=FUZZ&password=test" \
  http://target.com/login

# Multiple payload positions
wfuzz -c -z file,users.txt -z file,passes.txt \
  -d "user=FUZ1Z&pass=FUZ2Z" \
  http://target.com/login

# Filter by response size
wfuzz -c -z file,wordlist.txt --hh 1234 http://target.com/FUZZ

# Filter by word count
wfuzz -c -z file,wordlist.txt --hw 10 http://target.com/FUZZ

# With headers
wfuzz -c -z file,wordlist.txt \
  -H "Authorization: Bearer token123" \
  http://target.com/api/FUZZ
```

---

## curl — Command-Line HTTP Testing

```bash
# Basic GET
curl http://target.com

# HTTPS (ignore cert errors)
curl -k https://target.com

# Verbose (show request + response headers)
curl -v http://target.com

# Headers only
curl -I http://target.com

# Custom headers
curl -H "Authorization: Bearer token" \
     -H "Content-Type: application/json" \
     http://target.com/api

# POST request
curl -X POST http://target.com/login \
  -d "username=admin&password=test"

# JSON POST
curl -X POST http://target.com/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"test"}'

# With cookies
curl -b "session=abc123; csrf=xyz" http://target.com/dashboard

# Follow redirects
curl -L http://target.com

# Save response to file
curl -o response.html http://target.com

# Test specific HTTP methods
curl -X PUT http://target.com/resource -d '{"key":"value"}'
curl -X DELETE http://target.com/resource/42
curl -X OPTIONS http://target.com -v 2>&1 | grep Allow

# Upload file
curl -F "file=@payload.php" http://target.com/upload

# Through proxy (Burp)
curl -x 127.0.0.1:8080 -k http://target.com

# Show only response code
curl -o /dev/null -s -w "%{http_code}" http://target.com
```

---

## Recommended Wordlists (SecLists)

```bash
# Install SecLists
apt install seclists
# or
git clone https://github.com/danielmiessler/SecLists /usr/share/seclists

# Key wordlist locations:
/usr/share/seclists/Discovery/Web-Content/
  common.txt                              # Quick common paths
  directory-list-2.3-medium.txt          # Standard directory scan
  directory-list-2.3-big.txt             # Comprehensive (slow)
  api/api-endpoints.txt                  # API endpoint discovery
  api/objects.txt                        # API object names
  burp-parameter-names.txt               # HTTP parameter names
  PHP.fuzz.txt                           # PHP-specific paths
  CGIs.txt                               # CGI scripts
  
/usr/share/seclists/Discovery/DNS/
  subdomains-top1million-5000.txt        # Top 5000 subdomains
  subdomains-top1million-20000.txt       # Top 20000 subdomains
  
/usr/share/seclists/Passwords/
  Leaked-Databases/rockyou.txt.tar.gz    # RockYou (must extract)
  Common-Credentials/10k-most-common.txt # Top 10000 passwords
  
/usr/share/seclists/Fuzzing/
  number-list-100.txt                    # Numbers 1-100 (ID fuzzing)
  special-chars.txt                      # Special characters
  LFI/
    LFI-Jhaddix.txt                      # LFI payloads
```
