"""Tests for sdk_client.py — WebullSDKClient and UAT_ENDPOINTS."""

from __future__ import annotations

import os
import sys
import tempfile
from unittest.mock import MagicMock, call, patch

import pytest

from webull_openapi_mcp.config import ServerConfig
from webull_openapi_mcp.sdk_client import UAT_ENDPOINTS, WebullSDKClient


# ---------------------------------------------------------------------------
# UAT_ENDPOINTS structure
# ---------------------------------------------------------------------------

class TestUATEndpoints:
    def test_has_required_top_level_keys(self):
        assert "default_region" in UAT_ENDPOINTS
        assert "regions" in UAT_ENDPOINTS
        assert "region_mapping" in UAT_ENDPOINTS

    def test_default_region_is_us(self):
        assert UAT_ENDPOINTS["default_region"] == "us"

    def test_regions_list(self):
        assert set(UAT_ENDPOINTS["regions"]) == {"us", "hk", "jp", "sg"}

    def test_each_region_has_all_api_types(self):
        for region in ("us", "hk", "jp"):
            mapping = UAT_ENDPOINTS["region_mapping"][region]
            assert "api" in mapping
            assert "quotes-api" in mapping
            assert "events-api" in mapping

    def test_us_api_endpoints(self):
        us = UAT_ENDPOINTS["region_mapping"]["us"]
        assert us["api"] == "us-openapi-alb.uat.webullbroker.com"
        assert us["quotes-api"] == "us-openapi-quotes-api.uat.webullbroker.com"
        assert us["events-api"] == "us-openapi-events.uat.webullbroker.com"

    def test_hk_api_endpoints(self):
        hk = UAT_ENDPOINTS["region_mapping"]["hk"]
        assert hk["api"] == "api.sandbox.webull.hk"
        assert hk["quotes-api"] == "data-api.sandbox.webull.hk"
        assert hk["events-api"] == "events-api.sandbox.webull.hk"

    def test_jp_api_endpoints(self):
        jp = UAT_ENDPOINTS["region_mapping"]["jp"]
        assert jp["api"] == "jp-openapi-alb.uat.webullbroker.com"
        assert jp["quotes-api"] == "data-api.uat.webullbroker.com"
        assert jp["events-api"] == "jp-openapi-events.uat.webullbroker.com"


# ---------------------------------------------------------------------------
# WebullSDKClient — construction
# ---------------------------------------------------------------------------

class TestWebullSDKClientInit:
    def test_stores_config(self):
        cfg = ServerConfig(app_key="k", app_secret="s")
        client = WebullSDKClient(cfg)
        assert client._config is cfg

    def test_clients_none_before_init(self):
        cfg = ServerConfig(app_key="k", app_secret="s")
        client = WebullSDKClient(cfg)
        assert client._trade_client is None
        assert client._data_client is None

    def test_trade_property_raises_before_init(self):
        cfg = ServerConfig(app_key="k", app_secret="s")
        client = WebullSDKClient(cfg)
        with pytest.raises(RuntimeError, match="initialize"):
            _ = client.trade

    def test_data_property_raises_before_init(self):
        cfg = ServerConfig(app_key="k", app_secret="s")
        client = WebullSDKClient(cfg)
        with pytest.raises(RuntimeError, match="initialize"):
            _ = client.data


# ---------------------------------------------------------------------------
# WebullSDKClient.initialize — prod environment
# ---------------------------------------------------------------------------

