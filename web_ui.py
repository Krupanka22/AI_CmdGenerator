#!/usr/bin/env python3
"""
AI Command Generator - Web UI

Flask web application providing a modern web interface for the AI Command Generator.
"""

import os
import sys
import json
import datetime
import socket
from pathlib import Path
from typing import Dict, List, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, will use system environment variables

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from command_mapper import CommandMapper
from executor import CommandExecutor

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    from flask import Flask, render_template, request, jsonify, session
    from flask_socketio import SocketIO, emit
except ImportError:
    print("Flask not installed. Installing required packages...")
    os.system("pip install flask flask-socketio")
    from flask import Flask, render_template, request, jsonify, session
    from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ai-command-generator-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize components
command_mapper = CommandMapper()
executor = CommandExecutor()

# Initialize Groq AI
groq_api_key = os.getenv("GROQ_API_KEY")
groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
if Groq and groq_api_key:
    try:
        groq_client = Groq(api_key=groq_api_key)
        print(f"[OK] Groq AI initialized successfully with model: {groq_model}")
    except Exception as e:
        print(f"[ERROR] Groq AI initialization failed: {e}")
        groq_client = None
else:
    groq_client = None
    if not Groq:
        print("[WARN] Groq SDK not available")
    if not groq_api_key:
        print("[WARN] Groq API key not found. Set GROQ_API_KEY environment variable")

# Constants
NO_MESSAGE_ERROR = 'No message provided'

# Chat history storage (in memory for web session)
chat_history = []

