# agent_ws_backend
Real-time AI agent backend built with FastAPI and LangGraph. Streams live token-by-token responses, tool calls, and results over WebSockets instead of blocking until completion. Features per-session conversation state, clean task cancellation on disconnect/interrupt, and async-safe tool execution for production-grade concurrency.
