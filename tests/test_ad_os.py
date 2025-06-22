import pytest
from unittest.mock import AsyncMock, patch
from sdk.main import SubscriptionMiddleware
from sdk.ads import AdService
from tests.utils import make_fake_message


@pytest.mark.asyncio
async def test_ad_type_os_not_subscribed_shows_prompt():
    ad_payload: list[dict[str, str | list[str | dict[str, str]] | dict[str, str]]] = [{
        "type": "OS",
        "channels": {
            "Another Channel": "https://t.me/anotherchannel"
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

    with patch.object(message.__class__, "answer", new_callable=AsyncMock) as mock_answer:
        await middleware(handler, message, {})

        mock_answer.assert_called_once()
        handler.assert_not_called()
