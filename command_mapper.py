"""
Command Mapper - AI Integration and Command Mapping Logic

Handles the conversion of natural language to system commands using AI
and fallback pattern matching.
"""

import os
import re
import platform
import json
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from difflib import get_close_matches

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
    platform: str = "all"

class CommandMapper:
    """Maps natural language to system commands using AI and fallback rules."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.system = platform.system().lower()
        
        # Initialize Groq if available
        if Groq and (api_key or os.getenv("GROQ_API_KEY")):
            self.groq_client = Groq(api_key=api_key or os.getenv("GROQ_API_KEY"))
            self.use_ai = True
        else:
            self.groq_client = None
            self.use_ai = False
            print("Warning: Groq not available. Using fallback pattern matching only.")
        
        # Load fallback patterns
        self.fallback_patterns = self._load_fallback_patterns()
        
        # Common app mappings
        self.app_mappings = {
            "chrome": {
                "darwin": 'open -a "Google Chrome"',
                "windows": "start chrome",
                "linux": "google-chrome"
            },
            "firefox": {
                "darwin": 'open -a "Firefox"',
                "windows": "start firefox",
                "linux": "firefox"
            },
            "vscode": {
                "darwin": 'open -a "Visual Studio Code"',
                "windows": "code",
                "linux": "code"
            },
            "safari": {
                "darwin": 'open -a "Safari"',
                "windows": "start safari",
                "linux": "safari"
            }
        }
    
    def map_to_command(self, user_input: str) -> Optional[str]:
        """
        Map natural language input to a system command.
        
        Args:
            user_input: Natural language command
            
        Returns:
            System command string or None if mapping failed
        """
        user_input = user_input.strip().lower()
        
        # Try AI mapping first
        if self.use_ai:
            ai_command = self._ai_map_command(user_input)
            if ai_command:
                return ai_command
        
        # Fallback to pattern matching
        fallback_command = self._fallback_map_command(user_input)
        if fallback_command:
            return fallback_command
        
        return None
    
    def map_to_command_with_correction(self, user_input: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Map natural language input to a system command with spell correction.
        
        Args:
            user_input: Natural language command
            
        Returns:
            Tuple of (corrected_command, original_input, suggested_correction)
        """
        user_input = user_input.strip().lower()
        
        # First try exact match
        exact_command = self.map_to_command(user_input)
        if exact_command:
            return exact_command, user_input, None
        
        # Try spell correction
        corrected_input = self._correct_spelling(user_input)
        if corrected_input and corrected_input != user_input:
            corrected_command = self.map_to_command(corrected_input)
            if corrected_command:
                return corrected_command, user_input, corrected_input
        
        return None, user_input, None
    
    def _correct_spelling(self, user_input: str) -> Optional[str]:
        """
        Correct spelling mistakes in user input.
        
        Args:
            user_input: User input with potential spelling mistakes
            
        Returns:
            Corrected input or None if no correction found
        """
        # Known command keywords and their variations
        command_keywords = {
            # Redis commands
            "redis": ["redis", "reddis", "reds"],
            "sentinel": ["sentinel", "snetinel", "sental", "snetal", "snatel"],
            "server": ["server", "srever", "srvr"],
            "start": ["start", "sttart", "sart", "satrt"],
            "stop": ["stop", "sttop", "stp"],
            "restart": ["restart", "resttart", "restrt"],
            
            # Common system commands
            "check": ["check", "chek", "chck"],
            "status": ["status", "sttus", "staus"],
            "memory": ["memory", "memry", "memmory"],
            "ram": ["ram", "rm"],
            "cpu": ["cpu", "cuppu"],
            "disk": ["disk", "dsk"],
            "network": ["network", "netwrok", "netwrk"],
            "wifi": ["wifi", "wifi", "wifi"],
            "port": ["port", "prt"],
            "process": ["process", "proces", "prcess"],
            "file": ["file", "fil"],
            "folder": ["folder", "flder", "foler"],
            "copy": ["copy", "cpy", "coppy"],
            "move": ["move", "mov", "mve"],
            "delete": ["delete", "delte", "dlete"],
            "rename": ["rename", "renme", "renam"],
            "create": ["create", "creat", "crate"],
            "open": ["open", "opn", "ope"],
            "search": ["search", "serch", "seach"],
            "google": ["google", "googl", "gogle"],
            "youtube": ["youtube", "youtub", "yutube"],
            "gmail": ["gmail", "gmal", "gmil"],
            "facebook": ["facebook", "facebok", "fcebook"],
            "twitter": ["twitter", "twtter", "twiter"],
            "instagram": ["instagram", "instgram", "instagrm"],
            "spotify": ["spotify", "spotfy", "spotif"],
            "reddit": ["reddit", "redit", "redd"],
            "whatsapp": ["whatsapp", "whatsap", "whatspp"],
            "shutdown": ["shutdown", "shutdwn", "shutdn"],
            "restart": ["restart", "resttart", "restrt"],
            "clear": ["clear", "clr", "cler"],
            "system": ["system", "systm", "sysem"],
            "info": ["info", "inf", "infor"],
            "usage": ["usage", "usge", "usag"],
            "connect": ["connect", "conect", "connct"],
            "disconnect": ["disconnect", "disconect", "disconnct"],
            "list": ["list", "lst", "lits"],
            "available": ["available", "availble", "availabl"],
            "networks": ["networks", "netwrks", "netwks"],
            "calculator": ["calculator", "calc", "calcltr"],
            "notepad": ["notepad", "notepd", "notepd"],
            "chrome": ["chrome", "chrm", "chome"],
            "firefox": ["firefox", "firef", "firefx"],
            "safari": ["safari", "safri", "safr"],
            "vscode": ["vscode", "vscd", "vsc"],
            "weather": ["weather", "wether", "weathr"],
            "time": ["time", "tim", "tme"],
            "date": ["date", "dat", "dte"],
        }
        
        words = user_input.split()
        corrected_words = []
        
        for word in words:
            # Check if word needs correction
            if word in command_keywords:
                corrected_words.append(word)
                continue
            
            # Find the best match for this word
            best_match = None
            best_ratio = 0.8  # Minimum similarity threshold
            
            for correct_word, variations in command_keywords.items():
                # Check against the correct word and its variations
                all_variations = [correct_word] + variations
                for variation in all_variations:
                    if len(word) >= 3 and len(variation) >= 3:  # Only correct words with 3+ characters
                        similarity = self._string_similarity(word, variation)
                        if similarity > best_ratio:
                            best_ratio = similarity
                            best_match = correct_word
            
            if best_match:
                corrected_words.append(best_match)
            else:
                corrected_words.append(word)
        
        corrected_input = " ".join(corrected_words)
        return corrected_input if corrected_input != user_input else None
    
    def _string_similarity(self, a: str, b: str) -> float:
        """
        Calculate string similarity using difflib.
        
        Args:
            a: First string
            b: Second string
            
        Returns:
            Similarity ratio (0.0 to 1.0)
        """
        from difflib import SequenceMatcher
        return SequenceMatcher(None, a, b).ratio()
    
    def _ai_map_command(self, user_input: str) -> Optional[str]:
        """Use AI to map command."""
        try:
            system_prompt = self._get_system_prompt()
            
            if not self.groq_client:
                return None

            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Convert this to a system command: {user_input}"}
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            command = response.choices[0].message.content.strip()
            
            # Validate the command
            if self._is_safe_command(command):
                return command
            else:
                print(f"AI generated unsafe command: {command}")
                return None
                
        except Exception as e:
            print(f"AI mapping failed: {e}")
            return None
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for AI."""
        return f"""
