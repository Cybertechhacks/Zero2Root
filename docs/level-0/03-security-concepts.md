# Core Security Concepts

!!! info "Why This Matters"
    These concepts are the vocabulary of cybersecurity. You'll use them in every client report, every interview answer, and every conversation with a non-technical stakeholder. Get the fundamentals wrong and everything downstream suffers.

---

## The CIA Triad

The CIA Triad is the foundational model of information security. Every control, every attack, and every risk assessment maps back to these three properties.

### Confidentiality

**Definition:** Information is accessible only to those authorized to access it.

**In practice:** Encryption at rest (full disk encryption, database encryption), encryption in transit (TLS), access controls (least privilege), data masking, need-to-know principles.

**When it's violated:** A database is exposed without authentication (MongoDB, Elasticsearch left open), an unencrypted laptop is stolen, a misconfigured S3 bucket exposes PII, an insider leaks data, credentials are captured over cleartext protocols.

**Pentesting angle:** Confidentiality failures are often the primary finding in a pentest — exposed credentials, sensitive files readable by unauthorized users, unencrypted data in transit or at rest. When you find SQL injection, the impact on confidentiality is data exfiltration.

### Integrity

**Definition:** Information and systems are accurate and have not been tampered with by unauthorized parties.

**In practice:** Cryptographic hashing to detect file changes, digital signatures to verify authenticity, checksums, write-access controls, audit logging, version control.

**When it's violated:** An attacker modifies a financial transaction in transit, malware alters system binaries, a web application displays user-supplied data as HTML without sanitization (stored XSS), an unauthorized user modifies database records, software supply chain attacks (SolarWinds — the build system was compromised, so legitimate signed updates contained malicious code).

**Pentesting angle:** SQL injection allows data modification (INSERT, UPDATE, DELETE). XSS allows injecting scripts into pages viewed by other users. File upload vulnerabilities allow replacing application files. These all represent integrity failures.

### Availability

**Definition:** Systems and data are accessible to authorized users when needed.

**In practice:** Redundancy, failover, backups, disaster recovery plans, DDoS mitigation, capacity planning, patch management to fix crashing bugs.

**When it's violated:** Ransomware encrypts all data. DDoS overwhelms a server. A misconfigured firewall blocks legitimate traffic. A single point of failure fails. A software bug crashes a production database.

**Pentesting angle:** Scope matters here — you should almost never perform DoS attacks during an engagement unless explicitly authorized. Even if authorized, availability testing requires careful coordination. Testing for DoS *vulnerability* (e.g., identifying that a resource can be exhausted) is different from executing a DoS attack.

### The DAD Triad (Threat Model Counterpart)

The inverse of CIA is DAD: **Disclosure** (confidentiality failure), **Alteration** (integrity failure), **Destruction/Denial** (availability failure). Some risk frameworks map threats to CIA impact explicitly.

### Beyond CIA — AAA

**Authentication:** Verifying *who* you are. (Something you know, something you have, something you are.)
**Authorization:** Verifying *what you're allowed to do* once authenticated.
**Accounting (Audit):** Logging what authenticated, authorized users actually do — for accountability and forensics.

These three are distinct, and confusing them is a common interview mistake. A misconfigured application that logs in any user (authentication bypass) violates authentication. An application that logs in correctly but lets any user read any other user's data violates authorization. An application that never logs user actions fails accounting.

---

## Authentication — In Depth

### Authentication Factors

**Something you know:** Passwords, PINs, security questions. Weakest factor — susceptible to phishing, brute force, credential stuffing, shoulder surfing.

**Something you have:** Hardware token, smart card, authenticator app (TOTP), push notification, SMS OTP. Stronger, but SIM swapping attacks hardware against SMS; authenticator apps are harder to attack.

**Something you are:** Biometrics — fingerprint, face recognition, iris scan, voice. Strong for identity binding but: can't be changed if compromised, liveness detection bypass possible, not always reliable.

**Somewhere you are:** Geolocation, IP restriction. Supplementary control — easily bypassed by VPN, proxy.

**Multi-Factor Authentication (MFA):** Requires two or more *different* factors. A password + SMS OTP = MFA. Two passwords = NOT MFA. Important distinction: MFA dramatically reduces credential stuffing and phishing effectiveness, but does not eliminate all attacks — MITM real-time phishing kits (Evilginx2) can steal session cookies after MFA.

