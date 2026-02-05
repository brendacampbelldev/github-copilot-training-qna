#!/usr/bin/env python3
"""
Demo script to show what discussions would be created without actually creating them.
This is useful for testing the CSV processing and sanitization without GitHub credentials.
"""

from import_discussions import (
    read_csv_file,
    filter_questions,
    sanitize_content,
    generate_title,
    CSV_FILE
)


def main():
    print("=" * 80)
    print("GitHub Discussions Importer - DRY RUN MODE")
    print("=" * 80)
    print("\nThis demo shows what discussions would be created from the CSV file")
    print("without actually creating them on GitHub.\n")
    
    # Read CSV
    print(f"Reading CSV file: {CSV_FILE}")
    try:
        rows = read_csv_file(CSV_FILE)
        print(f"✓ Found {len(rows)} total rows")
    except Exception as e:
        print(f"✗ Error: {e}")
        return
    
    # Filter questions
    questions = filter_questions(rows)
    print(f"✓ Filtered to {len(questions)} ATTENDEE questions\n")
    
    if not questions:
        print("No questions found to process.")
        return
    
    # Process and display each question
    print("=" * 80)
    print("DISCUSSIONS THAT WOULD BE CREATED:")
    print("=" * 80)
    
    for i, question in enumerate(questions, 1):
        original_content = question['Content']
        sanitized_content = sanitize_content(original_content)
        title = generate_title(sanitized_content)
        
        print(f"\n{'─' * 80}")
        print(f"Discussion #{i}")
        print(f"{'─' * 80}")
        print(f"Title:     {title}")
        print(f"Category:  Session Questions")
        print(f"\nBody:")
        print(sanitized_content)
        
        # Show what was redacted/removed
        if original_content != sanitized_content:
            print(f"\n[Privacy Protection Applied]")
            if '@' in original_content:
                print("  - Email addresses redacted")
            if any(keyword in original_content.lower() for keyword in ['thanks', 'regards', 'best', 'cheers']):
                print("  - Signature lines removed")
    
    print("\n" + "=" * 80)
    print(f"Summary: {len(questions)} discussions would be created")
    print("=" * 80)
    print("\nTo actually create these discussions, run:")
    print("  export GITHUB_TOKEN='your_token'")
    print("  python import_discussions.py")


if __name__ == "__main__":
    main()
