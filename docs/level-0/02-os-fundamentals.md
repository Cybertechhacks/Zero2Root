# OS Fundamentals

!!! info "Why This Matters"
    Post-exploitation lives inside operating systems. Privilege escalation, lateral movement, persistence, and evidence collection all require deep OS knowledge. Interviewers test OS internals to verify you understand what happens *after* you land on a box — not just how you got there.

---

## Linux Fundamentals

### Linux Filesystem Hierarchy (FHS)

Understanding the Linux filesystem is non-negotiable. Every directory has a purpose, and knowing where things live is essential for both exploitation and forensics.

| Directory | Contents | Pentesting Relevance |
|-----------|----------|---------------------|
| `/` | Root of the filesystem | Starting point for traversal |
| `/etc` | System-wide configuration files | Password hashes (`/etc/shadow`), SSH config, cron jobs, service configs |
| `/etc/passwd` | User account information | Username, UID, GID, home, shell — readable by all |
| `/etc/shadow` | Password hashes | Readable only by root — cracking target |
| `/etc/hosts` | Static hostname resolution | Internal hostname mapping |
| `/etc/cron.d`, `/etc/cron.daily` | System cron jobs | Cron-based privesc if writable or calls writable scripts |
| `/home` | User home directories | Bash history, SSH keys, credentials in config files |
| `/root` | Root user's home | Highest-value target |
| `/var/log` | Log files | Evidence of your activity; also valuable for blue team analysis |
| `/var/mail` | User mail | May contain credentials or sensitive info |
| `/var/www` | Web server document root (typical) | Web application source code |
| `/tmp` | Temporary files | World-writable — useful for staging payloads |
| `/dev/shm` | Shared memory filesystem | World-writable, in-memory — payload staging, often not monitored |
| `/proc` | Virtual filesystem — kernel/process info | `/proc/net/tcp` for network connections, `/proc/[pid]/cmdline` for process args |
| `/sys` | Virtual filesystem — hardware/kernel | |
| `/opt` | Optional/third-party software | Installed software, sometimes with SUID binaries |
| `/usr/bin`, `/bin` | User executables | |
| `/usr/sbin`, `/sbin` | System admin executables | |
| `/usr/share` | Architecture-independent data | Man pages, exploit databases in Kali |
| `/lib`, `/usr/lib` | Shared libraries | Dynamic linker exploitation |
| `/boot` | Boot loader, kernel images | GRUB misconfig for local privilege escalation |
| `/mnt`, `/media` | Mount points | Mounted filesystems — external drives, NFS |
| `/run` | Runtime data | PID files, socket files |

### Linux File Permissions

Permissions are the most tested Linux topic in security interviews. Three sets of permissions apply to: Owner (user), Group, and Others.

```
-rwxrwxrwx  1  owner  group  size  date  filename
│└┬─┘└┬─┘└┬┘
│  │   │   └── Others permissions
│  │   └────── Group permissions
│  └────────── Owner permissions
└────────────── File type: - = regular, d = directory, l = symlink, s = socket, p = pipe
```

Each permission triplet: `r` (read = 4), `w` (write = 2), `x` (execute = 1).

- `rwx` = 7, `rw-` = 6, `r-x` = 5, `r--` = 4, `---` = 0
- `chmod 755` = `rwxr-xr-x` (owner full, group/others read+execute)
- `chmod 644` = `rw-r--r--` (owner read+write, group/others read only)

**Special permission bits — critical for privilege escalation:**

**SUID (Set User ID) — bit value 4000:**
When set on an executable, the process runs with the *file owner's* UID rather than the executing user's UID. If the owner is root and SUID is set, anyone who executes the file gets a root-effective process.

```bash
# Find SUID files owned by root
find / -perm -4000 -user root -type f 2>/dev/null

# Common legitimate SUID binaries: passwd, sudo, ping, su
# Dangerous if misconfigured: find, vim, python, bash, cp, nano, nmap (old versions)
```

If `find` has SUID root:
```bash
find . -exec /bin/sh -p \; -quit
# -p = privileged mode, preserves EUID (root)
```

**SGID (Set Group ID) — bit value 2000:**
On executables: process inherits the file's group GID. On directories: new files created inside inherit the directory's group (useful for shared directories).

```bash
find / -perm -2000 -type f 2>/dev/null
```

**Sticky Bit — bit value 1000:**
On directories: only the file's owner (or root) can delete or rename files, even if others have write permission. `/tmp` uses this — you can write files there but can't delete files owned by other users.

