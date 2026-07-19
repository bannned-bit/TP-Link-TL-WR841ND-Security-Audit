# TP-Link TL-WR841ND V11 — Command Injection PoC & Analysis

**PoC exploit:** Critical command injection in TP-Link TL-WR841ND V11 firmware (3.16.9 Build 150616). Allows root access via diagnostic ping. CVSS: 9.8.

> This repository contains a proof-of-concept (PoC) exploit script and an analysis of the vulnerability. It is provided for educational and authorized security testing only.

---

## Quick summary

- A Python PoC (exploit.py) demonstrates an OS command injection vulnerability in TP-Link TL-WR841ND V11 firmware's diagnostic functions (ping/traceroute web forms).
- Vulnerable endpoint(s): `/userRpm/PingIframeRpm.htm`, `/userRpm/DiagnosticRpm.htm`
- Vulnerable parameter: `ping_addr` (unsanitized user input used in a system ping command)
- Root cause: user input concatenated into a shell command and executed (e.g., via `popen()`/system call) without validation.
- Impact: Full root access on affected devices. Severity: CRITICAL (CVSS 9.8).

---

## Important legal & safety notice

Do NOT use this PoC against systems you do not own or do not have explicit written permission to test. Unauthorized use may violate local laws and can result in criminal or civil penalties.

This repository and the included scripts are intended for:
- Security researchers analyzing firmware vulnerabilities on devices they own.
- Network administrators testing and patching their own equipment.

If you are a vendor or administrator and you find this vulnerability in your environment, follow responsible disclosure guidelines and coordinate remediation.

---

## Files in this repository

- `exploit.py` — Main PoC exploit script (Python 3). Contains the full testing and exploitation workflow, banners, output formatting, and payloads used for confirmation.
- `README.md` — (this file) explains the vulnerability, how the PoC works, how to run it safely, and mitigation recommendations.

---

## How the PoC works (high level)

The PoC performs the following phases (implemented in `exploit.py`):

1. Reconnaissance — checks target reachability and looks for TP-Link web interface hints.
2. Authentication — attempts HTTP Basic authentication with default credentials (`admin:admin`) and sets headers/cookies.
3. Vulnerability scanning — probes diagnostic endpoints for the presence of a ping form and the `ping_addr` parameter.
4. Exploitation — injects commands by sending `;COMMAND;` as the `ping_addr` value. Semicolons terminate the ping command and cause additional shell commands to execute.
5. Result parsing — tries to parse the HTTP response (looking for JavaScript variables, `<pre>` blocks, or common Unix strings) to extract command output.

The script includes a set of test commands (id, hostname, uname -a, cat /etc/passwd, cat /etc/shadow, ifconfig, ps, cat /proc/version) to confirm exploitation and enumerate the target.

---

## Running the PoC (example)

Environment requirements:
- Python 3.8+
- `requests` library

Example usage (ONLY on targets you own/are authorized to test):

```bash
python3 exploit.py -t 192.168.0.1 -p 80 -u admin -P admin
```

The script will show a disclaimer and ask for confirmation before proceeding.

---

## Code analysis (exploit.py)

Overview:
- The PoC is a single-file Python program implementing a stateful HTTP session, default credentials, and a multi-step test/exploit flow.
- It is written to be user-friendly in a terminal (colorized output and banners).

Vulnerable pattern (identified in the firmware, not in this repo):
- The firmware builds a command string like `ping <user_input> timeout 5 times 3` via `sprintf()` and then calls `popen(cmd, "r")` without validating or sanitizing `user_input`.
- When the web form accepts `ping_addr` from the user and that value is inserted verbatim into a shell command, an attacker can inject shell metacharacters (e.g., `;`, `&&`) to run additional commands with the privileges of the process (typically root in embedded devices).

PoC injection technique used by script:
- The PoC sends `ping_addr=;<command>;` which relies on the firmware issuing a shell command where `;` acts as a command separator. That results in the included `<command>` being executed by the shell.

Response parsing and limitations:
- The script tries multiple heuristics to extract command output: JavaScript variables (`g_result`), `<pre>` blocks, and scanning HTML for common Unix strings (e.g., `uid=`, `root:`, `Linux`, `httpd`, `busybox`).
- Some firmware responses will not reflect command output (e.g., commands that do not print or when output is redirected), so the PoC may not reliably show output even if commands executed.
- The PoC assumes HTTP (not HTTPS) and Basic auth; if the device uses a different auth method or CSRF protections, the flow might need adaptation.

Limitations and false positives:
- The script's success heuristics are simple and can yield false negatives (command executed but no output captured) or false positives if unrelated text matches heuristics.
- Network intermediaries or WAFs could block or sanitize payloads.

---

## Detection and Indicators of Compromise (IoCs)

- Unexpected `ping` or `traceroute` web requests with unusual characters in `ping_addr` (e.g., semicolons, backticks, pipes).
- Shell command invocations from the web process in system logs (if available) that include `;` or sequences like `;id;`.
- Unusual outgoing network connections initiated by the device (reverse shells, DNS exfiltration).
- Presence of unknown accounts or modified `/etc/passwd` or `/etc/shadow`.

Suggested IDS signature (example):
- Detect HTTP POSTs to `/userRpm/PingIframeRpm.htm` or `/userRpm/DiagnosticRpm.htm` where `ping_addr` contains characters like `;` or `|` or `&&`.

---

## Mitigation and recommended fixes (for vendors / maintainers)

1. Input validation/whitelisting:
   - Accept only valid IP addresses or domain names for diagnostic fields.
   - Use strict validation and reject characters `;`, `|`, `&`, backticks, and other shell metacharacters.

2. Avoid invoking shell interpreters with user-controlled input:
   - Use exec-family functions with argument vectors (e.g., `execv`, `execlp`) instead of building a shell command string.
   - If using system/popen is necessary, sanitize and escape input thoroughly or better, validate before use.

3. Principle of least privilege:
   - Ensure web interface runs with minimum required privileges; avoid running as root.

4. Authentication, CSRF, and access control:
   - Enforce strong admin passwords and avoid shipping devices with default credentials.
   - Implement CSRF protections for forms that issue system commands.

5. Patch and update firmware:
   - Release firmware that fixes the command-building code and distributes updates to users.

---

## Responsible disclosure

If you discover this issue on a device you do not own, follow responsible disclosure practices:

1. Do not exploit beyond necessary verification.
2. Contact the vendor's security contact or CERT/CSIRT with details.
3. Provide reproduction steps and suggested mitigations.
4. Coordinate public disclosure with the vendor to allow time for patches.

---

## Contributing

Contributions should focus on:
- Improving detection rules and signatures (IDS/IPS rules).
- Adding safer parsing techniques or authenticated test modes.
- Documenting mitigation/patch status and CVE references when available.

Before submitting a pull request, remove any non-essential exploit code or ensure examples are safe and cannot be run accidentally.

---

## License

This repository does not include an explicit open-source license. By default, all rights are reserved to the repository owner. If you are the repository owner and want to add a license, consider an appropriate license for security research material (e.g., MIT).

---

## Contact / Credits

- Original PoC author mentioned in the script header: "Matad0r "
- Repo description: "PoC exploit : Critical command injection in TP-Link TL-WR841ND V11 firmware. Allows root access via diagnostic ping. CVSS 9.8. Firmware security research."

