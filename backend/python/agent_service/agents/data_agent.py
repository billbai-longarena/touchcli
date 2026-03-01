"""
Data Agent - Query and analytics handling
Executes database queries and provides data insights
"""

from agent_service.agents.base_agent import BaseAgent, AgentState
import logging

logger = logging.getLogger("agent.data")


class DataAgent(BaseAgent):
    """
    Data Agent - Handle analytics and data queries.

    Capabilities:
    - Customer data queries
    - Sales analytics
    - Report generation
    - Historical data analysis
    """

    def __init__(self, db_session=None):
        super().__init__("data", db_session)

    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute data query operations.

        Args:
            state: Current conversation state

        Returns:
            Updated state with query results
        """
        state.current_agent = "data"

        try:
            # Parse query intent
            query_type = self._determine_query_type(state.current_message)

            self.log_action(state, "data_query", {"query_type": query_type})

            # Execute appropriate query
            if query_type == "customer_list":
                state.agent_response = "I can show you a list of all customers. Would you like to filter by type, assigned owner, or search terms?"
            elif query_type == "opportunity_analysis":
                state.agent_response = "I'll analyze the opportunities. What time period or filters would you like?"
            elif query_type == "revenue_forecast":
                state.agent_response = "Here's the revenue forecast based on current pipeline and close probabilities."
            else:
                state.agent_response = "I can help you query customer data, opportunities, and sales metrics. What would you like to know?"

            self.record_message(state, "data", state.agent_response)

            # Route to next agent
            state.next_agent = "strategy"

        except Exception as e:
            self.record_error(state, f"Data agent error: {str(e)}")
            state.next_agent = "data"

        return state

    def _determine_query_type(self, message: str) -> str:
        """Determine type of data query"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["customer", "list", "show"]):
            return "customer_list"

        if any(word in message_lower for word in ["opportunity", "analysis", "pipeline"]):
            return "opportunity_analysis"

        if any(word in message_lower for word in ["revenue", "forecast", "predict"]):
            return "revenue_forecast"

        return "general_query"
