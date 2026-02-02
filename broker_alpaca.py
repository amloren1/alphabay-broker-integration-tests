"""Alpaca Broker implementation for trading and account management."""

import time
import requests
from typing import Optional, Dict, Any, List
from broker_errors import (
    BrokerAuthenticationError,
    BrokerRateLimitError,
    BrokerAPIError,
    BrokerNetworkError,
    OrderValidationError
)


class AlpacaBroker:
    """Alpaca Broker client for trading and account management."""
    
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None):
        self.api_key = api_key
        self.secret_key = secret_key
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.base_url = "https://paper-api.alpaca.markets/v2"
        self.headers = {}
    
    def _refresh_if_needed(self) -> bool:
        """Check and refresh token if expired."""
        if self.token_expires_at and time.time() >= self.token_expires_at:
            return self.refresh_access_token()
        return True
    
    def refresh_if_needed(self) -> bool:
        """Public wrapper for token refresh."""
        return self._refresh_if_needed()
    
    def authenticate(self, auth_code: str) -> bool:
        """Authenticate with Alpaca using OAuth2 authorization code."""
        # Implementation would call Alpaca OAuth endpoint
        self.access_token = f"access_token_{auth_code}"
        self.refresh_token = f"refresh_token_{auth_code}"
        self.token_expires_at = time.time() + 3600
        return True
    
    def refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token."""
        if not self.refresh_token:
            raise BrokerAuthenticationError("No refresh token available")
        
        # Implementation would call token refresh endpoint
        self.access_token = f"refreshed_token_{self.refresh_token}"
        self.token_expires_at = time.time() + 3600
        return True
    
    def get_account(self) -> Any:
        """Get account information."""
        try:
            response = requests.get(
                f"{self.base_url}/account",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            self._handle_http_error(e)
        except requests.exceptions.Timeout as e:
            raise BrokerNetworkError("Request timed out") from e
        except requests.exceptions.ConnectionError as e:
            raise BrokerNetworkError("Failed to connect") from e
    
    def get_account_with_retry(self, max_retries: int = 3) -> Any:
        """Get account information with retry logic."""
        for attempt in range(max_retries):
            try:
                return self.get_account()
            except BrokerRateLimitError:
                if attempt < max_retries - 1:
                    time.sleep(min(2  ** attempt, 60))
                else:
                    raise 
    
    def get_positions(self) -> List[Any]:
        """Get portfolio positions."""
        try:
            response = requests.get(
                f"{self.base_url}/positions",
                headers=self.headers
            )
            response.raise_for_status()
            return self._parse_positions(response.json())
        except requests.exceptions.HTTPError as e:
            self._handle_http_error(e)
        except requests.exceptions.Timeout as e:
            raise BrokerNetworkError("Request timed out") from e
        except requests.exceptions.ConnectionError as e:
            raise BrokerNetworkError("Failed to connect") from e
    
    def _parse_positions(self, positions_json: List[Dict]) -> List[Any]:
        """Parse position JSON into position objects."""
        return [self._parse_position(p) for p in positions_json]
    
    def _parse_position(self, position_json: Dict) -> Any:
        """Parse single position into object."""
        class PositionObj:
            def __init__(self, data):
                self.symbol = data.get("symbol")
                self.qty = float(data.get("qty", 0))
                self.market_value = float(data.get("market_value", 0))
                self.unrealized_pl = float(data.get("unrealized_pl", 0))
        return PositionObj(position_json)
    
    def get_transactions(self, limit: int = 100):
        """Get transaction history with pagination."""
        offset = 0
        remaining = limit
        
        while remaining > 0:
            batch_size = min(remaining, 100)
            try:
                response = requests.get(
                    f"{self.base_url}/activities",
                    params={"limit": batch_size, "offset": offset},
                    headers=self.headers
                )
                response.raise_for_status()
                yield response.json()
                remaining -= batch_size
                offset += batch_size
            except requests.exceptions.HTTPError as e:
                self._handle_http_error(e)
            except requests.exceptions.Timeout as e:
                raise BrokerNetworkError("Request timed out") from e
            except requests.exceptions.ConnectionError as e:
                raise BrokerNetworkError("Failed to connect") from e
    
    def get_asset(self, symbol: str) -> Any:
        """Get asset information."""
        try:
            response = requests.get(
                f"{self.base_url}/assets/{symbol}",
                headers=self.headers
            )
            response.raise_for_status()
            return self._parse_asset(response.json())
        except requests.exceptions.HTTPError as e:
            self._handle_http_error(e)
        except requests.exceptions.Timeout as e:
            raise BrokerNetworkError("Request timed out") from e
        except requests.exceptions.ConnectionError as e:
            raise BrokerNetworkError("Failed to connect") from e
    
    def _parse_asset(self, asset_json: Dict) -> Any:
        """Parse asset JSON into asset object."""
        class AssetObj:
            def __init__(self, data):
                self.symbol = data.get("symbol")
                self.exchange = data.get("exchange")
                self.tradable = data.get("tradable", False)
                self.marginable = data.get("marginable", False)
                self.fractionable = data.get("fractionable", False)
        return AssetObj(asset_json)
    
    def place_order(self, symbol: str, qty: float, side: str, type: str, 
                   time_in_force: str = "day", limit_price: Optional[float] = None,
                   notional: Optional[float] = None) -> Any:
        """Place an order."""
        try:
            order_data = {
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "type": type,
                "time_in_force": time_in_force
            }
            
            if limit_price is not None:
                order_data["limit_price"] = limit_price
            if notional is not None:
                order_data["notional"] = notional
                del order_data["qty"]
            
            response = requests.post(
                f"{self.base_url}/orders",
                json=order_data,
                headers=self.headers
            )
            response.raise_for_status()
            return self._parse_order(response.json())
        except requests.exceptions.HTTPError as e:
            self._handle_http_error(e)
        except requests.exceptions.Timeout as e:
            raise BrokerNetworkError("Connection timed out after 30 seconds") from e
        except requests.exceptions.ConnectionError as e:
            raise BrokerNetworkError("Failed to connect") from e
    
    def place_order_with_auto_refresh(self, **kwargs) -> Any:
        """Place an order with automatic token refresh on 401."""
        try:
            return self.place_order(**kwargs)
        except BrokerAuthenticationError:
            self.refresh_access_token()
            return self.place_order(**kwargs)
    
    def _parse_order(self, order_json: Dict) -> Any:
        """Parse order JSON into order object."""
        class OrderObj:
            def __init__(self, data):
                self.id = data.get("id")
                self.symbol = data.get("symbol")
                self.qty = float(data.get("qty", 0))
                self.status = data.get("status")
                self.type = data.get("type")
                self.side = data.get("side")
                self.time_in_force = data.get("time_in_force")
                self.limit_price = data.get("limit_price")
                self.filled_qty = float(data.get("filled_qty", 0))
                self.filled_avg_price = data.get("filled_avg_price")
        return OrderObj(order_json)
    
    def get_order_status(self, order_id: str) -> Any:
        """Get order status."""
        try:
            response = requests.get(
                f"{self.base_url}/orders/{order_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return self._parse_order_status(response.json())
        except requests.exceptions.HTTPError as e:
            self._handle_http_error(e)
        except requests.exceptions.Timeout as e:
            raise BrokerNetworkError("Request timed out") from e
        except requests.exceptions.ConnectionError as e:
            raise BrokerNetworkError("Failed to connect") from e
    
    def _parse_order_status(self, status_json: Dict) -> Any:
        """Parse order status from JSON."""
        class OrderStatusObj:
            def __init__(self, data):
                self.id = data.get("id")
                self.symbol = data.get("symbol")
                self.status = data.get("status")
                self.filled_qty = float(data.get("filled_qty", 0))
                self.filled_avg_price = data.get("filled_avg_price")
        return OrderStatusObj(status_json)
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        try:
            response = requests.delete(
                f"{self.base_url}/orders/{order_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json().get("status") == "canceled"
        except requests.exceptions.HTTPError as e:
            self._handle_http_error(e)
        except requests.exceptions.Timeout as e:
            raise BrokerNetworkError("Request timed out") from e
        except requests.exceptions.ConnectionError as e:
            raise BrokerNetworkError("Failed to connect") from e
    
    def _handle_http_error(self, error: requests.exceptions.HTTPError):
        """Handle HTTP errors and raise appropriate broker errors."""
        response = error.response
        status_code = response.status_code
        
        # Try to parse error response
        try:
            error_data = response.json()
            message = error_data.get("message", str(error))
        except:
            error_data = {}
            message = str(error)
        
        if status_code == 401:
            raise BrokerAuthenticationError(message, status_code, response)
        elif status_code == 429:
            retry_after = response.headers.get("x-ratelimit-reset")
            retry_after = int(retry_after) - int(time.time()) if retry_after else 60
            raise BrokerRateLimitError(message, status_code, response, retry_after)
        elif status_code == 403:
            if "insufficient" in message.lower():
                raise OrderValidationError(message, status_code, response)
            elif "trading halted" in message.lower():
                raise OrderValidationError(message, status_code, response)
            else:
                raise BrokerAPIError(message, status_code, response)
        elif status_code == 404:
            if "asset not found" in message:
                raise OrderValidationError(message, status_code, response)
            else:
                raise BrokerAPIError(message, status_code, response)
        elif status_code == 400:
            raise BrokerAPIError(message, status_code, response)
        elif status_code >= 500:
            raise BrokerAPIError(message, status_code, response)
        else:
            raise BrokerAPIError(message, status_code, response)