@patch("webull_openapi_mcp.sdk_client.DataClient")
@patch("webull_openapi_mcp.sdk_client.TradeClient")
@patch("webull_openapi_mcp.sdk_client.ApiClient")
class TestInitializeProd:
    def test_creates_api_client_with_credentials(self, MockApiClient, MockTrade, MockData):
        cfg = ServerConfig(app_key="my_key", app_secret="my_secret", region_id="us")
        client = WebullSDKClient(cfg)
        client.initialize()

        MockApiClient.assert_called_once_with(
            "my_key", "my_secret", "us",
            token_check_duration_seconds=WebullSDKClient.MCP_TOKEN_CHECK_DURATION,
            token_check_interval_seconds=WebullSDKClient.MCP_TOKEN_CHECK_INTERVAL,
        )

    def test_does_not_call_add_endpoint_for_prod(self, MockApiClient, MockTrade, MockData):
        cfg = ServerConfig(app_key="k", app_secret="s", environment="prod")
        client = WebullSDKClient(cfg)
        client.initialize()

        api = MockApiClient.return_value
        api.add_endpoint.assert_not_called()

    def test_sets_stream_logger_to_stderr(self, MockApiClient, MockTrade, MockData):
        import logging
        cfg = ServerConfig(app_key="k", app_secret="s")
        client = WebullSDKClient(cfg)
        client.initialize()

        api = MockApiClient.return_value
        api.set_stream_logger.assert_called_once_with(log_level=logging.WARNING, stream=sys.stderr)

    def test_creates_trade_and_data_clients(self, MockApiClient, MockTrade, MockData):
        cfg = ServerConfig(app_key="k", app_secret="s")
        client = WebullSDKClient(cfg)
        client.initialize()

        api = MockApiClient.return_value
        MockTrade.assert_called_once_with(api)
        MockData.assert_called_once_with(api)

    def test_trade_property_returns_client(self, MockApiClient, MockTrade, MockData):
        cfg = ServerConfig(app_key="k", app_secret="s")
        client = WebullSDKClient(cfg)
        client.initialize()

        assert client.trade is MockTrade.return_value

    def test_data_property_returns_client(self, MockApiClient, MockTrade, MockData):
        cfg = ServerConfig(app_key="k", app_secret="s")
        client = WebullSDKClient(cfg)
        client.initialize()

        assert client.data is MockData.return_value

    def test_no_set_token_dir_when_none(self, MockApiClient, MockTrade, MockData):
        cfg = ServerConfig(app_key="k", app_secret="s", token_dir=None)
        client = WebullSDKClient(cfg)
        client.initialize()

        api = MockApiClient.return_value
        api.set_token_dir.assert_not_called()

    def test_sets_token_dir_when_configured(self, MockApiClient, MockTrade, MockData):
        token_dir = os.path.join(tempfile.gettempdir(), "webull_test_tokens")
        cfg = ServerConfig(app_key="k", app_secret="s", token_dir=token_dir)
        client = WebullSDKClient(cfg)
        client.initialize()

        api = MockApiClient.return_value
        api.set_token_dir.assert_called_once_with(token_dir)


# ---------------------------------------------------------------------------
# WebullSDKClient.initialize — UAT environment
# ---------------------------------------------------------------------------

