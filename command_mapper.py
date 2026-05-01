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
        self.app_mappings = {
            "chrome": {"windows": "start chrome"},
            "firefox": {"windows": "start firefox"},
            "vscode": {"windows": "code"},
            "edge": {"windows": "start msedge"},
            "notepad": {"windows": "notepad"},
            "calculator": {"windows": "calc"},
        }
    
    def map_to_command(self, user_input: str) -> Optional[str]:
        user_input = user_input.strip().lower()
        if self.use_ai:
            ai_command = self._ai_map_command(user_input)
            if ai_command:
                return ai_command
        return self._fallback_map_command(user_input)
    
    def map_to_command_with_correction(self, user_input: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        user_input = user_input.strip().lower()
        exact_command = self.map_to_command(user_input)
        if exact_command:
            return exact_command, user_input, None
        corrected_input = self._correct_spelling(user_input)
        if corrected_input and corrected_input != user_input:
            corrected_command = self.map_to_command(corrected_input)
            if corrected_command:
                return corrected_command, user_input, corrected_input
        return None, user_input, None
    
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
            # File operations
            r"(create|make)\s+(a\s+)?(new\s+)?file\s+(called\s+)?(\S+)": lambda m: f"echo. > {m.group(5)}",
            r"(i\s+want\s+to\s+)?create\s+(a\s+)?file": "echo. > newfile.txt",
            r"list\s*(all\s+)?files": "dir",
            r"(i\s+want\s+to\s+)?list\s+files": "dir",
            r"show\s*(all\s+)?files": "dir",
            r"(create|make)\s+(a\s+)?(new\s+)?folder\s+(called\s+)?(\S+)": lambda m: f"mkdir {m.group(5)}",
            r"(i\s+want\s+to\s+)?create\s+(a\s+)?folder": "mkdir NewFolder",
            r"(remove|delete)\s+folder\s+(\S+)": lambda m: f"rmdir {m.group(2)}",
            r"(i\s+want\s+to\s+)?delete\s+(a\s+)?folder": "rmdir FolderName",
            r"(remove|delete)\s+file\s+(\S+)": lambda m: f"del {m.group(2)}",
            r"(i\s+want\s+to\s+)?delete\s+(a\s+)?file": "del filename.txt",
            r"copy\s+file\s+(\S+)\s+to\s+(\S+)": lambda m: f"copy {m.group(1)} {m.group(2)}",
            r"move\s+file\s+(\S+)\s+to\s+(\S+)": lambda m: f"move {m.group(1)} {m.group(2)}",
            r"rename\s+(\S+)\s+to\s+(\S+)": lambda m: f"rename {m.group(1)} {m.group(2)}",
            r"current\s*directory": "cd",
            r"where\s+am\s+i": "cd",
            # Port operations
            r"list.*port.*(\d{4,5})": lambda m: f"netstat -ano | findstr :{m.group(1)}",
            r"kill.*port.*(\d{4,5})": lambda m: f"for /f \"tokens=5\" %a in ('netstat -ano ^| findstr :{m.group(1)}') do taskkill /PID %a /F",
            r"find.*port.*(\d{4,5})": lambda m: f"netstat -ano | findstr :{m.group(1)}",
            r"check.*ports": "netstat -an",
            # Applications
            r"open\s+chrome": "start chrome",
            r"open\s+firefox": "start firefox",
            r"open\s+edge": "start msedge",
            r"open\s+vscode": "code",
            r"start\s+notepad": "notepad",
            r"open\s+notepad": "notepad",
            r"open\s+calculator": "calc",
            r"open\s+task\s*manager": "taskmgr",
            r"open\s+paint": "mspaint",
            r"open\s+explorer": "explorer",
            r"open\s+control\s+panel": "control",
            r"open\s+cmd": "start cmd",
            r"open\s+powershell": "start powershell",
            # Web services
            r"(open|launch|go\s+to)\s+youtube": "start https://www.youtube.com",
            r"search\s+youtube\s+for\s+(.+)": lambda m: f'start https://www.youtube.com/results?search_query={m.group(1).replace(" ", "+")}',
            r"(open|launch|check)\s+gmail": "start https://mail.google.com",
            r"(open|launch|go\s+to)\s+facebook": "start https://www.facebook.com",
            r"(open|launch|go\s+to)\s+instagram": "start https://www.instagram.com",
            r"(open|launch|go\s+to)\s+twitter": "start https://twitter.com",
            r"(open|launch|play)\s+spotify": "start https://open.spotify.com",
            r"(open|launch|go\s+to)\s+reddit": "start https://www.reddit.com",
            r"(open|launch)\s+whatsapp\s+web": "start https://web.whatsapp.com",
            r"search.*weather.*in\s+([a-zA-Z\s]+)": lambda m: f'start https://www.google.com/search?q=weather+in+{m.group(1).replace(" ", "+")}',
            r"search.*for\s+([a-zA-Z\s]+)": lambda m: f'start https://www.google.com/search?q={m.group(1).replace(" ", "+")}',
            r"google\s+([a-zA-Z\s]+)": lambda m: f'start https://www.google.com/search?q={m.group(1).replace(" ", "+")}',
            # System info
            r"check\s+system\s+info": "systeminfo",
            r"check\s+cpu\s+usage": "wmic cpu get loadpercentage",
            r"check\s+(memory|ram)\s+(usage|status)": "systeminfo | findstr /C:\"Total Physical Memory\" /C:\"Available Physical Memory\"",
            r"disk\s*space": "wmic logicaldisk get size,freespace,caption",
            r"check\s+disk": "wmic logicaldisk get size,freespace,caption",
            # Network
            r"connect\s+(to\s+)?wifi\s+(\S+)": lambda m: f'netsh wlan connect name="{m.group(2)}"',
            r"disconnect\s+(from\s+)?wifi": "netsh wlan disconnect",
            r"list\s+available\s+wifi": "netsh wlan show networks",
            r"check.*wifi": "netsh wlan show interfaces",
            r"wifi.*status": "netsh wlan show interfaces",
            r"network.*status": "ipconfig",
            r"ip\s*address": "ipconfig",
            r"flush\s+dns": "ipconfig /flushdns",
            # Date & Time
            r"show.*date": "date /t",
            r"what.*date": "date /t",
            r"current.*time": "time /t",
            r"what.*time": "time /t",
            r"display.*date": "date /t",
            r"display.*time": "time /t",
            r"today.*date": "date /t",
            r"check\s+date\s+and\s+time": "date /t & time /t",
            # Process management
            r"list.*processes": "tasklist",
            r"show.*processes": "tasklist",
            r"kill.*process.*(\d+)": lambda m: f"taskkill /PID {m.group(1)} /F",
            r"list.*services": "net start",
            # System control
            r"shutdown\s+(my\s+)?computer": "shutdown /s /t 0",
            r"restart\s+(my\s+)?(pc|computer)": "shutdown /r /t 0",
            r"sleep\s+(my\s+)?computer": "rundll32.exe powrprof.dll,SetSuspendState 0,1,0",
            r"lock\s+(my\s+)?(pc|computer|screen)": "rundll32.exe user32.dll,LockWorkStation",
            r"clear\s+the\s+screen": "cls",
            # Help
            r"list\s*(all\s+)?commands": "echo Use 'list all commands' in the chat to see available commands",
            r"show\s*(all\s+)?commands": "echo Use 'show all commands' in the chat to see available commands",
            r"help\s*commands": "echo Use 'help commands' in the chat to see available commands",
            # Windows version
            r"(check|show|what)\s*(is\s+)?(my\s+)?windows\s+version": "winver",
            r"environment\s+variables": "set",
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
            "File Operations": [
                {"example": "create a file called test.txt", "description": "Create a new file", "command": "echo. > test.txt"},
                {"example": "list files", "description": "List files in current directory", "command": "dir"},
                {"example": "create folder called MyFolder", "description": "Create a new folder", "command": "mkdir MyFolder"},
                {"example": "delete folder MyFolder", "description": "Remove a folder", "command": "rmdir MyFolder"},
                {"example": "delete file test.txt", "description": "Delete a file", "command": "del test.txt"},
                {"example": "copy file a.txt to b.txt", "description": "Copy a file", "command": "copy a.txt b.txt"},
                {"example": "move file a.txt to folder\\", "description": "Move a file", "command": "move a.txt folder\\"},
                {"example": "rename old.txt to new.txt", "description": "Rename a file", "command": "rename old.txt new.txt"},
                {"example": "where am i", "description": "Show current directory", "command": "cd"},
            ],
            "System Information": [
                {"example": "check system info", "description": "Show system information", "command": "systeminfo"},
                {"example": "check cpu usage", "description": "Check CPU load", "command": "wmic cpu get loadpercentage"},
                {"example": "check RAM status", "description": "Check memory usage", "command": "systeminfo | findstr /C:\"Total Physical Memory\""},
                {"example": "check disk space", "description": "Show disk space", "command": "wmic logicaldisk get size,freespace,caption"},
                {"example": "check Windows version", "description": "Show Windows version", "command": "winver"},
                {"example": "environment variables", "description": "List environment variables", "command": "set"},
            ],
            "Network & WiFi": [
                {"example": "check wifi status", "description": "Show WiFi interface info", "command": "netsh wlan show interfaces"},
                {"example": "list available wifi networks", "description": "Scan WiFi networks", "command": "netsh wlan show networks"},
                {"example": "connect to wifi MyNetwork", "description": "Connect to a WiFi network", "command": "netsh wlan connect name=\"MyNetwork\""},
                {"example": "disconnect from wifi", "description": "Disconnect WiFi", "command": "netsh wlan disconnect"},
                {"example": "check network status", "description": "Show IP configuration", "command": "ipconfig"},
                {"example": "flush dns", "description": "Flush DNS cache", "command": "ipconfig /flushdns"},
            ],
            "Port Operations": [
                {"example": "list port 8085", "description": "Find process on a port", "command": "netstat -ano | findstr :8085"},
                {"example": "check ports", "description": "Show all ports", "command": "netstat -an"},
                {"example": "kill port 8085", "description": "Kill process on a port", "command": "Dynamic command"},
            ],
            "Applications": [
                {"example": "open chrome", "description": "Open Google Chrome", "command": "start chrome"},
                {"example": "open firefox", "description": "Open Firefox", "command": "start firefox"},
                {"example": "open edge", "description": "Open Microsoft Edge", "command": "start msedge"},
                {"example": "open vscode", "description": "Open VS Code", "command": "code"},
                {"example": "open notepad", "description": "Open Notepad", "command": "notepad"},
                {"example": "open calculator", "description": "Open Calculator", "command": "calc"},
                {"example": "open task manager", "description": "Open Task Manager", "command": "taskmgr"},
                {"example": "open paint", "description": "Open Paint", "command": "mspaint"},
                {"example": "open explorer", "description": "Open File Explorer", "command": "explorer"},
                {"example": "open control panel", "description": "Open Control Panel", "command": "control"},
            ],
            "Web Services": [
                {"example": "open youtube", "description": "Open YouTube", "command": "start https://www.youtube.com"},
                {"example": "open gmail", "description": "Open Gmail", "command": "start https://mail.google.com"},
                {"example": "open facebook", "description": "Open Facebook", "command": "start https://www.facebook.com"},
                {"example": "search for weather in London", "description": "Search Google", "command": "Dynamic command"},
                {"example": "google machine learning", "description": "Google search", "command": "Dynamic command"},
            ],
            "Process Management": [
                {"example": "list processes", "description": "List running processes", "command": "tasklist"},
                {"example": "kill process 1234", "description": "Kill a process by PID", "command": "taskkill /PID 1234 /F"},
                {"example": "list services", "description": "List running services", "command": "net start"},
            ],
            "System Control": [
                {"example": "shutdown my computer", "description": "Shutdown PC", "command": "shutdown /s /t 0"},
                {"example": "restart my computer", "description": "Restart PC", "command": "shutdown /r /t 0"},
                {"example": "lock my computer", "description": "Lock screen", "command": "rundll32.exe user32.dll,LockWorkStation"},
                {"example": "sleep computer", "description": "Put PC to sleep", "command": "rundll32.exe powrprof.dll,SetSuspendState 0,1,0"},
                {"example": "clear the screen", "description": "Clear console", "command": "cls"},
            ],
            "Date & Time": [
                {"example": "show date", "description": "Show current date", "command": "date /t"},
                {"example": "what time is it", "description": "Show current time", "command": "time /t"},
                {"example": "check date and time", "description": "Show date and time", "command": "date /t & time /t"},
            ],
        }
        return categories