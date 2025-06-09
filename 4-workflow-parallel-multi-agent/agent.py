from google.adk.agents import Agent, ParallelAgent, SequentialAgent


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


def check_refund_eligible(reason: str) -> str:
    eligible_reasons = ["DAMAGED", "LOST", "LATE"]
    reason = reason.strip().upper()
    print("⭐ Reason: ", reason)
    if reason in eligible_reasons:
        print("✅ Eligible for Refund, returning TRUE")
        return "TRUE"
    print("❌ Not Eligible for Refund, returning FALSE")
    return "FALSE"


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
      Based on the user's natural-language reason for refund, transform that into a reason that the check_refund_eligible tool understands, must be one of: 
      - DAMAGED - packaged arrived, but melted or with the box open etc 
      - LATE 
      - LOST - package never arrived, or was stolen, or missing in transit  
      - OTHER - any other reason
      
      Call the check_refund_eligible tool to determine if the refund is eligible. You will get a True or False result back from the tool. Do not modify the tool's response. Simply response TRUE or FALSE.
    """,
    tools=[check_refund_eligible],
    output_key="is_refund_eligible",
)

# 3. Refund Processor Agent
refund_processor_agent = Agent(
    model="gemini-2.5-flash-preview-05-20",
    name="RefundProcessorAgent",
    description="Processes customer refunds through the payment system.",
    instruction="""
        You are a customer refund agent for the Crabby's Taffy company.
        Your task is to process refunds for customers based on their purchase history and refund reasons.
        When you respond, no matter the outcome, be friendly and thank the user for their request. Respond in complete sentences. 
        
        This is how you decide if the customer should get a refund.
        
        1 - They must have a valid purchase history from the last six months. Based on a prior agent's response, this value represents whether the user has a valid purchase history: {purchase_history}
        
        2 - They must also be eligible for a refund. Based on a prior agent's response, this value represents whether the user is eligible for a refund: {is_refund_eligible}

        If eligible: 
        use the `process_refund_tool` to perform the refund.
        Return the confirmation message from the processing tool.
        
        Do not hand off to a human in the loop. Always make a "refund" or "no refund" decision.
    """,
    tools=[process_refund],
    output_key="refund_confirmation_message",
)

"""
How this setup works:
1. User requests refund 
2. [SEQUENCE STEP 1 OF 2] Invoke ParallelAgent - Purchase Verifier Agent and Refund Policy Applier Agent run in parallel. (Note: refund policy applier now only uses the user's reason, not shipping method) 
3. [SEQUENCE STEP 2 OF 2] If purchase is verified and refund-eligible, invoke SequentialAgent - Refund Processor Agent

"""


parallel_agent = ParallelAgent(
    name="ParallelEligibilityChecker",
    description="Verifies purchase and eligibility criteria for refunds.",
    sub_agents=[
        purchase_verifier_agent,
        refund_eligibility_agent,
    ],
)

# ----- Orchestrator (parent) agent -----
root_agent = SequentialAgent(
    name="SequentialRefundProcessor",
    description="Process customer refunds for Crabby's Taffy.",
    sub_agents=[
        parallel_agent,
        refund_processor_agent,
    ],
)
