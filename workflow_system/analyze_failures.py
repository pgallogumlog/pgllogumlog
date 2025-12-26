"""
Analyze QA log failures and export detailed report.
"""
import os
import sys
import io
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Fix Windows console encoding issues
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from config.settings import Settings

def analyze_failures():
    """Read QA log and analyze failures."""
    settings = Settings()

    # Setup Google Sheets API
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_file(
        settings.google_sheets_credentials_file,
        scopes=SCOPES
    )
    service = build("sheets", "v4", credentials=creds)

    # Read from QA Logs sheet
    result = service.spreadsheets().values().get(
        spreadsheetId=settings.google_sheets_qa_log_id,
        range="QA Logs!A:G"
    ).execute()

    rows = result.get('values', [])

    if len(rows) <= 1:
        print("No test data found")
        return

    header = rows[0]
    data_rows = rows[1:]

    # Parse failures
    failures = []
    passes = []

    for row in data_rows:
        while len(row) < 7:
            row.append("")

        timestamp, run_id, client, score, status, audit, fixes = row[:7]

        test_data = {
            "timestamp": timestamp,
            "run_id": run_id,
            "client": client,
            "score": score,
            "status": status,
            "audit": audit,
            "fixes": fixes
        }

        if status == "FAIL":
            failures.append(test_data)
        elif status == "PASS":
            passes.append(test_data)

    # Print summary
    print("="*100)
    print(f"TEST RESULTS ANALYSIS")
    print("="*100)
    print(f"Total tests: {len(data_rows)}")
    print(f"Passes: {len(passes)} ({len(passes)/len(data_rows)*100:.1f}%)")
    print(f"Failures: {len(failures)} ({len(failures)/len(data_rows)*100:.1f}%)")
    print("="*100)

    # Analyze failure patterns
    print(f"\n{'='*100}")
    print(f"FAILURE ROOT CAUSE ANALYSIS ({len(failures)} failures)")
    print(f"{'='*100}\n")

    # Categorize failures
    consensus_failures = []
    qa_parser_failures = []
    other_failures = []

    for i, failure in enumerate(failures, 1):
        audit = failure['audit']

        print(f"FAILURE {i}/{len(failures)}")
        print(f"  Run ID: {failure['run_id']}")
        print(f"  Score: {failure['score']}")
        print(f"  Timestamp: {failure['timestamp']}")
        print(f"  Audit Explanation:")
        print(f"    {audit[:200]}...")  # First 200 chars
        print()

        # Categorize
        if "QA Parser Error" in audit or "Error code: 400" in audit:
            qa_parser_failures.append(failure)
            print(f"  >>> CATEGORY: QA Parser Error")
        elif "consensus" in audit.lower() or "confidence" in audit.lower():
            consensus_failures.append(failure)
            print(f"  >>> CATEGORY: Consensus/Confidence Issue")
        else:
            other_failures.append(failure)
            print(f"  >>> CATEGORY: Other")

        # Extract key issues
        if "Cause:" in audit:
            cause_start = audit.index("Cause:")
            cause_end = audit.find("\n", cause_start)
            if cause_end == -1:
                cause_end = len(audit)
            cause = audit[cause_start:cause_end].strip()
            print(f"  >>> ROOT CAUSE: {cause}")

        print(f"  Recommended Fix:")
        print(f"    {failure['fixes'][:200]}...")
        print("-"*100)
        print()

    # Summary by category
    print("\n" + "="*100)
    print("FAILURE CATEGORIES")
    print("="*100)
    print(f"Consensus/Confidence Issues: {len(consensus_failures)} ({len(consensus_failures)/len(failures)*100:.1f}% of failures)")
    print(f"QA Parser Errors: {len(qa_parser_failures)} ({len(qa_parser_failures)/len(failures)*100:.1f}% of failures)")
    print(f"Other Issues: {len(other_failures)} ({len(other_failures)/len(failures)*100:.1f}% of failures)")
    print("="*100)

    # Extract full audit texts for consensus failures
    print("\n" + "="*100)
    print("DETAILED CONSENSUS FAILURE ANALYSIS")
    print("="*100)

    for i, failure in enumerate(consensus_failures, 1):
        print(f"\nConsensus Failure {i}:")
        print(failure['audit'])
        print("-"*100)

    # Save detailed report
    report_path = "qa_failure_analysis.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("QA FAILURE ANALYSIS REPORT\n")
        f.write("="*100 + "\n\n")
        f.write(f"Total tests: {len(data_rows)}\n")
        f.write(f"Passes: {len(passes)} ({len(passes)/len(data_rows)*100:.1f}%)\n")
        f.write(f"Failures: {len(failures)} ({len(failures)/len(data_rows)*100:.1f}%)\n\n")

        f.write("\nFAILURE DETAILS\n")
        f.write("="*100 + "\n\n")

        for i, failure in enumerate(failures, 1):
            f.write(f"FAILURE {i}\n")
            f.write(f"Run ID: {failure['run_id']}\n")
            f.write(f"Score: {failure['score']}\n")
            f.write(f"Timestamp: {failure['timestamp']}\n")
            f.write(f"\nAudit Explanation:\n{failure['audit']}\n")
            f.write(f"\nRecommended Fixes:\n{failure['fixes']}\n")
            f.write("\n" + "-"*100 + "\n\n")

    print(f"\n✓ Full report saved to: {report_path}")

if __name__ == "__main__":
    analyze_failures()