```bash
ls -la /tmp
# drwxrwxrwt  — the 't' indicates sticky bit
```

**World-writable files and directories:**
```bash
find / -perm -0002 -type f 2>/dev/null  # world-writable files
find / -perm -0002 -type d 2>/dev/null  # world-writable directories
```

World-writable files called by root (via cron, service scripts) are privilege escalation vectors.

**Capabilities:**
A finer-grained alternative to SUID. Instead of granting full root privileges, capabilities grant specific permissions:
- `cap_net_raw`: Raw socket operations (like ping)
- `cap_setuid`: Can set arbitrary UIDs
- `cap_sys_admin`: Almost unrestricted — nearly equivalent to root

```bash
# Find files with capabilities
getcap -r / 2>/dev/null

# Example dangerous capability
python3 -c 'import os; os.setuid(0); os.system("/bin/bash")'
# If python3 has cap_setuid, this drops you to root
```

### Linux Users and Groups

- **UID 0** = root. Any process with effective UID 0 has unrestricted access.
- **UID 1-999** = system accounts (services). `/etc/passwd` shows `nologin` or `false` as shell — these shouldn't be able to log in interactively.
- **UID 1000+** = regular user accounts.

`/etc/passwd` format:
```
username:x:uid:gid:gecos:home:shell
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
```
The `x` in the password field means the hash is in `/etc/shadow`.

`/etc/shadow` format:
```
username:$type$salt$hash:lastchanged:min:max:warn:inactive:expire
root:$6$salt$longhash:18000:0:99999:7:::
```
Hash types: `$1$` = MD5, `$2a$` = bcrypt, `$5$` = SHA-256, `$6$` = SHA-512.

### Sudo

`sudo` allows a user to execute commands as another user (typically root), as defined in `/etc/sudoers`.

```bash
# Check what the current user can run with sudo
sudo -l

# Common privesc sudo misconfigs:
sudo /usr/bin/vim        # vim can execute shell commands: :!bash
sudo /usr/bin/less       # less can execute: !/bin/bash
sudo /usr/bin/python3    # python: import os; os.system('/bin/bash')
sudo /bin/cp             # copy /etc/shadow to a readable location
sudo /usr/bin/find       # find -exec /bin/bash \; -quit
sudo /usr/bin/tar        # tar --checkpoint-action=exec=/bin/bash
sudo ALL=(ALL) NOPASSWD: ALL  # full unrestricted sudo — instant root
```

`GTFOBins` (gtfobins.github.io) catalogs Unix binaries that can be abused when given elevated sudo or SUID permissions.

### Linux Processes and Services

```bash
ps aux              # all processes, BSD syntax
ps -ef              # all processes, UNIX syntax
ps -eo pid,ppid,user,command  # custom columns

top / htop          # real-time process view

# Process tree
pstree
ps -axjf

# Process details
ls -la /proc/[PID]/
cat /proc/[PID]/cmdline | tr '\0' ' '  # command line arguments
cat /proc/[PID]/environ | tr '\0' '\n'  # environment variables (may contain secrets)
ls -la /proc/[PID]/fd                  # open file descriptors

# Find processes listening on network sockets
ss -tulpn           # recommended (replaces netstat)
netstat -tulpn      # older systems
lsof -i             # all network connections with PIDs
```

### Cron Jobs

Cron executes scheduled tasks. A cron job that runs as root and calls a script writable by a lower-privileged user is a classic privilege escalation vector.

```bash
# System-wide cron
cat /etc/crontab
ls /etc/cron.d/
ls /etc/cron.daily/  /etc/cron.hourly/  /etc/cron.weekly/  /etc/cron.monthly/

# Per-user cron (stored in /var/spool/cron/crontabs/)
crontab -l

# Monitoring cron execution (useful in CTFs)
# pspy (process spy) — monitors without root
# https://github.com/DominicBreuker/pspy
./pspy64
```

**Cron format:**
```
* * * * * user command
│ │ │ │ │
│ │ │ │ └── Day of week (0-7, 0 and 7 = Sunday)
│ │ │ └──── Month (1-12)
│ │ └────── Day of month (1-31)
│ └──────── Hour (0-23)
└────────── Minute (0-59)
```

### Linux Environment Variables

```bash
env                 # show all environment variables
printenv PATH       # show PATH
echo $HOME

# Dangerous PATH manipulation:
# If a script calls 'python' without full path and PATH is user-controlled:
echo '#!/bin/bash' > /tmp/python
echo '/bin/bash' >> /tmp/python
chmod +x /tmp/python
export PATH=/tmp:$PATH
# Now when the script calls 'python', our fake python runs instead
```

