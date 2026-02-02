"""Test fixtures for Alpaca broker integration tests."""

import pytest
from unittest.mock import Mock, MagicMock
from broker_alpaca import AlpacaBroker


@pytest.fixture
def alpaca_broker():
    """Create a basic AlpacaBroker instance for testing."""
    broker = AlpacaBroker()
    return broker


@pytest.fixture
def alpaca_broker_authenticated():
    """Create an authenticated AlpacaBroker instance."""
    import time
    broker = AlpacaBroker()
    broker.access_token = "test_access_token_12345"
    broker.refresh_token = "test_refresh_token_67890"
    broker.token_expires_at = time.time() + 3600
    broker.headers = {
        "Authorization": f"Bearer {broker.access_token}",
        "Content-Type": "application/json"
    }
    return broker


@pytest.fixture
def mock_alpaca_auth(monkeypatch):
    """Mock Alpaca OAuth2 authorization."""
    mock_auth = Mock()
    
    def _mock_auth(*args, **kwargs):
        return mock_auth(*args, **kwargs)
    
    monkeypatch.setattr(AlpacaBroker, 'authenticate', _mock_auth)
    return mock_auth


@pytest.fixture
def mock_alpaca_token_refresh(monkeypatch):
    """Mock Alpaca token refresh."""
    mock_refresh = Mock()
    
    def _mock_refresh(*args, **kwargs):
        return mock_refresh(*args, **kwargs)
    
    monkeypatch.setattr(AlpacaBroker, 'refresh_access_token', _mock_refresh)
    return mock_refresh


@pytest.fixture
def mock_alpaca_api_error(monkeypatch):
    """Mock API error responses."""
    mock_error = MagicMock()
    mock_error.response = Mock()
    mock_error.response.json = Mock()
    
    def _mock_get_account(*args, **kwargs):
        return mock_error
    
    monkeypatch.setattr(AlpacaBroker, 'get_account', _mock_get_account)
    return mock_error


@pytest.fixture
def mock_alpaca_positions(monkeypatch):
    """Mock position retrieval."""
    mock_positions = Mock()
    mock_positions.return_value.return_value = []
    
    def _mock_get_positions(*args, **kwargs):
        return mock_positions(*args, **kwargs)
    
    monkeypatch.setattr(AlpacaBroker, 'get_positions', _mock_get_positions)
    return mock_positions


@pytest.fixture
def mock_alpaca_transactions(monkeypatch):
    """Mock transaction retrieval."""
    mock_transactions = Mock()
    
    def _mock_get_transactions(*args, **kwargs):
        transactions = [{"id": f"txn_{i}", "symbol": "AAPL", "amount": "100.0"} for i in range(10)]
        yield transactions
    
    monkeypatch.setattr(AlpacaBroker, 'get_transactions', _mock_get_transactions)
    return mock_transactions


@pytest.fixture
def mock_alpaca_account(monkeypatch):
    """Mock account retrieval."""
    mock_account = Mock()
    
    def _mock_get_account(*args, **kwargs):
        return mock_account(*args, **kwargs)
    
    monkeypatch.setattr(AlpacaBroker, 'get_account', _mock_get_account)
    return mock_account


@pytest.fixture
def mock_alpaca_asset(monkeypatch):
    """Mock asset lookup."""
    mock_asset = Mock()
    mock_asset.return_value = {}
    
    def _mock_get_asset(*args, **kwargs):
        return mock_asset(*args, **kwargs)
    
    monkeypatch.setattr(AlpacaBroker, 'get_asset', _mock_get_asset)
    return mock_asset


@pytest.fixture
def mock_alpaca_order(monkeypatch):
    """Mock order placement."""
    mock_order = Mock()
    
    def _mock_place_order(*args, **kwargs):
        return mock_order(*args, **kwargs)
    
    monkeypatch.setattr(AlpacaBroker, 'place_order', _mock_place_order)
    return mock_order


@pytest.fixture
def mock_alpaca_order_status(monkeypatch):
    """Mock order status retrieval."""
    mock_status = Mock()
    
    def _mock_get_order_status(*args, **kwargs):
        return mock_status(*args, **kwargs)
    
    monkeypatch.setattr(AlpacaBroker, 'get_order_status', _mock_get_order_status)
    return mock_status


@pytest.fixture
def mock_alpaca_cancel_order(monkeypatch):
    """Mock order cancellation."""
    mock_cancel = Mock()
    
    def _mock_cancel_order(*args, **kwargs):
        return mock_cancel(*args, **kwargs)
    
    monkeypatch.setattr(AlpacaBroker, 'cancel_order', _mock_cancel_order)
    return mock_cancel


@pytest.fixture
def mock_alpaca_order_error(monkeypatch):
    """Mock order placement error."""
    import requests
    mock_error = MagicMock()
    mock_error.response = Mock()
    mock_error.response.json = Mock()
    mock_error.response.json.return_value = {
        "code": 40010000,
        "message": "invalid order"
    }
    
    def _mock_place_order(*args, **kwargs):
        raise requests.HTTPError(response=mock_error.response)
    
    monkeypatch.setattr(AlpacaBroker, 'place_order', _mock_place_order)
    return mock_error


