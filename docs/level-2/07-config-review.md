# Configuration Review

!!! info "Why This Matters"
    Configuration review is one of the most common assessment types in commercial VAPT — especially for compliance-driven clients (PCI-DSS, ISO 27001). It doesn't involve exploitation, but it requires systematic knowledge of what "secure" looks like for each technology. Interviewers ask you to walk through a review methodology and explain specific checks.

---

## What Is Configuration Review?

Configuration review (also called hardening assessment or security baseline review) compares a system's actual configuration against a security standard:

- **CIS Benchmarks** — Center for Internet Security publishes detailed benchmarks for almost every OS, application, and cloud platform. The most widely used standard.
- **DISA STIGs** — US Defense Information Systems Agency. More strict than CIS, mandatory for US federal systems.
- **Vendor hardening guides** — Microsoft's Security Compliance Toolkit, NIST SP 800-series.
- **PCI-DSS requirements** — Specific configuration requirements for cardholder data environments.

The output is a compliance gap report — which controls pass, which fail, and remediation guidance for each failure.

---

## Linux Configuration Review

### Account and Authentication

```bash
# Check password policy (/etc/login.defs)
grep -E "^PASS_MAX_DAYS|^PASS_MIN_DAYS|^PASS_MIN_LEN|^PASS_WARN_AGE" /etc/login.defs
# CIS expects: PASS_MAX_DAYS 365 or less, PASS_MIN_LEN 14+, PASS_WARN_AGE 7+

# Check for accounts without passwords
awk -F: '($2 == "" ) { print $1 " has no password" }' /etc/shadow

# Check for UID 0 accounts (should only be root)
awk -F: '($3 == 0) { print $1 }' /etc/passwd

# Check sudo access
cat /etc/sudoers
ls -la /etc/sudoers.d/
# Look for NOPASSWD entries, ALL=(ALL) ALL for non-admin users

# SSH root login
grep "^PermitRootLogin" /etc/ssh/sshd_config
# Should be: PermitRootLogin no

# SSH password authentication
grep "^PasswordAuthentication" /etc/ssh/sshd_config
# Should be: PasswordAuthentication no (key-based only)

# SSH protocol version
grep "^Protocol" /etc/ssh/sshd_config
# Should be: Protocol 2 (SSH1 is deprecated)

# Empty password SSH
grep "^PermitEmptyPasswords" /etc/ssh/sshd_config
# Should be: PermitEmptyPasswords no
```

### File System Security

```bash
# World-writable files (outside /tmp)
find / -xdev -type f -perm -0002 ! -path "/proc/*" ! -path "/tmp/*" 2>/dev/null

# SUID/SGID files (unexpected ones)
find / -xdev \( -perm -4000 -o -perm -2000 \) -type f 2>/dev/null

# Files without owner
find / -xdev \( -nouser -o -nogroup \) -type f 2>/dev/null

# /tmp sticky bit
ls -la / | grep tmp
# Should show: drwxrwxrwt (t = sticky bit)

# Home directory permissions
ls -la /home
# Directories should be 700 or 750, not 777

# Critical file permissions
ls -la /etc/passwd /etc/shadow /etc/group /etc/sudoers
# /etc/shadow should be 640 or 000 (not readable by world)
# /etc/passwd should be 644
```

### Services and Network

```bash
# Listening services
ss -tulpn
# Review each listening service: is it necessary? Is it properly secured?

# Firewall status
ufw status verbose      # Ubuntu
firewall-cmd --list-all  # RHEL/CentOS

# Unnecessary services running
systemctl list-units --type=service --state=running
# Check for: telnet, rsh, rlogin, rexec, finger, chargen, echo, discard

# NFS exports (can expose filesystem to network)
cat /etc/exports
# Verify no wildcard exports (exports to * = all hosts)

# Cron permissions
ls -la /etc/cron*
# World-writable cron directories/files = privilege escalation risk

# Core dumps disabled
grep "hard core" /etc/security/limits.conf
sysctl fs.suid_dumpable
# Should be: fs.suid_dumpable = 0 (disable SUID core dumps)
```

### Kernel Parameters (sysctl)

