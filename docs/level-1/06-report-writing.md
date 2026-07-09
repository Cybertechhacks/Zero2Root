# Report Writing

!!! info "Why This Matters"
    The report is the only deliverable a client keeps. Your exploitation was impressive — they weren't watching. What they read in the report shapes their security investment, their remediation priorities, and whether they hire you again. Bad reports lose clients. Interviewers routinely ask to see a sample finding or ask you to walk through how you'd report a specific vulnerability.

---

## The Two Audiences Problem

Every pentest report is read by two completely different audiences:

**Technical audience:** System administrators, developers, security engineers. They need:
- Exact reproduction steps
- Code snippets, HTTP requests/responses
- Affected system hostnames and IPs
- Specific CVE references
- Technical remediation steps

**Executive audience:** CISO, CTO, CFO, Board. They need:
- Business risk in plain language
- Financial/regulatory/reputational impact
- Strategic priority ranking
- Resource implications of remediation

The mistake most junior pentesters make is writing the entire report in technical language. An executive should be able to read the first 2-3 pages and understand: how bad is it, what could happen if we don't fix it, and what's the priority order.

---

## Report Structure

### 1. Cover Page
- Report title and type (Internal Penetration Test, External VA, Web Application Assessment, etc.)
- Client organization name
- Date range of testing
- Date of report
- Report version
- Prepared by (your firm name)
- Confidentiality notice

### 2. Table of Contents

### 3. Executive Summary (1-2 pages)

The most important section. Written last, but placed first. Must stand alone — executives often read only this.

**Contents:**
- **Engagement overview:** What was tested, when, at what level of access
- **Overall risk posture:** One sentence characterizing the severity of what was found. "The assessment identified critical vulnerabilities that would allow an unauthenticated remote attacker to fully compromise the internal network."
- **Key findings summary:** Top 3-5 findings by business impact (not CVSS). Describe in business terms — not "SQL injection in the login form" but "an attacker without any account could bypass the login system and access all customer data."
- **Risk distribution chart:** Bar or pie chart showing finding count by severity (Critical/High/Medium/Low/Informational)
- **Strategic recommendations:** What the organization needs to do in priority order — not specific technical fixes but strategic direction

**Executive Summary Language Guide:**

| Technical term | Executive language |
|----------------|-------------------|
| SQL injection | The login form can be manipulated to extract all customer data |
| Unauthenticated | Without needing any username or password |
| RCE | Complete takeover of the server |
| Lateral movement | From one compromised server, attackers can access other systems |
| CVSS 9.8 Critical | Represents the most severe class of vulnerability |
| Missing patch | The server software hasn't been updated and contains a known flaw |

### 4. Scope and Methodology
- IP ranges, domains, applications in scope
- Testing dates and hours
- Testing type (black/white/grey box)
- Methodology framework referenced (PTES, OWASP, custom)
- Tools used (high level — Nmap, Nessus, Burp Suite, custom scripts)
- Limitations (e.g., testing was unauthenticated; some services were unavailable during testing window)

### 5. Findings (bulk of the report)

Each finding follows a consistent format (covered in detail below).

Findings should be ordered by severity: Critical → High → Medium → Low → Informational.

### 6. Risk Summary Matrix

A table summarizing all findings with severity, affected system, and brief description. Useful for remediation tracking.

### 7. Remediation Roadmap

Prioritized action plan:
- **Immediate (0-7 days):** Critical findings
- **Short term (7-30 days):** High findings
- **Medium term (30-90 days):** Medium findings
- **Long term (90+ days / next development cycle):** Low findings

### 8. Appendices
- Raw tool output (Nmap scans, Nessus XML export)
- Additional screenshots
- Code snippets too long for the main body
- Glossary (if client is non-technical)

---

## The Finding Format — In Depth

Each finding should have these sections:

### Finding Title
Short, clear, describes the vulnerability type and context:
- ✅ "Unauthenticated SQL Injection in Customer Login Portal"
- ✅ "Remote Code Execution via Outdated Apache Struts (CVE-2017-5638)"
- ❌ "SQL Injection Found"
- ❌ "Server is Vulnerable"

### Severity Rating

Use a consistent system. CVSS v3.1 base score maps to:

| Score | Rating | Color |
|-------|--------|-------|
| 9.0 – 10.0 | Critical | Red |
| 7.0 – 8.9 | High | Orange |
| 4.0 – 6.9 | Medium | Yellow |
| 0.1 – 3.9 | Low | Blue |
| 0.0 | Informational | Grey |

