"""Pytest configuration for Alpaca broker integration tests."""

import pytest
import sys
import os

# Add the project root to sys.path so tests can import the broker modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import all fixtures
pytest_plugins = [
    "tests.fixtures.alpaca_fixtures"
]

# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "slow: mark test as slow")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        # Add integration marker for tests in integration directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


# Test data fixtures
@pytest.fixture
def test_oauth_auth_code():
    """Test OAuth authorization code."""
    return "test_auth_code_12345"


@pytest.fixture
def test_oauth_tokens():
    """Test OAuth tokens response."""
    return {
        "access_token": "access_token_xyz",
        "refresh_token": "refresh_token_abc",
        "expires_in": 3600,
        "token_type": "Bearer"
    }


@pytest.fixture
def test_account_data():
    """Test account data."""
    return {
        "id": "1f4f7e0b-2e6a-4c5b-8c9d-3e2f1a0b9c8d",
        "account_number": "12345678",
        "status": "ACTIVE",
        "buying_power": "400000",
        "cash": "100000",
        "portfolio_value": "115662.3"
    }


@pytest.fixture
def test_positions_data():
    """Test positions data."""
    return [
        {
            "asset_id": "b0b6dd9d-8b9b-48a9-ba46-bfa13b4a2386",
            "symbol": "AAPL",
            "exchange": "NASDAQ",
            "asset_class": "us_equity",
            "avg_entry_price": "100.0",
            "qty": "10",
            "side": "long",
            "market_value": "1050.0",
            "cost_basis": "1000.0",
            "unrealized_pl": "50.0",
            "unrealized_plpc": "0.05",
            "current_price": "105.0",
            "lastday_price": "104.0",
            "change_today": "0.0096",
            "asset_marginable": True
        },
        {
            "asset_id": "9c6b5e2c-6a8e-4c2c-b41c-3d6f5c9b3e8a",
            "symbol": "TSLA",
            "exchange": "NASDAQ",
            "asset_class": "us_equity",
            "avg_entry_price": "200.0",
            "qty": "5",
            "side": "long",
            "market_value": "1100.0",
            "cost_basis": "1000.0",
            "unrealized_pl": "100.0",
            "unrealized_plpc": "0.10",
            "current_price": "220.0",
            "lastday_price": "210.0",
            "change_today": "0.0476",
            "asset_marginable": True
        }
    ]


@pytest.fixture
def test_order_data():
    """Test order data."""
    return {
        "id": "61e69015-8549-4bfd-b9c3-01e75843f47d",
        "client_order_id": "eb9e2aaa-f71a-4f51-b5b4-52a6c565dad4",
        "created_at": "2022-01-03T17:03:34.217138Z",
        "updated_at": "2022-01-03T17:03:34.217138Z",
        "submitted_at": "2022-01-03T17:03:34.217138Z",
        "filled_at": None,
        "expired_at": None,
        "canceled_at": None,
        "failed_at": None,
        "replaced_at": None,
        "replaced_by": None,
        "replaces": None,
        "asset_id": "b0b6dd9d-8b9b-48a9-ba46-bfa13b4a2386",
        "symbol": "AAPL",
        "asset_class": "us_equity",
        "notional": None,
        "qty": "10",
        "filled_qty": "0",
        "filled_avg_price": None,
        "order_class": "",
        "order_type": "market",
        "type": "market",
        "side": "buy",
        "time_in_force": "day",
        "limit_price": None,
        "stop_price": None,
        "status": "accepted",
        "extended_hours": False,
        "legs": None,
        "trail_percent": None,
        "trail_price": None,
        "hwm": None,
        "commission": "1.25",
        "source": "access_key"
    }


@pytest.fixture
def test_asset_data():
    """Test asset data."""
    return {
        "id": "b0b6dd9d-8b9b-48a9-ba46-bfa13b4a2386",
        "class": "us_equity",
        "exchange": "NASDAQ",
        "symbol": "AAPL",
        "status": "active",
        "tradable": True,
        "marginable": True,
        "shortable": True,
        "easy_to_borrow": True,
        "fractionable": True
    }