```bash
# Key sysctl security settings
sysctl -a 2>/dev/null | grep -E "net.ipv4.tcp_syncookies|net.ipv4.ip_forward|net.ipv4.conf.all.rp_filter|kernel.randomize_va_space"

# Expected secure values:
# net.ipv4.tcp_syncookies = 1        (SYN cookies enabled)
# net.ipv4.ip_forward = 0            (not a router)
# net.ipv4.conf.all.rp_filter = 1    (reverse path filtering)
# kernel.randomize_va_space = 2      (full ASLR)
# net.ipv4.conf.all.accept_redirects = 0  (no ICMP redirects)
# net.ipv4.conf.all.send_redirects = 0    (don't send redirects)
# kernel.dmesg_restrict = 1          (restrict dmesg to root)
# kernel.kptr_restrict = 2           (hide kernel pointers)
```

### Logging and Auditing

```bash
# Auditd running
systemctl status auditd

# Audit rules configured
auditctl -l
# Should include: monitoring of /etc/passwd, /etc/shadow, /etc/sudoers changes
# Monitoring of privileged command execution
# Monitoring of login failures

# Syslog configured
cat /etc/rsyslog.conf
# Verify logs are being sent to centralized SIEM (remote logging)

# Log file permissions
ls -la /var/log/
# Log files should not be world-readable
```

---

## Windows Configuration Review

### Account Policies

```powershell
# Password policy
net accounts
# Or via Group Policy:
# Computer Configuration → Windows Settings → Security Settings → Account Policies

# Key values (CIS Level 1):
# Minimum password length: 14+ characters
# Password history: 24+ passwords remembered
# Maximum password age: 60-90 days
# Account lockout threshold: 5-10 attempts
# Account lockout duration: 15+ minutes
# Account lockout observation window: 15+ minutes

# Local accounts
net user
# Disable default accounts: Guest (should be disabled), Administrator (should be renamed)

# Check for accounts not requiring passwords
Get-LocalUser | Where-Object {$_.PasswordRequired -eq $false}

# Check for accounts with non-expiring passwords
Get-LocalUser | Where-Object {$_.PasswordExpires -eq $null} | Select Name
```

### Security Options

```powershell
# Check key registry settings
# LM and NTLMv1 disabled
reg query "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v LmCompatibilityLevel
# Should be 5 = NTLMv2 only, refuse LM and NTLMv1

# WDigest disabled (no cleartext creds in LSASS)
reg query "HKLM\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest" /v UseLogonCredential
# Should be 0 or not set

# Credential Guard
reg query "HKLM\SOFTWARE\Policies\Microsoft\Windows\DeviceGuard"
# VirtualizationBasedSecurity = 1

# UAC configured
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v EnableLUA
# Should be 1 (UAC enabled)
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v ConsentPromptBehaviorAdmin
# Should be 2 (prompt for credentials) or 1 (prompt with secure desktop)

# SMB signing
reg query "HKLM\SYSTEM\CurrentControlSet\Services\LanManServer\Parameters" /v RequireSecuritySignature
# Should be 1 for critical servers

# Remote Registry disabled
Get-Service RemoteRegistry | Select Status
# Should be Stopped and Disabled
```

### Firewall and Network

```powershell
# Windows Firewall status
netsh advfirewall show allprofiles
# All profiles (Domain, Private, Public) should be enabled

# Network shares
net share
# Remove default admin shares? (C$, ADMIN$, IPC$ — discuss with client)
# Remove any unnecessary shares

# Remote services
Get-Service RemoteRegistry | Select Status  # Should be Disabled
Get-Service TelnetServer 2>$null | Select Status  # Should not exist
Get-Service FTPSVC 2>$null | Select Status  # Should not exist or be disabled if not needed

# Windows Remote Management (WinRM)
Get-Service WinRM | Select Status
# If enabled: verify authentication requirements and who can connect
```

### Patch Status

```powershell
# Installed patches
Get-HotFix | Sort-Object InstalledOn -Descending | Select -First 20

# Missing patches (using WSUS or Windows Update API)
# Easier with tools: Nessus authenticated scan, or Windows Update Agent API

# Last update check
(New-Object -ComObject Microsoft.Update.AutoUpdate).Results.LastInstallationSuccessDate
```

---

## Network Device Configuration Review

For routers, switches, and firewalls (Cisco, Juniper, Palo Alto):