### Authentication Protocols

**Basic Authentication:** Base64-encodes `username:password` in the `Authorization: Basic` header. Not encryption — easily decoded. Must only be used over HTTPS.

**Digest Authentication:** MD5 hash of credentials + nonce. Avoids cleartext but vulnerable to relay attacks and MD5 weaknesses.

**NTLM (NT LAN Manager):** Windows challenge-response protocol. Server sends a challenge; client responds with NT hash of password XOR'd with the challenge. Does not send the hash directly but the hash *is* the credential (Pass-the-Hash). NTLM is susceptible to relay attacks (Responder, ntlmrelayx) where the response is relayed to another service.

**Kerberos:** Ticket-based authentication. The Key Distribution Center (KDC) issues a Ticket Granting Ticket (TGT) upon credential verification. The TGT is exchanged for Service Tickets for specific services. Never sends the password over the network. Covered in depth at Level 2.

**OAuth 2.0:** Authorization framework (not authentication). Allows a third-party application to access user resources on behalf of the user without sharing credentials. The actual authentication is delegated to an Identity Provider. Common misconfigurations: incorrect redirect_uri validation, missing state parameter (CSRF), using implicit flow with tokens in URL fragments.

**OpenID Connect (OIDC):** Authentication layer on top of OAuth 2.0. Returns an ID Token (JWT) containing user identity claims in addition to OAuth's access token.

**SAML (Security Assertion Markup Language):** XML-based SSO protocol common in enterprise environments. Identity Provider (IdP) issues signed XML assertions to Service Providers (SP). Attack surface: XML signature wrapping (modify unsigned parts of the assertion), XXE in XML parser, signature verification bypass.

---

## Encryption

The distinction between encryption, encoding, and hashing is tested at every interview level.

### Encoding

**Encoding is not security.** Base64, URL encoding, HTML encoding — these transform data into a different representation that anyone can reverse without a key. Used for compatibility (transmitting binary data over text protocols), not confidentiality.

```
Base64("password") = "cGFzc3dvcmQ="  — trivially reversed
URL encode("hello world") = "hello%20world"
```

### Symmetric Encryption

One key for both encryption and decryption. Both parties must share the key — **key distribution** is the central challenge.

**Speed:** Fast. Suitable for bulk data encryption.

**Common algorithms:**

| Algorithm | Key Size | Notes |
|-----------|----------|-------|
| AES-128 | 128 bits | Considered secure |
| AES-256 | 256 bits | Preferred for sensitive data |
| 3DES | 112/168 effective bits | Deprecated — SWEET32 attack |
| DES | 56 bits | Broken — brute-forceable |
| RC4 | Variable | Broken — statistical biases |
| ChaCha20 | 256 bits | Modern, fast, used in TLS 1.3 |
| Blowfish | 32–448 bits | Older, 64-bit block = SWEET32 risk |

**Modes of operation (how to encrypt data larger than one block):**
- **ECB (Electronic Code Book):** Each block encrypted independently with the same key. Same plaintext block → same ciphertext block. Pattern-preserving. Never use. (The "Linux penguin" ECB example is the standard illustration.)

- **CBC (Cipher Block Chaining):** Each plaintext block XOR'd with previous ciphertext block before encryption. Requires an IV (Initialization Vector). Susceptible to padding oracle attacks (POODLE, BEAST).

- **CTR (Counter):** Turns block cipher into a stream cipher. Parallelizable. The counter must never repeat with the same key.

- **GCM (Galois/Counter Mode):** CTR + authentication tag. Provides both confidentiality and integrity (AEAD — Authenticated Encryption with Associated Data). Standard in modern TLS.

### Asymmetric Encryption

Two mathematically related keys: a **public key** (share freely) and a **private key** (never share). What one key encrypts, only the other can decrypt.

**Speed:** Slow. Computationally expensive. Not suitable for bulk data. Used for key exchange and digital signatures.

**How it's used in TLS:** Asymmetric cryptography (Diffie-Hellman or RSA) establishes a shared secret; that secret becomes the symmetric encryption key for the session. This combines the security of asymmetric (no key pre-sharing needed) with the speed of symmetric (for actual data transfer).

