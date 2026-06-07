"""
Command Mapper - Windows-Only Command Mapping Logic

Handles the conversion of natural language to Windows CMD/PowerShell commands
using AI and fallback pattern matching.
"""

import os
import re
import platform
import json
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from difflib import get_close_matches, SequenceMatcher

try:
    from groq import Groq
except ImportError:
    Groq = None

@dataclass
class CommandMapping:
    """Represents a command mapping with confidence score."""
    command: str
    confidence: float
    description: str
    platform: str = "windows"

class CommandMapper:
    """Maps natural language to Windows system commands using AI and fallback rules."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.system = "windows"
        
        if Groq and (api_key or os.getenv("GROQ_API_KEY")):
            self.groq_client = Groq(api_key=api_key or os.getenv("GROQ_API_KEY"))
            self.use_ai = True
        else:
            self.groq_client = None
            self.use_ai = False
            print("Warning: Groq not available. Using fallback pattern matching only.")
        
        self.fallback_patterns = self._load_fallback_patterns()
        self.app_mappings = {}
    
    def map_to_command(self, user_input: str) -> Tuple[Optional[str], Optional[str]]:
        user_input = user_input.strip().lower()
        
        # 1. Check local mappings first
        local_command = self._fallback_map_command(user_input)
        if local_command:
            return local_command, "local"
            
        # 2. If not available locally, use AI API
        if self.use_ai:
            ai_command = self._ai_map_command(user_input)
            if ai_command:
                return ai_command, "api"
                
        return None, None
    
    def map_to_command_with_correction(self, user_input: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        user_input = user_input.strip().lower()
        exact_command, source = self.map_to_command(user_input)
        if exact_command:
            return exact_command, user_input, None, source
        
        corrected_input = self._correct_spelling(user_input)
        if corrected_input and corrected_input != user_input:
            corrected_command, source = self.map_to_command(corrected_input)
            if corrected_command:
                return corrected_command, user_input, corrected_input, source
                
        return None, user_input, None, None
    
    def _correct_spelling(self, user_input: str) -> Optional[str]:
        command_keywords = {
            "start": ["sttart", "sart", "satrt"], "stop": ["sttop", "stp"],
            "check": ["chek", "chck"], "status": ["sttus", "staus"],
            "memory": ["memry", "memmory"], "ram": ["rm"],
            "cpu": ["cuppu"], "disk": ["dsk"], "network": ["netwrok", "netwrk"],
            "wifi": ["wfi"], "port": ["prt"], "process": ["proces", "prcess"],
            "file": ["fil"], "folder": ["flder", "foler"],
            "copy": ["cpy", "coppy"], "move": ["mov", "mve"],
            "delete": ["delte", "dlete"], "rename": ["renme", "renam"],
            "create": ["creat", "crate"], "open": ["opn", "ope"],
            "search": ["serch", "seach"], "list": ["lst", "lits"],
            "shutdown": ["shutdwn", "shutdn"], "restart": ["resttart", "restrt"],
            "clear": ["clr", "cler"], "system": ["systm", "sysem"],
            "chrome": ["chrm", "chome"], "firefox": ["firef", "firefx"],
            "notepad": ["notepd"], "vscode": ["vscd", "vsc"],
            "weather": ["wether", "weathr"], "time": ["tim", "tme"],
            "date": ["dat", "dte"], "calculator": ["calc", "calcltr"],
            "taskmanager": ["taskmgr", "tskmgr"],
        }
        words = user_input.split()
        corrected_words = []
        for word in words:
            if word in command_keywords:
                corrected_words.append(word)
                continue
            best_match = None
            best_ratio = 0.8
            for correct_word, variations in command_keywords.items():
                for variation in [correct_word] + variations:
                    if len(word) >= 3 and len(variation) >= 3:
                        similarity = SequenceMatcher(None, word, variation).ratio()
                        if similarity > best_ratio:
                            best_ratio = similarity
                            best_match = correct_word
            corrected_words.append(best_match if best_match else word)
        corrected = " ".join(corrected_words)
        return corrected if corrected != user_input else None
    
    def _ai_map_command(self, user_input: str) -> Optional[str]:
        try:
            if not self.groq_client:
                return None
            prompt = self._get_system_prompt()
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Convert this to a Windows command: {user_input}"}
                ],
                max_tokens=100, temperature=0.1
            )
            command = response.choices[0].message.content.strip()
            if self._is_safe_command(command):
                return command
            print(f"AI generated unsafe command: {command}")
            return None
        except Exception as e:
            print(f"AI mapping failed: {e}")
            return None
    
    def _get_system_prompt(self) -> str:
        return """You are a Windows command line assistant. Convert natural language to Windows CMD or PowerShell commands.
