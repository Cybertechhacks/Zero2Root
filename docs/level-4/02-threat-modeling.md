# Threat Modeling

!!! info "Why This Matters"
    Threat modeling is how security shifts left — identifying design-level security issues before code is written, rather than finding them in production. Senior pentesters and architects are expected to run threat modeling sessions with development teams. This is also a common interview topic for senior and lead roles.

---

## What Is Threat Modeling?

Threat modeling is a structured process for identifying potential threats to a system and designing appropriate controls before implementation. The output is a prioritized set of risks and the security requirements derived from them.

**When to threat model:**
- During system design (most valuable — cheapest to fix)
- When evaluating an acquisition
- When significant architectural changes are made
- As part of an incident response to understand attack paths

---

## STRIDE — Microsoft's Threat Framework

STRIDE is a mnemonic for six threat categories, originally developed at Microsoft. It maps naturally to security properties.

| Threat | Description | Violated Property | Example |
|--------|-------------|-------------------|---------|
| **S**poofing | Pretending to be someone else | Authentication | Forged JWT token, ARP poisoning |
| **T**ampering | Modifying data without authorization | Integrity | SQL injection, MITM modification |
| **R**epudiation | Denying actions without accountability | Non-repudiation | Missing audit logs, log deletion |
| **I**nformation Disclosure | Exposing data to unauthorized parties | Confidentiality | IDOR, cleartext storage |
| **D**enial of Service | Making a system unavailable | Availability | SYN flood, resource exhaustion |
| **E**levation of Privilege | Gaining higher permissions than authorized | Authorization | SUID abuse, SQL to OS shell |

### Applying STRIDE to a System

1. **Draw a Data Flow Diagram (DFD):** Map all components (processes, data stores, external entities) and the data flows between them.

2. **Identify trust boundaries:** Where does data cross from one trust zone to another? Trust boundaries are where threats most often materialize.

3. **Apply STRIDE to each element:**
   - Processes: subject to all 6 STRIDE threats
   - Data Stores: subject to Tampering, Information Disclosure, Denial of Service, Repudiation
   - Data Flows: subject to Spoofing, Tampering, Information Disclosure, Denial of Service
   - External Entities: subject to Spoofing, Repudiation

4. **Rate each threat:** Severity (High/Medium/Low) based on CVSS or DREAD (Damage, Reproducibility, Exploitability, Affected Users, Discoverability).

5. **Identify mitigations:** For each identified threat, what control addresses it?

---

## PASTA — Process for Attack Simulation and Threat Analysis

PASTA is a 7-stage, risk-centric threat modeling methodology. More business-aligned than STRIDE — it explicitly ties threats to business impact.

**Stage 1: Define Objectives** — What are the business goals? What are the security objectives that support them?

**Stage 2: Define Technical Scope** — What is the technical environment? Architecture diagrams, data flows, components.

**Stage 3: Application Decomposition** — Break down the application into components, identify use cases, data flows, trust boundaries.

**Stage 4: Threat Analysis** — What threats exist in the environment? Reference threat intelligence feeds, attack databases.

**Stage 5: Weakness and Vulnerability Analysis** — Identify existing weaknesses (code review, SAST, design flaws).

**Stage 6: Attack Modeling** — Simulate actual attack scenarios using attack trees, threat actor profiles.

**Stage 7: Risk/Impact Analysis** — Map threats to business impact, prioritize by risk, recommend controls.

---

## Attack Trees

Attack trees model how an attacker achieves a goal by breaking it down into sub-goals recursively. Useful for communicating complex attack paths to stakeholders.

```
Root Goal: Exfiltrate Customer PII
├── AND: Gain access to customer database
│   ├── OR: Exploit web application vulnerability
│   │   ├── SQL injection on login form
│   │   ├── File upload vulnerability → web shell
│   │   └── SSRF to internal database
│   ├── OR: Compromise DB credentials
│   │   ├── Brute force weak credentials
│   │   ├── Phish employee with DB access
│   │   └── Steal credentials from config file
│   └── OR: Physical access to DB server
└── AND: Bypass data exfiltration controls
    ├── OR: Exfiltrate over allowed protocols
    │   ├── HTTP/S to external endpoint
    │   └── DNS tunneling
    └── OR: Compress and encrypt before exfiltration
```

