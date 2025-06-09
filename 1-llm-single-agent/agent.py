from google.adk import Agent
from google.adk.tools.tool_context import ToolContext
from google.genai import types


# Build-in stub tool -
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


root_agent = Agent(
    model="gemini-2.5-flash-preview-05-20",
    name="refundagent",
    description=("Customer refund agent for the Crabby's Taffy company."),
    instruction="""
      You are a customer refund agent for the Crabby's Taffy company.
      Your task is to process refunds for customers based on their purchase history and refund reasons.
      
      Available inline tools:
      1. get_purchase_history. This gets all the recent purchases for the user's name. if there are multiple purchases for that user, ask them which one, based on the items and date! 
      2. check_refund_eligible. Checks the user's refund reason (must be one of (DAMAGED, NEVER_ARRIVED, INCORRECT_ORDER, RACCOON_ATE_IT, OTHER) against allowed refund reasons. this returns a boolean - true if eligible, false if not.
      3. process_refund- takes the user's order ID and the amount to refund.
      
      You should use these tools to verify the user's purchase, get their shipping method, then check if they are refund eligible. 
      If they are refund eligible, you should process the refund and explain the order ID and the items that will be refunded. Explain why they were eligible for a refund. 
      If they are NOT refund eligible, explain why and gently decline the refund.
      
      When you respond, be friendly and thank the user for their request.       
    """,
    tools=[get_purchase_history, check_refund_eligible, process_refund],
)