**Common algorithms:**

| Algorithm | Use | Notes |
|-----------|-----|-------|
| RSA | Encryption, signatures | Key size ≥ 2048 bits; 4096 bits preferred |
| ECC (ECDSA, ECDH) | Signatures, key exchange | Smaller keys for equivalent security; preferred in modern systems |
| DSA | Signatures only | Largely superseded by ECDSA |
| Diffie-Hellman | Key exchange only | Never used for encryption directly |
| ECDH | Key exchange | Elliptic curve variant of DH; used in TLS 1.3 |

**Encryption vs Signing (critical distinction):**
- **Encryption:** Encrypt with recipient's *public key* → only recipient (with private key) can decrypt.

- **Signing:** Sign with sender's *private key* → anyone with sender's *public key* can verify the signature.

Confusing these is a common mistake. "Encrypt with private key" for signing is sometimes said colloquially but is technically incorrect — signing uses a signature algorithm, not raw encryption.

---

## Hashing

A hash function takes arbitrary input and produces a fixed-size output (digest). Properties:

- **Deterministic:** Same input always produces same output.

- **One-way (pre-image resistance):** Cannot derive input from output. (Not reversible — cracking means finding a match, not reversing.)

- **Collision resistance:** Hard to find two different inputs producing the same output. (MD5 and SHA-1 are broken for collision resistance — never use for security.)

- **Avalanche effect:** A single bit change in input completely changes the output.

**Common hash functions:**

| Algorithm | Output Size | Status |
|-----------|-------------|--------|
| MD5 | 128 bits (32 hex chars) | Broken (collisions); still used for checksums |
| SHA-1 | 160 bits (40 hex chars) | Broken (collisions in 2017); avoid for signatures |
| SHA-256 | 256 bits | Secure; standard |
| SHA-512 | 512 bits | Secure; slower but stronger |
| bcrypt | Variable | Password hashing; intentionally slow; salted |
| Argon2 | Variable | Modern password hashing; winner of Password Hashing Competition |
| NTLM | 128 bits (MD4) | Unsalted; vulnerable to rainbow tables and Pass-the-Hash |

**Password hashing:** Passwords must be hashed with a *slow*, *salted* algorithm designed for the purpose (bcrypt, scrypt, Argon2, PBKDF2). Using MD5 or SHA-256 unsalted for passwords is a critical vulnerability — these are fast (attackers can compute billions per second on GPUs) and without salt, rainbow tables precompute all hashes.

**Salt:** A random value prepended to the password before hashing. Makes precomputed rainbow tables useless — each account has a unique salt, so you must crack each hash independently. Salt does not need to be secret; it's stored alongside the hash.

**Rainbow tables:** Precomputed hash→password lookup tables. Defeated by salts. Effective against unsalted MD5/SHA-1/NTLM hashes.

**Hashing vs Encryption (interview trap):**
- Hashing is one-way. You cannot "decrypt" a hash.

- Encryption is two-way. You can decrypt if you have the key.

- Passwords should be *hashed*, not encrypted. If a system stores passwords in a way that the admin can "retrieve" a forgotten password (not reset it), the passwords are encrypted, not hashed — a serious vulnerability.

---

## PKI — Public Key Infrastructure

PKI is the system that makes asymmetric cryptography practical at internet scale by solving the problem: how do you know that a public key actually belongs to who you think it does?

**Certificate Authority (CA):** A trusted third party that issues digital certificates. The CA signs the certificate with its own private key — anyone with the CA's public key can verify the signature, confirming the CA vouches for the certificate.

**Digital Certificate (X.509):** Contains: subject (who the cert is for), public key, validity period, issuer (CA), and CA's signature. When your browser connects to `https://www.example.com`, it receives the server's certificate, verifies the CA signature is from a trusted CA, and checks the domain matches.

**Certificate Chain:**
```
Root CA (self-signed, in your OS/browser trust store)
  └── Intermediate CA (signed by Root CA)
        └── End-entity certificate (signed by Intermediate CA, for example.com)
```

Browsers trust Root CAs. An Intermediate CA allows Root CAs to be kept offline (airgapped) for security — the Intermediate CA handles day-to-day signing. If an Intermediate CA is compromised, only its certificates are revoked, not the Root.

