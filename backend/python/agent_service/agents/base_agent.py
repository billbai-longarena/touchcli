"""
Base Agent class with common functionality for all subagents
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentState:
    """Conversation state passed through agent workflow"""
    conversation_id: UUID
    user_id: UUID
    customer_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None

    # Message and conversation context
    messages: List[Dict[str, str]] = None
    current_message: str = ""
    conversation_mode: str = "text"

    # Agent routing and execution
    current_agent: str = "router"
    next_agent: str = "router"
    agent_actions: List[Dict[str, Any]] = None
    execution_history: List[Dict[str, Any]] = None

    # Context and memory
    user_context: Dict[str, Any] = None
    customer_context: Dict[str, Any] = None
    opportunity_context: Dict[str, Any] = None
    memory: Dict[str, Any] = None

    # Results and responses
    agent_response: str = ""
    action_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    # Metadata
    start_time: datetime = None
    last_update: datetime = None
    confidence: float = 0.0

    def __post_init__(self):
        if self.messages is None:
            self.messages = []
        if self.agent_actions is None:
            self.agent_actions = []
        if self.execution_history is None:
            self.execution_history = []
        if self.user_context is None:
            self.user_context = {}
        if self.customer_context is None:
            self.customer_context = {}
        if self.opportunity_context is None:
            self.opportunity_context = {}
        if self.memory is None:
            self.memory = {}
        if self.start_time is None:
            self.start_time = datetime.utcnow()
        if self.last_update is None:
            self.last_update = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for storage"""
        return {
            "conversation_id": str(self.conversation_id),
            "user_id": str(self.user_id),
            "customer_id": str(self.customer_id) if self.customer_id else None,
            "opportunity_id": str(self.opportunity_id) if self.opportunity_id else None,
            "messages": self.messages,
            "current_message": self.current_message,
            "current_agent": self.current_agent,
            "next_agent": self.next_agent,
            "agent_actions": self.agent_actions,
            "execution_history": self.execution_history,
            "user_context": self.user_context,
            "customer_context": self.customer_context,
            "opportunity_context": self.opportunity_context,
            "memory": self.memory,
            "agent_response": self.agent_response,
            "error": self.error,
            "confidence": self.confidence,
            "start_time": self.start_time.isoformat(),
            "last_update": self.last_update.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentState":
        """Create state from dictionary"""
        return cls(
            conversation_id=UUID(data["conversation_id"]),
            user_id=UUID(data["user_id"]),
            customer_id=UUID(data["customer_id"]) if data.get("customer_id") else None,
            opportunity_id=UUID(data["opportunity_id"]) if data.get("opportunity_id") else None,
            messages=data.get("messages", []),
            current_message=data.get("current_message", ""),
            current_agent=data.get("current_agent", "router"),
            next_agent=data.get("next_agent", "router"),
            agent_actions=data.get("agent_actions", []),
            execution_history=data.get("execution_history", []),
            user_context=data.get("user_context", {}),
            customer_context=data.get("customer_context", {}),
            opportunity_context=data.get("opportunity_context", {}),
            memory=data.get("memory", {}),
            agent_response=data.get("agent_response", ""),
            error=data.get("error"),
            confidence=data.get("confidence", 0.0),
        )


class BaseAgent:
    """
    Base class for all agents in the conversation workflow.

    Defines common interface and utilities for agent implementation.
    """

    def __init__(self, agent_type: str, db_session=None):
        """
        Initialize agent.

        Args:
            agent_type: Type of agent (router, sales, data, strategy, sentinel, memory)
            db_session: Database session for queries
        """
        self.agent_type = agent_type
        self.db_session = db_session
        self.logger = logging.getLogger(f"agent.{agent_type}")

    async def execute(self, state: AgentState) -> AgentState:
        """
        Main execution method - to be overridden by subclasses.

        Args:
            state: Current conversation state

        Returns:
            Updated conversation state
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement execute()")

    def log_action(self, state: AgentState, action_type: str, details: Dict[str, Any]):
        """Log an agent action to execution history"""
        action = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": self.agent_type,
            "action_type": action_type,
            "details": details,
        }
        state.execution_history.append(action)
        self.logger.info(f"Action: {action_type} - {details}")

    def record_message(self, state: AgentState, role: str, content: str):
        """Record a message in conversation history"""
        state.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def update_context(self, state: AgentState, context_type: str, data: Dict[str, Any]):
        """Update agent context data"""
        if context_type == "user":
            state.user_context.update(data)
        elif context_type == "customer":
            state.customer_context.update(data)
        elif context_type == "opportunity":
            state.opportunity_context.update(data)
        elif context_type == "memory":
            state.memory.update(data)
        else:
            self.logger.warning(f"Unknown context type: {context_type}")

        state.last_update = datetime.utcnow()

    def set_next_agent(self, state: AgentState, next_agent: str):
        """Set the next agent to execute"""
        state.next_agent = next_agent
        self.logger.debug(f"Next agent set to: {next_agent}")

    def record_error(self, state: AgentState, error_msg: str):
        """Record an error in the current state"""
        state.error = error_msg
        state.last_update = datetime.utcnow()
        self.logger.error(f"Error: {error_msg}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(type={self.agent_type})"