@patch("webull_openapi_mcp.sdk_client.DataClient")
@patch("webull_openapi_mcp.sdk_client.TradeClient")
@patch("webull_openapi_mcp.sdk_client.ApiClient")
class TestInitializeUAT:
    def test_registers_all_endpoint_types_for_uat_us(self, MockApiClient, MockTrade, MockData):
        cfg = ServerConfig(app_key="k", app_secret="s", region_id="us", environment="uat")
        client = WebullSDKClient(cfg)
        client.initialize()

        api = MockApiClient.return_value
        # Should register all three endpoint types
        assert api.add_endpoint.call_count == 3
        
        # Verify each endpoint type was registered
        from webull.core.common.api_type import DEFAULT, QUOTES, EVENTS
        calls = api.add_endpoint.call_args_list
        call_args = [(c[0][0], c[0][1], c[0][2]) for c in calls]
        
        assert ("us", "us-openapi-alb.uat.webullbroker.com", DEFAULT) in call_args
        assert ("us", "us-openapi-quotes-api.uat.webullbroker.com", QUOTES) in call_args
        assert ("us", "us-openapi-events.uat.webullbroker.com", EVENTS) in call_args

    def test_registers_all_endpoint_types_for_uat_hk(self, MockApiClient, MockTrade, MockData):
        cfg = ServerConfig(app_key="k", app_secret="s", region_id="hk", environment="uat")
        client = WebullSDKClient(cfg)
        client.initialize()

        api = MockApiClient.return_value
        # Should register all three endpoint types
        assert api.add_endpoint.call_count == 3
        
        # Verify each endpoint type was registered
        from webull.core.common.api_type import DEFAULT, QUOTES, EVENTS
        calls = api.add_endpoint.call_args_list
        call_args = [(c[0][0], c[0][1], c[0][2]) for c in calls]
        
        assert ("hk", "api.sandbox.webull.hk", DEFAULT) in call_args
        assert ("hk", "data-api.sandbox.webull.hk", QUOTES) in call_args
        assert ("hk", "events-api.sandbox.webull.hk", EVENTS) in call_args

    def test_registers_all_endpoint_types_for_uat_jp(self, MockApiClient, MockTrade, MockData):
        cfg = ServerConfig(app_key="k", app_secret="s", region_id="jp", environment="uat")
        client = WebullSDKClient(cfg)
        client.initialize()

        api = MockApiClient.return_value
        assert api.add_endpoint.call_count == 3

        from webull.core.common.api_type import DEFAULT, QUOTES, EVENTS
        calls = api.add_endpoint.call_args_list
        call_args = [(c[0][0], c[0][1], c[0][2]) for c in calls]

        assert ("jp", "jp-openapi-alb.uat.webullbroker.com", DEFAULT) in call_args
        assert ("jp", "data-api.uat.webullbroker.com", QUOTES) in call_args
        assert ("jp", "jp-openapi-events.uat.webullbroker.com", EVENTS) in call_args

    def test_no_add_endpoint_for_unknown_region_uat(self, MockApiClient, MockTrade, MockData):
        cfg = ServerConfig(app_key="k", app_secret="s", region_id="xx", environment="uat")
        client = WebullSDKClient(cfg)
        client.initialize()

        api = MockApiClient.return_value
        api.add_endpoint.assert_not_called()


# ---------------------------------------------------------------------------
# WebullSDKClient.initialize — Device registration error handling
# ---------------------------------------------------------------------------

@patch("webull_openapi_mcp.sdk_client.DataClient")
@patch("webull_openapi_mcp.sdk_client.TradeClient")
@patch("webull_openapi_mcp.sdk_client.ApiClient")
class TestInitializeDeviceNotRegistered:
    def test_raises_device_not_registered_error_on_no_available_device(
        self, MockApiClient, MockTrade, MockData
    ):
        from webull.core.exception.exceptions import ServerException
        from webull_openapi_mcp.sdk_client import DeviceNotRegisteredError

        # Simulate NO_AVAILABLE_DEVICE error from SDK
        MockTrade.side_effect = ServerException(
            code="NO_AVAILABLE_DEVICE",
            msg="Please download the latest Webull app and do your 2FA verification from there",
            http_status=417,
        )

        cfg = ServerConfig(app_key="k", app_secret="s", region_id="hk", environment="uat")
        client = WebullSDKClient(cfg)

        with pytest.raises(DeviceNotRegisteredError) as exc_info:
            client.initialize()

        # Verify error message contains key information
        error_msg = str(exc_info.value)
        assert "Device Not Registered" in error_msg
        assert "Webull mobile app" in error_msg
        assert "HK" in error_msg
        assert "UAT" in error_msg

    def test_reraises_other_server_exceptions(self, MockApiClient, MockTrade, MockData):
        from webull.core.exception.exceptions import ServerException

        # Simulate a different server error
        MockTrade.side_effect = ServerException(
            code="INVALID_CREDENTIALS",
            msg="Invalid app key or secret",
            http_status=401,
        )

        cfg = ServerConfig(app_key="k", app_secret="s", region_id="us", environment="prod")
        client = WebullSDKClient(cfg)

        with pytest.raises(ServerException) as exc_info:
            client.initialize()

        assert exc_info.value.error_code == "INVALID_CREDENTIALS"
