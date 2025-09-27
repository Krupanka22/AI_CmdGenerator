# AI Command Generator 🤖

Convert natural language to system commands using AI and intelligent pattern matching.

## 🖥️ Platform Support

- ✅ **macOS**: Fully supported
- ✅ **Windows**: Fully supported (see [WINDOWS_SETUP.md](WINDOWS_SETUP.md))
- ✅ **Linux**: Fully supported

## 🚀 Quick Start

### Setup Local Environment

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment:**
   ```bash
   # On macOS/Linux:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the chatbot:**
   ```bash
   python chatbot.py
   ```

Convert natural language to system commands using AI and intelligent pattern matching.

## ✨ Features

- **🤖 AI-Powered**: Uses OpenAI GPT to understand natural language commands
- **🔄 Fallback System**: Pattern matching when AI is unavailable
- **🖥️ Cross-Platform**: Works on macOS, Windows, and Linux
- **🛡️ Safe Execution**: Built-in safety checks and command validation
- **📚 Command History**: Tracks all executed commands
- **🎨 Rich CLI**: Beautiful terminal interface with syntax highlighting
- **💬 Chatbot Interface**: Interactive conversation with history tracking
- **📊 Statistics**: Track command success rates and AI usage
- **🌐 Web UI**: Modern browser-based interface with real-time communication
- **🔧 Spell Correction**: Intelligent command suggestions for typos
- **📋 Command Categories**: Organized command listings by category

## Installation

1. **Clone or download the project:**
   ```bash
   git clone <repository-url>
   cd ai_command_generator
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up AI APIs (optional but recommended):**
   
   **OpenAI API:**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
   
   **Google Gemini API:**
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key-here"
   # or alternatively
   export GOOGLE_API_KEY="your-gemini-api-key-here"
   ```
   
   Or create a `.env` file:
   ```
   OPENAI_API_KEY=your-api-key-here
   GEMINI_API_KEY=your-gemini-api-key-here
   ```
   
   **Getting API Keys:**
   - OpenAI: Visit [OpenAI API](https://platform.openai.com/api-keys)
   - Gemini: Visit [Google AI Studio](https://aistudio.google.com/)

## Usage

### Interactive Mode
```bash
python main.py
```

### Single Command Mode
```bash
python main.py --input "open chrome"
python main.py -i "list all ports with 8085"
```

### With Custom API Key
```bash
python main.py --api-key "your-key" --input "check wifi status"
```

### Chatbot Interface
```bash
# Interactive chatbot with conversation history
python chatbot.py

# Single command via chatbot
python chatbot.py --input "show me today's date"

# Advanced chatbot with statistics
python advanced_chatbot.py

# View chat history
python show_history.py
```

### Web UI Interface
```bash
# Launch web-based chatbot interface (auto-finds free port)
python launch_web_ui.py

# Or run the web server directly (auto-finds free port)
python web_ui.py

# Find available ports
python port_finder.py find

# Check specific port availability
python port_finder.py check 5000
```

The web interface includes two AI-powered buttons:
- **Send**: Uses OpenAI to convert natural language to commands
- **✨ Gemini AI**: Uses Google Gemini to extract commands from text

Both buttons will ask for user confirmation before executing the generated commands.

## Examples

| Natural Language | Generated Command | Platform |
|------------------|-------------------|----------|
| "list all ports with 8085" | `lsof -i tcp:8085` | All |
| "kill port 8085" | `kill -9 $(lsof -t -i tcp:8085)` | All |
| "open chrome" | `open -a "Google Chrome"` | macOS |
| "open chrome" | `start chrome` | Windows |
| "open chrome" | `google-chrome` | Linux |
| "search for weather in Bangalore" | `open "https://www.google.com/search?q=weather+in+Bangalore"` | All |
| "show me today's date" | `date` | All |
| "check wifi status" | `networksetup -getinfo Wi-Fi` | macOS |
| "check wifi status" | `netsh wlan show interfaces` | Windows |
| "check wifi status" | `iwconfig` | Linux |

## Supported Commands

### System Information
- Date and time
- WiFi/Network status
- Disk space
- Memory usage
- CPU usage
- Current directory

### Application Management
- Open Chrome, Firefox, Safari, VS Code
- Platform-specific commands

### Network Operations
- List processes on specific ports
- Kill processes on ports
- Network status checks

### File Operations
- List files in current directory
- Show current working directory

### Web Searches
- Google searches
- Weather queries
- General web searches

### Process Management
- List running processes
- Kill specific processes

### System Control
- Restart computer
- Shutdown computer
- Sleep computer

## Safety Features

- **Dangerous Command Detection**: Blocks potentially harmful commands
- **Execution Confirmation**: Asks for confirmation before executing
- **Timeout Protection**: 30-second timeout on command execution
- **Platform Validation**: Ensures commands are appropriate for your OS

## Command History

The tool maintains a history of all executed commands:

```bash
# View history
python main.py
> history

# History shows:
# - Original natural language input
# - Generated system command
# - Execution success/failure
# - Execution time
# - Timestamp
```

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENAI_MODEL`: Model to use (default: gpt-3.5-turbo)

### Command Line Options
- `--input, -i`: Direct command input
- `--interactive, -t`: Force interactive mode
- `--api-key`: Specify API key
- `--model`: Specify OpenAI model

## Fallback System

When AI is unavailable, the tool uses intelligent pattern matching:

1. **Regex Patterns**: Matches common command patterns
2. **Platform Detection**: Uses OS-specific commands
3. **Keyword Matching**: Recognizes common terms and phrases

## Project Structure

```
ai_command_generator/
├── main.py                 # CLI entry point
├── command_mapper.py       # AI integration & mapping logic
├── executor.py             # Safe command execution
├── chatbot.py              # Interactive chatbot interface
├── advanced_chatbot.py     # Advanced chatbot with statistics
├── web_ui.py              # Flask web application
├── launch_web_ui.py       # Web UI launcher script
├── port_finder.py         # Port availability utility
├── show_history.py         # Display chat history
├── requirements.txt        # Dependencies
├── README.md              # This file
├── templates/             # Web UI templates
│   └── index.html         # Main web interface
├── command_history.json    # Command history (auto-generated)
├── chat_history.json       # Chat conversation history (auto-generated)
└── advanced_chat_history.json # Advanced chat history (auto-generated)
```

## Development

### Adding New Commands

To add new command patterns, edit the `_load_fallback_patterns()` method in `command_mapper.py`:

```python
r"your pattern here": {
    "darwin": "macOS command",
    "windows": "Windows command", 
    "linux": "Linux command",
    "all": "Universal command"
}
```

### Safety Considerations

- Always test new commands thoroughly
- Avoid commands that could damage the system
- Use platform-specific commands when possible
- Include proper error handling

## Troubleshooting

### Common Issues

1. **"OpenAI not available"**: Set your API key or the tool will use fallback patterns
2. **"Command not found"**: Some commands may not be available on your system
3. **"Permission denied"**: Some commands require elevated privileges

### Getting Help

```bash
python main.py
> help
```

## License

This project is open source. Feel free to contribute and improve!

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Note**: This tool is designed for convenience and should be used responsibly. Always review generated commands before execution. 