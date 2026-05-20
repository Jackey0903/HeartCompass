
"""WP4.5: WebSocket reconnection tests."""
import pytest
from unittest.mock import patch
@pytest.mark.asyncio
async def test_ws_connect_disconnect():
    from src.channels.lark.websocket import LarkWebSocket
    ws=LarkWebSocket('test_id','test_secret')
    with patch('websockets.connect'):
        await ws.connect('test_open')
    await ws.disconnect('test_open')
    assert 'test_open' not in ws._connections
