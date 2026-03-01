"""
Conversation Workflow Orchestrator
Manages the multi-agent conversation flow using a state machine pattern
(LangGraph integration point for future enhancement)
"""

from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from agent_service.agents.base_agent import AgentState
from agent_service.agents.router_agent import RouterAgent
from agent_service.agents.sales_agent import SalesAgent
from agent_service.agents.data_agent import DataAgent
from agent_service.agents.strategy_agent import StrategyAgent
from agent_service.models import Conversation, Message, AgentState as DBAgentState

logger = logging.getLogger("workflow")


class ConversationWorkflow:
    """
    Orchestrates multi-agent conversation workflow.

    Flow:
    1. Router Agent: Analyze intent and route
    2. Specialized Agents: Handle specific domain (Sales, Data, Strategy)
    3. Sentinel Agent: Monitor quality and escalate if needed
    4. Memory: Persist context for future conversations
    """

    def __init__(self, db_session: Session):
        """
        Initialize workflow.

        Args:
            db_session: Database session for persistence
        """
        self.db_session = db_session

        # Initialize agents
        self.agents = {
            "router": RouterAgent(db_session),
            "sales": SalesAgent(db_session),
            "data": DataAgent(db_session),
            "strategy": StrategyAgent(db_session),
        }

        self.logger = logging.getLogger("workflow")

    async def process_message(
        self,
        conversation_id: UUID,
        user_id: UUID,
        message: str,
        customer_id: Optional[UUID] = None,
        opportunity_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Process user message through agent workflow.

        Args:
            conversation_id: Conversation UUID
            user_id: User UUID
            message: User message content
            customer_id: Optional customer context
            opportunity_id: Optional opportunity context

        Returns:
            Workflow result with agent responses and actions
        """
        logger.info(f"Processing message for conversation {conversation_id}")

        # Load or create state
        state = await self._load_or_create_state(
            conversation_id, user_id, customer_id, opportunity_id
        )
        state.current_message = message

        # Execute agent workflow
        try:
            state = await self._execute_workflow(state)

            # Persist state
            await self._persist_state(conversation_id, state)

            # Return result
            return {
                "conversation_id": str(conversation_id),
                "message": message,
                "agent_response": state.agent_response,
                "next_agent": state.next_agent,
                "confidence": state.confidence,
                "actions": state.agent_actions,
                "execution_history": state.execution_history[-3:],  # Last 3 actions
            }

        except Exception as e:
            logger.error(f"Workflow error: {e}")
            return {
                "conversation_id": str(conversation_id),
                "error": str(e),
                "agent_response": "I encountered an error processing your request. Please try again.",
            }

    async def _load_or_create_state(
        self,
        conversation_id: UUID,
        user_id: UUID,
        customer_id: Optional[UUID] = None,
        opportunity_id: Optional[UUID] = None,
    ) -> AgentState:
        """Load existing state or create new state"""
        # TODO: Load from Redis cache or database checkpoint
        return AgentState(
            conversation_id=conversation_id,
            user_id=user_id,
            customer_id=customer_id,
            opportunity_id=opportunity_id,
        )

    async def _execute_workflow(self, state: AgentState) -> AgentState:
        """
        Execute agent workflow.

        Sequence:
        1. Router → determine intent and route
        2. Specialized Agent → execute domain action
        3. Sentinel → monitor quality (TODO)
        4. Memory → persist learnings (TODO)
        """
        max_iterations = 5
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Get current agent
            agent_name = state.current_agent
            agent = self.agents.get(agent_name)

            if not agent:
                logger.warning(f"Unknown agent: {agent_name}, routing to sales")
                agent = self.agents["sales"]
                agent_name = "sales"

            # Execute agent
            logger.debug(f"Executing agent: {agent_name}")
            state = await agent.execute(state)

            # Check if workflow should continue
            if state.next_agent == state.current_agent or state.error:
                # Agent completed or error occurred
                logger.debug(f"Workflow iteration {iteration} complete")
                break

            # Move to next agent
            state.current_agent = state.next_agent

        return state

    async def _persist_state(self, conversation_id: UUID, state: AgentState):
        """
        Persist workflow state.

        TODO: Implement persistence to:
        - Redis (cache for quick access)
        - PostgreSQL (durable storage)
        - Message history (for conversation context)
        """
        try:
            # Serialize state for storage
            state_dict = state.to_dict()

            # TODO: Store in database
            # db_state = AgentState(
            #     conversation_id=conversation_id,
            #     agent_type="system",
            #     state=state_dict,
            #     checkpoint_id=str(uuid4())
            # )
            # self.db_session.add(db_state)
            # self.db_session.commit()

            logger.debug(f"State persisted for conversation {conversation_id}")

        except Exception as e:
            logger.error(f"Failed to persist state: {e}")

    async def get_conversation_history(
        self, conversation_id: UUID, limit: int = 50
    ) -> list:
        """
        Get conversation history.

        Args:
            conversation_id: Conversation UUID
            limit: Maximum number of messages

        Returns:
            List of message records
        """
        messages = self.db_session.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).limit(limit).all()

        return [
            {
                "id": str(m.id),
                "content": m.content,
                "sender_role": m.sender_role,
                "timestamp": m.created_at.isoformat(),
            }
            for m in reversed(messages)
        ]

    async def resume_conversation(self, conversation_id: UUID) -> AgentState:
        """
        Resume conversation from checkpoint.

        Args:
            conversation_id: Conversation UUID

        Returns:
            Loaded agent state
        """
        # TODO: Load from database checkpoint
        db_conversation = self.db_session.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not db_conversation:
            raise ValueError(f"Conversation not found: {conversation_id}")

        state = AgentState(
            conversation_id=conversation_id,
            user_id=db_conversation.user_id,
            customer_id=db_conversation.customer_id,
            opportunity_id=db_conversation.opportunity_id,
        )

        return state
