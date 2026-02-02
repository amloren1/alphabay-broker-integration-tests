"""
Integration tests for Alpaca broker workflows.

This module provides comprehensive test coverage for:
- OAuth authentication and token management
- Account synchronization (positions, transactions, balances)
- Order placement and management (market, limit orders)
- Error handling (rate limits, API failures, network issues)
- Edge cases (token expiration, timeouts, trading halts)
"""

import json
import time
from unittest.mock import Mock, patch, MagicMock
import pytest
import requests
from requests.exceptions import Timeout, ConnectionError

from broker_alpaca import AlpacaBroker
from broker_errors import (
    BrokerAuthenticationError,
    BrokerRateLimitError,
    BrokerAPIError,
    BrokerNetworkError,
    OrderValidationError
)


class TestAlpacaOAuthFlow:
    """Test OAuth2 authentication and token management."""

    def test_oauth_authorization_success(self, mock_alpaca_auth, alpaca_broker):
        """Test successful OAuth2 authorization flow."""
        # Arrange
        auth_code = "test_auth_code_12345"
        expected_access_token = "access_token_xyz"
        expected_refresh_token = "refresh_token_abc"

        mock_alpaca_auth.return_value = {
            "access_token": expected_access_token,
            "refresh_token": expected_refresh_token,
            "expires_in": 3600,
            "token_type": "Bearer"
        }

        # Act
        result = alpaca_broker.authenticate(auth_code)

        # Assert
        assert result is True
        assert alpaca_broker.access_token == expected_access_token
        assert alpaca_broker.refresh_token == expected_refresh_token
        mock_alpaca_auth.assert_called_once_with(auth_code)

    def test_token_refresh_success(self, mock_alpaca_token_refresh, alpaca_broker):
        """Test successful token refresh."""
        # Arrange
        alpaca_broker.access_token = "expired_token"
        alpaca_broker.refresh_token = "valid_refresh_token"
        alpaca_broker.token_expires_at = time.time() - 100  # Expired

        new_access_token = "new_access_token_789"
        new_refresh_token = "new_refresh_token_456"

        mock_alpaca_token_refresh.return_value = {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "expires_in": 3600,
            "token_type": "Bearer"
        }

        # Act
        result = alpaca_broker.refresh_access_token()

        # Assert
        assert result is True
        assert alpaca_broker.access_token == new_access_token
        assert alpaca_broker.refresh_token == new_refresh_token
        assert alpaca_broker.token_expires_at > time.time()
        mock_alpaca_token_refresh.assert_called_once()

    def test_invalid_token_handling(self, mock_alpaca_api_error, alpaca_broker):
        """Test handling of invalid/expired tokens."""
        # Arrange
        alpaca_broker.access_token = "invalid_token"
        mock_alpaca_api_error.status_code = 401
        mock_alpaca_api_error.response.json.return_value = {
            "code": 40110000,
            "message": "Invalid or expired token"
        }

        # Act & Assert
        with pytest.raises(BrokerAuthenticationError) as exc_info:
            alpaca_broker.get_account()

        assert "Invalid or expired token" in str(exc_info.value)
        assert exc_info.value.status_code == 401

    def test_concurrent_token_refresh(self, mock_alpaca_token_refresh, alpaca_broker):
        """Test concurrent token refresh scenarios."""
        # Arrange
        alpaca_broker.access_token = "expired_token"
        alpaca_broker.refresh_token = "valid_refresh_token"
        alpaca_broker.token_expires_at = time.time() - 100

        refresh_count = 0

        def simulate_refresh(*args, **kwargs):
            nonlocal refresh_count
            refresh_count += 1
            time.sleep(0.1)  # Simulate network delay
            return {
                "access_token": f"new_token_{refresh_count}",
                "refresh_token": "new_refresh",
                "expires_in": 3600,
                "token_type": "Bearer"
            }

        mock_alpaca_token_refresh.side_effect = simulate_refresh

        # Act - Simulate concurrent calls
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(alpaca_broker.refresh_if_needed)
                for _ in range(3)
            ]
            results = [f.result() for f in futures]

        # Assert - Should only refresh once due to locking
        assert refresh_count == 1
        assert all(results)


