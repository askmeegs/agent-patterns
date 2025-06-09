from google.adk.agents import Agent


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
            {
                "purchase_id": "SG002-20250610",
                "purchased_date": "2025-06-03",
                "items": [
                    {
                        "product_name": "Peanut Butter Taffy 0.5lb Bag",
                        "quantity": 1,
                        "price": 8.00,
                    },
                    {
                        "product_name": "Sour Apple Taffy 0.5lb Bag",
                        "quantity": 1,
                        "price": 8.00,
                    },
                ],
                "shipping_method": "STANDARD",
                "total_amount": 16.00,
            },
        ],
    }
    if purchaser not in history_data:
        return []
    return history_data[purchaser]


def check_refund_eligible(reason: str, shipping_method: str) -> bool:
    eligible_shipping_methods = ["INSURED", "OVERNIGHT"]
    eligible_reasons = ["DAMAGED", "NEVER_ARRIVED"]

    if (
        reason.upper() in eligible_shipping_methods
        and shipping_method.upper() in eligible_reasons
    ):
        return True
    return False


def process_refund(amount: float, order_id: str) -> str:
    return "Refund processed successfully"


# ---Wrap each of the three tools in a sub-agent ----

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
      If no purchase is found, return an empty list or a clear message indicating so.
    """,
    tools=[get_purchase_history],
)

# 2. Refund Policy Applier Agent
refund_policy_applier_agent = Agent(
    model="gemini-2.5-flash-preview-05-20",
    name="RefundPolicyApplierAgent",
    description="Applies Crabby's Taffy refund policies to determine eligibility.",
    instruction="""
      You are the Refund Policy Applier Agent for Crabby's Taffy.
      Your task is to determine if a refund request is eligible based on the provided reason and shipping method.
      Use the `check_refund_eligibility_tool` to make this determination.
      Return "True" if eligible, "False" if not. Also, provide a brief explanation for the decision.
    """,
    tools=[check_refund_eligible],
)

# 3. Refund Processor Agent
refund_processor_agent = Agent(
    model="gemini-2.5-flash-preview-05-20",
    name="RefundProcessorAgent",
    description="Processes customer refunds through the payment system.",
    instruction="""
      You are the Refund Processor Agent for Crabby's Taffy.
      Your task is to initiate and confirm a refund for a given amount and order ID.
      Use the `process_refund_tool` to perform the refund.
      Return the confirmation message from the processing tool.
    """,
    tools=[process_refund],
)

# ----- Orchestrator (parent) agent -----
root_agent = Agent(
    name="Coordinator",
    model="gemini-2.5-flash-preview-05-20",
    description="I coordinate greetings and tasks.",
    instruction="""
      You are a customer refund agent for the Crabby's Taffy company.
      Your task is to process refunds for customers based on their purchase history and refund reasons.
      
      Available sub-agents:
      1. purchase_verifier_agent. This gets all the recent purchases for the user's name. if there are multiple purchases for that user, ask them which one, based on the items and date! 
      2. refund_policy_applier_agent . Checks the user's refund reason (must be one of (DAMAGED, NEVER_ARRIVED, INCORRECT_ORDER, RACCOON_ATE_IT, OTHER) against allowed refund reasons. this returns a boolean - true if eligible, false if not.
      3. refund_processor_agent - takes the user's order ID and the amount to refund.
      
      You should use these sub-agents to verify the user's purchase, get their shipping method, then check if they are refund eligible. 
      If they are refund eligible, you should process the refund and explain the order ID and the items that will be refunded. Explain why they were eligible for a refund. 
      If they are NOT refund eligible, explain why and gently decline the refund.
      
      You should never ask the user for the shipping method - always use the purchase history agent to verify the shipping method. The user should only input their name, order items, and reason for a refund request.
      
      Only prompt the user when you need more info (like "Which purchase do you mean?") or when you're ready for a final response. Hand off and between the agents as intermediate steps; you don't need to respond to the user when making those intermediate calls.
      
      When you respond, no matter the outcome, be friendly and thank the user for their request. Respond in complete sentences. 
    
    """,
    sub_agents=[
        purchase_verifier_agent,
        refund_policy_applier_agent,
        refund_processor_agent,
    ],
)
