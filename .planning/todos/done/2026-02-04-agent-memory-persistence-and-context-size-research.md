---
created: 2026-02-04T19:31
title: Agent memory persistence and context size research
area: api
files:
  - backend/agents/graph.py
  - backend/api/routers/chat.py
---

## Problem

Need to verify whether agent memory (LangGraph checkpointing) is persistent per chat tab, ensuring conversation flows smoothly across multiple queries within the same file context. Additionally, need to research solutions for maintaining manageable context size as conversations grow longer to prevent:

1. Token limit issues
2. Performance degradation
3. Cost escalation
4. Loss of context quality

Current implementation uses PostgresSaver for checkpointing with thread ID format: `file_{file_id}_user_{user_id}`, which should provide per-file chat isolation. However, this needs verification through testing.

Context size management is currently unaddressed - conversations could grow unbounded, leading to potential issues with:
- LLM token limits
- Increased latency
- Higher API costs
- Reduced response quality from diluted context

## Solution

**Memory Persistence Verification:**
- Test chat queries across multiple messages in same tab
- Verify thread_id correctly isolates conversations by file
- Confirm PostgresSaver maintains state between requests
- Check if previous query context influences subsequent queries

**Context Size Management Research:**
- Summarization strategies (periodic conversation summarization)
- Sliding window approaches (keep N most recent messages)
- Hybrid: keep first message + recent N + summarized middle
- Token counting and truncation strategies
- LangGraph memory management patterns
- Consider implementing max_messages limit per thread
- Research checkpoint pruning/cleanup strategies

**Files to Review:**
- `backend/agents/graph.py` - LangGraph setup and checkpointing
- `backend/api/routers/chat.py` - Thread ID generation and chat endpoint
- `backend/services/chat_service.py` - Chat service layer
- LangGraph documentation on memory management
