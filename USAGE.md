# GitHub Copilot Training Q&A - Discussion Importer

This repository contains a script to automatically import Q&A questions from training sessions into GitHub Discussions.

## Overview

The `import_discussions.py` script reads a CSV file containing Q&A data from training sessions and creates GitHub Discussions for attendee questions. It applies privacy and redaction rules to ensure no personal information is exposed.

## Features

- **Automated Import**: Reads questions from CSV and creates GitHub Discussions
- **Privacy Protection**: 
  - Redacts email addresses (replaced with `[redacted-email]`)
  - Removes signature lines that may contain names
  - Filters to only process ATTENDEE questions
- **Smart Title Generation**: Creates concise titles from question content
- **GitHub API Integration**: Uses GraphQL API to create discussions

## Setup

### Prerequisites

- Python 3.7 or higher
- GitHub Personal Access Token with:
  - `repo` scope (for private repos) or `public_repo` scope (for public repos)
  - `write:discussion` scope

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/brendacampbelldev/github-copilot-training-qna.git
   cd github-copilot-training-qna
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up GitHub token:
   ```bash
   export GITHUB_TOKEN="your_github_token_here"
   ```

## Usage

### Prepare Your Data

1. Place your Q&A CSV file at `data/Q&A ReportClean.csv`

2. Ensure the CSV has these columns:
   - `Source`: Who created the entry (e.g., ATTENDEE, MODERATOR, SPEAKER)
   - `Type`: Type of entry (e.g., QUESTION, ANSWER, COMMENT)
   - `Content`: The actual question or comment text
   - `Reactions`: Number of reactions (optional)

3. The CSV should already be "cleaned" - no Identity column with personal info

### Create Discussion Category

Before running the import:

1. Go to your repository on GitHub
2. Navigate to Discussions tab
3. Click on "Categories" (gear icon)
4. Create a new category named **"Session Questions"**

### Run the Import

First, preview what will be created (no token required):

```bash
python demo.py
```

Then run the actual import:

```bash
python import_discussions.py
```

The script will:
1. Read the CSV file
2. Filter to only ATTENDEE + QUESTION rows
3. Apply privacy/redaction rules to each question
4. Create one discussion per question in the "Session Questions" category

### Environment Variables

You can customize the behavior with environment variables:

- `GITHUB_TOKEN` (required): Your GitHub Personal Access Token
- `GITHUB_REPOSITORY_OWNER` (optional): Repository owner, defaults to `brendacampbelldev`
- `GITHUB_REPOSITORY_NAME` (optional): Repository name, defaults to `github-copilot-training-qna`

Example:
```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
export GITHUB_REPOSITORY_OWNER="myorg"
export GITHUB_REPOSITORY_NAME="myrepo"
python import_discussions.py
```

## CSV Format

Example CSV file:

```csv
Source,Type,Content,Reactions
ATTENDEE,QUESTION,"How do I install GitHub Copilot in VS Code?",5
MODERATOR,ANSWER,"You can install it from the Extensions marketplace.",2
ATTENDEE,QUESTION,"What are the pricing options?",3
ATTENDEE,COMMENT,"Great session, thank you!",10
```

## Privacy & Redaction Rules

The script applies the following privacy protections:

1. **Email Redaction**: All email addresses are replaced with `[redacted-email]`
   - Pattern: `user@domain.com` → `[redacted-email]`

2. **Signature Removal**: Lines starting with these patterns are removed:
   - Thanks, Thank you
   - Regards, Best regards
   - Cheers, Sincerely
   - From:, Sent:, To:, Cc:, Bcc:, Subject:

3. **Filtering**: Only processes rows where:
   - `Source == "ATTENDEE"`
   - `Type == "QUESTION"`

## Discussion Format

Each created discussion will have:

- **Title**: `Q&A: [first ~60 characters of question]...`
- **Body**: The sanitized question content
- **Category**: "Session Questions"

## Troubleshooting

### Error: GITHUB_TOKEN environment variable not set

Make sure you've exported your GitHub token:
```bash
export GITHUB_TOKEN="your_token_here"
```

### Error: Could not find category 'Session Questions'

Create the category in your repository's Discussions settings first.

### Error: CSV file not found

Ensure the CSV file is at `data/Q&A ReportClean.csv` (relative to script location).

### Permission Denied

Ensure your GitHub token has the required scopes:
- `repo` or `public_repo`
- `write:discussion`

## Development

### Running Tests

To test the redaction functions without creating discussions:

```python
python3 -c "
from import_discussions import sanitize_content

test_text = '''
How do I use Copilot?
Contact me at user@example.com
Thanks,
John Doe
'''

print(sanitize_content(test_text))
"
```

### Sample Data

A sample CSV file is included at `data/Q&A ReportClean.csv` for testing purposes.

## License

This project is provided as-is for use with GitHub Copilot training sessions.

## Support

For issues or questions, please open an issue in this repository.