def extract_command_with_groq(user_input: str) -> Dict:
    """Extract command from text using Groq Llama."""
    if not groq_client:
        return {
            'error': 'Groq AI is not available. Please check your API key configuration.',
            'timestamp': datetime.datetime.now().isoformat()
        }
    
    try:
        # Create a prompt for command extraction
        prompt = f"""
You are a Windows command line assistant that converts natural language to Windows CMD or PowerShell commands.
Current platform: Windows

Rules:
1. Extract ONLY the Windows command from the user's text, no explanations
2. Use ONLY Windows CMD or PowerShell commands
3. For opening applications, use 'start' command
4. For web searches, use 'start' to open URLs in the default browser
5. Be safe - avoid dangerous commands like 'format', 'del /f /s /q C:\\'
6. If the text doesn't contain a clear command request, return "NO_COMMAND_FOUND"
7. NEVER return Linux (ls, rm, grep) or macOS (open -a, pbcopy) commands

Examples:
- "open chrome" → start chrome
- "list files" → dir
- "create a file" → echo. > newfile.txt
- "search for weather" → start https://www.google.com/search?q=weather
- "show date" → date /t
- "check ports" → netstat -an
- "kill process 1234" → taskkill /PID 1234 /F

User input: {user_input}

Extract the Windows command:"""

        # Generate response using Groq
        response = groq_client.chat.completions.create(
            model=groq_model,
            messages=[
                {"role": "system", "content": "You are a command line assistant that converts natural language to system commands."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=120,
            temperature=0.1
        )
        
        if not response.choices or not response.choices[0].message.content:
            return {
                'error': 'Groq AI did not return a response',
                'timestamp': datetime.datetime.now().isoformat()
            }
        
        extracted_command = response.choices[0].message.content.strip()
        
        # Check if Groq found a command
        if extracted_command == "NO_COMMAND_FOUND" or not extracted_command:
            return {
                'message': '🤖 I couldn\'t extract a clear command from your text. Please try rephrasing with a specific action.',
                'mapped_command': None,
                'user_input': user_input,
                'timestamp': datetime.datetime.now().isoformat(),
                'execution_result': None,
                'success': False
            }
        
        # Validate the command for safety
        if command_mapper._is_safe_command(extracted_command):
            return {
                'message': '🤖 Groq Llama extracted command from your text:',
                'mapped_command': extracted_command,
                'user_input': user_input,
                'timestamp': datetime.datetime.now().isoformat(),
                'execution_result': None,
                'success': True,
                'needs_confirmation': True
            }
        else:
            return {
                'message': f'🚫 Groq Llama extracted a potentially unsafe command: {extracted_command}',
                'mapped_command': None,
                'user_input': user_input,
                'timestamp': datetime.datetime.now().isoformat(),
                'execution_result': None,
                'success': False,
                'needs_confirmation': False
            }
            
    except Exception as e:
        return {
            'error': f'Groq AI error: {str(e)}',
            'timestamp': datetime.datetime.now().isoformat()
        }

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages via REST API."""
    data = request.get_json()
    user_input = data.get('message', '').strip()
    
    if not user_input:
        return jsonify({'error': NO_MESSAGE_ERROR})
    
    # Process the command
    result = process_command(user_input)
    
    return jsonify(result)

@socketio.on('send_message')
def handle_message(data):
    """Handle WebSocket messages."""
    user_input = data.get('message', '').strip()
    
    if not user_input:
        emit('error', {'error': NO_MESSAGE_ERROR})
        return
    
    # Process the command
    result = process_command(user_input)
    
    # Emit response back to client
    emit('bot_response', result)

def process_command(user_input: str) -> Dict:
    """Process a user command and return result."""
    try:
        # Map to command
        # Use spell correction and mapping
        mapped_command, _, suggested_correction = command_mapper.map_to_command_with_correction(user_input)
        
        if not mapped_command:
            return {
                'type': 'error',
                'message': "I couldn't understand that command. Please try rephrasing.",
                'timestamp': datetime.datetime.now().isoformat(),
                'user_input': user_input,
                'mapped_command': None,
                'execution_result': None,
                'success': False
            }
        
        # Check if this is a command listing request
        is_command_listing = any(keyword in user_input.lower() for keyword in ['list all commands', 'show all commands', 'help commands'])
        
        # Check if there was a spelling correction
        if suggested_correction:
            if is_command_listing:
                message = f"I think you meant: '{suggested_correction}'\n\nI'll show you all available commands organized by category."
            else:
                message = f"I think you meant: '{suggested_correction}'\n\nI'll execute: {mapped_command}"
        else:
            if is_command_listing:
                message = "I'll show you all available commands organized by category."
            else:
                message = f"I'll execute: {mapped_command}"
        
        # For web UI, we'll show the command but not execute it automatically
        # User can choose to execute via a separate action
        return {
            'type': 'command_mapped',
            'message': message,
            'timestamp': datetime.datetime.now().isoformat(),
            'user_input': user_input,
            'mapped_command': mapped_command,
            'execution_result': None,
            'success': True,
            'needs_confirmation': True,
            'suggested_correction': suggested_correction,
            'is_command_listing': is_command_listing
        }
        
    except Exception as e:
        return {
            'type': 'error',
            'message': f"Error processing command: {str(e)}",
            'timestamp': datetime.datetime.now().isoformat(),
            'user_input': user_input,
            'mapped_command': None,
            'execution_result': None,
            'success': False
        }

@app.route('/api/groq', methods=['POST'])
def groq_extract():
    """Extract command from text using Groq Llama."""
    data = request.get_json()
    user_input = data.get('message', '').strip()
    
    if not user_input:
        return jsonify({'error': NO_MESSAGE_ERROR})
    
    # Extract command using Groq
    result = extract_command_with_groq(user_input)
    
    # Add to chat history
    chat_history.append({
        'user_input': user_input,
        'response': result,
        'timestamp': result.get('timestamp', datetime.datetime.now().isoformat()),
        'type': 'groq'
    })
    
    return jsonify(result)

@app.route('/api/execute', methods=['POST'])
def execute_command():
    """Execute a mapped command."""
    data = request.get_json()
    mapped_command = data.get('command', '').strip()
    user_input = data.get('user_input', '').strip()
    
    if not mapped_command:
        return jsonify({'error': 'No command provided'})
    
    try:
        # Execute the command
        result = executor.execute(mapped_command, user_input)
        
        return jsonify({
            'type': 'execution_result',
            'success': result.success,
            'output': result.output,
            'error': result.error,
            'execution_time': result.execution_time,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'type': 'error',
            'error': f"Execution error: {str(e)}",
            'timestamp': datetime.datetime.now().isoformat()
        })

@app.route('/api/history')
def get_history():
    """Get chat history."""
    return jsonify(chat_history)

@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    """Clear chat history."""
    global chat_history
    chat_history = []
    return jsonify({'message': 'History cleared'})

@app.route('/api/help')
def get_help():
    """Get help information."""
    help_data = {
        'examples': [
            "open chrome",
            "list files in current directory",
            "create a file called test.txt",
            "create a folder called MyFolder",
            "delete a file",
            "check wifi status",
            "search for weather in London",
            "what is the current time",
            "display current date",
            "check RAM status",
            "check cpu usage",
            "check disk space",
            "list all commands",
            "shutdown my computer",
            "check system info",
            "open task manager"
        ],
        'groq_examples': [
            "how to find large files on Windows",
            "command to compress a folder in PowerShell",
            "how to kill a process by name on Windows",
            "check disk usage in human readable format",
            "download a file from URL using PowerShell",
            "create a new directory recursively",
            "find my IP address on Windows",
            "check which ports are listening",
            "search for text in files using findstr",
            "how to monitor system resources in task manager",
            "how to check git status and branches",
            "how to restart a Windows service",
            "list all running services on Windows",
            "how to flush DNS cache",
            "how to check Windows version",
            "how to export environment variables"
        ],
        'features': [
            "Natural language to Windows command conversion",
            "Windows CMD & PowerShell support",
            "AI-powered mapping (with Groq API)",
            "Fallback pattern matching",
            "Safe command execution",
            "Command history tracking"
        ]
    }
    return jsonify(help_data)

@app.route('/api/commands')
def get_commands():
    """Get all available commands organized by category."""
    try:
        from command_mapper import CommandMapper
        mapper = CommandMapper()
        categories = mapper.get_commands_by_category()
        
        # Format the data for the frontend
        formatted_categories = {}
        for category, commands in categories.items():
            formatted_categories[category] = []
            for cmd in commands:
                formatted_categories[category].append({
                    'example': cmd['example'],
                    'description': cmd['description'],
                    'command': cmd['command']
                })
        
        return jsonify({
            'categories': formatted_categories,
            'total_commands': sum(len(cmds) for cmds in categories.values())
        })
    except Exception as e:
        return jsonify({
            'error': f'Error loading commands: {str(e)}',
            'categories': {},
            'total_commands': 0
        })

def find_free_port(start_port=5000, max_attempts=100):
    """Find a free port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find a free port in range {start_port}-{start_port + max_attempts}")

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    # Find a free port
    try:
        port = find_free_port()
        print("AI Command Generator - Web UI")
        print("=" * 40)
        print(f"Platform: {command_mapper.system}")
        print(f"AI Available: {command_mapper.use_ai}")
        print(f"Server starting on http://localhost:{port}")
        print("Press Ctrl+C to stop")
        
        socketio.run(app, debug=False, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
    except RuntimeError as e:
        print(f"[ERROR]: {e}")
        sys.exit(1) 