```
# Cisco IOS key checks:

# Authentication
service password-encryption  ← Should be present
enable secret md5hash        ← Should be 'enable secret' not 'enable password'
no service password-recovery ← Prevents console password bypass

# Unused services (should be disabled)
no service finger
no service tcp-small-servers
no service udp-small-servers
no ip bootp server
no ip http server    ← Disable HTTP management interface
ip http secure-server  ← HTTPS management is acceptable

# Logging
logging on
logging host 192.168.1.50     ← Centralized syslog server
logging trap notifications
service timestamps log datetime msec timezone show-timezone

# SSH (instead of Telnet)
ip ssh version 2
no transport input telnet   ← Applied to VTY lines
transport input ssh

# Banner (legal warning)
banner login ^WARNING: Unauthorized access prohibited^

# SNMP
no snmp-server community public RO    ← Remove default communities
snmp-server community strongrandomstring RO   ← If SNMP v2c needed
# Prefer SNMPv3 with authentication and privacy:
snmp-server group mygroup v3 priv

# Spanning Tree (prevent topology changes)
spanning-tree portfast bpduguard default    ← On access ports

# DHCP snooping
ip dhcp snooping
ip dhcp snooping vlan 1-100
ip dhcp snooping limit rate 15   ← Rate limit DHCP requests

# Dynamic ARP Inspection
ip arp inspection vlan 1-100
```

---

## Cloud Configuration Review

### AWS

```bash
# AWS CLI based checks (or use Scout Suite / Prowler)

# S3 bucket public access
aws s3api get-bucket-acl --bucket bucket-name
aws s3api get-bucket-policy --bucket bucket-name
aws s3api get-public-access-block --bucket bucket-name
# All four public access block settings should be true

# IAM password policy
aws iam get-account-password-policy
# Check: MinimumPasswordLength >= 14, RequireSymbols=true, MaxPasswordAge <= 90

# Root account MFA
aws iam get-account-summary | grep -i "AccountMFAEnabled"
# Should be 1

# Users without MFA
aws iam list-users | jq -r '.Users[].UserName' | while read user; do
  mfa=$(aws iam list-mfa-devices --user-name $user | jq '.MFADevices | length')
  if [ "$mfa" == "0" ]; then echo "$user has no MFA"; fi
done

# CloudTrail enabled
aws cloudtrail describe-trails
aws cloudtrail get-trail-status --name TrailName

# Security Groups with 0.0.0.0/0
aws ec2 describe-security-groups --query 'SecurityGroups[?IpPermissions[?IpRanges[?CidrIp==`0.0.0.0/0`]]].{Name:GroupName,ID:GroupId}'

# Access keys age
aws iam list-users | jq -r '.Users[].UserName' | while read user; do
  aws iam list-access-keys --user-name $user | jq -r '.AccessKeyMetadata[] | "'$user': \(.AccessKeyId) created \(.CreateDate)"'
done
# Flag access keys older than 90 days

# Scout Suite — automated AWS configuration review
scoutsuite aws --report-dir report/

# Prowler — CIS benchmark checks for AWS
prowler -g cislevel1
prowler -g pci
```

### Azure

```bash
# Azure CLI checks
az account list  # Active subscriptions

# MFA status
az ad user list --query "[].{UPN:userPrincipalName}" --output table
# Check Entra ID → MFA registration

# Security Center / Defender for Cloud
az security assessment list --output table

# Storage accounts with public access
az storage account list --query "[?allowBlobPublicAccess==true].name" --output table

# Network Security Groups allowing any inbound
az network nsg list --query "[].{Name:name,Rules:securityRules}" | grep -i "0.0.0.0/0"

# Key Vault access policies
az keyvault list --query "[].name" | while read vault; do
  az keyvault show --name $vault --query "properties.accessPolicies"
done
```

---

## CIS Benchmark Levels

CIS Benchmarks come in two levels:

**Level 1:** Basic hardening that doesn't significantly impact functionality or operations. Apply to all systems. Generally low effort, high value.

**Level 2:** Defense-in-depth hardening. May impact functionality. Suitable for environments requiring higher security (financial systems, military, healthcare). Requires more testing before deployment.

**In a configuration review report:** State which CIS Benchmark version and level you assessed against. Each finding should reference the specific CIS control number:
```
Finding: SSH Root Login Not Disabled
CIS Benchmark: CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0, Section 5.2.8
Expected: PermitRootLogin no
Actual: PermitRootLogin yes
Severity: High
```

