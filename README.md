# Agent WebSocket Backend

A FastAPI backend that runs a LangGraph agent per WebSocket connection,
streaming live updates (LLM tokens, tool calls, tool results, final answer)
to the client in real time — instead of blocking until the whole response
is ready.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```
ANTHROPIC_API_KEY=your_key_here
MODEL_PROVIDER=anthropic
MODEL_NAME=claude-sonnet-4-6
```

(Switch `MODEL_PROVIDER=openai` and set `OPENAI_API_KEY` to use OpenAI instead.)

## Run

```bash
uvicorn main:app --reload
```

Test it without building a frontend:

```bash
python test_client.py
```

Try asking: `"What's the weather in Paris and what's 23 * 19?"` — you'll see
tool_call_start/tool_call_end events for both tools, interleaved with the
streamed final answer.

## Architecture

```
client (WebSocket)
   |
   v
main.py            -- accepts connection, assigns session_id, receives messages
   |
   v
connection/manager.py  -- runs each agent turn as a cancellable asyncio.Task,
   |                      forwards LangGraph's astream_events() as JSON events
   v
agents/graph.py    -- the actual LangGraph graph (agent node <-> tools node)
agents/tools.py    -- tool definitions (swap in your RAG retriever, DB calls, etc)
```

### Key design decisions (and why)

1. **One compiled graph, many sessions.** We don't build a new LangGraph
   graph per connection — that would be wasteful. Instead, a single
   compiled graph is reused, and per-session isolation comes from passing
   a different `thread_id` in the `config` at invoke time. LangGraph's
   checkpointer (`MemorySaver` here) keeps each thread's message history
   separate.

2. **Cancellation on overlap.** If a user sends a new message while the
   previous agent run is still streaming, `manager.run_agent()` cancels
   the in-flight `asyncio.Task` first. Without this, you'd get two
   overlapping streams writing to the same socket and racing each other.

3. **`astream_events(version="v2")` instead of `astream()`.** Plain
   `astream()` only gives you state snapshots after each graph node
   finishes — you wouldn't see individual LLM tokens or tool start/end
   as separate moments. `astream_events` gives you the fine-grained
   event stream needed for a responsive UI.

4. **Fire-and-forget task per message, not per connection.** The main
   `while True` loop in `main.py` keeps listening for new messages
   immediately after scheduling a run — it doesn't `await` the run to
   finish before going back to `receive_text()`. This is what makes
   "interrupt the agent mid-thought" possible.

## Swap-in points for your own use case

- **`agents/tools.py`** — replace the demo tools with your RAG retriever,
  database queries, or external APIs.
- **`agents/graph.py`** — add more nodes (e.g. a router node, a
  human-in-the-loop approval node, parallel tool execution) — this is
  a minimal ReAct-style graph; LangGraph supports much more complex
  topologies.
- **Persistent checkpointer** — `MemorySaver` loses state on restart.
  For production, swap in `AsyncPostgresSaver` or a Redis-backed
  checkpointer so conversations survive deploys.
- **Auth** — there's no auth on the WebSocket endpoint yet. Add a token
  check (e.g. via query param or first message) before accepting the
  connection if this needs to be multi-user/production.

## Things worth experimenting with next

- Reconnect handling: persist `session_id` client-side and pass it back
  on reconnect to resume the same conversation thread.
- Horizontal scaling: if you run multiple server instances, in-memory
  `ConnectionManager` state won't be shared — you'd need Redis pub/sub
  to route messages/cancellations correctly across instances.
- Human-in-the-loop: LangGraph supports interrupting a graph run to wait
  for human approval before a tool executes — a good next feature to
  add given you already understand the event-streaming plumbing here.
