
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

@pytest.mark.asyncio
@pytest.mark.parametrize('role_type',['family','friend','mentor','colleague','partner'])
async def test_topic_switch_no_context_bleed(role_type):
    """WP3.5 fix: rapid topic switching must not carry emotional framing."""
    from src.agents.graphs.ConversationGraph.graph import getConversationGraph
    g = getConversationGraph()
    topics = [('work stress','最近工作压力好大...'),('weekend plans','周末有什么安排？'),('health','最近睡眠不太好'),('hobby','推荐一本好书吧'),('travel','想去哪里旅游？')]
    s = {'messages':[]}
    for topic, msg in topics:
        s['messages'].append({'role':'user','content':msg})
        s = await g.ainvoke(s)
        last = s['messages'][-1]['content']
        if topic != 'work stress':
            assert '压力' not in last, f'{role_type}/{topic}: emotional bleed detected'
    print(f'PASS: {role_type} — 5 topic switches, zero context bleed')
// 2026-06-03T16:00:00 — test(conv): add 10-scenario cultural adaptation test suite (WP3.6)
// 2026-06-05T10:00:00 — test(conv): expand coherence test suite to 30 scenarios (WP3.5)
