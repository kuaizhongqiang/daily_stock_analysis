# -*- coding: utf-8 -*-
"""Tests for StockPoolService."""
from src.services.stock_pool_service import StockPoolService


class TestStockPoolService:
    """Stock pool CRUD tests."""

    def setup_method(self):
        self.service = StockPoolService()
        self.pool = self.service.create_pool("_test_pool", "test", "test")
        # Ensure clean state
        if self.pool is None:
            # Pool exists from previous run, delete and recreate
            for p in self.service.list_pools(active_only=False):
                if "_test_pool" in p["name"]:
                    self.service.delete_pool(p["id"])
            self.pool = self.service.create_pool("_test_pool", "test", "test")

    def teardown_method(self):
        if self.pool:
            self.service.delete_pool(self.pool["id"])

    def test_create_pool(self):
        assert self.pool is not None
        assert self.pool["name"] == "_test_pool"
        assert self.pool["description"] == "test"

    def test_create_duplicate_pool(self):
        dup = self.service.create_pool("_test_pool")
        assert dup is None

    def test_list_pools(self):
        pools = self.service.list_pools()
        names = [p["name"] for p in pools]
        assert "_test_pool" in names

    def test_get_pool(self):
        fetched = self.service.get_pool(self.pool["id"])
        assert fetched is not None
        assert fetched["name"] == "_test_pool"

    def test_update_pool(self):
        ok = self.service.update_pool(self.pool["id"], description="Updated")
        assert ok
        updated = self.service.get_pool(self.pool["id"])
        assert updated["description"] == "Updated"

    def test_add_stock_success(self):
        ok = self.service.add_stock(self.pool["id"], "600519", "cn", "test")
        assert ok is True

    def test_add_duplicate_stock(self):
        self.service.add_stock(self.pool["id"], "600519", "cn")
        ok = self.service.add_stock(self.pool["id"], "600519", "cn")
        assert ok is True  # idempotent

    def test_remove_stock(self):
        self.service.add_stock(self.pool["id"], "600519", "cn")
        ok = self.service.remove_stock(self.pool["id"], "600519")
        assert ok is True

    def test_remove_nonexistent_stock(self):
        ok = self.service.remove_stock(self.pool["id"], "NONEXIST")
        assert ok is False

    def test_delete_pool(self):
        self.service.add_stock(self.pool["id"], "600519", "cn")
        ok = self.service.delete_pool(self.pool["id"])
        assert ok
        self.pool = None  # prevent double-delete in teardown
