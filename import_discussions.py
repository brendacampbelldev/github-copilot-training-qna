#!/usr/bin/env python3
"""
Script to import Q&A questions from CSV and create GitHub Discussions.

This script reads a CSV file containing Q&A data and creates GitHub Discussions
for attendee questions while applying privacy and redaction rules.
"""

import csv
import os
import re
import sys
from typing import List, Dict, Optional

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)


# Configuration
CSV_FILE = "data/Q&A ReportClean.csv"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "brendacampbelldev")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY_NAME", "github-copilot-training-qna")
DISCUSSION_CATEGORY = "Session Questions"
TITLE_PREFIX = "Q&A: "
TITLE_MAX_LENGTH = 60  # Maximum chars from content to use in title
# Ensures truncated titles are at least this fraction of target length when breaking at word boundary
TITLE_WORD_BOUNDARY_THRESHOLD = 0.7


def redact_emails(text: str) -> str:
    """
    Redact email addresses from text by replacing them with [redacted-email].
    
    Args:
        text: Input text that may contain email addresses
        
    Returns:
        Text with email addresses replaced
    """
    # Comprehensive email regex pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.sub(email_pattern, '[redacted-email]', text)


def remove_signature_lines(text: str) -> str:
    """
    Remove signature-like lines that may contain names.
    
    Removes lines starting with common signature patterns like:
    - Thanks, Regards, Best, Cheers (with optional comma)
    - From:, Sent:, To:, Cc:
    And removes all subsequent lines after a signature pattern is found.
    
    Also handles inline signatures by removing trailing signature patterns
    like ", Thanks, Name" or ". Regards, Name" from the end of text.
    
    Args:
        text: Input text that may contain signature lines
        
    Returns:
        Text with signature lines removed
    """
    lines = text.split('\n')
    cleaned_lines = []
    
    # Signature patterns to match at the start of lines (case-insensitive)
    signature_patterns = [
        r'^\s*thanks[\s,]',
        r'^\s*thank you[\s,]',
        r'^\s*regards[\s,]',
        r'^\s*best[\s,]',
        r'^\s*cheers[\s,]',
        r'^\s*sincerely[\s,]',
        r'^\s*from\s*:',
        r'^\s*sent\s*:',
        r'^\s*to\s*:',
        r'^\s*cc\s*:',
        r'^\s*bcc\s*:',
        r'^\s*subject\s*:',
    ]
    
    found_signature = False
    
    for line in lines:
        # Once we find a signature, skip all remaining lines
        if found_signature:
            continue
            
        # Check if line matches any signature pattern
        is_signature = False
        for pattern in signature_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                is_signature = True
                found_signature = True
                break
        
        if not is_signature:
            cleaned_lines.append(line)
    
    result = '\n'.join(cleaned_lines).strip()
    
    # Handle inline signatures at the end of text
    # Pattern: [.!?] [Thanks|Regards|Best|Cheers|Sincerely][, ].*$
    # This removes everything from the signature keyword to the end
    inline_signature_pattern = r'[.!?]?\s+(thanks|thank you|regards|best regards|best|cheers|sincerely)[\s,]+.*$'
    result = re.sub(inline_signature_pattern, '', result, flags=re.IGNORECASE)
    
    # Also handle signatures preceded by comma like ", Thanks, Name"
    inline_signature_pattern2 = r',\s+(thanks|thank you|regards|best regards|best|cheers|sincerely)[\s,]+.*$'
    result = re.sub(inline_signature_pattern2, '', result, flags=re.IGNORECASE)
    
    # Clean up by ensuring proper sentence ending
    result = result.rstrip()
    if result and not result[-1] in '.!?':
        result += '.'
    
    return result.strip()


def sanitize_content(content: str) -> str:
    """
    Apply all privacy and redaction rules to content.
    
    Args:
        content: Raw content from CSV
        
    Returns:
        Sanitized content safe for public discussion
    """
    # First redact emails
    content = redact_emails(content)
    
    # Then remove signature lines
    content = remove_signature_lines(content)
    
    return content.strip()


def generate_title(content: str, max_length: int = TITLE_MAX_LENGTH) -> str:
    """
    Generate a discussion title from content.
    
    Args:
        content: Question content
        max_length: Maximum length of content to include in title
        
    Returns:
        Title string in format "Q&A: [first N chars of content]"
    """
    # Take first max_length characters
    title_content = content[:max_length]
    
    # If we truncated, add ellipsis
    if len(content) > max_length:
        # Try to cut at last word boundary
        last_space = title_content.rfind(' ')
        if last_space > max_length * TITLE_WORD_BOUNDARY_THRESHOLD:
            title_content = title_content[:last_space]
        title_content += "..."
    
    return f"{TITLE_PREFIX}{title_content}"


def read_csv_file(filepath: str) -> List[Dict[str, str]]:
    """
    Read CSV file and return list of row dictionaries.
    
    Args:
        filepath: Path to CSV file
        
    Returns:
        List of dictionaries, one per row
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If CSV format is invalid
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CSV file not found: {filepath}")
    
    rows = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Validate required columns
        required_columns = {'Source', 'Type', 'Content', 'Reactions'}
        if not required_columns.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"CSV must contain columns: {required_columns}")
        
        for row in reader:
            rows.append(row)
    
    return rows


def filter_questions(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Filter rows to only include attendee questions.
    
    Args:
        rows: List of all CSV rows
        
    Returns:
        Filtered list containing only ATTENDEE + QUESTION rows
    """
    filtered = []
    for row in rows:
        if row.get('Source', '').upper() == 'ATTENDEE' and \
           row.get('Type', '').upper() == 'QUESTION':
            filtered.append(row)
    
    return filtered