**Always include both the CVSS score and the rating label.**

**Contextual vs Base Severity:** Note when you've adjusted severity based on environment. "While the CVSS base score is 7.8 (High), the contextual severity has been rated Critical given this service processes cardholder data and is accessible from the corporate network."

### CVSS Vector String

Include the full vector string so the reader can verify:
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:L
Base Score: 9.4 (Critical)
```

### Affected Systems

List every affected host, URL, or component:
```
- 192.168.1.50 (webserver01.corp.local)
- https://customer-portal.example.com/login
```

### Vulnerability Description

3-5 paragraphs explaining:
1. What the vulnerability is (concept, technical but accessible)
2. Where it exists in the target (what code path, what parameter)
3. What an attacker could do with it (impact)

Avoid jargon without explanation. Not everyone reading this knows what UNION SELECT means.

**Example:**
> SQL injection is a vulnerability that allows an attacker to interfere with the queries that an application makes to its database. The `user_id` parameter in the `/api/profile` endpoint was found to be vulnerable — user-supplied input is incorporated directly into a SQL query without sanitization or parameterization.
>
> During testing, it was possible to extract the entire `users` database table, which contains email addresses, password hashes, and personal information for 47,000 customers. Additionally, the database account used by the application had DBA privileges, allowing the use of `xp_cmdshell` to execute operating system commands on the underlying database server.

### Steps to Reproduce

Numbered, exact steps to recreate the finding. A developer who reads this should be able to reproduce it themselves to verify and test their fix.

**Format:**
1. Navigate to `https://app.example.com/api/profile`
2. Authenticate as a regular user with credentials: `testuser / testpass`
3. Send the following HTTP request (captured with Burp Suite):

```http
GET /api/profile?user_id=1%27%20UNION%20SELECT%20username%2Cpassword%2C3%20FROM%20users-- HTTP/1.1
Host: app.example.com
Cookie: session=abc123
```

4. Observe that the response returns usernames and password hashes from the `users` table.

**Evidence:** [Screenshot or response body showing extracted data]

### Evidence

Screenshots, HTTP requests/responses, tool output, extracted data samples. For sensitive data — mask/redact PII in the report. Don't include 47,000 customer records as evidence — show 2-3 rows with email addresses partially redacted.

**Screenshot format:**
- Caption every screenshot: "Figure 1: SQL injection response showing extracted password hashes"
- Highlight the relevant portion if the screenshot is large
- Include the URL/context in the screenshot (not just isolated data)

### Business Impact

Translate the technical finding to business consequence:

> **Confidentiality:** An attacker could extract all 47,000 customer records including personal information and hashed passwords. This represents a potential GDPR breach notification obligation and regulatory fine.
>
> **Integrity:** With DBA privileges, an attacker could modify customer data, pricing information, or order records.
>
> **Availability:** Using OS command execution capabilities, an attacker could install ransomware, delete database records, or fully disrupt the service.

### Risk Rating Justification

Explain why you assigned this severity — especially if it differs from the CVSS base score:

> This finding is rated Critical based on: (1) no authentication required — any internet user can exploit it, (2) the database contains PII subject to GDPR obligations, (3) the DBA account allows OS command execution, extending impact beyond the database tier, and (4) active exploitation of similar vulnerabilities by ransomware groups has been observed.

### Remediation Recommendation

Specific, actionable, technology-appropriate remediation steps:

> **Short term (immediate):** Remove DBA privileges from the web application database account. Create a restricted account with only SELECT, INSERT, UPDATE on the required tables.
>
> **Short term (this sprint):** Implement parameterized queries (prepared statements) for all database interactions. Do not use string concatenation to build SQL queries. Example (Python):
>
> ```python
> # Vulnerable:
> query = "SELECT * FROM users WHERE id = " + user_id
>
> # Fixed:
> cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
> ```
>
> **Medium term:** Implement a Web Application Firewall (WAF) with SQL injection rules as a compensating control. Conduct a code review of all database interaction code.

### References

- CVE number if applicable: CVE-2021-XXXXX
- OWASP category: OWASP Top 10 A03:2021 – Injection
- Vendor advisory: link
- CWE: CWE-89 (SQL Injection)

---

## CVSS Scoring in Reports

Every finding needs a justified CVSS vector. Common mistakes:

**Mistake 1:** Copying the NVD CVSS score for a CVE without adjusting for context. The NVD score is the worst-case base score — your environment may reduce the exploitability (e.g., the vulnerable service requires authentication that NVD didn't account for).

**Mistake 2:** Marking internal-only vulnerabilities as Network scope. If a finding requires you to already be inside the network (LAN access), AV should be Adjacent or Local, not Network.

**Mistake 3:** Assigning PR:None when authentication is required. If you need a low-privilege user account to exploit it, PR:Low. If you need admin, PR:High.

---

## Writing Style Guide

**Use active voice:**
- ❌ "SQL injection was identified in the login form"
- ✅ "An attacker can exploit SQL injection in the login form to extract all customer data"

**Use impact-first language:**
- ❌ "The application does not implement rate limiting on login attempts"
- ✅ "Without rate limiting on the login form, an attacker can attempt unlimited password guesses against any account, enabling automated credential brute force"

**Quantify when possible:**
- ❌ "Several users are affected"
- ✅ "All 47,000 registered users are affected"

**Be precise about scope:**
- ❌ "The system is vulnerable"
- ✅ "`/api/v2/profile` on app.example.com is vulnerable"

**Match technical depth to the section:**
- Executive summary: business language
- Finding description: accessible technical language
- Steps to reproduce: full technical detail
- Remediation: specific code examples where appropriate

---

## Common Report Mistakes

1. **Pasting raw tool output** as findings — Nessus output is not a pentest report. Validate each finding, add context, remove false positives.

2. **Missing business impact** — Listing CVEs without explaining what an attacker could actually achieve.

3. **Copy-paste remediation** — "Update the software to the latest version" is valid but insufficient. Name the specific version, provide the vendor advisory link, note any compatibility considerations.

4. **CVSS inflation** — Rating everything High/Critical destroys severity differentiation. Clients tune out if everything is critical.

5. **CVSS deflation** — Under-rating to avoid difficult conversations. If it's critical, call it critical and justify it.

6. **No evidence** — "We found SQL injection" without a single screenshot or request is unjustifiable. A developer can deny it.

7. **Sensitive data in reports** — Actual PII, passwords, or financial records in report appendices. Redact these.

8. **Inconsistent format** — Some findings have impact sections, some don't. Use a template and stick to it.

---

## Sample Finding — Complete

---

**Finding: Unauthenticated SQL Injection in Login Portal**

**Severity:** Critical
**CVSS Score:** 9.8
**CVSS Vector:** `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`
**Affected System:** `https://portal.example.com/login` (195.10.20.30)
**CVE:** N/A (custom application)
**CWE:** CWE-89 — Improper Neutralization of Special Elements used in an SQL Command

---

**Description**

The customer login portal at `https://portal.example.com/login` was found to be vulnerable to SQL injection in the `username` parameter. User-supplied input is incorporated into a database query without parameterization, allowing an attacker to modify the query's logic.

This vulnerability does not require any existing account or credentials to exploit. By submitting a crafted username value, an attacker can bypass the authentication mechanism entirely and access the application as any user, including administrative accounts. Furthermore, the database account used by the application has DBA privileges, enabling OS-level command execution on the database server.

**Business Impact**

This vulnerability allows a remote, unauthenticated attacker to: (1) bypass authentication and impersonate any user, including administrators; (2) extract the full contents of the database, including the personal information and hashed passwords of all registered customers; and (3) execute arbitrary commands on the database server operating system, potentially enabling ransomware deployment, data destruction, or use of the server as an attack pivot into the internal network.

**Steps to Reproduce**

1. Navigate to `https://portal.example.com/login` in a browser.
2. In the username field, enter: `admin'--`
3. In the password field, enter any value (e.g., `test`).
4. Click Login.
5. Observe successful authentication as the `admin` user without the correct password.

**Evidence**

*[Figure 1: Login bypass with username admin'-- showing admin dashboard]*

*[Figure 2: HTTP request demonstrating the SQL injection payload]*

**Remediation**

*Immediate:* Restrict the database account to the minimum necessary permissions (SELECT, INSERT, UPDATE on specific tables only). Remove DBA privileges.

*Short-term:* Replace all dynamic SQL query construction with parameterized queries (prepared statements). Example:

```python
# Vulnerable code:
query = "SELECT * FROM users WHERE username='" + username + "'"

# Fixed code:
cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
```

*Medium-term:* Deploy a WAF with SQL injection rules as a compensating control. Conduct a full code review of all database interaction code in the application.

**References**

- OWASP Top 10 2021: A03 – Injection
- OWASP SQL Injection Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html

---
