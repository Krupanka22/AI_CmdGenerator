#!/usr/bin/env python3
"""
AI Command Generator - Main CLI Entry Point

Converts natural language input to system commands using AI.
"""

import sys
import argparse
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax
import platform

from command_mapper import CommandMapper
from executor import CommandExecutor

console = Console()

def print_banner():
    """Display the application banner."""
    banner = Text("🤖 AI Command Generator", style="bold blue")
    subtitle = Text("Convert natural language to system commands", style="italic")
    
    console.print(Panel.fit(
        banner + "\n" + subtitle,
        border_style="blue",
        padding=(1, 2)
    ))

def print_help():
    """Display help information."""
    help_text = """
[bold]Usage Examples:[/bold]
• "list all ports with 8085" → lsof -i tcp:8085
• "kill port 8085" → kill -9 <pid>
• "open chrome" → open -a "Google Chrome" (macOS)
• "search for weather in Bangalore" → opens browser with search
• "show me today's date" → date command
• "check wifi status" → network status command

[bold]Commands:[/bold]
• Type your request in natural language
• Type 'help' for this information
• Type 'quit' or 'exit' to close
• Type 'history' to see command history
    """
    
    console.print(Panel(help_text, title="[bold]Help[/bold]", border_style="green"))

def main():
    """Main application loop."""
    parser = argparse.ArgumentParser(description="AI Command Generator")
    parser.add_argument("--input", "-i", help="Direct input command")
    parser.add_argument("--interactive", "-t", action="store_true", help="Interactive mode")
    parser.add_argument("--api-key", help="Groq API key")
    parser.add_argument("--model", default="llama-3.1-8b-instant", help="Groq model to use")
    
    args = parser.parse_args()
    
    # Initialize components
    try:
        command_mapper = CommandMapper(api_key=args.api_key, model=args.model)
        executor = CommandExecutor()
    except Exception as e:
        console.print(f"[red]Error initializing components: {e}[/red]")
        return 1
    
    print_banner()
    
    # Show system info
    system_info = f"Platform: {platform.system()} {platform.release()}"
    console.print(f"[dim]{system_info}[/dim]\n")
    
    if args.input:
        # Single command mode
        process_command(args.input, command_mapper, executor)
    else:
        # Interactive mode
        interactive_mode(command_mapper, executor)
    
    return 0

def process_command(user_input, command_mapper, executor):
    """Process a single command."""
    if user_input.lower() in ['quit', 'exit', 'q']:
        console.print("[yellow]Goodbye![/yellow]")
        return
    
    if user_input.lower() == 'help':
        print_help()
        return
    
    if user_input.lower() == 'history':
        executor.show_history()
        return
    
    try:
        # Map natural language to command
        console.print(f"[bold]Input:[/bold] {user_input}")
        
        with console.status("[bold green]Analyzing command..."):
            mapped_command = command_mapper.map_to_command(user_input)
        
        if not mapped_command:
            console.print("[red]Could not interpret the command. Please try rephrasing.[/red]")
            return
        
        # Display the mapped command
        console.print(f"[bold]Interpreted Command:[/bold]")
        syntax = Syntax(mapped_command, "bash", theme="monokai")
        console.print(Panel(syntax, border_style="yellow"))
        
        # Ask for confirmation
        confirm = Prompt.ask(
            "Execute this command?",
            choices=["y", "n", "yes", "no"],
            default="y"
        )
        
        if confirm.lower() in ['y', 'yes']:
            # Execute the command
            with console.status("[bold green]Executing command..."):
                result = executor.execute(mapped_command, user_input)
            
            # Display results
            if result.success:
                console.print("[bold green]✓ Command executed successfully[/bold green]")
                if result.output:
                    console.print(Panel(result.output, title="[bold]Output[/bold]", border_style="green"))
            else:
                console.print(f"[bold red]✗ Command failed[/bold red]")
                if result.error:
                    console.print(Panel(result.error, title="[bold]Error[/bold]", border_style="red"))
        else:
            console.print("[yellow]Command execution cancelled.[/yellow]")
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

def interactive_mode(command_mapper, executor):
    """Run in interactive mode."""
    print_help()
    
    while True:
        try:
            user_input = Prompt.ask("\n[bold blue]Enter your command[/bold blue]")
            process_command(user_input, command_mapper, executor)
        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        except EOFError:
            console.print("\n[yellow]Goodbye![/yellow]")
            break

if __name__ == "__main__":
    sys.exit(main()) 