def get_discussion_category_id(token: str, owner: str, repo: str, category_name: str) -> Optional[str]:
    """
    Get the category ID for a discussion category by name.
    
    Args:
        token: GitHub API token
        owner: Repository owner
        repo: Repository name
        category_name: Name of the discussion category
        
    Returns:
        Category ID string, or None if not found
    """
    # GraphQL query to get discussion categories
    query = """
    query($owner: String!, $repo: String!) {
      repository(owner: $owner, name: $repo) {
        discussionCategories(first: 10) {
          nodes {
            id
            name
          }
        }
      }
    }
    """
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": {"owner": owner, "repo": repo}},
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error fetching categories: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    categories = data.get("data", {}).get("repository", {}).get("discussionCategories", {}).get("nodes", [])
    
    for category in categories:
        if category["name"] == category_name:
            return category["id"]
    
    return None


def create_discussion(token: str, repo_id: str, category_id: str, title: str, body: str) -> bool:
    """
    Create a GitHub Discussion using GraphQL API.
    
    Args:
        token: GitHub API token
        repo_id: Repository ID
        category_id: Discussion category ID
        title: Discussion title
        body: Discussion body content
        
    Returns:
        True if successful, False otherwise
    """
    # GraphQL mutation to create discussion
    mutation = """
    mutation($repositoryId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
      createDiscussion(input: {repositoryId: $repositoryId, categoryId: $categoryId, title: $title, body: $body}) {
        discussion {
          id
          url
        }
      }
    }
    """
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    response = requests.post(
        "https://api.github.com/graphql",
        json={
            "query": mutation,
            "variables": {
                "repositoryId": repo_id,
                "categoryId": category_id,
                "title": title,
                "body": body
            }
        },
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error creating discussion: {response.status_code}")
        print(response.text)
        return False
    
    data = response.json()
    if "errors" in data:
        print(f"GraphQL errors: {data['errors']}")
        return False
    
    discussion_url = data.get("data", {}).get("createDiscussion", {}).get("discussion", {}).get("url")
    if discussion_url:
        print(f"Created discussion: {discussion_url}")
        return True
    
    return False


def get_repository_id(token: str, owner: str, repo: str) -> Optional[str]:
    """
    Get the repository ID using GraphQL API.
    
    Args:
        token: GitHub API token
        owner: Repository owner
        repo: Repository name
        
    Returns:
        Repository ID string, or None if not found
    """
    query = """
    query($owner: String!, $repo: String!) {
      repository(owner: $owner, name: $repo) {
        id
      }
    }
    """
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": {"owner": owner, "repo": repo}},
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error fetching repository: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    return data.get("data", {}).get("repository", {}).get("id")


def main():
    """Main entry point for the script."""
    print("=" * 60)
    print("GitHub Discussions Importer for Q&A Questions")
    print("=" * 60)
    
    # Validate environment
    if not GITHUB_TOKEN:
        print("\nError: GITHUB_TOKEN environment variable not set.")
        print("Please set it with a token that has 'repo' and 'write:discussion' scopes.")
        sys.exit(1)
    
    print(f"\nRepository: {REPO_OWNER}/{REPO_NAME}")
    print(f"CSV File: {CSV_FILE}")
    print(f"Discussion Category: {DISCUSSION_CATEGORY}")
    
    # Read CSV file
    print(f"\nReading CSV file...")
    try:
        rows = read_csv_file(CSV_FILE)
        print(f"Found {len(rows)} total rows")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Filter to attendee questions
    questions = filter_questions(rows)
    print(f"Filtered to {len(questions)} attendee questions")
    
    if not questions:
        print("\nNo questions to import. Exiting.")
        return
    
    # Get repository ID
    print(f"\nFetching repository information...")
    repo_id = get_repository_id(GITHUB_TOKEN, REPO_OWNER, REPO_NAME)
    if not repo_id:
        print("Error: Could not fetch repository ID")
        sys.exit(1)
    print(f"Repository ID: {repo_id}")
    
    # Get category ID
    print(f"Fetching discussion category '{DISCUSSION_CATEGORY}'...")
    category_id = get_discussion_category_id(GITHUB_TOKEN, REPO_OWNER, REPO_NAME, DISCUSSION_CATEGORY)
    if not category_id:
        print(f"Error: Could not find category '{DISCUSSION_CATEGORY}'")
        print("Please create the category in your repository's Discussions settings.")
        sys.exit(1)
    print(f"Category ID: {category_id}")
    
    # Process each question
    print(f"\nCreating discussions...")
    print("-" * 60)
    
    created_count = 0
    failed_count = 0
    
    for i, question in enumerate(questions, 1):
        content = question.get('Content', '')
        
        # Sanitize content
        sanitized_content = sanitize_content(content)
        
        # Generate title
        title = generate_title(sanitized_content)
        
        print(f"\n[{i}/{len(questions)}] Creating discussion:")
        print(f"  Title: {title}")
        print(f"  Content preview: {sanitized_content[:80]}...")
        
        # Create discussion
        success = create_discussion(GITHUB_TOKEN, repo_id, category_id, title, sanitized_content)
        
        if success:
            created_count += 1
        else:
            failed_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Successfully created: {created_count}")
    print(f"  Failed: {failed_count}")
    print("=" * 60)
    
    if failed_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