**Certificate Revocation:**
- **CRL (Certificate Revocation List):** Periodically published list of revoked certificates. Large, slow to update.

- **OCSP (Online Certificate Status Protocol):** Real-time per-certificate status check. Requires the client to contact the CA's OCSP responder.

- **OCSP Stapling:** Server periodically fetches its own OCSP response and includes (staples) it in the TLS handshake. Reduces latency and privacy concern of OCSP queries.

**Common PKI Attack Scenarios in Pentests:**
- Self-signed certificates without proper validation → MITM possible

- Expired certificates → indicates poor certificate hygiene

- Certificates with too-broad Subject Alternative Names

- Misconfigured Certificate Transparency (CT) monitoring → new certs for your domain issued without your knowledge

- AD Certificate Services (ADCS) misconfigurations → domain privilege escalation (ESC1–ESC13 attack paths, covered at Level 3)

---

## Security Controls

Controls are safeguards or countermeasures to reduce risk. They're categorized by function and type.

### By Function

**Preventive:** Stop the attack from succeeding. Firewall, MFA, access controls, input validation, patching.

**Detective:** Identify when an attack has occurred. SIEM, IDS, audit logs, file integrity monitoring (FIM), honeypots.

**Corrective:** Respond to and recover from an attack. Incident response, backups, patch management, malware removal, system restore.

**Deterrent:** Discourage attackers. Warning banners, security cameras, legal notices (though these don't stop motivated attackers).

**Compensating:** Alternative control when the primary control isn't feasible. Network segmentation as compensation for an unpatchable legacy system.

### By Type

**Administrative (Managerial):** Policies, procedures, training, background checks, security awareness programs, acceptable use policies. Controls that govern how people behave.

**Technical (Logical):** Implemented through technology — firewalls, encryption, authentication systems, IDS/IPS, access control lists.

**Physical:** Protect physical access — locks, badge readers, security guards, CCTV, mantrap/airlock entries, cable locks.

**Defense in Depth:** Layer multiple controls so that failure of any single control doesn't result in a complete compromise. An attacker who bypasses the perimeter firewall still faces host-based firewalls, network segmentation, authentication, and endpoint protection.

### Principle of Least Privilege

Grant only the minimum access necessary for a user, process, or system to perform its function. A web server process shouldn't run as root. An employee in finance shouldn't have access to engineering source code. A database account for a web application should only have SELECT on the specific tables it needs, not DBA rights.

Least privilege is one of the most commonly violated security principles. Finding over-privileged service accounts, database users, and AD objects is a staple of internal pentests.

---

## Common Attack Classifications

A basic taxonomy for classifying attacks, used in reports and interviews:

**Active vs Passive:**
- Passive: Observe without interfering (network sniffing, OSINT, reconnaissance). Harder to detect.

- Active: Interact with the target (scanning, exploitation). Leaves traces.

**Insider vs Outsider:**
- Insider threat: Authorized user abusing access (malicious) or making mistakes (negligent).

- Outsider threat: External attacker with no legitimate access.

**Social Engineering:** Manipulating people into performing actions or divulging information.

- Phishing: Mass email-based

- Spear phishing: Targeted email

- Vishing: Voice (phone)

- Smishing: SMS

- Pretexting: Creating a fabricated scenario

- Baiting: Physical media (USB drops)

- Tailgating/Piggybacking: Physical access by following authorized person

**Man-in-the-Middle (MITM):** Attacker positions themselves between two communicating parties, intercepting and potentially modifying traffic. Enabled by ARP poisoning, rogue Wi-Fi AP, SSL stripping, DNS poisoning.

**Replay Attack:** Capture and retransmit valid authentication messages. Mitigated by nonces, timestamps, and session tokens.

**Brute Force:** Exhaustively try all possible values. Rate limiting, account lockout, CAPTCHA mitigate.

**Dictionary Attack:** Try common words and passwords from a wordlist. More efficient than pure brute force.

**Credential Stuffing:** Try username/password pairs from previous breaches on other services. Exploits password reuse.

**Zero-Day:** A vulnerability for which no patch yet exists. Often referenced in threat intelligence reports; relevant when assessing whether a target's controls would detect unknown attack patterns.