Attack trees help development teams visualize how their security controls map to attacker goals — making the value of each control concrete.

---

## Running a Threat Modeling Workshop

As a lead or architect, you'll facilitate these sessions with development teams:

**Participants:** Development lead, architect, security engineer, product manager (for business context), operations (for deployment context).

**Duration:** 2-4 hours for a focused service or feature. Large systems may need multiple sessions.

**Output:** Documented threats with risk ratings, security requirements for the design, items to track in the security backlog.

**Common challenges:**
- Developers see threat modeling as slowing down delivery — frame it as finding bugs earlier when they're 100x cheaper to fix
- Scope creep — focus on one service or feature per session
- Incomplete DFDs — spend the first 30 minutes getting the DFD right before moving to threats

---

# Red Team Program Design

Building a red team capability from scratch is a common question at senior/lead level.

---

## Program Design Considerations

### In-House vs Outsourced

**In-house red team:**
- Deeper organizational knowledge over time
- Better aligned to internal culture and priorities
- Expensive — fully-loaded cost per operator is ₹30-80L/year or more
- Suitable for large organizations (1000+ employees in security-sensitive industries)

**Outsourced (boutique firm):**
- Fresh perspective, no organizational blind spots
- Variable depth — depends heavily on the firm and team assigned
- Cost-effective for most organizations
- May lack deep institutional knowledge

**Hybrid (recommended for most):** Internal security team handles continuous monitoring and purple team exercises; external firm conducts annual red team assessments that the internal team can't objectively conduct against themselves.

### Team Composition

A mature in-house red team typically has:
- **Red Team Lead:** Manages operations, client/stakeholder communication, methodology
- **Senior Operator (2-3):** Leads individual engagements, specialized expertise (cloud, AD, mobile)
- **Operator (2-4):** Executes engagements under senior oversight
- **Intel Analyst:** Threat intelligence, campaign tracking, purple team coordination

### Metrics and Program Effectiveness

Red teams that can't measure their impact lose budget. Key metrics:

**Dwell time:** How long did the red team operate before detection? Goal: make this short (but not zero — some dwell is expected; the question is whether detection and response works).

**Objective completion rate:** Of defined engagement objectives, what percentage were achieved? 100% means defenses are too weak; 0% may mean scope was too narrow or engagement too short.

**ATT&CK coverage:** What percentage of MITRE ATT&CK techniques were tested? Which tactics had zero detection?

**Mean time to detect (MTTD):** When the red team performed a specific technique, how long before SOC detected it?

**Mean time to respond (MTTR):** After detection, how long to contain?

**Year-over-year improvement:** The most important metric — are these numbers improving? A mature program shows measurable improvement in detection capability.

---

## Purple Team Exercises

Purple teaming is collaborative red-blue sessions where the red team executes specific techniques while the blue team watches, detects, and discusses in real time.

**Why purple teaming matters:** Traditional red team → report → blue team tries to improve is a slow feedback loop. Purple team sessions provide immediate, specific feedback: "When we executed T1003.001 (LSASS Memory), your SIEM generated this alert — it fired 4 minutes after execution."

**Session structure:**
1. Define scope: specific ATT&CK techniques to exercise (e.g., a full attack chain or specific tactic)
2. Red team executes each technique in a controlled way
3. Blue team observes and notes detection (or lack thereof)
4. Joint discussion: why was/wasn't it detected? How to improve?
5. Blue team implements detection logic
6. Re-test to validate detection works

**Output:** A detection coverage matrix against ATT&CK, specific SIEM rule improvements, documented TTPs tested and detection confidence for each.

---

## Worked Example — STRIDE on a Web API

Applying STRIDE to a concrete system makes it tangible. Here's a threat model for a typical REST API with JWT authentication.

