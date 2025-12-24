"""QA Dashboard data fetcher with caching."""
from typing import List, Dict, Any
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class QADashboardDataFetcher:
    """Fetches and caches QA data from Google Sheets."""

    def __init__(
        self,
        sheets_adapter,
        spreadsheet_id: str,
        cache_ttl_seconds: int = 300,  # 5 minutes
    ):
        """
        Initialize the data fetcher.

        Args:
            sheets_adapter: Google Sheets adapter for reading data
            spreadsheet_id: ID of the spreadsheet containing QA logs
            cache_ttl_seconds: Time-to-live for cached data in seconds
        """
        self._sheets = sheets_adapter
        self._spreadsheet_id = spreadsheet_id
        self._cache_ttl = cache_ttl_seconds
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}

    async def fetch_workflow_summary(self) -> List[Dict[str, Any]]:
        """
        Fetch from 'Workflow QA Summary' sheet with caching.

        Returns:
            List of workflow summary dictionaries from the sheet
        """
        cache_key = "workflow_summary"

        # Check cache
        if self._is_cache_valid(cache_key):
            logger.debug("cache_hit", key=cache_key)
            return self._cache[cache_key]

        # Fetch from Sheets
        try:
            data = await self._sheets.read_sheet(
                spreadsheet_id=self._spreadsheet_id, sheet_name="Workflow QA Summary"
            )

            # Update cache
            self._cache[cache_key] = data
            self._cache_timestamps[cache_key] = datetime.now()

            logger.info("data_fetched", sheet="Workflow QA Summary", rows=len(data))
            return data

        except Exception as e:
            logger.error("sheets_fetch_failed", error=str(e), sheet="Workflow QA Summary")
            return []

    def _is_cache_valid(self, key: str) -> bool:
        """
        Check if cache entry is still valid.

        Args:
            key: Cache key to check

        Returns:
            True if cache is valid, False otherwise
        """
        if key not in self._cache or key not in self._cache_timestamps:
            return False

        age = datetime.now() - self._cache_timestamps[key]
        return age.total_seconds() < self._cache_ttl
