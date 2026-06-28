
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

@pytest.mark.asyncio
@pytest.mark.integration
async def test_live_sandbox_reconnect():
    """WP4.5: Live Lark sandbox reconnection — exponential backoff 1s/2s/4s, max 3."""
    from src.channels.lark.websocket import LarkWebSocket
    import os
    ws = LarkWebSocket(os.getenv('LARK_APP_ID'), os.getenv('LARK_APP_SECRET'))
    await ws.connect('test_sandbox_open')
    await ws._simulate_disconnect('test_sandbox_open')
    await ws.reconnect('test_sandbox_open', max_retries=3)
    assert 'test_sandbox_open' in ws._connections
    assert ws._reconnect_attempts['test_sandbox_open'] <= 3
    await ws.disconnect('test_sandbox_open')
