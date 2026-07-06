import asyncio
import uuid
from fastapi import WebSocket
from langchain_core.messages import HumanMessage, AIMessageChunk

from agents.graph import compiled_graph
from connection.events import (
    RunStartEvent,
    LLMTokenEvent,
    ToolCallStartEvent,
    ToolCallEndEvent,
    RunEndEvent,
    ErrorEvent,
)
class ConnectionManager:
    def __init__(self):
        self._active_tasks: dict[str, asyncio.Task] = {}
    def new_session_id(self) -> str:
        return str(uuid.uuid4())

    async def cancel_active_run(self, session_id: str):
        """Cancel any in-flight agent run for this session (e.g. user sent a new message
        before the previous one finished, or the socket is closing)."""
        task = self._active_tasks.get(session_id)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._active_tasks.pop(session_id, None)
    async def run_agent(self, websocket: WebSocket, session_id: str, user_message: str):
        """
        Stream a LangGraph agent run over the websocket as a series of JSON events.
        Wrapped in its own task so a new incoming message (or disconnect) can cancel it.
        """
        await self.cancel_active_run(session_id)

        task = asyncio.create_task(self._stream_run(websocket, session_id, user_message))
        self._active_tasks[session_id] = task

    async def _stream_run(self, websocket: WebSocket, session_id: str, user_message: str):
        config = {"configurable": {"thread_id": session_id}}
        inputs = {"messages": [HumanMessage(content=user_message)]}

        await self._send(websocket, RunStartEvent())

        try:
            async for event in compiled_graph.astream_events(inputs, config=config, version="v2"):
                kind = event["event"]

                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if isinstance(chunk, AIMessageChunk) and chunk.content:
                        # content can be str or list of content blocks depending on provider
                        text = chunk.content if isinstance(chunk.content, str) else "".join(
                            block.get("text", "") for block in chunk.content if isinstance(block, dict)
                        )
                        if text:
                            await self._send(websocket, LLMTokenEvent(data={"token": text}))

                elif kind == "on_tool_start":
                    await self._send(websocket, ToolCallStartEvent(data={
                        "tool": event["name"],
                        "args": event["data"].get("input", {}),
                        "call_id": event["run_id"],
                    }))

                elif kind == "on_tool_end":
                    await self._send(websocket, ToolCallEndEvent(data={
                        "tool": event["name"],
                        "result": str(event["data"].get("output", "")),
                        "call_id": event["run_id"],
                    }))

            final_state = await compiled_graph.aget_state(config)
            last_message = final_state.values["messages"][-1]
            final_text = last_message.content if isinstance(last_message.content, str) else str(last_message.content)

            await self._send(websocket, RunEndEvent(data={"final_answer": final_text}))

        except asyncio.CancelledError:
            raise
        except Exception as e:
            await self._send(websocket, ErrorEvent(data={"message": str(e)}))

    @staticmethod
    async def _send(websocket: WebSocket, event):
        try:
            await websocket.send_json(event.model_dump())
        except Exception:
            pass


manager = ConnectionManager()
