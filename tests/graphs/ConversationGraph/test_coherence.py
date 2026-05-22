
"""WP3.5: Multi-turn coherence tests."""
import pytest
@pytest.mark.asyncio
@pytest.mark.parametrize('turns',[5,10,20])
async def test_multi_turn(turns):
    from src.agents.graphs.ConversationGraph.graph import getConversationGraph
    g=getConversationGraph()
    s={'messages':[]}
    for i in range(turns):
        s['messages'].append({'role':'user','content':f'Round {i+1}'})
        s=await g.ainvoke(s)
    assert len(s.get('messages',[]))>=turns
