# -*- coding: utf-8 -*-
"""Tests for HistoryRetentionService."""
import json
from src.services.history_retention_service import HistoryRetentionService


class TestHistoryRetentionService:
    """History service tests."""

    def setup_method(self):
        self.service = HistoryRetentionService()

    def test_get_stats(self):
        stats = self.service.get_stats()
        assert "analysis_count" in stats
        assert "conversation_count" in stats
        assert isinstance(stats["analysis_count"], int)

    def test_search_and_export(self):
        results = self.service.search_history("test", days=3650, limit=5)
        assert isinstance(results, list)

        json_data = self.service.export_analysis_json(days=3650)
        parsed = json.loads(json_data)
        assert isinstance(parsed, list)

        csv_data = self.service.export_analysis_csv(days=3650)
        assert isinstance(csv_data, str)

    def test_sessions(self):
        sessions = self.service.list_sessions(days=3650)
        assert isinstance(sessions, list)
