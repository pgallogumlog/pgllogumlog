"""
Google Sheets Adapter.
Implements the SheetsClient interface for Google Sheets API.
Uses Service Account authentication (no browser required).
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import structlog

logger = structlog.get_logger()

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds


class SheetsAdapter:
    """
    Adapter for Google Sheets API.

    Implements the SheetsClient protocol for dependency injection.
    Uses Service Account for authentication.
    """

    def __init__(self, credentials_file: str):
        self._credentials_file = credentials_file
        self._service = None

    def _get_service(self):
        """Lazy-load Google Sheets API service with Service Account."""
        if self._service is None:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build

            SCOPES = [
                "https://www.googleapis.com/auth/spreadsheets",
            ]

            creds = Credentials.from_service_account_file(
                self._credentials_file,
                scopes=SCOPES
            )

            self._service = build("sheets", "v4", credentials=creds)
            logger.info("sheets_service_initialized", credentials_file=self._credentials_file)

        return self._service

    async def append_row(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        values: list[Any],
    ) -> bool:
        """
        Append a row to a Google Sheet with retry logic.

        Args:
            spreadsheet_id: The spreadsheet ID from the URL
            sheet_name: Name of the worksheet tab
            values: List of values for the row

        Returns:
            True if successful
        """

        def _append():
            service = self._get_service()
            body = {"values": [values]}
            service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A:A",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body,
            ).execute()
            return True

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                result = await asyncio.to_thread(_append)
                logger.info(
                    "sheets_row_appended",
                    spreadsheet_id=spreadsheet_id,
                    sheet_name=sheet_name,
                )
                return result
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    logger.warning(
                        "sheets_append_retry",
                        attempt=attempt + 1,
                        max_retries=MAX_RETRIES,
                        error=str(e),
                    )
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    logger.error(
                        "sheets_append_failed",
                        spreadsheet_id=spreadsheet_id,
                        error=str(e),
                    )
        return False

    async def read_sheet(
        self,
        spreadsheet_id: str,
        sheet_name: str,
    ) -> list[dict]:
        """
        Read all rows from a Google Sheet as dictionaries.

        Args:
            spreadsheet_id: The spreadsheet ID from the URL
            sheet_name: Name of the worksheet tab

        Returns:
            List of dictionaries (one per row, keys from header row)
        """

        def _read():
            service = self._get_service()
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=sheet_name,
            ).execute()

            rows = result.get("values", [])
            if len(rows) < 2:
                return []

            headers = rows[0]
            records = []
            for row in rows[1:]:
                # Pad row to match headers length
                padded_row = row + [""] * (len(headers) - len(row))
                records.append(dict(zip(headers, padded_row)))

            return records

        try:
            return await asyncio.to_thread(_read)
        except Exception as e:
            logger.error(
                "sheets_read_failed",
                spreadsheet_id=spreadsheet_id,
                error=str(e),
            )
            return []

    async def update_cell(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        row: int,
        col: int,
        value: Any,
    ) -> bool:
        """
        Update a single cell in a Google Sheet.

        Args:
            spreadsheet_id: The spreadsheet ID
            sheet_name: Name of the worksheet tab
            row: Row number (1-indexed)
            col: Column number (1-indexed)
            value: Value to set

        Returns:
            True if successful
        """

        def _update():
            service = self._get_service()
            # Convert col number to letter (1=A, 2=B, etc.)
            col_letter = chr(64 + col)
            range_notation = f"{sheet_name}!{col_letter}{row}"

            body = {"values": [[value]]}
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_notation,
                valueInputOption="USER_ENTERED",
                body=body,
            ).execute()
            return True

        try:
            return await asyncio.to_thread(_update)
        except Exception as e:
            logger.error(
                "sheets_update_failed",
                spreadsheet_id=spreadsheet_id,
                row=row,
                col=col,
                error=str(e),
            )
            return False