class TestAlpacaAccountSync:
    """Test account data retrieval and synchronization."""

    def test_get_positions_success(self, mock_alpaca_positions, alpaca_broker_authenticated):
        """Test successful portfolio positions retrieval."""
        # Arrange
        expected_positions = [
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

        mock_alpaca_positions.return_value = expected_positions

        # Act
        positions = alpaca_broker_authenticated.get_positions()

        # Assert
        assert len(positions) == 2
        assert positions[0].symbol == "AAPL"
        assert positions[0].qty == 10.0
        assert positions[0].market_value == 1050.0
        assert positions[1].symbol == "TSLA"
        assert positions[1].unrealized_pl == 100.0
        mock_alpaca_positions.assert_called_once()

    def test_get_transactions_pagination(self, mock_alpaca_transactions, alpaca_broker_authenticated):
        """Test transaction history with pagination."""
        # Arrange - Mock multiple pages
        page1 = [
            {"id": f"txn_{i}", "symbol": "AAPL", "amount": "100.0"}
            for i in range(100)
        ]
        page2 = [
            {"id": f"txn_{i+100}", "symbol": "TSLA", "amount": "200.0"}
            for i in range(50)
        ]

        mock_alpaca_transactions.side_effect = [page1, page2]

        # Act
        all_transactions = []
        for batch in alpaca_broker_authenticated.get_transactions(limit=150):
            all_transactions.extend(batch)

        # Assert
        assert len(all_transactions) == 150
        assert mock_alpaca_transactions.call_count == 2
        # Verify pagination params were passed correctly
        calls = mock_alpaca_transactions.call_args_list
        assert calls[0][1]["limit"] == 100
        assert calls[1][1]["limit"] == 50

    def test_get_account_balance(self, mock_alpaca_account, alpaca_broker_authenticated):
        """Test account balance and status retrieval."""
        # Arrange
        expected_account = {
            "id": "1f4f7e0b-2e6a-4c5b-8c9d-3e2f1a0b9c8d",
            "account_number": "12345678",
            "status": "ACTIVE",
            "crypto_status": "ACTIVE",
            "currency": "USD",
            "buying_power": "400000",
            "regt_buying_power": "400000",
            "daytrading_buying_power": "400000",
            "effective_buying_power": "400000",
            "non_marginable_buying_power": "200000",
            "cash": "100000",
            "accrued_fees": "0",
            "portfolio_value": "115662.3",
            "pattern_day_trader": False,
            "trading_blocked": False,
            "transfers_blocked": False,
            "account_blocked": False,
            "created_at": "2022-01-01T00:00:00Z",
            "trade_suspended_by_user": False,
            "multiplier": "4",
            "shorting_enabled": True,
            "short_market_value": "0",
            "long_market_value": "115662.3",
            "equity": "115662.3",
            "last_equity": "115000.50",
            "initial_margin": "0",
            "maintenance_margin": "0",
            "last_maintenance_margin": "0",
            "sma": "0",
            "daytrade_count": "0"
        }

        mock_alpaca_account.return_value = expected_account

        # Act
        account = alpaca_broker_authenticated.get_account()

        # Assert
        assert account.status == "ACTIVE"
        assert account.buying_power == 400000.0
        assert account.portfolio_value == 115662.3
        assert account.cash == 100000.0
        assert account.pattern_day_trader is False
        mock_alpaca_account.assert_called_once()

    def test_get_asset_info_success(self, mock_alpaca_asset, alpaca_broker_authenticated):
        """Test asset information lookup."""
        # Arrange
        expected_asset = {
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

        mock_alpaca_asset.return_value = expected_asset

        # Act
        asset = alpaca_broker_authenticated.get_asset("AAPL")

        # Assert
        assert asset.symbol == "AAPL"
        assert asset.exchange == "NASDAQ"
        assert asset.tradable is True
        assert asset.marginable is True
        assert asset.fractionable is True
        mock_alpaca_asset.assert_called_once_with("AAPL")


class TestAlpacaOrderPlacement:
    """Test order placement and management."""

    def test_place_market_order_success(self, mock_alpaca_order, alpaca_broker_authenticated):
        """Test successful market order placement."""
        # Arrange
        order_data = {
            "symbol": "AAPL",
            "qty": 10,
            "side": "buy",
            "type": "market",
            "time_in_force": "day"
        }

        expected_order = {
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

        mock_alpaca_order.return_value = expected_order

        # Act
        order = alpaca_broker_authenticated.place_order(**order_data)

        # Assert
        assert order.id == "61e69015-8549-4bfd-b9c3-01e75843f47d"
        assert order.symbol == "AAPL"
        assert order.qty == 10.0
        assert order.status == "accepted"
        assert order.type == "market"
        mock_alpaca_order.assert_called_once()

    def test_place_limit_order_success(self, mock_alpaca_order, alpaca_broker_authenticated):
        """Test successful limit order placement."""
        # Arrange
        order_data = {
            "symbol": "TSLA",
            "qty": 5,
            "side": "buy",
            "type": "limit",
            "limit_price": 200.0,
            "time_in_force": "gtc"
        }

        expected_order = {
            "id": "82f7f8d3-1b3b-4c4d-9c6d-2e3f4a5b6c7d",
            "symbol": "TSLA",
            "qty": "5",
            "type": "limit",
            "limit_price": "200.0",
            "side": "buy",
            "time_in_force": "gtc",
            "status": "accepted"
        }

        mock_alpaca_order.return_value = expected_order

        # Act
        order = alpaca_broker_authenticated.place_order(**order_data)

        # Assert
        assert order.type == "limit"
        assert float(order.limit_price) == 200.0
        assert order.time_in_force == "gtc"
        mock_alpaca_order.assert_called_once()

    def test_check_order_status(self, mock_alpaca_order_status, alpaca_broker_authenticated):
        """Test order status checking."""
        # Arrange
        order_id = "61e69015-8549-4bfd-b9c3-01e75843f47d"
        expected_status = {
            "id": order_id,
            "symbol": "AAPL",
            "qty": "10",
            "filled_qty": "5",
            "status": "partially_filled",
            "filled_avg_price": "105.5"
        }

        mock_alpaca_order_status.return_value = expected_status

        # Act
        status = alpaca_broker_authenticated.get_order_status(order_id)

        # Assert
        assert status.id == order_id
        assert status.status == "partially_filled"
        assert status.filled_qty == 5.0
        assert float(status.filled_avg_price) == 105.5
        mock_alpaca_order_status.assert_called_once_with(order_id)

    def test_cancel_order_success(self, mock_alpaca_cancel_order, alpaca_broker_authenticated):
        """Test successful order cancellation."""
        # Arrange
        order_id = "61e69015-8549-4bfd-b9c3-01e75843f47d"
        mock_alpaca_cancel_order.return_value = {"status": "canceled"}

        # Act
        result = alpaca_broker_authenticated.cancel_order(order_id)

        # Assert
        assert result is True
        mock_alpaca_cancel_order.assert_called_once_with(order_id)

    def test_order_validation_insufficient_funds(self, mock_alpaca_order_error, alpaca_broker_authenticated):
        """Test order validation for insufficient funds."""
        # Arrange
        order_data = {
            "symbol": "AAPL",
            "notional": 1000000,  # Way more than available
            "side": "buy",
            "type": "market",
            "time_in_force": "day"
        }

        mock_alpaca_order_error.status_code = 403
        mock_alpaca_order_error.response.json.return_value = {
            "code": 40310000,
            "message": "insufficient buying power"
        }

        # Act & Assert
        with pytest.raises(OrderValidationError) as exc_info:
            alpaca_broker_authenticated.place_order(**order_data)

        assert "insufficient buying power" in str(exc_info.value)
        assert exc_info.value.status_code == 403

    def test_order_validation_invalid_symbol(self, mock_alpaca_order_error, alpaca_broker_authenticated):
        """Test order validation for invalid symbols."""
        # Arrange
        order_data = {
            "symbol": "INVALID",
            "qty": 10,
            "side": "buy",
            "type": "market",
            "time_in_force": "day"
        }

        mock_alpaca_order_error.status_code = 404
        mock_alpaca_order_error.response.json.return_value = {
            "code": 40410000,
            "message": "asset not found"
        }

        # Act & Assert
        with pytest.raises(OrderValidationError) as exc_info:
            alpaca_broker_authenticated.place_order(**order_data)

        assert "asset not found" in str(exc_info.value)
        assert exc_info.value.status_code == 404


class TestAlpacaErrorHandling:
    """Test error handling scenarios."""

    def test_rate_limit_handling(self, mock_alpaca_rate_limit, alpaca_broker_authenticated):
        """Test rate limit error handling."""
        # Arrange
        mock_alpaca_rate_limit.status_code = 429
        mock_alpaca_rate_limit.response.headers = {"x-ratelimit-reset": str(int(time.time()) + 60)}
        mock_alpaca_rate_limit.response.json.return_value = {
            "code": 42910000,
            "message": "rate limit exceeded"
        }

        # Act & Assert
        with pytest.raises(BrokerRateLimitError) as exc_info:
            alpaca_broker_authenticated.get_account()

        assert "rate limit exceeded" in str(exc_info.value)
        assert exc_info.value.retry_after == 60
        assert exc_info.value.status_code == 429

    def test_rate_limit_retry_with_backoff(self, mock_alpaca_rate_limit_then_success, alpaca_broker_authenticated):
        """Test rate limit retry with exponential backoff."""
        # Arrange
        successful_response = {
            "id": "test_account",
            "status": "ACTIVE",
            "cash": "100000"
        }

        # First call returns 429, second call succeeds
        mock_alpaca_rate_limit_then_success.side_effect = [
            requests.HTTPError(response=Mock(status_code=429)),
            successful_response
        ]

        # Act
        account = alpaca_broker_authenticated.get_account_with_retry(max_retries=2)

        # Assert
        assert account["status"] == "ACTIVE"
        assert mock_alpaca_rate_limit_then_success.call_count == 2

    def test_500_error_handling(self, mock_alpaca_server_error, alpaca_broker_authenticated):
        """Test 500 Internal Server Error handling."""
        # Arrange
        mock_alpaca_server_error.status_code = 500
        mock_alpaca_server_error.response.json.return_value = {
            "code": 50010000,
            "message": "internal server error"
        }

        # Act & Assert
        with pytest.raises(BrokerAPIError) as exc_info:
            alpaca_broker_authenticated.get_account()

        assert "internal server error" in str(exc_info.value)
        assert exc_info.value.status_code == 500

    def test_network_timeout_handling(self, mock_alpaca_timeout, alpaca_broker_authenticated):
        """Test network timeout handling."""
        # Arrange
        mock_alpaca_timeout.side_effect = Timeout("Request timed out")

        # Act & Assert
        with pytest.raises(BrokerNetworkError) as exc_info:
            alpaca_broker_authenticated.get_account()

        assert "Request timed out" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, Timeout)

    def test_connection_error_handling(self, mock_alpaca_connection_error, alpaca_broker_authenticated):
        """Test connection error handling."""
        # Arrange
        mock_alpaca_connection_error.side_effect = ConnectionError("Failed to connect")

        # Act & Assert
        with pytest.raises(BrokerNetworkError) as exc_info:
            alpaca_broker_authenticated.get_account()

        assert "Failed to connect" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, ConnectionError)

    def test_invalid_request_error(self, mock_alpaca_bad_request, alpaca_broker_authenticated):
