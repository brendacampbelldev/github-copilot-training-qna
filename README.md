# GitHub Copilot Training Q&A

FAQ and automated discussion importer for GitHub Copilot training sessions.

## Features

- **Automated Discussion Import**: Import Q&A questions from CSV files into GitHub Discussions
- **Privacy Protection**: Automatic redaction of emails and personal information
- **Smart Filtering**: Only imports attendee questions, filters out other content

## Quick Start

See [USAGE.md](USAGE.md) for detailed setup and usage instructions.

### Preview Mode (No GitHub Token Required)

Run the demo script to see what discussions would be created:

```bash
python demo.py
```

### Full Import

```bash
# Install dependencies
pip install -r requirements.txt

# Set your GitHub token
export GITHUB_TOKEN="your_token_here"

# Run the import
python import_discussions.py
```

## Documentation

- [USAGE.md](USAGE.md) - Comprehensive usage guide
- [import_discussions.py](import_discussions.py) - Main import script
- [demo.py](demo.py) - Preview what discussions would be created (no token required)
