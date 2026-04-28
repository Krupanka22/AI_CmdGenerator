# Windows Setup Guide for AI Command Generator

## ✅ Windows Compatibility Status: **GOOD**

The AI Command Generator is compatible with Windows with some minor considerations.

## 🚀 Quick Setup

### 1. Prerequisites
- **Python 3.8+** installed on Windows
- **Git** (optional, for cloning the repository)
- **Windows 10/11** (recommended)

### 2. Installation

```bash
# Clone or download the project
git clone <repository-url>
cd ai_command_generator

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Setup
Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
```

## 🔧 Windows-Specific Considerations

### Command Differences
The application automatically detects Windows and uses appropriate commands:

| Feature | Windows Command | Notes |
|---------|----------------|-------|
| **Applications** | `start chrome`, `start firefox` | Uses Windows `start` command |
| **File Operations** | `copy`, `move`, `rename` | Windows equivalents of Unix commands |
| **System Info** | `ipconfig`, `wmic` | Windows system commands |
| **Process Management** | `tasklist`, `taskkill` | Windows process commands |
| **Network** | `netsh wlan show interfaces` | Windows network commands |

### Redis Setup (Optional)
If you want to use Redis commands:

1. **Download Redis for Windows**:
   - Download from: https://github.com/microsoftarchive/redis/releases
   - Or use WSL2 with Redis

2. **Install Redis**:
   ```bash
   # Using Chocolatey (recommended)
   choco install redis-64

   # Or download and install manually
   ```

3. **Update Configuration**:
   - Edit `redis_sentinel_manager.py` if needed
   - Update paths to match your Redis installation

### Port Management
- The application automatically finds free ports
- Default port range: 5000-5010
- Windows Firewall may prompt for permission

## 🎯 Usage

### Command Line Interface
```bash
# Basic usage
python main.py "open chrome"

# Interactive mode
python main.py --interactive
```

### Web Interface
```bash
# Launch web UI
python launch_web_ui.py

# Or directly
python web_ui.py
```

### Chatbot Interface
```bash
# Basic chatbot
python chatbot.py

# Advanced chatbot
python advanced_chatbot.py
```

## 🔍 Troubleshooting

### Common Issues

#### 1. **"python-docx not found"**
```bash
pip install python-docx
```

#### 2. **Port already in use**
- The application automatically finds free ports
- If issues persist, check Windows Firewall settings

#### 3. **Redis commands not working**
- Ensure Redis is installed and in PATH
- Check if Redis service is running: `redis-cli ping`

#### 4. **Permission denied errors**
- Run Command Prompt as Administrator if needed
- Check Windows Defender/Firewall settings

#### 5. **Path issues**
- Use forward slashes `/` or escaped backslashes `\\` in paths
- The application handles path conversion automatically

### Windows-Specific Commands

#### System Information
```bash
# Check system info
python main.py "check system info"

# Check RAM status
python main.py "check RAM status"

# Check CPU usage
python main.py "check cpu usage"
```

#### File Operations
```bash
# List files
python main.py "list files"

# Create folder
python main.py "create folder my_folder"

# Copy file
python main.py "copy file source.txt to destination.txt"
```

#### Applications
```bash
# Open applications
python main.py "open chrome"
python main.py "open firefox"
python main.py "open vscode"
```

## 📋 Supported Windows Commands

### ✅ Fully Supported
- File operations (copy, move, rename, mkdir, rmdir)
- Application launching (Chrome, Firefox, VS Code, Notepad, Calculator)
- System information (CPU, RAM, disk space)
- Network status (WiFi, network interfaces)
- Web browsing and searches
- Process management
- Date and time commands

### ⚠️ Limited Support
- **Redis**: Requires Redis installation
- **Zookeeper/Kafka**: Requires separate installation
- **Unix-specific tools**: Some commands may not work

### ❌ Not Supported
- Unix-specific commands (grep, awk, sed)
- macOS-specific applications (Safari, TextEdit)

## 🎉 Success Indicators

You'll know everything is working when:

1. ✅ `python main.py "show me today's date"` returns the current date
2. ✅ `python main.py "open chrome"` opens Chrome browser
3. ✅ `python main.py "check system info"` shows system information
4. ✅ Web UI launches without errors
5. ✅ Chatbot responds to commands

## 📞 Support

If you encounter issues:
1. Check this guide first
2. Verify Python and dependencies are installed
3. Check Windows Firewall settings
4. Run as Administrator if needed
5. Check the main README.md for general troubleshooting

---

**Note**: This application is designed to be cross-platform but may have some limitations on Windows due to command differences. Most core functionality works well on Windows! 