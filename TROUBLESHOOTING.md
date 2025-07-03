# Troubleshooting Guide

## Dependency Installation Issues

### Common Problems and Solutions

#### 1. `sqlite3` Installation Error
**Error**: `ERROR: Could not find a version that satisfies the requirement sqlite3`

**Solution**: 
- `sqlite3` is built into Python 3.x and doesn't need to be installed
- Use the updated `requirements.txt` or `requirements-core.txt`
- Run: `python setup_dependencies.py` for automatic handling

#### 2. `anthropicai` Package Not Found
**Error**: `ERROR: Could not find a version that satisfies the requirement anthropicai`

**Solution**:
- The correct package name is `anthropic`, not `anthropicai`
- This has been fixed in the updated requirements files

#### 3. Python Version Compatibility
**Error**: Various version requirement errors

**Solution**:
- Ensure you're using Python 3.8+ (recommended: Python 3.10+)
- Check version: `python --version`
- Some packages may not support Python 3.12+ yet

#### 4. `pyaudio` Installation Fails
**Error**: Microsoft Visual C++ 14.0 is required

**Solutions**:
- **Windows**: Install Visual C++ Build Tools
- **Alternative**: Use `pip install pipwin && pipwin install pyaudio`
- **Skip**: Voice input will be disabled but app will work

#### 5. PyQt6 Installation Issues
**Error**: Various PyQt6 compilation errors

**Solutions**:
- Try: `pip install PyQt6 --no-cache-dir`
- **Alternative**: Use Streamlit-only mode
- **Windows**: Ensure you have latest Visual C++ redistributables

### Installation Strategies

#### Strategy 1: Smart Installer (Recommended)
```bash
python setup_dependencies.py
```
- Handles errors gracefully
- Provides detailed reports
- Skips problematic packages

#### Strategy 2: Core Dependencies Only
```bash
pip install -r requirements-core.txt
```
- Essential packages only
- Higher success rate
- Add optional packages later

#### Strategy 3: Manual Installation
```bash
# Core packages first
pip install google-api-python-client requests python-dotenv
pip install pandas numpy Pillow pydantic

# UI frameworks
pip install streamlit  # Web UI
pip install PyQt6      # Desktop UI (optional)

# Optional enhancements
pip install plotly altair rich click
```

#### Strategy 4: Virtual Environment
```bash
# Create clean environment
python -m venv youtube_analyzer_env

# Windows
youtube_analyzer_env\Scripts\activate

# Install dependencies
python setup_dependencies.py
```

### System-Specific Issues

#### Windows
- Install Visual C++ Build Tools if needed
- Use PowerShell or Command Prompt as Administrator
- Consider using Anaconda/Miniconda for complex packages

#### macOS
- Install Xcode Command Line Tools: `xcode-select --install`
- Use Homebrew for system dependencies if needed

#### Linux
- Install development packages: `sudo apt-get install python3-dev build-essential`
- For audio: `sudo apt-get install portaudio19-dev`

### Verification Steps

#### 1. Check Installation
```bash
python -c "import googleapiclient; print('Google API: OK')"
python -c "import streamlit; print('Streamlit: OK')"
python -c "import pandas; print('Pandas: OK')"
```

#### 2. Run Dependency Checker
```bash
python -m utils.dependency_checker --report
```

#### 3. Test Application
```bash
# Test main application
python main.py

# Test Streamlit UI
streamlit run ui/streamlit_app.py
```

### Getting Help

#### Before Reporting Issues
1. Run: `python setup_dependencies.py` and share the report
2. Check Python version: `python --version`
3. Try core dependencies only: `pip install -r requirements-core.txt`
4. Check system requirements (Visual C++, build tools, etc.)

#### Useful Commands for Debugging
```bash
# Check pip version
pip --version

# List installed packages
pip list

# Check for conflicts
pip check

# Clear pip cache
pip cache purge

# Upgrade pip
python -m pip install --upgrade pip
```

### Fallback Options

#### Minimal Installation
If all else fails, install only the absolute essentials:
```bash
pip install requests python-dotenv streamlit pandas
```

This provides:
- Basic HTTP requests
- Environment variable loading
- Web UI via Streamlit
- Data processing with Pandas

#### Docker Alternative
Consider using Docker for a consistent environment:
```dockerfile
FROM python:3.11-slim
COPY requirements-core.txt .
RUN pip install -r requirements-core.txt
```

### Performance Tips

- Use `--no-cache-dir` for problematic packages
- Install packages one by one to identify issues
- Use virtual environments to avoid conflicts
- Keep pip and setuptools updated
- Consider using conda for scientific packages