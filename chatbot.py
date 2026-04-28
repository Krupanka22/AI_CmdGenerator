#!/usr/bin/env python3
"""
AI Command Generator - Chatbot Interface

Provides an interactive chatbot experience for converting natural language
to system commands with conversation history.
"""

import sys
import os
import json
import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from command_mapper import CommandMapper
from executor import CommandExecutor
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.align import Align

console = Console()

@dataclass
class ChatMessage:
    """Represents a chat message."""
    timestamp: str
    user_input: str
    mapped_command: Optional[str]
    execution_result: Optional[str]
    success: bool
    message_type: str  # 'user', 'system', 'error'

class ChatbotInterface:
    """Interactive chatbot interface for AI Command Generator."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.command_mapper = CommandMapper(api_key=api_key, model=model)
        self.executor = CommandExecutor()
        self.conversation_history: List[ChatMessage] = []
        self.chat_history_file = Path("chat_history.json")
        self.load_chat_history()
        
        # Chatbot personality
        self.bot_name = "🤖 AI Command Assistant"
        self.welcome_message = "Hello! I'm your AI command assistant. I can help you convert natural language to system commands. Just tell me what you want to do!"
        
    def load_chat_history(self):
        """Load chat history from file."""
        if self.chat_history_file.exists():
            try:
                with open(self.chat_history_file, 'r') as f:
                    data = json.load(f)
                    self.conversation_history = [ChatMessage(**msg) for msg in data]
            except (json.JSONDecodeError, IOError):
                self.conversation_history = []
        else:
            self.conversation_history = []
    
    def save_chat_history(self):
        """Save chat history to file."""
        try:
            with open(self.chat_history_file, 'w') as f:
                json.dump([asdict(msg) for msg in self.conversation_history], f, indent=2)
        except IOError:
            pass  # Silently fail if can't save
    
    def add_message(self, user_input: str, mapped_command: Optional[str] = None, 
                   execution_result: Optional[str] = None, success: bool = True, 
                   message_type: str = "user"):
        """Add a message to the conversation history."""
        message = ChatMessage(
            timestamp=datetime.datetime.now().isoformat(),
            user_input=user_input,
            mapped_command=mapped_command,
            execution_result=execution_result,
            success=success,
            message_type=message_type
        )
        self.conversation_history.append(message)
        self.save_chat_history()
    
    def display_welcome(self):
        """Display welcome message and system info."""
        welcome_panel = Panel(
            Text(self.welcome_message, style="bold blue"),
            title=self.bot_name,
            border_style="blue",
            padding=(1, 2)
        )
        console.print(welcome_panel)
        
        # System info
        system_info = f"Platform: {self.command_mapper.system} | AI Available: {self.command_mapper.use_ai}"
        console.print(f"[dim]{system_info}[/dim]\n")
        
        # Quick help
        help_text = """
[bold]Quick Commands:[/bold]
• Type your request in natural language
• Type 'help' for detailed help
• Type 'history' to see conversation history
• Type 'clear' to clear history
• Type 'quit' or 'exit' to close
        """
        console.print(Panel(help_text, title="[bold]Quick Help[/bold]", border_style="green"))
    
    def display_help(self):
        """Display detailed help information."""
        help_content = """
[bold]How to use me:[/bold]

[bold]Basic Commands:[/bold]
• "open chrome" → Opens Google Chrome
• "list all ports with 8085" → Shows processes on port 8085
• "kill port 8085" → Kills processes on port 8085
• "show me today's date" → Shows current date/time
• "check wifi status" → Shows network information
• "search for weather in London" → Opens weather search

[bold]System Information:[/bold]
• "disk space" → Shows disk usage
• "memory usage" → Shows memory information
• "cpu usage" → Shows CPU information
• "list files" → Shows files in current directory
• "current directory" → Shows working directory

[bold]Process Management:[/bold]
• "list processes" → Shows running processes
• "kill process 1234" → Kills process with PID 1234

[bold]Web Searches:[/bold]
• "google python tutorial" → Opens Google search
• "search for restaurants near me" → Opens location search