### SSH Keys

```bash
# Location of SSH private/public key pairs
~/.ssh/id_rsa           # Private key (protect this)
~/.ssh/id_rsa.pub       # Public key
~/.ssh/authorized_keys  # Keys authorized to log into this account
~/.ssh/known_hosts      # Servers this user has connected to
~/.ssh/config           # SSH client configuration

# During post-exploitation, always check:
cat ~/.ssh/id_rsa        # Steal private key for lateral movement
cat ~/.ssh/authorized_keys  # Understand who can SSH in as this user
```

---

## Windows Fundamentals

### Windows Architecture Overview

Windows has a layered architecture relevant to understanding attacks:

- **User mode:** Application code runs here. Restricted access to hardware. Processes cannot directly access kernel memory or hardware.
- **Kernel mode:** Operating system kernel, hardware drivers. Full access to system resources. A kernel exploit elevates from user mode to kernel mode.
- **Windows API (Win32/Win64):** User-mode applications call Windows API functions. These are wrappers for Native API calls.
- **Native API (ntdll.dll):** The bridge between user mode and kernel mode. System calls (syscalls) cross the boundary here. Direct syscalls bypass security software monitoring Win32 API.
- **Hardware Abstraction Layer (HAL):** Abstracts hardware differences.

### Windows Registry

The Windows Registry is a hierarchical database storing configuration for the OS, services, hardware, and applications.

**Hive structure:**

| Hive | Abbreviation | Contents |
|------|-------------|----------|
| HKEY_LOCAL_MACHINE | HKLM | Machine-wide settings — services, hardware, installed software |
| HKEY_CURRENT_USER | HKCU | Current user's settings — preferences, user-level software |
| HKEY_USERS | HKU | All loaded user profiles |
| HKEY_CLASSES_ROOT | HKCR | File associations, COM object registrations |
| HKEY_CURRENT_CONFIG | HKCC | Hardware profile currently in use |

**Pentesting-relevant registry locations:**

```powershell
# AutoRun locations — persistence mechanisms
HKLM\Software\Microsoft\Windows\CurrentVersion\Run
HKCU\Software\Microsoft\Windows\CurrentVersion\Run
HKLM\Software\Microsoft\Windows NT\CurrentVersion\Winlogon

# Stored credentials and saved passwords
HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon
# Autologon: DefaultUserName, DefaultPassword may be set here

# Services — each service has a key here
HKLM\SYSTEM\CurrentControlSet\Services\

# Installed software
HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\
HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\

# SAM database (password hashes) — accessible only as SYSTEM
HKLM\SAM
```

### Windows SAM and Password Hashes

The Security Account Manager (SAM) database stores local user account hashes. Located at `C:\Windows\System32\config\SAM`. Locked while Windows is running, but the key from `HKLM\SYSTEM\CurrentControlSet\Control\Lsa` is needed to decrypt it.

**Hash format (NT Hash):** `NT hash = MD4(UTF-16LE(password))`. No salt. If you've seen the hash, you can pass it directly (Pass-the-Hash) without cracking it.

**Extracting SAM hashes:**
```
# As SYSTEM (e.g., via Meterpreter or PSEXEC)
reg save HKLM\SAM C:\sam.hive
reg save HKLM\SYSTEM C:\system.hive
# Transfer files and extract offline with impacket
impacket-secretsdump -sam sam.hive -system system.hive LOCAL

# Via Volume Shadow Copy (bypass file lock)
vssadmin list shadows
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SAM C:\

# Mimikatz (requires SYSTEM or SeDebugPrivilege)
privilege::debug
token::elevate
lsadump::sam
```

### LSASS — Local Security Authority Subsystem Service

LSASS (`lsass.exe`) is one of the most targeted processes in Windows post-exploitation. It handles:
- Authentication (validating credentials)
- Security policy
- Storing credentials in memory (Credential Cache)

**Why LSASS matters:** LSASS caches credentials in memory — NTLM hashes, Kerberos tickets, and sometimes cleartext passwords (when WDigest is enabled, which it was by default before Windows 8.1/Server 2012 R2). Mimikatz's `sekurlsa::logonpasswords` reads these from LSASS memory.