### System Description

A customer-facing REST API for a banking application:
- Mobile app clients authenticate via POST /auth/login → receive JWT
- Authenticated endpoints: GET /account/balance, POST /transfer, GET /transactions
- Backend: Node.js + Express, PostgreSQL database
- Deployed on AWS EC2, behind an Application Load Balancer
- JWT signed with HS256 using a shared secret

### Data Flow Diagram

```
[Mobile App] ──HTTPS──▶ [ALB] ──HTTP──▶ [API Server] ──TCP──▶ [PostgreSQL]
                                              │
                                              ▼
                                        [JWT Validation]
                                        [Business Logic]
```

Trust boundaries:
- Internet → ALB (public boundary)
- ALB → API Server (internal, but ALB header injection possible)
- API Server → PostgreSQL (internal network)

### STRIDE Analysis

**SPOOFING:**
- *Threat:* Attacker forges JWT tokens to impersonate users
- *Root cause:* HS256 with weak shared secret; algorithm confusion (RS256→HS256)
- *Mitigation:* Strong random secret (≥256 bits), validate `alg` header, prefer RS256
- *Finding type:* Authentication weakness

- *Threat:* Attacker spoofs client IP via X-Forwarded-For header
- *Root cause:* ALB passes X-Forwarded-For; API trusts it for rate limiting
- *Mitigation:* Use ALB's real client IP header, not X-Forwarded-For from client

**TAMPERING:**
- *Threat:* Attacker modifies transfer amount or recipient in transit
- *Root cause:* No message signing on request body
- *Mitigation:* HTTPS enforced (TLS in transit), HSTS header
- *Finding type:* Transport security

- *Threat:* SQL injection in transaction search parameters
- *Root cause:* String concatenation in database queries
- *Mitigation:* Parameterized queries throughout

**REPUDIATION:**
- *Threat:* User denies initiating a transfer, no audit trail
- *Root cause:* Insufficient audit logging — logs don't capture user identity + action + timestamp
- *Mitigation:* Log all state-changing operations with: user ID, action, parameters, timestamp, IP, result

**INFORMATION DISCLOSURE:**
- *Threat:* Error messages reveal database schema or stack traces
- *Root cause:* Express default error handling returns stack traces in development mode
- *Mitigation:* Custom error handler, disable verbose errors in production

- *Threat:* JWT payload contains sensitive user data
- *Root cause:* Developer added PII to JWT claims for convenience
- *Mitigation:* JWT payload is base64 encoded, not encrypted — only include non-sensitive claims

- *Threat:* Transaction history exposed to wrong user (IDOR)
- *Root cause:* GET /transactions?account=12345 — no ownership check
- *Mitigation:* Server-side ownership validation on every request

**DENIAL OF SERVICE:**
- *Threat:* Unauthenticated login endpoint overwhelmed with requests
- *Root cause:* No rate limiting on /auth/login
- *Mitigation:* Rate limiting (100 req/min per IP), CAPTCHA after 5 failures, account lockout

- *Threat:* Large transaction history query exhausts database connections
- *Root cause:* No pagination limit enforced
- *Mitigation:* Maximum page size, query timeout, connection pooling

