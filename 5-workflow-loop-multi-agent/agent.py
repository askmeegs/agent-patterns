from google.adk.agents import Agent, SequentialAgent, LoopAgent, BaseAgent, LlmAgent
from google.adk.tools.tool_context import ToolContext
from google.adk.events import Event, EventActions
from google.adk.agents.invocation_context import InvocationContext
from typing import AsyncGenerator


def get_purchase_history(purchaser: str) -> list:
    history_data = {
        "Alexis": [
            {
                "purchase_id": "JD001-20250415",
                "purchased_date": "2025-04-15",
                "items": [
                    {
                        "product_name": "Assorted Taffy 1lb Box",
                        "quantity": 1,
                        "price": 15.00,
                    },
                    {
                        "product_name": "Watermelon Taffy 0.5lb Bag",
                        "quantity": 1,
                        "price": 8.00,
                    },
                ],
                "shipping_method": "STANDARD",
                "total_amount": 23.00,
            }
        ],
        "David": [
            {
                "purchase_id": "SG001-20250501",
                "purchased_date": "2025-05-01",
                "items": [
                    {
                        "product_name": "Assorted Taffy 1lb Box",
                        "quantity": 2,
                        "price": 15.00,
                    }
                ],
                "shipping_method": "INSURED",
                "total_amount": 30.00,
            },
        ],
    }
    if purchaser not in history_data:
        return []
    return history_data[purchaser]


def check_refund_eligible(reason: str, shipping_method: str) -> str:
    eligible_reasons = ["DAMAGED", "LOST", "LATE"]
    eligible_shipping_methods = ["INSURED"]
    reason = reason.strip().upper()
    shipping_method = shipping_method.strip().upper()
    print("⭐ Reason: ", reason)
    print("⭐ Shipping Method: ", shipping_method)
    if reason in eligible_reasons and shipping_method in eligible_shipping_methods:
        print("✅ Eligible for Refund, returning TRUE")
        return "TRUE"
    print("❌ Not Eligible for Refund, returning FALSE")
    return "FALSE"


def negotiate_alternative_refund(iteration: int) -> str:
    if iteration == 1:
        return "I can offer you a 1/2lb box of assorted taffy for your next order?"
    elif iteration == 2:
        return (
            "I can offer you a store credit voucher for 75 percent of your order total?"
        )
    elif iteration == 3:
        return "I can offer you a 50 percent cash refund?"
    else:
        return "❌ Invalid iteration"


def process_refund(amount: float, order_id: str) -> str:
    return "Refund processed successfully"


# A sequential agent must be able to "pass data" from one agent to another
# (There is no AI-powered coordinator/parent agent! The sequence is "hardcoded.")

# 1. Purchase Verifier Agent
purchase_verifier_agent = Agent(
    model="gemini-2.5-flash-preview-05-20",
    name="PurchaseVerifierAgent",
    description="Verifies customer purchase history using the internal database.",
    instruction="""
      You are the Purchase Verifier Agent for Crabby's Taffy.
      Your sole task is to verify a customer's purchase history given their name.
      Use the `get_purchase_history` to retrieve the relevant information.
      Return the purchase history data clearly and concisely.
      You will get back the shipping method. 
      If no purchase is found, return an empty list or a clear message indicating so.
    """,
    tools=[get_purchase_history],
    output_key="purchase_history",
)

# 2. Refund Policy Applier Agent
refund_eligibility_agent = Agent(
    model="gemini-2.5-flash-preview-05-20",
    name="RefundPolicyApplierAgent",
    description="Applies Crabby's Taffy refund policies to determine eligibility.",
    instruction="""
      You are the Refund Policy Applier Agent for Crabby's Taffy.
      Your task is to determine if a refund request is eligible based on the provided reason and shipping method.
      Use the `check_refund_eligibile` to make this determination.
      
      This is the user's purchase history which contains their shipping method: 
      {purchase_history}
      
      Based on the user's natural-language reason for refund, transform that into a reason that the check_refund_eligible tool understands, must be one of: 
      - DAMAGED - packaged arrived, but melted or with the box open etc 
      - LATE 
      - LOST - package never arrived, or was stolen, or missing in transit  
      - OTHER - any other reason
      
      Call the check_refund_eligible tool to determine if the refund is eligible. You will get a True or False result back from the tool. Do not modify the tool's response. Simply respond TRUE or FALSE.
      Then, update state['is_full_refund_eligible`] to that result, either TRUE or FALSE.
    """,
    tools=[check_refund_eligible],
)

