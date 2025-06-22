import pytest
from sdk.main import SubscriptionMiddleware
from sdk.ads import AdService
from tests.utils import make_fake_message
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_middleware_launches_without_errors():
    # Подставим одну NS-рекламу
    ad_payload: list[dict[str, str | list[str | dict[str, str]] | dict[str, str]]] = [{
        "type": "NS",
        "channels": {
            "Some Channel": "https://t.me/somechannel"
        }
    }]

    mock_ad_service = AsyncMock(spec=AdService)
    mock_ad_service.fetch_ad.return_value = ad_payload
    mock_ad_service.get_channels.return_value = (ad_payload[0]["channels"], {})

    mock_log_service = AsyncMock()
    dispatcher = AsyncMock()

    middleware = SubscriptionMiddleware(sdk_key="dummy", dispatcher=dispatcher)
    middleware.ad_service = mock_ad_service
    middleware.log_service = mock_log_service

    handler = AsyncMock()
    message = make_fake_message(42)

    # Обходим вызов .answer()
    with patch.object(message.__class__, "answer", new_callable=AsyncMock):
        await middleware(handler, message, {})

    # Не подписан, handler НЕ вызывается
    handler.assert_not_called()
