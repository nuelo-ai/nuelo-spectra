#!/usr/bin/env python3
"""Verification script for memory persistence fix.

This script tests that conversation memory is being persisted correctly
across multiple queries using the checkpointer.

Usage:
    python test_memory_verification.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))


async def verify_memory_persistence():
    """Verify that memory persistence is working correctly."""
    print("=" * 80)
    print("MEMORY PERSISTENCE VERIFICATION TEST")
    print("=" * 80)
    print()

    try:
        from app.agents.graph import get_or_create_graph
        from app.core.config import settings
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from langchain_core.messages import HumanMessage
        import asyncpg

        print("✓ Imports successful")
        print()

        # Step 1: Create checkpointer
        print("Step 1: Creating checkpointer...")
        connection_kwargs = {
            "host": "localhost",
            "port": 5432,
            "database": "spectra",
            "user": "postgres",
            "password": "postgres",
        }

        async with AsyncPostgresSaver.from_conn_string(
            f"postgresql://{connection_kwargs['user']}:{connection_kwargs['password']}@"
            f"{connection_kwargs['host']}:{connection_kwargs['port']}/{connection_kwargs['database']}"
        ) as checkpointer:
            await checkpointer.setup()
            print("✓ Checkpointer created and tables verified")
            print()

            # Step 2: Get graph
            print("Step 2: Getting compiled graph...")
            graph = get_or_create_graph(checkpointer)
            print("✓ Graph compiled with checkpointer")
            print()

            # Step 3: Test with a unique thread_id
            test_thread_id = "test_memory_verification_001"
            config = {"configurable": {"thread_id": test_thread_id}}
            print(f"Step 3: Testing with thread_id: {test_thread_id}")
            print()

            # Step 4: First query - add message via aupdate_state
            print("Step 4: First query - adding message via aupdate_state...")
            await graph.aupdate_state(
                config,
                {"messages": [HumanMessage(content="First test message")]}
            )

            # Check state
            state_after_first = await graph.aget_state(config)
            messages_after_first = state_after_first.values.get("messages", []) if state_after_first.values else []
            print(f"  Messages after first update: {len(messages_after_first)}")
            for i, msg in enumerate(messages_after_first):
                print(f"    {i+1}. {type(msg).__name__}: {msg.content[:50]}...")

            if len(messages_after_first) != 1:
                print("✗ FAILED: Expected 1 message after first update")
                return False

            print("✓ First message added correctly")
            print()

            # Step 5: Second query - add another message
            print("Step 5: Second query - adding another message...")
            await graph.aupdate_state(
                config,
                {"messages": [HumanMessage(content="Second test message")]}
            )

            # Check state again
            state_after_second = await graph.aget_state(config)
            messages_after_second = state_after_second.values.get("messages", []) if state_after_second.values else []
            print(f"  Messages after second update: {len(messages_after_second)}")
            for i, msg in enumerate(messages_after_second):
                print(f"    {i+1}. {type(msg).__name__}: {msg.content[:50]}...")

            if len(messages_after_second) != 2:
                print("✗ FAILED: Expected 2 messages after second update")
                print(f"  Got {len(messages_after_second)} messages instead")
                return False

            print("✓ Second message appended correctly (add_messages reducer working)")
            print()

            # Step 6: Verify messages persisted
            print("Step 6: Verifying messages are both test messages...")
            if messages_after_second[0].content == "First test message" and \
               messages_after_second[1].content == "Second test message":
                print("✓ Messages persisted correctly in order")
            else:
                print("✗ FAILED: Messages not in expected order or content")
                return False

            print()
            print("=" * 80)
            print("MEMORY PERSISTENCE VERIFICATION: PASSED ✓")
            print("=" * 80)
            print()
            print("The fix is working correctly:")
            print("1. aupdate_state() creates checkpoint on first call")
            print("2. aupdate_state() appends messages via add_messages reducer")
            print("3. Messages are persisted and retrievable via aget_state()")
            print()
            return True

    except Exception as e:
        print()
        print("=" * 80)
        print("MEMORY PERSISTENCE VERIFICATION: FAILED ✗")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(verify_memory_persistence())
    sys.exit(0 if result else 1)