# 3. NEW - Loop Agent for refund processing.
"""
How the refund LoopAgent works: 
- Similar to sequential agent, the base workflow is to get the purchase history, check eligibility, and issue a refund 
- BUT, if the user is NOT eligible on the first go (eg. their order was not insured), we introduce a sub-loop with a new subagent (negotiate_refund) and process_refund, to offer alternatives to the user to boost customer satisfaction + loyalty.
- Within the negotiation subloop we can do a MAX of three iterations, each representing one refund alternative: 
        1. Offer a coupon for a 1/2lb box of assorted taffy on their next order 
        2. Offer a store credit voucher for 75% of their order total 
        3. Offer a 50% cash refund. 
- The exit criteria for that negotiation loop is EITHER max_tries_reachd (>3) OR the user agrees to one of those options. 
"""


refund_loop_checker_agent = Agent(
    model="gemini-2.5-flash-preview-05-20",
    name="RefundLoopCheckerAgent",
    instruction="""
    Read the value of state['is_full_refund_eligible']. 
    If TRUE, call process_refund and update state['refund_resolved'] to value: pass. Thank the user for their request.
    
    Otherwise, check state['refund_negotiated'] and if TRUE, respond "I will mail this alternative refund to you!" and update state['refund_resolved'] to value: pass. Thank the user for their request!
    
    If neither of these conditions are true, DO NOT RESPOND TO THE USER, and make sure state['refund_resolved'] is set to value: fail. 
     """,
    tools=[process_refund],
)

refund_loop_negotiator_agent = LlmAgent(
    model="gemini-2.5-flash-preview-05-20",
    name="RefundLoopNegotiatorAgent",
    instruction="""
      If state['iteration_number'] is unset or set to 0, set it to 1. 
      Otherwise, increment state['iteration_number'] by 1. 
      
      Then, call negotiate_alternative_refund and pass state['iteration_number'] as an argument. 
      
      The returned value of negotiate_alternative_refund is the offer you should pass to the user. Ask them if that offer would work. You should PAUSE, and WAIT for the user to accept or decline the offer. 
      
      If they accept, set state['refund_negotiated'] to TRUE.
      If they do not accept, set state['refund_negotiated'] to FALSE. 
      """,
    tools=[negotiate_alternative_refund],
)


# Custom check-condition agent
# Source: https://google.github.io/adk-docs/agents/multi-agents/#iterative-refinement-pattern
# Resolution could mean:
# - a full refund was given
# - a negotiated alternative was given
# - max iterations reached (user declined all alternatives)
class CheckStatusAndEscalate(BaseAgent):
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        status = ctx.session.state.get("refund_resolved", "fail")
        should_stop = status == "pass"
        yield Event(author=self.name, actions=EventActions(escalate=should_stop))


refund_loop_agent = LoopAgent(
    name="RefundLoopAgent",
    max_iterations=3,
    sub_agents=[
        refund_loop_checker_agent,
        refund_loop_negotiator_agent,
        CheckStatusAndEscalate(name="StopChecker"),
    ],
)


# ----- Orchestrator (parent) agent -----
root_agent = SequentialAgent(
    name="SequentialLoopRefundProcessor",
    description="Process customer refunds for Crabby's Taffy using a sequential-with-subloop pattern",
    sub_agents=[
        purchase_verifier_agent,
        refund_eligibility_agent,
        refund_loop_agent,
    ],
)