You are a command line assistant that converts natural language to system commands.
Current platform: {self.system}

Rules:
1. Return ONLY the command, no explanations
2. Use platform-appropriate commands
3. For macOS, use 'open -a' for applications
4. For Windows, use 'start' for applications
5. For Linux, use direct command names
6. For web searches, return a command that opens the browser
7. Be safe - avoid dangerous commands like 'rm -rf /'

Examples:
- "open chrome" → {self.app_mappings.get('chrome', {}).get(self.system, 'open -a "Google Chrome"')}
- "list ports with 8085" → lsof -i tcp:8085
- "kill port 8085" → kill -9 $(lsof -t -i tcp:8085)
- "search for weather" → open "https://www.google.com/search?q=weather"
- "show date" → date
- "check wifi" → networksetup -getinfo Wi-Fi (macOS) or ipconfig (Windows) or iwconfig (Linux)
"""
    
    def _fallback_map_command(self, user_input: str) -> Optional[str]:
        """Use pattern matching as fallback."""
        for pattern, mapping in self.fallback_patterns.items():
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                command = mapping.get(self.system, mapping.get("all"))
                if callable(command):
                    return command(match)
                elif command:
                    return command
        return None
    
    def _load_fallback_patterns(self) -> Dict[str, Dict[str, str]]:
        """Load fallback pattern mappings."""
        return {
            # Port operations
            r"list.*port.*(\d{4,5})": {
                "all": lambda m: f"lsof -i tcp:{m.group(1)}"
            },
            r"kill.*port.*(\d{4,5})": {
                "all": lambda m: f"kill -9 $(lsof -t -i tcp:{m.group(1)})"
            },
            r"find.*port.*(\d{4,5})": {
                "all": lambda m: f"lsof -i tcp:{m.group(1)}"
            },
            
            # File operations (from training data)
            r"copy\s+file\s+(\S+)\s+to\s+(\S+)": {
                "darwin": lambda m: f"cp {m.group(1)} {m.group(2)}",
                "windows": lambda m: f"copy {m.group(1)} {m.group(2)}",
                "linux": lambda m: f"cp {m.group(1)} {m.group(2)}"
            },
            r"move\s+file\s+(\S+)\s+to\s+(\S+)": {
                "darwin": lambda m: f"mv {m.group(1)} {m.group(2)}",
                "windows": lambda m: f"move {m.group(1)} {m.group(2)}",
                "linux": lambda m: f"mv {m.group(1)} {m.group(2)}"
            },
            r"rename\s+(\S+)\s+to\s+(\S+)": {
                "darwin": lambda m: f"mv {m.group(1)} {m.group(2)}",
                "windows": lambda m: f"rename {m.group(1)} {m.group(2)}",
                "linux": lambda m: f"mv {m.group(1)} {m.group(2)}"
            },
            r"(create|make)\s+(a\s+)?(new\s+)?folder\s+called\s+(\S+)": {
                "darwin": lambda m: f"mkdir {m.group(4)}",
                "windows": lambda m: f"mkdir {m.group(4)}",
                "linux": lambda m: f"mkdir {m.group(4)}"
            },
            r"(remove|delete)\s+folder\s+(\S+)": {
                "darwin": lambda m: f"rmdir {m.group(2)}",
                "windows": lambda m: f"rmdir {m.group(2)}",
                "linux": lambda m: f"rmdir {m.group(2)}"
            },
            
            # Application opening
            r"open.*chrome": {
                "darwin": 'open -a "Google Chrome"',
                "windows": "start chrome",
                "linux": "google-chrome"
            },
            r"open.*firefox": {
                "darwin": 'open -a "Firefox"',
                "windows": "start firefox",
                "linux": "firefox"
            },
            r"open.*vscode": {
                "darwin": 'open -a "Visual Studio Code"',
                "windows": "code",
                "linux": "code"
            },
            r"open.*safari": {
                "darwin": 'open -a "Safari"',
                "windows": "start safari",
                "linux": "safari"
            },
            r"start\s+notepad": {
                "darwin": "open -a TextEdit",
                "windows": "notepad",
                "linux": "gedit"
            },
            r"open\s+calculator": {
                "darwin": "open -a Calculator",
                "windows": "calc",
                "linux": "gnome-calculator"
            },
            
            # Web applications (from training data)
            r"(open|launch|go\s+to)\s+youtube": {
                "darwin": "open https://www.youtube.com",
                "windows": "start https://www.youtube.com",
                "linux": "xdg-open https://www.youtube.com"
            },
            r"search\s+youtube\s+for\s+(.+)": {
                "darwin": lambda m: f'open https://www.youtube.com/results?search_query={m.group(1).replace(" ", "+")}',
                "windows": lambda m: f'start https://www.youtube.com/results?search_query={m.group(1).replace(" ", "+")}',
                "linux": lambda m: f'xdg-open https://www.youtube.com/results?search_query={m.group(1).replace(" ", "+")}'
            },
            r"(open|launch|check)\s+gmail": {
                "darwin": "open https://mail.google.com",
                "windows": "start https://mail.google.com",
                "linux": "xdg-open https://mail.google.com"
            },
            r"(open|launch|go\s+to)\s+facebook": {
                "darwin": "open https://www.facebook.com",
                "windows": "start https://www.facebook.com",
                "linux": "xdg-open https://www.facebook.com"
            },
            r"(open|launch|go\s+to)\s+instagram": {
                "darwin": "open https://www.instagram.com",
                "windows": "start https://www.instagram.com",
                "linux": "xdg-open https://www.instagram.com"
            },
            r"(open|launch|go\s+to)\s+twitter": {
                "darwin": "open https://twitter.com",
                "windows": "start https://twitter.com",
                "linux": "xdg-open https://twitter.com"
            },
            r"(tweet|send\s+a\s+tweet)\s+[""'](.+)[""']": {
                "darwin": lambda m: f'open https://twitter.com/intent/tweet?text={m.group(2).replace(" ", "+")}',
                "windows": lambda m: f'start https://twitter.com/intent/tweet?text={m.group(2).replace(" ", "+")}',
                "linux": lambda m: f'xdg-open https://twitter.com/intent/tweet?text={m.group(2).replace(" ", "+")}'
            },
            r"(open|launch|play)\s+spotify": {
                "darwin": "open https://open.spotify.com",
                "windows": "start https://open.spotify.com",
                "linux": "xdg-open https://open.spotify.com"
            },
            r"search\s+spotify\s+for\s+(.+)": {
                "darwin": lambda m: f'open https://open.spotify.com/search/{m.group(1).replace(" ", "%20")}',
                "windows": lambda m: f'start https://open.spotify.com/search/{m.group(1).replace(" ", "%20")}',
                "linux": lambda m: f'xdg-open https://open.spotify.com/search/{m.group(1).replace(" ", "%20")}'
            },
            r"(open|launch|go\s+to)\s+reddit": {
                "darwin": "open https://www.reddit.com",
                "windows": "start https://www.reddit.com",
                "linux": "xdg-open https://www.reddit.com"
            },
            r"search\s+reddit\s+for\s+(.+)": {
                "darwin": lambda m: f'open https://www.reddit.com/search/?q={m.group(1).replace(" ", "+")}',
                "windows": lambda m: f'start https://www.reddit.com/search/?q={m.group(1).replace(" ", "+")}',
                "linux": lambda m: f'xdg-open https://www.reddit.com/search/?q={m.group(1).replace(" ", "+")}'
            },
            r"(open|launch)\s+whatsapp\s+web": {
                "darwin": "open https://web.whatsapp.com",
                "windows": "start https://web.whatsapp.com",
                "linux": "xdg-open https://web.whatsapp.com"
            },
            
            # Web searches
            r"search.*weather.*in\s+([a-zA-Z\s]+)": {
                "darwin": lambda m: f'open https://www.google.com/search?q=weather+in+{m.group(1).replace(" ", "+")}',
                "windows": lambda m: f'start https://www.google.com/search?q=weather+in+{m.group(1).replace(" ", "+")}',
                "linux": lambda m: f'xdg-open https://www.google.com/search?q=weather+in+{m.group(1).replace(" ", "+")}'
            },
            r"search.*for\s+([a-zA-Z\s]+)": {
                "darwin": lambda m: f'open https://www.google.com/search?q={m.group(1).replace(" ", "+")}',
                "windows": lambda m: f'start https://www.google.com/search?q={m.group(1).replace(" ", "+")}',
                "linux": lambda m: f'xdg-open https://www.google.com/search?q={m.group(1).replace(" ", "+")}'
            },
            r"google\s+([a-zA-Z\s]+)": {
                "darwin": lambda m: f'open https://www.google.com/search?q={m.group(1).replace(" ", "+")}',
                "windows": lambda m: f'start https://www.google.com/search?q={m.group(1).replace(" ", "+")}',
                "linux": lambda m: f'xdg-open https://www.google.com/search?q={m.group(1).replace(" ", "+")}'
            },
            
            # System operations (from training data)
            r"shutdown\s+(my\s+)?computer": {
                "darwin": "sudo shutdown -h now",
                "windows": "shutdown /s /t 0",
                "linux": "sudo shutdown -h now"
            },
            r"restart\s+(my\s+)?(pc|computer)": {
                "darwin": "sudo shutdown -r now",
                "windows": "shutdown /r /t 0",
                "linux": "sudo shutdown -r now"
            },
            r"clear\s+the\s+screen": {
                "darwin": "clear",
                "windows": "cls",
                "linux": "clear"
            },
            r"check\s+system\s+info": {
                "darwin": "system_profiler SPHardwareDataType",
                "windows": "systeminfo",
                "linux": "uname -a"
            },
            r"check\s+date\s+and\s+time": {
                "darwin": "date",
                "windows": "time /t & date /t",
                "linux": "date"
            },
            r"check\s+cpu\s+usage": {
                "darwin": "top -l 1 | grep 'CPU usage'",
                "windows": "wmic cpu get loadpercentage",
                "linux": "top -bn1 | grep 'Cpu(s)'"
            },
            r"check\s+(memory|ram)\s+usage": {
                "darwin": "vm_stat",
                "windows": "systeminfo | findstr /C:'Total Physical Memory'",
                "linux": "free -h"
            },
            r"check\s+(memory|ram)\s+status": {
                "darwin": "vm_stat",
                "windows": "systeminfo | findstr /C:'Total Physical Memory'",
                "linux": "free -h"
            },
            
            # Network operations (from training data)
            r"connect\s+(to\s+)?wifi\s+(\S+)": {
                "darwin": lambda m: f"networksetup -setairportnetwork en0 {m.group(2)}",
                "windows": lambda m: f'netsh wlan connect name="{m.group(2)}"',
                "linux": lambda m: f"nmcli device wifi connect {m.group(2)}"
            },
            r"disconnect\s+(from\s+)?wifi": {
                "darwin": "networksetup -setairportpower en0 off",
                "windows": "netsh wlan disconnect",
                "linux": "nmcli device disconnect"
            },
            r"list\s+available\s+wifi\s+networks": {
                "darwin": "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s",
                "windows": "netsh wlan show networks",
                "linux": "nmcli device wifi list"
            },
            
            # Redis commands
            r"start\s+redis\s+sentinel": {
                "darwin": "python -c \"from redis_sentinel_manager import RedisSentinelManager; manager = RedisSentinelManager(); print(manager.start_sentinel())\"",
                "windows": "redis-sentinel sentinel.conf",
                "linux": "redis-sentinel /etc/redis/sentinel.conf"
            },
            r"start\s+redis\s+server": {
                "darwin": "redis-server /Users/lakshmikanthd/Downloads/redis-5.0.7/redis.conf",
                "windows": "redis-server",
                "linux": "redis-server /etc/redis/redis.conf"
            },
            r"stop\s+redis": {
                "darwin": "redis-cli shutdown",
                "windows": "redis-cli shutdown",
                "linux": "redis-cli shutdown"
            },
            r"restart\s+redis": {
                "darwin": "redis-cli shutdown",
                "windows": "redis-cli shutdown",
                "linux": "redis-cli shutdown"
            },
            r"check\s+redis\s+status": {
                "darwin": "redis-cli info server",
                "windows": "redis-cli info server",
                "linux": "redis-cli info server"
            },
            r"check\s+redis\s+sentinel\s+status": {
                "darwin": "python -c \"from redis_sentinel_manager import RedisSentinelManager; manager = RedisSentinelManager(); print(manager.get_sentinel_status())\"",
                "windows": "redis-cli -p 26379 info server",
                "linux": "redis-cli -p 26379 info server"
            },
            
            # System information
            r"show.*date": {
                "all": "date"
            },
            r"show.*me.*date": {
                "all": "date"
            },
            r"show.*today.*date": {
                "all": "date"
            },
            r"what.*date": {
                "all": "date"
            },
            r"current.*time": {
                "all": "date"
            },
            r"what.*time": {
                "all": "date"
            },
            r"display.*date": {
                "all": "date"
            },
            r"display.*time": {
                "all": "date"
            },
            r"today.*date": {
                "all": "date"
            },
            r"check.*wifi": {
                "darwin": "networksetup -getinfo Wi-Fi",
                "windows": "netsh wlan show interfaces",
                "linux": "iwconfig"
            },
            r"wifi.*status": {
                "darwin": "networksetup -getinfo Wi-Fi",
                "windows": "netsh wlan show interfaces",
                "linux": "iwconfig"
            },
            r"network.*status": {
                "darwin": "ifconfig",
                "windows": "ipconfig",
                "linux": "ip addr"
            },
            r"disk.*space": {
                "darwin": "df -h",
                "windows": "wmic logicaldisk get size,freespace,caption",
                "linux": "df -h"
            },
            r"memory.*usage": {
                "darwin": "top -l 1 | head -n 10",
                "windows": "wmic OS get TotalVisibleMemorySize,FreePhysicalMemory",
                "linux": "free -h"
            },
            r"cpu.*usage": {
                "darwin": "top -l 1 | grep 'CPU usage'",
                "windows": "wmic cpu get loadpercentage",
                "linux": "top -bn1 | grep 'Cpu(s)'"
            },
            
            # File operations
            r"list.*files": {
                "all": "ls -la"
            },
            r"show.*files": {
                "all": "ls -la"
            },
            r"current.*directory": {
                "all": "pwd"
            },
            r"where.*am.*i": {
                "all": "pwd"
            },
            
            # Process operations
            r"list.*processes": {
                "all": "ps aux"
            },
            r"show.*processes": {
                "all": "ps aux"
            },
            r"kill.*process.*(\d+)": {
                "all": lambda m: f"kill -9 {m.group(1)}"
            },
            
            # System control
            r"restart.*computer": {
                "darwin": "sudo shutdown -r now",
                "windows": "shutdown /r /t 0",
                "linux": "sudo reboot"
            },
            r"shutdown.*computer": {
                "darwin": "sudo shutdown -h now",
                "windows": "shutdown /s /t 0",
                "linux": "sudo shutdown -h now"
            },
            r"sleep.*computer": {
                "darwin": "pmset sleepnow",
                "windows": "powercfg /hibernate off && rundll32.exe powrprof.dll,SetSuspendState 0,1,0",
                "linux": "systemctl suspend"
            },
            
            # Help and listing commands
            r"list.*all.*commands": {
                "all": "python -c \"from command_mapper import CommandMapper; mapper = CommandMapper(); categories = mapper.get_commands_by_category(); print('Available Commands by Category:'); [print(f'\\n{cat}:\\n' + '\\n'.join([f'  • {cmd.get(\\\"example\\\", \\\"Try the command\\\")}' for cmd in cmds])) for cat, cmds in categories.items()]\""
            },
            r"show.*all.*commands": {
                "all": "python -c \"from command_mapper import CommandMapper; mapper = CommandMapper(); categories = mapper.get_commands_by_category(); print('Available Commands by Category:'); [print(f'\\n{cat}:\\n' + '\\n'.join([f'  • {cmd.get(\\\"example\\\", \\\"Try the command\\\")}' for cmd in cmds])) for cat, cmds in categories.items()]\""
            },
            r"help.*commands": {
                "all": "python -c \"from command_mapper import CommandMapper; mapper = CommandMapper(); categories = mapper.get_commands_by_category(); print('Available Commands by Category:'); [print(f'\\n{cat}:\\n' + '\\n'.join([f'  • {cmd.get(\\\"example\\\", \\\"Try the command\\\")}' for cmd in cmds])) for cat, cmds in categories.items()]\""
            },
            r"list.*redis.*commands": {
                "all": "python -c \"from command_mapper import CommandMapper; mapper = CommandMapper(); redis_commands = [cmd for cat, cmds in mapper.get_commands_by_category().items() if 'redis' in cat.lower() for cmd in cmds]; print('Redis Commands:'); [print(f'  • {cmd.get(\\\"example\\\", \\\"Try the command\\\")}') for cmd in redis_commands]\""
            },
            r"show.*redis.*commands": {
                "all": "python -c \"from command_mapper import CommandMapper; mapper = CommandMapper(); redis_commands = [cmd for cat, cmds in mapper.get_commands_by_category().items() if 'redis' in cat.lower() for cmd in cmds]; print('Redis Commands:'); [print(f'  • {cmd.get(\\\"example\\\", \\\"Try the command\\\")}') for cmd in redis_commands]\""
            },
            
            # Zookeeper commands
            r"start.*zookeeper": {
                "darwin": "cd ~/Downloads/kafka_2.12-3.9.1 && bin/zookeeper-server-start.sh config/zookeeper.properties",
                "windows": "cd %USERPROFILE%\\Downloads\\kafka_2.12-3.9.1 && bin\\zookeeper-server-start.bat config\\zookeeper.properties",
                "linux": "cd ~/Downloads/kafka_2.12-3.9.1 && bin/zookeeper-server-start.sh config/zookeeper.properties"
            },
            
            # Kafka commands
            r"start.*kafka": {
                "darwin": "cd ~/Downloads/kafka_2.12-3.9.1 && bin/kafka-server-start.sh config/server.properties",
                "windows": "cd %USERPROFILE%\\Downloads\\kafka_2.12-3.9.1 && bin\\kafka-server-start.bat config\\server.properties",
                "linux": "cd ~/Downloads/kafka_2.12-3.9.1 && bin/kafka-server-start.sh config/server.properties"
            },
            r"list.*kafka.*topics": {
                "all": "kafka-topics --list --bootstrap-server localhost:9092"
            },
            r"show.*kafka.*topics": {
                "all": "kafka-topics --list --bootstrap-server localhost:9092"
            },
            r"delete.*kafka.*topic.*(\S+)": {
                "all": lambda m: f"kafka-topics --bootstrap-server localhost:9092 --delete --topic {m.group(1)}"
            },
            r"delete.*topic.*(\S+)": {
                "all": lambda m: f"kafka-topics --bootstrap-server localhost:9092 --delete --topic {m.group(1)}"
            }
        }
    
    def _is_safe_command(self, command: str) -> bool:
        """Check if a command is safe to execute."""
        dangerous_patterns = [
            r"rm\s+-rf\s+/",
            r"dd\s+if=/dev/zero",
            r":\(\)\{\s*:\|:\s*&\s*\};:",
            r"mkfs\.",
            r"fdisk",
            r"parted",
            r"sudo\s+rm\s+-rf",
            r"sudo\s+dd",
            r"sudo\s+mkfs",
            r"sudo\s+fdisk",
            r"sudo\s+parted"
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return False
        
        return True
    
    def get_available_commands(self) -> List[str]:
        """Get list of available commands for help."""
        commands = []
        for pattern, mapping in self.fallback_patterns.items():
            if isinstance(mapping, dict):
                command = mapping.get(self.system, mapping.get("all"))
                if command and not callable(command):
                    commands.append(command)
        
        return sorted(list(set(commands)))
    
    def get_commands_by_category(self) -> Dict[str, List[Dict[str, str]]]:
        """Get all available commands organized by category."""
        categories = {
            "System Information": [],
            "File Operations": [],
            "Network & WiFi": [],
            "Applications": [],
            "Web Services": [],
            "Redis Operations": [],
            "Zookeeper Operations": [],
            "Kafka Operations": [],
            "Process Management": [],
            "System Control": [],
            "Date & Time": [],
            "Port Operations": []
        }
        
        # Define category mappings for patterns
        category_patterns = {
            "System Information": [
                r"check\s+system\s+info",
                r"check\s+cpu\s+usage",
                r"check\s+(memory|ram)\s+(usage|status)",
                r"disk.*space",
                r"memory.*usage",
                r"cpu.*usage"
            ],
            "File Operations": [
                r"copy\s+file",
                r"move\s+file",
                r"rename",
                r"(create|make).*folder",
                r"(remove|delete)\s+folder",
                r"list.*files",
                r"show.*files",
                r"current.*directory",
                r"where.*am.*i"
            ],
            "Network & WiFi": [
                r"connect.*wifi",
                r"disconnect.*wifi",
                r"list.*available.*wifi",
                r"check.*wifi",
                r"wifi.*status",
                r"network.*status"
            ],
            "Applications": [
                r"open.*chrome",
                r"open.*firefox",
                r"open.*vscode",
                r"open.*safari",
                r"start\s+notepad",
                r"open\s+calculator"
            ],
            "Web Services": [
                r"(open|launch|go\s+to)\s+youtube",
                r"search\s+youtube",
                r"(open|launch|check)\s+gmail",
                r"(open|launch|go\s+to)\s+facebook",
                r"(open|launch|go\s+to)\s+instagram",
                r"(open|launch|go\s+to)\s+twitter",
                r"(tweet|send\s+a\s+tweet)",
                r"(open|launch|play)\s+spotify",
                r"search\s+spotify",
                r"(open|launch|go\s+to)\s+reddit",
                r"search\s+reddit",
                r"(open|launch)\s+whatsapp\s+web",
                r"search.*weather",
                r"search.*for",
                r"google"
            ],
            "Redis Operations": [
                r"start\s+redis\s+sentinel",
                r"start\s+redis\s+server",
                r"stop\s+redis",
                r"restart\s+redis",
                r"check\s+redis\s+status",
                r"check\s+redis\s+sentinel\s+status"
            ],
            "Zookeeper Operations": [
                r"start.*zookeeper"
            ],
            "Kafka Operations": [
                r"start.*kafka",
                r"list.*kafka.*topics",
                r"show.*kafka.*topics",
                r"delete.*kafka.*topic",
                r"delete.*topic"
            ],
            "Process Management": [
                r"list.*processes",
                r"show.*processes",
                r"kill.*process"
            ],
            "System Control": [
                r"shutdown.*computer",
                r"restart.*computer",
                r"sleep.*computer",
                r"clear\s+the\s+screen"
            ],
            "Date & Time": [
                r"show.*date",
                r"show.*me.*date",
                r"show.*today.*date",
                r"what.*date",
                r"current.*time",
                r"what.*time",
                r"display.*date",
                r"display.*time",
                r"today.*date",
                r"check\s+date\s+and\s+time"
            ],
            "Port Operations": [
                r"list.*port",
                r"kill.*port",
                r"find.*port"
            ]
        }
        
        # Process each pattern and categorize it
        for pattern, mapping in self.fallback_patterns.items():
            if isinstance(mapping, dict):
                command = mapping.get(self.system, mapping.get("all"))
                if command:
                    # Find which category this pattern belongs to
                    category_found = False
                    for category, patterns in category_patterns.items():
                        for cat_pattern in patterns:
                            # Use exact pattern matching instead of regex search
                            if pattern == cat_pattern:
                                # Extract a human-readable description from the pattern
                                description = self._extract_description_from_pattern(pattern)
                                categories[category].append({
                                    "pattern": pattern,
                                    "description": description,
                                    "command": command if not callable(command) else "Dynamic command",
                                    "example": self._get_example_from_pattern(pattern)
                                })
                                category_found = True
                                break
                        if category_found:
                            break
                    
                    # If no category found, add to "Other"
                    if not category_found:
                        if "Other" not in categories:
                            categories["Other"] = []
                        description = self._extract_description_from_pattern(pattern)
                        categories["Other"].append({
                            "pattern": pattern,
                            "description": description,
                            "command": command if not callable(command) else "Dynamic command",
                            "example": self._get_example_from_pattern(pattern)
                        })
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def _extract_description_from_pattern(self, pattern: str) -> str:
        """Extract a human-readable description from a regex pattern."""
        # Remove regex syntax and make it readable
        description = pattern.replace(r"\s+", " ").replace(r"\d+", "NUMBER").replace(r"\S+", "FILENAME")
        description = description.replace(r"(\S+)", "FILENAME").replace(r"(\d+)", "NUMBER").replace(r"(\d{4,5})", "PORT")
        description = description.replace(r"([a-zA-Z\s]+)", "TEXT").replace(r"(.+)", "TEXT")
        description = description.replace(r"[""'](.+)[""']", "TEXT")
        description = description.replace(r"(\S+)", "FILENAME").replace(r"(\d+)", "NUMBER")
        
        # Clean up common patterns
        description = description.replace(".*", " ").replace("\\s+", " ").replace("\\d+", "NUMBER")
        description = description.replace("\\S+", "FILENAME").replace("\\w+", "WORD")
        
        # Make it more readable
        description = description.replace("_", " ").replace("-", " ")
        description = " ".join(description.split())  # Remove extra spaces
        
        return description.title()
    
    def _get_example_from_pattern(self, pattern: str) -> str:
        """Get an example input from a pattern."""
        examples = {
            # Port Operations
            r"list.*port.*(\d{4,5})": "list all ports with 8085",
            r"kill.*port.*(\d{4,5})": "kill port 8085",
            r"find.*port.*(\d{4,5})": "find port 8085",
            
            # System Information
            r"check\s+cpu\s+usage": "check cpu usage",
            r"check\s+(memory|ram)\s+(usage|status)": "check RAM status",
            r"check\s+(memory|ram)\s+usage": "check RAM usage",
            r"check\s+(memory|ram)\s+status": "check RAM status",
            r"check\s+system\s+info": "check system info",
            r"disk.*space": "check disk space",
            r"memory.*usage": "check memory usage",
            r"cpu.*usage": "check cpu usage",
            
            # File Operations
            r"copy\s+file\s+(\S+)\s+to\s+(\S+)": "copy file source.txt to destination.txt",
            r"move\s+file\s+(\S+)\s+to\s+(\S+)": "move file source.txt to destination.txt",
            r"rename\s+(\S+)\s+to\s+(\S+)": "rename oldname.txt to newname.txt",
            r"(create|make)\s+(a\s+)?(new\s+)?folder\s+called\s+(\S+)": "create folder my_folder",
            r"(remove|delete)\s+folder\s+(\S+)": "delete folder my_folder",
            r"list.*files": "list files in current directory",
            r"show.*files": "show files in current directory",
            r"current.*directory": "show current directory",
            r"where.*am.*i": "where am i",
            
            # Applications
            r"open.*chrome": "open chrome",
            r"open.*firefox": "open firefox",
            r"open.*vscode": "open vscode",
            r"open.*safari": "open safari",
            r"start\s+notepad": "start notepad",
            r"open\s+calculator": "open calculator",
            
            # Network & WiFi
            r"connect.*wifi.*(\S+)": "connect to wifi MyNetwork",
            r"connect\s+(to\s+)?wifi\s+(\S+)": "connect to wifi MyNetwork",
            r"disconnect\s+(from\s+)?wifi": "disconnect from wifi",
            r"list\s+available\s+wifi\s+networks": "list available wifi networks",
            r"check.*wifi": "check wifi status",
            r"wifi.*status": "check wifi status",
            r"network.*status": "check network status",
            
            # Web Services
            r"(open|launch|go\s+to)\s+youtube": "open youtube",
            r"search\s+youtube\s+for\s+(.+)": "search youtube for music",
            r"(open|launch|check)\s+gmail": "open gmail",
            r"(open|launch|go\s+to)\s+facebook": "open facebook",
            r"(open|launch|go\s+to)\s+instagram": "open instagram",
            r"(open|launch|go\s+to)\s+twitter": "open twitter",
            r"(tweet|send\s+a\s+tweet)\s+['](.+)[']": "tweet 'Hello world!'",
            r"(open|launch|play)\s+spotify": "open spotify",
            r"search\s+spotify\s+for\s+(.+)": "search spotify for songs",
            r"(open|launch|go\s+to)\s+reddit": "open reddit",
            r"search\s+reddit\s+for\s+(.+)": "search reddit for programming",
            r"(open|launch)\s+whatsapp\s+web": "open whatsapp web",
            r"search.*weather.*in\s+([a-zA-Z\s]+)": "search for weather in London",
            r"search.*for\s+([a-zA-Z\s]+)": "search for python tutorial",
            r"google\s+([a-zA-Z\s]+)": "google machine learning",
            
            # Redis Operations
            r"start\s+redis\s+sentinel": "start redis sentinel",
            r"start\s+redis\s+server": "start redis server",
            r"stop\s+redis": "stop redis",
            r"restart\s+redis": "restart redis",
            r"check\s+redis\s+status": "check redis status",
            r"check\s+redis\s+sentinel\s+status": "check redis sentinel status",
            
            # Zookeeper Operations
            r"start.*zookeeper": "start zookeeper",
            
            # Kafka Operations
            r"start.*kafka": "start kafka",
            r"list.*kafka.*topics": "list kafka topics",
            r"show.*kafka.*topics": "show kafka topics",
            r"delete.*kafka.*topic.*(\S+)": "delete kafka topic my_topic",
            r"delete.*topic.*(\S+)": "delete topic my_topic",
            
            # Process Management
            r"list.*processes": "list processes",
            r"show.*processes": "show processes",
            r"kill.*process.*(\d+)": "kill process 1234",
            
            # System Control
            r"shutdown.*computer": "shutdown my computer",
            r"shutdown\s+(my\s+)?computer": "shutdown my computer",
            r"restart.*computer": "restart my computer",
            r"restart\s+(my\s+)?(pc|computer)": "restart my computer",
            r"clear\s+the\s+screen": "clear the screen",
            r"sleep.*computer": "sleep computer",
            
            # Date & Time
            r"show.*date": "show me today's date",
            r"show.*me.*date": "show me today's date",
            r"show.*today.*date": "show today's date",
            r"what.*date": "what date is it",
            r"current.*time": "what time is it",
            r"what.*time": "what time is it",
            r"display.*date": "display current date",
            r"display.*time": "display current time",
            r"today.*date": "show today's date",
            r"check\s+date\s+and\s+time": "check date and time",
            
            # Command Listing
            r"list.*all.*commands": "list all commands",
            r"show.*all.*commands": "show all commands",
            r"help.*commands": "help commands",
            r"list.*redis.*commands": "list redis commands",
            r"show.*redis.*commands": "show redis commands"
        }
        
        return examples.get(pattern, "Try the command") 