**WDigest:** A legacy authentication protocol that stored credentials in cleartext in LSASS. Disabled by default in modern Windows but can be re-enabled (attackers do this for persistence, defenders check for it):
```
HKLM\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest
"UseLogonCredential"=dword:00000001  # 1 = enable cleartext (bad)
```

**LSASS protection:**
- **PPL (Protected Process Light):** LSASS running as a protected process — direct memory reads from user mode are blocked. Bypass requires a vulnerable driver or kernel exploit.
- **Credential Guard:** Stores secrets in a virtualization-based isolated container — even SYSTEM cannot read them from LSASS memory.
- **ASR (Attack Surface Reduction):** Windows Defender rule to block credential dumping from LSASS.

### Windows Services

Services are long-running processes managed by the Service Control Manager (SCM). Each service runs under a specific account — `SYSTEM`, `Local Service`, `Network Service`, or a dedicated service account.

```powershell
# List all services
sc query type= all state= all
Get-Service

# Service details (including binary path)
sc qc ServiceName
Get-WmiObject Win32_Service | Select Name, PathName, StartMode, State, StartName

# Services with unquoted paths — privilege escalation vector
# If path is: C:\Program Files\Vulnerable Service\service.exe (unquoted with spaces)
# Windows tries: C:\Program.exe, C:\Program Files\Vulnerable.exe, etc.
# Placing a malicious binary at C:\Program.exe runs it as the service account
wmic service get name,pathname | findstr /i /v "C:\Windows\\" | findstr /i /v '\"'

# Writable service binary paths
icacls "C:\path\to\service.exe"
# If your user has WRITE access to the binary, replace it with a payload
```

**Service permissions — check with AccessChk:**
```cmd
accesschk.exe -ucqv "everyone" * /accepteula     # Services everyone can modify
accesschk.exe -uwcqv "BUILTIN\Users" * /accepteula
```

If a user can `SERVICE_CHANGE_CONFIG` on a service running as SYSTEM, they can change the binary path to a payload and restart the service.

### Windows Filesystem and NTFS

**Key directories:**
```
C:\Windows\System32\    Core OS binaries, DLLs
C:\Windows\SysWOW64\    32-bit binaries on 64-bit Windows
C:\Windows\System32\config\    SAM, SECURITY, SYSTEM hives
C:\Windows\System32\drivers\etc\hosts    Static host resolution
C:\Users\Username\      User home directory
C:\Users\Username\AppData\Roaming\    Roaming profile data
C:\Users\Username\AppData\Local\      Local application data
C:\Program Files\       64-bit installed applications
C:\Program Files (x86)\ 32-bit installed applications
C:\ProgramData\         Application data for all users
C:\Temp or C:\Windows\Temp    Temporary files
```

**NTFS Alternate Data Streams (ADS):**
NTFS supports multiple data streams in a single file. The default stream is `filename:$DATA`. ADS allows hiding data:
```cmd
# Write data to an alternate stream
echo "hidden data" > file.txt:secret

# Read it back
more < file.txt:secret

# List streams
dir /r
streams.exe file.txt     # Sysinternals

# Malware using ADS:
type payload.exe > legitimate.txt:payload.exe
wscript legitimate.txt:payload.exe
```

**DLL Search Order — DLL Hijacking:**
When an application loads a DLL, Windows searches in this order (simplified):
1. Application directory
2. System directories (`System32`, `System`)
3. Windows directory
4. Current directory
5. Directories in `%PATH%`

If a DLL is missing and an earlier directory in the search order is writable by an attacker, they can place a malicious DLL there. The application loads the attacker's DLL with the application's privileges.

```powershell
# Find DLL hijacking opportunities with Process Monitor
# Filter on: Result = NAME NOT FOUND, Path ends with .dll
# Look for DLL searches in writable locations
```

### Windows Privilege Escalation Quick Reference

| Category | Technique | Key Check |
|----------|-----------|-----------|
| Service misconfig | Unquoted service path | `wmic service get name,pathname` |
| Service misconfig | Writable service binary | `icacls <service binary>` |
| Service misconfig | Weak service permissions | `accesschk.exe -uwcqv *` |
| AlwaysInstallElevated | MSI runs as SYSTEM | `reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer` + HKCU |
| Token privileges | SeImpersonatePrivilege | Check `whoami /priv` — Potato family exploits |
| Token privileges | SeBackupPrivilege | Read any file; dump SAM |
| Token privileges | SeRestorePrivilege | Write any file; replace binaries |
| Token privileges | SeTakeOwnershipPrivilege | Take ownership of any file |
| DLL hijacking | Missing DLL in writable path | Process Monitor |
| Credential in files | Unattended install files | `C:\Windows\Panther\Unattend.xml` |
| Credential in files | Config files | `*.config, *.xml, *.ini, *.txt` |
| Scheduled tasks | Writable task binary | `schtasks /query /fo LIST /v` |
| Kernel exploit | Old unpatched system | `systeminfo` + exploit suggester |

