
# WP5.4 System Integration Test Plan

## Critical-Path Scenarios (8)

1. **Onboarding→Persona→Conversation** — End-to-end: register → create FR → build persona → 20-turn conversation → verify feed sync
2. **Multi-Session Evolution** — 3 sessions × 10 turns each, verify FR core fields evolve correctly across sessions
3. **Concurrent Graph Execution** — 5 simultaneous ConversationGraph instances, verify Semaphore isolation and no state leakage
4. **WebSocket Disconnect/Reconnect** — Force disconnect mid-conversation, verify message queue + replay on reconnect
5. **DB Pool Under Load** — 20 concurrent connections, verify connection pooling and graceful degradation
6. **LLM Failure Recovery** — Simulate 3 consecutive 5xx errors, verify retry → graceful fallback message
7. **Docker Restart State Recovery** — docker compose restart, verify PostgresSaver checkpoint restoration
8. **Cross-Platform Delivery** — Verify Lark desktop + mobile + web message uniformity

## Schedule
- Manual execution (scenarios 1-4): Week 12, Day 1-2
- Automated execution (scenarios 5-8): Week 12, Day 3-4
- Report compilation: Week 12, Day 5

## Success Criteria
- 8/8 scenarios pass (100%)
- Zero data loss across restarts
- <5s p95 latency for all API paths
