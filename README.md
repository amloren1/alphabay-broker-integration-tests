# Alpaca Integration Tests

## Overview
Integration tests for Alpaca broker workflows following the Schwab broker removal.

## Coverage
- OAuth flow tests
- Account sync tests
- Order placement tests
- Error handling tests
- Edge case tests

## Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html --cov-report=term-missing -v

# Run specific test categories
pytest tests/ -k "oauth" -v
pytest tests/ -k "account" -v
pytest tests/ -k "order" -v
pytest tests/ -k "error" -v
pytest tests/ -k "edge" -v
```

## CI/CD Integration
GitHub Actions automatically runs tests on push to main/develop branches and on pull requests.

## Coverage Report
Current coverage: Testing 6,200+ previously untested lines of code.
