"""
Sales Agent - Opportunity and deal management
Handles customer context, opportunity creation, and sales workflows
"""

from agent_service.agents.base_agent import BaseAgent, AgentState
from agent_service.models import Customer, Opportunity
from sqlalchemy import desc
import logging
from datetime import datetime

logger = logging.getLogger("agent.sales")


class SalesAgent(BaseAgent):
    """
    Sales Agent - Handle opportunity and deal-related operations.

    Capabilities:
    - Customer context retrieval
    - Opportunity creation and updates
    - Sales stage progression
    - Deal analysis and recommendations
    - Customer interaction history
    """

    def __init__(self, db_session=None):
        super().__init__("sales", db_session)

    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute sales operations.

        Process:
        1. Load customer and opportunity context
        2. Determine sales action (create, update, analyze)
        3. Execute action against database
        4. Generate response for user
        5. Update state

        Args:
            state: Current conversation state

        Returns:
            Updated state with sales action result
        """
        state.current_agent = "sales"

        try:
            # Load customer context if customer_id provided
            if state.customer_id and self.db_session:
                await self._load_customer_context(state)

            # Determine sales action from message
            action = self._determine_action(state.current_message)
            self.log_action(state, "sales_analysis", {"action_type": action})

            # Execute appropriate action
            if action == "create_opportunity":
                await self._handle_create_opportunity(state)
            elif action == "update_opportunity":
                await self._handle_update_opportunity(state)
            elif action == "analyze_pipeline":
                await self._handle_analyze_pipeline(state)
            elif action == "customer_summary":
                await self._handle_customer_summary(state)
            else:
                await self._handle_general_query(state)

            # Route to next agent (or complete)
            state.next_agent = "sentinel"  # Next for monitoring/alerts

        except Exception as e:
            self.record_error(state, f"Sales agent error: {str(e)}")
            state.next_agent = "sales"  # Retry

        return state

    async def _load_customer_context(self, state: AgentState):
        """Load customer data into context"""
        try:
            customer = self.db_session.query(Customer).filter(
                Customer.id == state.customer_id
            ).first()

            if customer:
                state.customer_context = {
                    "id": str(customer.id),
                    "name": customer.name,
                    "type": customer.type,
                    "email": customer.email,
                    "phone": customer.phone,
                    "tags": customer.tags,
                }

                # Load related opportunities
                if hasattr(customer, 'opportunities'):
                    state.customer_context["opportunities_count"] = len(customer.opportunities)
                    state.customer_context["recent_opportunities"] = [
                        {
                            "id": str(o.id),
                            "name": o.name,
                            "amount": o.amount,
                            "status": o.status,
                        }
                        for o in customer.opportunities[:5]
                    ]

                self.log_action(state, "customer_context_loaded", {
                    "customer_id": str(customer.id),
                    "customer_name": customer.name,
                })

        except Exception as e:
            logger.error(f"Failed to load customer context: {e}")

    def _determine_action(self, message: str) -> str:
        """Determine which sales action to perform"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["create", "new", "add"]):
            if any(word in message_lower for word in ["opportunity", "deal", "opp"]):
                return "create_opportunity"

        if any(word in message_lower for word in ["update", "modify", "change"]):
            return "update_opportunity"

        if any(word in message_lower for word in ["pipeline", "forecast", "opportunities"]):
            return "analyze_pipeline"

        if any(word in message_lower for word in ["summary", "overview", "profile"]):
            return "customer_summary"

        return "general_query"

    async def _handle_create_opportunity(self, state: AgentState):
        """Handle opportunity creation"""
        if not state.customer_id:
            state.agent_response = "I need to know which customer this opportunity is for. Could you provide the customer name or ID?"
            return

        state.agent_response = f"I'll help you create a new opportunity for this customer. Please provide details like the deal name, amount, and expected close date."

        self.update_context(state, "memory", {
            "creating_opportunity": True,
            "customer_id": str(state.customer_id),
        })

    async def _handle_update_opportunity(self, state: AgentState):
        """Handle opportunity updates"""
        if not state.opportunity_id:
            state.agent_response = "Which opportunity would you like to update? Please provide the opportunity name or ID."
            return

        state.agent_response = "What would you like to change about this opportunity?"

    async def _handle_analyze_pipeline(self, state: AgentState):
        """Analyze sales pipeline"""
        state.agent_response = "Here's a summary of the current sales pipeline with all active opportunities."

    async def _handle_customer_summary(self, state: AgentState):
        """Provide customer summary"""
        if state.customer_context:
            customer_name = state.customer_context.get("name", "the customer")
            opps_count = state.customer_context.get("opportunities_count", 0)
            state.agent_response = f"Here's the summary for {customer_name}: {opps_count} active opportunities, contact info on file."
        else:
            state.agent_response = "Please specify which customer you'd like a summary for."

    async def _handle_general_query(self, state: AgentState):
        """Handle general sales-related queries"""
        state.agent_response = "I can help you with opportunities, customer information, and sales strategies. What would you like to know?"

        self.record_message(state, "sales", state.agent_response)
