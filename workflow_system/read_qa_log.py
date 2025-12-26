"""
Quick script to read QA log from Google Sheets for analysis.
"""
import os
import sys
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Fix Windows console encoding issues
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from config.settings import Settings

def read_qa_log():
    """Read all QA log entries from Google Sheets."""
    settings = Settings()

    # Setup Google Sheets API
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_file(
        settings.google_sheets_credentials_file,
        scopes=SCOPES
    )
    service = build("sheets", "v4", credentials=creds)

    # First, get sheet metadata to find sheet names
    sheet_metadata = service.spreadsheets().get(
        spreadsheetId=settings.google_sheets_qa_log_id
    ).execute()

    sheets = sheet_metadata.get('sheets', [])
    print(f"Available sheets: {[s['properties']['title'] for s in sheets]}")

    # Try reading from first sheet (or specific sheet name)
    sheet_name = sheets[0]['properties']['title'] if sheets else 'Sheet1'
    print(f"Reading from sheet: {sheet_name}")

    # Read all data from QA Log sheet
    result = service.spreadsheets().values().get(
        spreadsheetId=settings.google_sheets_qa_log_id,
        range=f"{sheet_name}!A:G"  # Columns: Timestamp, Run ID, Client, Score, Status, Audit, Fixes
    ).execute()

    rows = result.get('values', [])

    if not rows:
        print("No data found in QA Log")
        return

    # Print header
    print("Total rows:", len(rows))
    print("\n" + "="*150)

    # Print all rows
    for i, row in enumerate(rows):
        # Pad row to ensure 7 columns
        while len(row) < 7:
            row.append("")

        if i == 0:
            # Header row
            print(f"{'Timestamp':<20} {'Run ID':<12} {'Client':<15} {'Score':<6} {'Status':<7} {'Audit Explanation':<50} {'Fixes':<30}")
            print("="*150)
        else:
            timestamp, run_id, client, score, status, audit, fixes = row[0], row[1], row[2], row[3], row[4], row[5] if len(row) > 5 else "", row[6] if len(row) > 6 else ""
            # Truncate long text
            audit_short = (audit[:47] + "...") if len(audit) > 50 else audit
            fixes_short = (fixes[:27] + "...") if len(fixes) > 30 else fixes
            print(f"{timestamp:<20} {run_id:<12} {client:<15} {score:<6} {status:<7} {audit_short:<50} {fixes_short:<30}")

    print("="*150)

    # Count failures
    failures = [row for row in rows[1:] if len(row) > 4 and row[4] == "FAIL"]
    passes = [row for row in rows[1:] if len(row) > 4 and row[4] == "PASS"]

    print(f"\nSummary:")
    print(f"  Total tests: {len(rows) - 1}")
    print(f"  Passes: {len(passes)}")
    print(f"  Failures: {len(failures)}")
    print(f"  Success rate: {len(passes)/(len(rows)-1)*100:.1f}%")

    return rows

if __name__ == "__main__":
    read_qa_log()
