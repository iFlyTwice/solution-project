# SolutionGUI

A Python-based GUI application for managing various system operations and utilities.

## Features

- VPN Settings Management
- Security Key Management
- System Tray Integration
- Automated Browser Actions
- Device Monitoring
- Notification System

## Project Structure

```
solutiongui2/
├── Core.py                    # Main application core
├── gui_helpers.py            # GUI utility functions
├── settings_window.py        # Settings window implementation
├── utils/
│   └── logging_utils.py      # Centralized logging system
├── tests/                    # Test suite
└── requirements.txt          # Project dependencies
```

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Dependencies

- python-dotenv (≥1.0.0): Environment variable management
- customtkinter (≥5.2.0): Modern UI widgets
- playwright (≥1.40.0): Browser automation
- Additional dependencies listed in requirements.txt

## Usage

Run the application:
```bash
python Core.py
```

## Development

### Setting Up Development Environment

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install development dependencies:
```bash
pip install -r requirements.txt
```

### Running Tests

```bash
python -m pytest tests/
```

### Logging

The application uses a centralized logging system (`utils/logging_utils.py`). Logs are stored in the `logs` directory with daily rotation.

To use logging in your module:
```python
from utils.logging_utils import get_logger

logger = get_logger()
logger.info("Your log message")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Your License Here]
