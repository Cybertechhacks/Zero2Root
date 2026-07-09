# Tools Reference

A quick-reference guide for tools used across all assessment types. Each section covers the tool's purpose, key usage patterns, and interview relevance.

---

## Navigation

| Category | Tools Covered |
|----------|--------------|
| [Recon Tools](01-recon-tools.md) | theHarvester, amass, subfinder, crt.sh, shodan, recon-ng |
| [Scanning Tools](02-scanning-tools.md) | Nmap, masscan, Nessus, nuclei, testssl.sh |
| [Web App Tools](03-web-tools.md) | Burp Suite, OWASP ZAP, gobuster, ffuf, sqlmap, nikto |
| [Network & Infra Tools](04-network-tools.md) | Wireshark, netcat, impacket, CrackMapExec, enum4linux, BloodHound |
| [Mobile Tools](05-mobile-tools.md) | apktool, jadx, MobSF, Frida, objection, ADB |

---

## Tool Selection by Assessment Type

| Assessment Type | Primary Tools |
|----------------|--------------|
| External recon | theHarvester, amass, shodan, crt.sh, Google dorks |
| External VA/PT | Nmap, Nessus/nuclei, testssl.sh, Burp Suite |
| Web application | Burp Suite, gobuster/ffuf, sqlmap, nuclei |
| Internal network | Nmap, CrackMapExec, enum4linux, impacket suite |
| Active Directory | BloodHound/SharpHound, impacket, Rubeus, CrackMapExec |
| Android mobile | apktool, jadx, MobSF, ADB, Frida, objection |
| iOS mobile | Frida, objection, class-dump, Ghidra/Hopper |
| Source code | Semgrep, Bandit, npm audit, dependency-check |
| Cloud (AWS/Azure) | ScoutSuite, Prowler, Pacu, az CLI, aws CLI |
| Config review | Nessus (authenticated), Lynis, CIS-CAT |
