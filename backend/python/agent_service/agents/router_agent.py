"""
Router Agent - Intent detection and agent routing
Entry point for all conversations
"""

from agent_service.agents.base_agent import BaseAgent, AgentState
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger("agent.router")


class RouterAgent(BaseAgent):
    """
    Router Agent - Initial message processing and intent detection.

    Analyzes user input and determines which subagent should handle the request:
    - Sales: Opportunity/deal related inquiries
    - Data: Query and analytics requests
    - Strategy: Complex strategic questions
    - Sentinel: Monitoring and alert scenarios
    - Memory: Knowledge retrieval and context
    """

    def __init__(self, db_session=None):
        super().__init__("router", db_session)

    async def execute(self, state: AgentState) -> AgentState:
        """
        Route incoming message to appropriate agent.

        Process:
        1. Extract intent from user message
        2. Determine confidence score
        3. Route to appropriate agent
        4. Handle fallback scenarios

        Args:
            state: Current conversation state

        Returns:
            Updated state with routing decision
        """
        state.current_agent = "router"
        message = state.current_message.lower()

        # Record the incoming message
        self.record_message(state, "user", state.current_message)
        self.log_action(state, "message_received", {
            "message_length": len(state.current_message),
            "conversation_id": str(state.conversation_id)
        })

        # Intent detection (simplified keyword-based routing)
        intent, confidence = self._detect_intent(message)
        state.confidence = confidence

        # Route to appropriate agent
        next_agent = self._route_agent(intent)
        state.next_agent = next_agent

        # Record routing decision
        self.record_message(state, "system", f"Routing to {next_agent} agent with confidence {confidence:.2f}")
        self.log_action(state, "intent_detection", {
            "intent": intent,
            "confidence": confidence,
            "routed_to": next_agent
        })

        # Update memory with intent
        self.update_context(state, "memory", {
            "last_intent": intent,
            "last_confidence": confidence,
            "routing_timestamp": datetime.utcnow().isoformat(),
        })

        return state

    def _detect_intent(self, message: str) -> tuple[str, float]:
        """
        Detect user intent from message.

        Returns:
            Tuple of (intent_type, confidence_score)
        """
        # Keywords for each intent type
        intent_keywords = {
            "sales": [
                "deal", "opportunity", "create", "close", "proposal", "quote",
                "customer", "prospect", "pipeline", "forecast", "revenue"
            ],
            "data": [
                "query", "report", "analytics", "data", "search", "find",
                "list", "show", "historical", "trend", "analysis"
            ],
            "strategy": [
                "strategy", "plan", "advice", "recommend", "improve",
                "best practice", "approach", "help", "guide"
            ],
            "memory": [
                "remember", "recall", "history", "previous", "context",
                "note", "save", "store", "remind"
            ]
        }

        # Score each intent
        scores = {intent: 0.0 for intent in intent_keywords}

        for intent, keywords in intent_keywords.items():
            for keyword in keywords:
                if keyword in message:
                    scores[intent] += 1.0

        # Find best match
        best_intent = max(scores, key=scores.get)
        confidence = min(0.99, scores[best_intent] / len(message) * 100)

        # Default to sales if low confidence
        if confidence < 0.1:
            best_intent = "sales"
            confidence = 0.5  # Neutral confidence

        return best_intent, confidence

    def _route_agent(self, intent: str) -> str:
        """
        Determine next agent based on detected intent.

        Args:
            intent: Detected intent type

        Returns:
            Next agent name
        """
        routing_map = {
            "sales": "sales",
            "data": "data",
            "strategy": "strategy",
            "memory": "memory",
        }

        return routing_map.get(intent, "sales")  # Default to sales

    def _handle_error(self, state: AgentState, error: str) -> AgentState:
        """Handle routing errors"""
        self.record_error(state, error)
        state.next_agent = "sales"  # Fallback to sales agent
        return state
