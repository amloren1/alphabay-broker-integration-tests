"""Broker error classes for handling API errors."""


class BrokerError(Exception):
    """Base exception class for all broker-related errors."""
    
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response


class BrokerAuthenticationError(BrokerError):
    """Raised when authentication fails (e.g., invalid/expired tokens)."""
    pass


class BrokerRateLimitError(BrokerError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message, status_code=None, response=None, retry_after=None):
        super().__init__(message, status_code, response)
        self.retry_after = retry_after


class BrokerAPIError(BrokerError):
    """Raised for generic API errors (4xx, 5xx)."""
    pass


class BrokerNetworkError(BrokerError):
    """Raised for network-related errors (timeouts, connection errors)."""
    pass


class OrderValidationError(BrokerAPIError):
    """Raised when order validation fails (e.g., insufficient funds, invalid symbol)."""
    pass