@pytest.fixture
def mock_alpaca_rate_limit(monkeypatch):
    """Mock rate limit error."""
    import requests
    mock_error = MagicMock()
    mock_error.response = Mock()
    mock_error.response.headers = {}
    mock_error.response.json = Mock()
    
    def _mock_get_account(*args, **kwargs):
        raise requests.HTTPError(response=mock_error.response)
    
    monkeypatch.setattr(AlpacaBroker, 'get_account', _mock_get_account)
    return mock_error


@pytest.fixture
def mock_alpaca_rate_limit_then_success(monkeypatch):
    """Mock rate limit followed by success."""
    import requests
    mock_error = MagicMock()
    mock_error.response = Mock()
    mock_error.response.status_code = 429
    
    call_count = 0
    
    def _mock_get_account_with_retry(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise requests.HTTPError(response=mock_error.response)
        return {"id": "test_account", "status": "ACTIVE"}
    
    monkeypatch.setattr(AlpacaBroker, 'get_account_with_retry', _mock_get_account_with_retry)
    return mock_error


@pytest.fixture
def mock_alpaca_server_error(monkeypatch):
    """Mock 500 server error."""
    import requests
    mock_error = MagicMock()
    mock_error.response = Mock()
    mock_error.response.json = Mock()
    
    def _mock_get_account(*args, **kwargs):
        raise requests.HTTPError(response=mock_error.response)
    
    monkeypatch.setattr(AlpacaBroker, 'get_account', _mock_get_account)
    return mock_error


@pytest.fixture
def mock_alpaca_timeout(monkeypatch):
    """Mock timeout error."""
    from requests import Timeout
    mock_timeout = Mock()
    
    def _mock_get_account(*args, **kwargs):
        raise Timeout("Request timed out")
    
    def _mock_place_order(*args, **kwargs):
        raise Timeout("Connection timed out after 30 seconds")
    
    monkeypatch.setattr(AlpacaBroker, 'get_account', _mock_get_account)
    monkeypatch.setattr(AlpacaBroker, 'place_order', _mock_place_order)
    return mock_timeout


@pytest.fixture
def mock_alpaca_connection_error(monkeypatch):
    """Mock connection error."""
    from requests import ConnectionError
    mock_connection_error = Mock()
    
    def _mock_get_account(*args, **kwargs):
        raise ConnectionError("Failed to connect")
    
    monkeypatch.setattr(AlpacaBroker, 'get_account', _mock_get_account)
    return mock_connection_error


@pytest.fixture
def mock_alpaca_bad_request(monkeypatch):
    """Mock bad request error."""
    import requests
    mock_error = MagicMock()
    mock_error.response = Mock()
    mock_error.response.json = Mock()
    
    def _mock_place_order(*args, **kwargs):
        raise requests.HTTPError(response=mock_error.response)
    
    monkeypatch.setattr(AlpacaBroker, 'place_order', _mock_place_order)
    return mock_error


@pytest.fixture
def mock_alpaca_expired_token_then_refresh(monkeypatch):
    """Mock expired token then refresh."""
    import requests
    from unittest.mock import Mock
    mock_error = MagicMock()
    mock_error.response = Mock()
    mock_error.response.status_code = 401
    
    call_count = 0
    
    def _mock_place_order_with_auto_refresh(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        
        if call_count == 1:
            raise requests.HTTPError(response=mock_error.response)
        elif call_count == 2:
            return {"access_token": "refreshed_token", "refresh_token": "new_refresh", "expires_in": 3600}
        else:
            return {"id": "order_after_refresh", "symbol": "AAPL", "status": "accepted"}
    
    monkeypatch.setattr(AlpacaBroker, 'place_order_with_auto_refresh', _mock_place_order_with_auto_refresh)
    return mock_error


@pytest.fixture
def mock_alpaca_order_status_updates(monkeypatch):
    """Mock order status updates for partial fills."""
    import itertools
    from collections import deque
    
    mock_updates = deque()
    
    def _mock_get_order_status(*args, **kwargs):
        if mock_updates:
            return mock_updates.popleft()
        raise Exception("No more status updates available")
    
    monkeypatch.setattr(AlpacaBroker, 'get_order_status', _mock_get_order_status)
    return mock_updates


@pytest.fixture
def mock_alpaca_trading_halted(monkeypatch):
    """Mock trading halted error."""
    import requests
    mock_error = MagicMock()
    mock_error.response = Mock()
    mock_error.response.json = Mock()
    
    def _mock_place_order(*args, **kwargs):
        raise requests.HTTPError(response=mock_error.response)
    
    monkeypatch.setattr(AlpacaBroker, 'place_order', _mock_place_order)
    return mock_error


@pytest.fixture
def mock_alpaca_rate_limit_exhaustion(monkeypatch):
    """Mock rate limit exhaustion with multiple calls."""
    import requests
    import time
    mock_error = MagicMock()
    mock_error.response = Mock()
    mock_error.response.status_code = 429
    mock_error.response.headers = {"x-ratelimit-reset": str(int(time.time()) + 60)}
    
    def rate_limited_response(*args, **kwargs):
        pass  # Handled by test
    
    return mock_error