**ELEVATION OF PRIVILEGE:**
- *Threat:* Regular user accesses admin endpoints
- *Root cause:* Role check missing on /admin/* endpoints
- *Mitigation:* Middleware enforces role check on every admin route

- *Threat:* JWT with manipulated `role` claim grants admin access
- *Root cause:* Role derived from JWT payload which user controls
- *Mitigation:* Derive role from database at request time, not from JWT

### Output — Security Requirements

From this STRIDE analysis, derive concrete security requirements:

```
SR-001: All JWT tokens MUST use RS256 with 2048-bit RSA keys
SR-002: JWT `alg` header MUST be validated server-side; `none` MUST be rejected
SR-003: All database queries MUST use parameterized statements
SR-004: All state-changing operations MUST be logged with user, action, timestamp
SR-005: Production error responses MUST NOT include stack traces
SR-006: All authenticated endpoints MUST verify resource ownership
SR-007: /auth/login MUST enforce rate limiting: max 10 req/min per IP
SR-008: User role MUST be fetched from database per request, not from JWT
SR-009: API responses MUST include HSTS header with min-age 31536000
SR-010: Transaction queries MUST enforce max page size of 100
```

These requirements go into the security backlog and are testable.

---

## Threat Modeling for Cloud-Native Architectures

Microservices and serverless architectures have a different threat surface than traditional monoliths. Key differences:

**Expanded attack surface:** 10 microservices = 10 separate authentication surfaces, 10 sets of API endpoints, 10 databases. Each service boundary is a potential trust boundary violation.

**Service-to-service authentication:** How do microservices authenticate to each other? mTLS, service mesh (Istio), or JWT? Unauthenticated service-to-service calls (assuming internal traffic is trusted) is a common vulnerability — if one service is compromised, it can impersonate any other.

**Secrets management:** Where do services get their database passwords and API keys? Hardcoded = terrible. Environment variables in Docker = better but still risky. Vault/AWS Secrets Manager/Azure Key Vault = correct.

**Container escape:** If the service runs in a container, what happens if there's code execution? Can the attacker escape to the host? Is the container running as root? Is the Docker socket mounted?

**Serverless (Lambda/Functions) threats:** Cold start injection, event data manipulation (can attacker control the event that triggers the function?), overly permissive IAM roles on functions.

### Cloud Threat Modeling Template Additions

For cloud architectures, add these to your standard STRIDE analysis:

```
ADDITIONAL THREAT CATEGORIES FOR CLOUD:

Identity and Access:
- IAM role with excessive permissions (principle of least privilege violation)
- Instance metadata service exposed to SSRF
- Long-lived credentials (no rotation)
- Cross-account trust misconfiguration

Data Exposure:
- S3 bucket with public read/write
- Unencrypted data at rest (EBS, RDS, S3)
- Sensitive data in CloudWatch logs
- Secrets in Lambda environment variables (visible in console)

Network:
- Security group with 0.0.0.0/0 inbound
- No VPC endpoint for S3/DynamoDB (traffic traverses internet)
- Unencrypted inter-service communication

Logging and Monitoring:
- CloudTrail disabled
- No alerting on root account usage
- No VPC flow logs
- S3 access logging disabled on sensitive buckets

Supply Chain:
- Unverified container images from public registries
- No image scanning in CI/CD pipeline
- Dependencies not pinned to versions (supply chain attack risk)
```

---

## Microsoft Threat Modeling Tool

Microsoft's free threat modeling tool implements STRIDE and produces DFDs, threat lists, and mitigations automatically.

```
Download: https://aka.ms/threatmodelingtool

Workflow:
1. Create new model
2. Draw DFD: add process, data store, external entity elements
3. Draw data flows between elements
4. Mark trust boundaries (dotted lines)
5. Tool auto-generates STRIDE threats for each element
6. Review each threat: accept, mitigate, or transfer
7. Add mitigations for each non-accepted threat
8. Export report (Word document)

Output:
- Threat list with STRIDE category and description
- Suggested mitigations for each threat
- Risk summary

Integration: Can be used in design reviews before any code is written.
Export format: .tm7 file (shareable between team members)
```

---

## When NOT to Threat Model

Threat modeling adds value at design time. It's less valuable when:

- **System already exists and is fully built:** Post-hoc threat modeling is useful for structured risk analysis but doesn't prevent design flaws already implemented. A penetration test is more efficient for finding actual vulnerabilities.

- **Too early in ideation:** If requirements change weekly, the threat model will be outdated before it's useful. Wait until architecture is stable enough to model.

- **Wrong team composition:** A threat model done only by security engineers without development team input will miss implementation constraints and generate findings the team can't act on. Developers must be in the room.

The goal of threat modeling is actionable security requirements *before* code is written. If that window has passed, pivot to secure code review and penetration testing instead.
