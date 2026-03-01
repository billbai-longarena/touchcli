"""
Strategy Agent - Advice and strategic recommendations
Provides sales strategy guidance and best practices
"""

from agent_service.agents.base_agent import BaseAgent, AgentState
import logging

logger = logging.getLogger("agent.strategy")


class StrategyAgent(BaseAgent):
    """
    Strategy Agent - Provide strategic advice and recommendations.

    Capabilities:
    - Sales strategy recommendations
    - Best practice guidance
    - Deal strategy analysis
    - Negotiation advice
    """

    def __init__(self, db_session=None):
        super().__init__("strategy", db_session)

    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute strategy operations.

        Args:
            state: Current conversation state

        Returns:
            Updated state with strategic recommendations
        """
        state.current_agent = "strategy"

        try:
            # Parse strategy intent
            strategy_type = self._determine_strategy(state.current_message)

            self.log_action(state, "strategy_analysis", {"strategy_type": strategy_type})

            # Provide strategic guidance
            if strategy_type == "deal_strategy":
                state.agent_response = "Here's my recommendation for the deal strategy: Focus on the customer's pain points and demonstrate clear ROI. Consider starting with a proposal meeting."
            elif strategy_type == "sales_approach":
                state.agent_response = "I recommend a consultative approach: Ask open-ended questions, listen actively, and position solutions around their specific needs."
            elif strategy_type == "negotiation":
                state.agent_response = "In negotiations, remember to: establish your BATNA, focus on mutual value, avoid anchoring too low, and leave room for creative solutions."
            elif strategy_type == "expansion":
                state.agent_response = "For account expansion: Look for adjacent needs, build champion relationships, demonstrate quick wins, and plan cross-sell opportunities."
            else:
                state.agent_response = "I can help with sales strategy, deal approaches, negotiation tactics, and account expansion plans. What's your specific challenge?"

            self.record_message(state, "strategy", state.agent_response)

            # Route to completion or sentinel monitoring
            state.next_agent = "sentinel"

        except Exception as e:
            self.record_error(state, f"Strategy agent error: {str(e)}")
            state.next_agent = "strategy"

        return state

    def _determine_strategy(self, message: str) -> str:
        """Determine type of strategy question"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["deal", "strategy", "approach"]):
            return "deal_strategy"

        if any(word in message_lower for word in ["how", "approach", "method", "way"]):
            return "sales_approach"

        if any(word in message_lower for word in ["negotiate", "negotiation", "price", "discount"]):
            return "negotiation"

        if any(word in message_lower for word in ["expand", "upsell", "cross-sell", "grow"]):
            return "expansion"

        return "general_advice"