---

## Common Configuration Review Findings — Ranked by Frequency

After conducting dozens of configuration reviews, these findings appear most consistently:

### Critical / High Frequency Findings

**1. Default or Weak Credentials on Services**
Printers, switches, routers, and management interfaces with admin/admin or vendor defaults. Found in nearly every environment.

**2. Missing Critical Patches (OS and Application)**
Systems more than 90 days behind on critical patches. Windows Server Update Services (WSUS) misconfigurations frequently cause large patch gaps across enterprise environments.

**3. Excessive User Privileges**
Local administrator rights granted to standard users "for convenience." In AD environments, excessive group memberships — helpdesk staff in Domain Admins, developers with DBA rights.

**4. No Account Lockout Policy or Weak Password Policy**
Allows unlimited password guessing. Often found on legacy systems excluded from group policy.

**5. SSH Root Login Enabled**
`PermitRootLogin yes` in `/etc/ssh/sshd_config`. Allows direct remote root authentication — bypasses all principle-of-least-privilege controls.

**6. SMB Signing Not Required**
Enables NTLM relay attacks. Found on file servers, workstations, and sometimes even DCs where signing is only "enabled" not "required."

**7. SNMP v1/v2c with Default Community Strings**
Network devices with "public" and "private" still set. Exposes device configuration, routing tables, and sometimes configuration modification.

**8. NTP Not Synchronized**
Kerberos authentication fails when time skew exceeds 5 minutes. Poorly configured NTP also breaks log correlation.

---

## Linux Hardening — Extended Checks

```bash
# PAM Password Configuration
grep "pam_pwquality" /etc/pam.d/common-password /etc/pam.d/system-auth 2>/dev/null
cat /etc/security/pwquality.conf
# CIS expects: minlen=14, minclass=4 (upper, lower, digit, special)
# dcredit=-1, ucredit=-1, lcredit=-1, ocredit=-1

# Ensure failed login attempts are tracked
grep "pam_faillock\|pam_tally2" /etc/pam.d/common-auth /etc/pam.d/system-auth 2>/dev/null
# Should be configured with deny=5, unlock_time=900 (15 minutes)

# Check for inactive accounts (accounts not logged in for >90 days)
lastlog | awk '$NF != "Never" {print}' | \
  awk -v cutoff=$(date -d "-90 days" +%s) '
    NR>1 && $0 !~ /Never/ {
      cmd = "date -d \"" $4 " " $5 " " $6 " " $7 " " $8 "\" +%s"
      cmd | getline ts
      close(cmd)
      if (ts < cutoff) print $1 " last login: " $4 " " $5 " " $6
    }'

# Check for accounts with no expiry (service accounts should have expiry set)
for user in $(awk -F: '$3 >= 1000 {print $1}' /etc/passwd); do
  expiry=$(chage -l $user 2>/dev/null | grep "Account expires" | cut -d: -f2)
  echo "$user: Account expires: $expiry"
done

# Check installed packages for known vulnerable software
# Debian/Ubuntu
apt list --installed 2>/dev/null | grep -iE "telnet|ftp|rsh|rlogin|tftp"
dpkg --list telnetd vsftpd rsh-server 2>/dev/null | grep "^ii"

# RHEL/CentOS
rpm -qa | grep -iE "telnet-server|vsftpd|rsh-server|tftp-server"

# Unnecessary services to check for
systemctl list-units --type=service --state=running | \
  grep -iE "avahi|cups|rpcbind|nfs|bluetooth|isc-dhcp"

# Check for world-writable cron directories
find /etc/cron* /var/spool/cron -perm -002 2>/dev/null

# AppArmor / SELinux status
getenforce 2>/dev/null || echo "SELinux not present"
aa-status 2>/dev/null || echo "AppArmor not present"
# At least one MAC framework should be enforcing

# Check for unattended-upgrades (automatic security patching)
dpkg -l unattended-upgrades 2>/dev/null
cat /etc/apt/apt.conf.d/20auto-upgrades 2>/dev/null

# Umask settings (new file default permissions)
grep "UMASK\|umask" /etc/login.defs /etc/profile /etc/bashrc 2>/dev/null
# Should be 027 or 022 at minimum (not 000 or 002)

# Core dump configuration
grep "hard core" /etc/security/limits.conf /etc/security/limits.d/*.conf 2>/dev/null
# Should have: * hard core 0
sysctl fs.suid_dumpable
# Should be 0
```

