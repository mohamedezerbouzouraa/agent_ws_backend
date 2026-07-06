from typing import Any, Literal, Optional
from pydantic import BaseModel

class AgentEvent(BaseModel):
    type: Literal[
        "run_start",       
        "llm_token",      
        "tool_call_start", 
        "tool_call_end",   
        "run_end",        
        "error",]
    data: dict[str, Any] = {}
class RunStartEvent(AgentEvent):
    type: Literal["run_start"] = "run_start"
class LLMTokenEvent(AgentEvent):
    type: Literal["llm_token"] = "llm_token"
class ToolCallStartEvent(AgentEvent):
    type: Literal["tool_call_start"] = "tool_call_start"
class ToolCallEndEvent(AgentEvent):
    type: Literal["tool_call_end"] = "tool_call_end"
class RunEndEvent(AgentEvent):
    type: Literal["run_end"] = "run_end"


class ErrorEvent(AgentEvent):
    type: Literal["error"] = "error"
    # data: {"message": str}
