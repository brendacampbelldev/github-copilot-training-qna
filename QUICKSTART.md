# Quick Reference Guide

## Setup (One-time)

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Create a GitHub Personal Access Token
# Go to: GitHub Settings → Developer settings → Personal access tokens
# Required scopes: repo, write:discussion

# 3. Create "Session Questions" category in your repository
# Go to: Repository → Discussions → Categories (gear icon) → New category
```

## Usage

### Preview Questions (No Token Required)
```bash
python demo.py
```

### Import Questions to GitHub Discussions
```bash
export GITHUB_TOKEN="ghp_your_token_here"
python import_discussions.py
```

### Custom Repository
```bash
export GITHUB_TOKEN="ghp_your_token_here"
export GITHUB_REPOSITORY_OWNER="your-org"
export GITHUB_REPOSITORY_NAME="your-repo"
python import_discussions.py
```

## CSV Format

Place your CSV at `data/Q&A ReportClean.csv`:

```csv
Source,Type,Content
ATTENDEE,QUESTION,"Your question here"
```

**Required columns:**
- `Source`: Must be "ATTENDEE" for questions to be imported
- `Type`: Must be "QUESTION" for questions to be imported
- `Content`: The question text (will be sanitized)

## Privacy Rules Applied

✓ Emails redacted: `user@example.com` → `[redacted-email]`
✓ Signatures removed: `Thanks, John` → removed
✓ Only ATTENDEE questions imported
✓ Names after signatures removed

## Troubleshooting

**Error: GITHUB_TOKEN not set**
```bash
export GITHUB_TOKEN="your_token_here"
```

**Error: Category 'Session Questions' not found**
- Create the category in your repository's Discussions settings first

**Error: CSV file not found**
- Ensure file is at `data/Q&A ReportClean.csv`
- File name must match exactly (including spaces and ampersand)

## Examples

### Test with sample data:
```bash
# See what would be created
python demo.py

# Output shows:
# - 4 discussions from sample CSV
# - Privacy protection applied
# - Generated titles and content
```

### Run actual import:
```bash
export GITHUB_TOKEN="ghp_xxxx"
python import_discussions.py

# Output shows:
# - Progress for each discussion
# - Success/failure status
# - Direct links to created discussions
```

## Files

- `import_discussions.py` - Main import script
- `demo.py` - Preview mode (no API calls)
- `data/Q&A ReportClean.csv` - Input CSV file
- `USAGE.md` - Full documentation