Rules:
1. Return ONLY the command, no explanations
2. Use ONLY Windows CMD or PowerShell commands
3. Use 'start' for opening applications and URLs
4. NEVER use Linux/macOS commands (ls, rm, grep, open -a, etc.)
5. Be safe - avoid dangerous commands
Examples:
- "open chrome" -> start chrome
- "list files" -> dir
- "create file test.txt" -> echo. > test.txt
- "check wifi" -> netsh wlan show interfaces
- "show date" -> date /t
- "kill process 1234" -> taskkill /PID 1234 /F"""
    
    def _fallback_map_command(self, user_input: str) -> Optional[str]:
        for pattern, command in self.fallback_patterns.items():
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                if callable(command):
                    return command(match)
                return command
        return None
    
    def _load_fallback_patterns(self) -> Dict:
        return {
            # System Identity
            r"^ver$": "ver",
            r"(check|show|what)\s*(is\s+)?(my\s+)?windows\s+version": "ver",
            r"^hostname$": "hostname",
            r"^whoami$": "whoami",
            
            # Date & Time
            r"^date$": "date /t",
            r"show.*date": "date /t",
            r"what.*date": "date /t",
            r"display.*date": "date /t",
            r"today.*date": "date /t",
            r"^time$": "time /t",
            r"current.*time": "time /t",
            r"what.*time": "time /t",
            r"display.*time": "time /t",
            
            # Screen & Console
            r"^cls$": "cls",
            r"clear\s+the\s+screen": "cls",
            r"^title\s+my\s+cmd\s+window$": "title My CMD Window",
            
            # Directory Listing
            r"^dir$": "dir",
            r"list\s*(all\s+)?files": "dir",
            r"(i\s+want\s+to\s+)?list\s+files": "dir",
            r"show\s*(all\s+)?files": "dir",
            
            # Networking
            r"^ipconfig$": "ipconfig",
            r"network.*status": "ipconfig",
            r"ip\s*address": "ipconfig",
            r"^netstat$": "netstat",
            r"check.*ports": "netstat",
            r"^getmac$": "getmac",
            r"^nslookup\s+google\.com$": "nslookup google.com",
            r"^ping\s+localhost$": "ping localhost",
            
            # System Information & Processes
            r"^systeminfo$": "systeminfo",
            r"check\s+system\s+info": "systeminfo",
            r"^tasklist$": "tasklist",
            r"list.*processes": "tasklist",
            r"show.*processes": "tasklist",
            r"^driverquery$": "driverquery",
            
            # Environment & Configuration
            r"^set$": "set",
            r"environment\s+variables": "set",
            r"^path$": "path",
            r"^assoc$": "assoc",
            
            # Help
            r"list\s*(all\s+)?commands": "echo Use 'list all commands' in the chat to see available commands",
            r"show\s*(all\s+)?commands": "echo Use 'show all commands' in the chat to see available commands",
            r"help\s*commands": "echo Use 'help commands' in the chat to see available commands",
        }
    

    def _is_safe_command(self, command: str) -> bool:
        dangerous = [
            r"format\s+[a-zA-Z]:", r"del\s+/[sfq].*[a-zA-Z]:\\",
            r"rmdir\s+/s\s+/q\s+[a-zA-Z]:\\", r"rd\s+/s\s+/q\s+[a-zA-Z]:\\",
            r"reg\s+delete", r"bcdedit",
        ]
        for p in dangerous:
            if re.search(p, command, re.IGNORECASE):
                return False
        return True
    
    def get_available_commands(self) -> List[str]:
        commands = []
        for pattern, cmd in self.fallback_patterns.items():
            if not callable(cmd):
                commands.append(cmd)
        return sorted(list(set(commands)))
    
    def get_commands_by_category(self) -> Dict[str, List[Dict[str, str]]]:
        categories = {
            "System Identity": [
                {"example": "ver", "description": "Displays the current Windows OS version number", "command": "ver"},
                {"example": "hostname", "description": "Displays the name of the current computer on the network", "command": "hostname"},
                {"example": "whoami", "description": "Displays the currently logged-in user's domain and username", "command": "whoami"},
            ],
            "Date & Time": [
                {"example": "date /t", "description": "Displays the current system date without prompting to change it", "command": "date /t"},
                {"example": "time /t", "description": "Displays the current system time without prompting to change it", "command": "time /t"},
            ],
            "Screen & Console": [
                {"example": "cls", "description": "Clears all text from the Command Prompt screen", "command": "cls"},
                {"example": "title My CMD Window", "description": "Sets a custom title for the CMD window's title bar", "command": "title My CMD Window"},
            ],
            "Directory Listing": [
                {"example": "dir", "description": "Lists all files and subdirectories in the current directory", "command": "dir"},
            ],
            "Networking": [
                {"example": "ipconfig", "description": "Displays IP address, subnet mask, and default gateway for all adapters", "command": "ipconfig"},
                {"example": "netstat", "description": "Displays active TCP connections, listening ports, and network statistics", "command": "netstat"},
                {"example": "getmac", "description": "Displays the MAC address of all network adapters", "command": "getmac"},
                {"example": "nslookup google.com", "description": "Queries the DNS server to find the IP address of a domain", "command": "nslookup google.com"},
                {"example": "ping localhost", "description": "Tests network connectivity by sending ICMP echo requests", "command": "ping localhost"},
            ],
            "System Information & Processes": [
                {"example": "systeminfo", "description": "Displays detailed system configuration (OS, hardware, network)", "command": "systeminfo"},
                {"example": "tasklist", "description": "Displays all currently running processes with PID and memory usage", "command": "tasklist"},
                {"example": "driverquery", "description": "Displays a list of all installed hardware device drivers", "command": "driverquery"},
            ],
            "Environment & Configuration": [
                {"example": "set", "description": "Displays all current environment variables and their values", "command": "set"},
                {"example": "path", "description": "Displays the system PATH variable used to locate executables", "command": "path"},
                {"example": "assoc", "description": "Displays file extension associations (which program opens each type)", "command": "assoc"},
            ],
        }
        return categories