[bold]Chat Commands:[/bold]
• 'help' → Show this help
• 'history' → Show conversation history
• 'clear' → Clear conversation history
• 'quit' or 'exit' → Close the chatbot
        """
        
        console.print(Panel(help_content, title="[bold]Help[/bold]", border_style="green"))
    
    def display_history(self, limit: int = 20):
        """Display conversation history."""
        if not self.conversation_history:
            console.print("[yellow]No conversation history available.[/yellow]")
            return
        
        console.print(f"\n[bold]Conversation History (last {min(limit, len(self.conversation_history))} messages):[/bold]")
        console.print("=" * 80)
        
        # Create table for history
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Time", style="dim", width=12)
        table.add_column("Type", style="cyan", width=8)
        table.add_column("Input", style="white")
        table.add_column("Command", style="yellow")
        table.add_column("Status", style="green", width=8)
        
        for msg in self.conversation_history[-limit:]:
            timestamp = datetime.datetime.fromisoformat(msg.timestamp).strftime("%H:%M:%S")
            status = "✓" if msg.success else "✗"
            msg_type = msg.message_type.capitalize()
            
            # Truncate long inputs
            user_input = msg.user_input[:50] + "..." if len(msg.user_input) > 50 else msg.user_input
            command = msg.mapped_command[:40] + "..." if msg.mapped_command and len(msg.mapped_command) > 40 else msg.mapped_command or ""
            
            table.add_row(timestamp, msg_type, user_input, command, status)
        
        console.print(table)
        console.print()
    
    def process_user_input(self, user_input: str) -> bool:
        """Process user input and return True if should continue."""
        user_input = user_input.strip()
        
        if not user_input:
            return True
        
        # Handle special commands
        if user_input.lower() in ['quit', 'exit', 'q']:
            console.print("[yellow]Goodbye! Thanks for using AI Command Assistant![/yellow]")
            return False
        
        if user_input.lower() == 'help':
            self.display_help()
            return True
        
        if user_input.lower() == 'history':
            self.display_history()
            return True
        
        if user_input.lower() == 'clear':
            self.conversation_history = []
            self.save_chat_history()
            console.print("[green]Conversation history cleared![/green]")
            return True
        
        # Process natural language command
        try:
            console.print(f"\n[bold]You:[/bold] {user_input}")
            
            # Map to command
            with console.status("[bold green]Analyzing command..."):
                mapped_command = self.command_mapper.map_to_command(user_input)
            
            if not mapped_command:
                console.print("[red]I couldn't understand that command. Please try rephrasing or type 'help' for examples.[/red]")
                self.add_message(user_input, message_type="error", success=False)
                return True
            
            # Display mapped command
            console.print(f"[bold]🤖 Assistant:[/bold] I'll execute: [yellow]{mapped_command}[/yellow]")
            
            # Ask for confirmation
            confirm = Prompt.ask(
                "Execute this command?",
                choices=["y", "n", "yes", "no"],
                default="y"
            )
            
            if confirm.lower() in ['y', 'yes']:
                # Execute command
                with console.status("[bold green]Executing command..."):
                    result = self.executor.execute(mapped_command, user_input)
                
                # Display results
                if result.success:
                    console.print("[bold green]✓ Command executed successfully![/bold green]")
                    if result.output:
                        console.print(Panel(result.output, title="[bold]Output[/bold]", border_style="green"))
                    self.add_message(user_input, mapped_command, result.output, True)
                else:
                    console.print(f"[bold red]✗ Command failed[/bold red]")
                    if result.error:
                        console.print(Panel(result.error, title="[bold]Error[/bold]", border_style="red"))
                    self.add_message(user_input, mapped_command, result.error, False)
            else:
                console.print("[yellow]Command execution cancelled.[/yellow]")
                self.add_message(user_input, mapped_command, "Cancelled by user", True)
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled by user.[/yellow]")
            self.add_message(user_input, message_type="error", success=False)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            self.add_message(user_input, message_type="error", success=False)
        
        return True
    
    def run(self):
        """Run the chatbot interface."""
        self.display_welcome()
        
        while True:
            try:
                user_input = Prompt.ask("\n[bold blue]You[/bold blue]")
                if not self.process_user_input(user_input):
                    break
            except KeyboardInterrupt:
                console.print("\n[yellow]Goodbye![/yellow]")
                break
            except EOFError:
                console.print("\n[yellow]Goodbye![/yellow]")
                break

def main():
    """Main entry point for the chatbot."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Command Generator Chatbot")
    parser.add_argument("--api-key", help="Groq API key")
    parser.add_argument("--model", default="llama-3.1-8b-instant", help="Groq model to use")
    parser.add_argument("--clear-history", action="store_true", help="Clear chat history on startup")
    parser.add_argument("--input", "-i", help="Direct input command (non-interactive mode)")
    
    args = parser.parse_args()
    
    # Initialize chatbot
    chatbot = ChatbotInterface(api_key=args.api_key, model=args.model)
    
    if args.clear_history:
        chatbot.conversation_history = []
        chatbot.save_chat_history()
        console.print("[green]Chat history cleared![/green]")
    
    # Handle direct input or interactive mode
    if args.input:
        # Single command mode
        chatbot.display_welcome()
        chatbot.process_user_input(args.input)
    else:
        # Interactive mode
        chatbot.run()

if __name__ == "__main__":
    main() 