---

## Windows Hardening — Extended Checks

```powershell
# Check Windows Defender status
Get-MpComputerStatus | Select AntivirusEnabled, RealTimeProtectionEnabled, AntispywareEnabled

# Check Windows Firewall profile status
Get-NetFirewallProfile | Select Name, Enabled, DefaultInboundAction, DefaultOutboundAction

# Check for AutoRun/AutoPlay disabled
Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer" `
  -Name "NoDriveTypeAutoRun" 2>$null
# Should be 255 (disable all autorun)

# Check PowerShell execution policy
Get-ExecutionPolicy -List
# Per-machine: should be RemoteSigned or more restrictive

# Check PowerShell script block logging
Get-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" `
  2>$null | Select EnableScriptBlockLogging
# Should be 1 (enabled)

# Check Windows Remote Management (WinRM) configuration
Get-WSManInstance -ResourceURI winrm/config/listener
# If enabled: verify HTTPS only (not HTTP)
winrm get winrm/config/service | Select AllowUnencrypted
# Should be: false

# Bitlocker status (full disk encryption)
Get-BitLockerVolume | Select MountPoint, VolumeStatus, EncryptionPercentage, KeyProtector
# Should be: FullyEncrypted

# Check for cleartext credentials in common locations
Get-ChildItem -Path C:\ -Include "*.xml","*.ini","*.txt","*.config" -Recurse -ErrorAction SilentlyContinue |
  Select-String -Pattern "password|passw|pwd" -CaseSensitive:$false |
  Where-Object {$_.Line -notmatch "<!--"} |
  Select Path, LineNumber, Line | Format-List

# Check Windows Event Log retention policy
Get-WinEvent -ListLog Security | Select MaximumSizeInBytes, LogMode
# Security log should be at minimum 1GB (1073741824 bytes)

# Check for LLMNR disabled (prevents LLMNR/NBT-NS poisoning)
Get-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" `
  -Name "EnableMulticast" 2>$null
# Should be 0

# Check for NBT-NS disabled
Get-WmiObject Win32_NetworkAdapterConfiguration | Where-Object {$_.IPEnabled} |
  Select Description, TcpipNetbiosOptions
# TcpipNetbiosOptions: 0=default, 1=enable, 2=disable — should be 2

# Check Windows Defender Credential Guard
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard" `
  -Name "EnableVirtualizationBasedSecurity" 2>$null
# Should be 1 or 2

# Check SMB settings
Get-SmbServerConfiguration | Select EnableSMB1Protocol, RequireSecuritySignature, EncryptData
# SMB1 should be False; RequireSecuritySignature should be True for sensitive servers
```

---

## Configuration Review Report — Interview Context

**"How do you approach a configuration review engagement?"**

"A config review follows three phases. First, scope and baseline selection — I confirm with the client which framework and level applies. For most enterprise systems CIS Level 1 is the default; Level 2 is for higher-security environments. For compliance-driven engagements (PCI, ISO 27001), I use the framework controls mapped to configuration requirements.

Second, assessment — I combine automated tools with manual verification. For Linux I use Lynis (`lynis audit system`); for Windows I use CIS-CAT or a custom PowerShell script based on the CIS benchmark; for cloud I use ScoutSuite or Prowler. Automated tools have a false positive rate, so I manually verify all High findings before reporting.

Third, reporting — each finding maps to a specific CIS control number, shows the expected value versus actual value, and includes the specific remediation command or configuration change. The report is organized by severity so the team can prioritize immediate fixes.

A config review is a compliance gap assessment, not exploitation — I'm documenting what deviates from the baseline, not confirming whether the deviation is exploitable. That distinction matters for scoping."

**Common follow-up: "What's the most impactful misconfiguration you typically find?"**

"Consistently: SSH root login enabled combined with password authentication — it means anyone who guesses or brute-forces the root password has direct privileged access with no MFA, no audit trail of which key was used, nothing. The fix is two lines in sshd_config and generating SSH keys for administrators. The gap between how easy it is to fix and how much risk it removes makes it the highest-value finding per remediation hour in almost any Linux environment."
