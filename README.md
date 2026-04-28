# AI Command Generator

Convert natural language into safe, platform-aware system commands using Groq and intelligent fallbacks.

## Highlights

- Groq Llama powered command generation
- Fallback pattern matching when AI is unavailable
- Cross-platform support (Windows, macOS, Linux)
- Command safety checks and execution confirmation
- CLI, chatbot, and web UI modes

## Requirements

- Python 3.9+
- Groq API key (optional but recommended)

## Install

```bash
python -m venv venv
```

```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

```bash
pip install -r requirements.txt
```

## Configure Groq (optional)

Set environment variables:

```bash
# Windows (PowerShell)
$env:GROQ_API_KEY="your-api-key"
$env:GROQ_MODEL="llama-3.1-8b-instant"
```

```bash
# macOS/Linux
export GROQ_API_KEY="your-api-key"
export GROQ_MODEL="llama-3.1-8b-instant"
```

Or create a `.env` file:

```
GROQ_API_KEY=your-api-key
GROQ_MODEL=llama-3.1-8b-instant
```

Get a Groq key at https://console.groq.com/keys

## Usage

### CLI

```bash
python main.py
```

```bash
python main.py --input "open chrome"
```

### Chatbot

```bash
python chatbot.py
```

```bash
python advanced_chatbot.py
```

### Web UI

```bash
python launch_web_ui.py
```

## Safety

Commands are validated before execution and may require confirmation. Always review generated commands.

## Project Structure

```
.
├── main.py
├── command_mapper.py
├── executor.py
├── chatbot.py
├── advanced_chatbot.py
├── web_ui.py
├── launch_web_ui.py
├── port_finder.py
├── templates/
│   └── index.html
├── requirements.txt
└── WINDOWS_SETUP.md
```

## License

MIT