### Windows Command Line Essentials for Pentesters

```cmd
REM System information
systeminfo                     # OS version, hotfixes, hardware
whoami /all                    # Current user, privileges, group memberships
hostname                       # Computer name
ipconfig /all                  # Network configuration
netstat -ano                   # Active connections with PIDs
tasklist /v                    # Running processes
net user                       # List local users
net localgroup administrators  # Members of local administrators
net share                      # Shared resources
net use                        # Current network connections

REM File operations
dir /a /s C:\*.config          # Find all config files
findstr /si password *.txt *.xml *.ini   # Search files for passwords
type C:\path\to\file.txt
icacls C:\path                 # Show permissions

REM Registry
reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
reg query HKCU\Software\Microsoft\Internet Explorer\Main
```

```powershell
# PowerShell equivalents (preferred for scripting)
Get-LocalUser
Get-LocalGroupMember -Group "Administrators"
Get-Process | Sort CPU -desc | Select -first 20
Get-NetTCPConnection | Where State -eq "Listen"
Get-WmiObject Win32_Product | Select Name, Version  # Installed software
Get-ChildItem -Path C:\ -Include *.password* -Recurse -ErrorAction SilentlyContinue
```

---

## Active Directory — Introduction

Active Directory (AD) is Microsoft's directory service for Windows domain environments. It deserves its own deep module (Level 2), but you must understand the basics at Level 0 because AD environments are the default in enterprise internal pentests.

**Domain:** A logical grouping of objects (users, computers, groups, policies) that share a central authentication database and are managed as a unit. A domain has a DNS name (e.g., `corp.example.com`).

**Domain Controller (DC):** The server that hosts Active Directory Domain Services (AD DS). Stores the AD database (`ntds.dit`), handles authentication via Kerberos and NTLM, applies Group Policy, and replicates with other DCs.

**Forest:** The top-level container — a collection of one or more domains sharing a schema, configuration, and global catalog. The first domain created is the forest root domain. All domains in a forest implicitly trust each other (transitive trusts).

**Trust:** A relationship allowing authentication in one domain to be trusted by another. Types: one-way vs two-way, transitive vs non-transitive, external vs forest trust.

**Organizational Units (OUs):** Containers within a domain for organizing objects (users, computers, groups). Group Policy Objects (GPOs) can be linked to OUs, applying configuration to all objects within.

**Group Policy Objects (GPOs):** Policy settings applied to users or computers in the domain — password policies, software installation, script execution, firewall rules, etc. GPO misconfigurations are a significant attack surface.

**LDAP (Lightweight Directory Access Protocol):** The protocol used to query and modify AD. All AD queries use LDAP under the hood. Port 389 (LDAP) and 636 (LDAPS).

**Kerberos:** The primary authentication protocol in AD environments. Port 88. Replaces NTLM in modern environments (though NTLM still falls back). Kerberos is ticket-based — once authenticated, a user holds tickets granting access to services without re-entering passwords. The security of Kerberos is the foundation of attacks like Kerberoasting, Golden Ticket, and Pass-the-Ticket.

---

## Summary: OS Commands Every Pentester Must Know Cold

**Linux:**
```bash
id                              # Who am I?
whoami                          # Current user
cat /etc/passwd                 # User list
cat /etc/shadow                 # Password hashes (root only)
sudo -l                         # What can I sudo?
find / -perm -4000 2>/dev/null  # SUID files
find / -writable -type f 2>/dev/null  # Writable files
ps aux                          # Running processes
ss -tulpn                       # Listening ports
crontab -l && cat /etc/crontab  # Cron jobs
env                             # Environment variables
cat ~/.bash_history             # Command history
ls -la ~/.ssh/                  # SSH keys
```

**Windows:**
```cmd
whoami /all                    # User + privileges + groups
systeminfo                     # OS info, patches
ipconfig /all                  # Network
net user && net localgroup     # Users and groups
tasklist /v                    # Processes
netstat -ano                   # Connections
reg query HKLM\...\Run         # Autorun entries
dir /s /b *.xml *.ini *.config # Config files
findstr /si password *.txt     # Grep for passwords
```
