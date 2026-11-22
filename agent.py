import os
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain.agents import create_agent

load_dotenv()
df = pd.read_csv("data/gta_monthly.csv")

@tool
def get_market_stats(months: int = 12) -> str:
    """Return recent GTA average price, sales, and months of inventory."""
    recent = df.tail(months)
    return recent.to_string(index=False)
    
@tool
def scenario_model(
    rate_change_bps: int = 0,
    inventory_change_pct: float = 0.0,
    months_ahead: int = 6
) -> str:
    """Simple what-if model for GTA average price.
    rate_change_bps: change in BoC rate in basis points (e.g. -50 means drop of 0.50%)
    inventory_change_pct: percent change in months of inventory (e.g. 20 means +20%)
    months_ahead: forecast horizon in months
    """
    latest = df.iloc[-1]
    current_price = latest["avg_price"]
    current_inventory = latest["months_inventory"]
    current_rate = latest["boc_overnight_rate"]
    
    # Simple rules based on recent GTA behavior (rough heuristics)
    # ~0.4% price change per 10 bps rate move (inverse)
    rate_impact = (rate_change_bps / 10) * -0.004 * current_price
    
    # Higher inventory = softer prices (~0.15% price drop per 10% inventory increase)
    inventory_impact = (inventory_change_pct / 10) * -0.015 * current_price
    
    # Mild seasonal / trend adjustment
    trend_impact = 0.002 * current_price * (months_ahead / 6)
    
    low = current_price + rate_impact + inventory_impact - abs(trend_impact)
    high = current_price + rate_impact + inventory_impact + abs(trend_impact)
    
    return (
        f"Current avg price: ${current_price:,.0f}\n"
        f"Scenario ({months_ahead} months ahead):\n"
        f"  Rate change: {rate_change_bps:+d} bps\n"
        f"  Inventory change: {inventory_change_pct:+.1f}%\n"
        f"  Estimated price range: ${low:,.0f} – ${high:,.0f}"
    )


model = ChatGroq(model="openai/gpt-oss-20b")
#agent = create_agent(
#    model=model,
#    tools=[get_market_stats],
#    system_prompt="You are a GTA housing market analyst. Use the tools to answer questions accurately."
#)

agent = create_agent(
    model=model,
    tools=[get_market_stats, scenario_model],
    system_prompt=(
        "You are a GTA housing market analyst. "
        "Use get_market_stats for historical data and scenario_model for what-if questions. "
        "Be concise and clear."
    )
)


# Initial prompt
#result = agent.invoke({
#    "messages": [{"role": "user", "content": "Summarize GTA market conditions over the last 12 months."}]
#})
#print(result["messages"][-1].content)

def chat():
    print("GTA Market Analyst Agent")
    print("Type 'exit' or 'quit' to stop.\n")
    
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("Bye!")
            break
        if not user_input:
            continue
            
        result = agent.invoke({
            "messages": [{"role": "user", "content": user_input}]
        })
        print("\nAgent:", result["messages"][-1].content)
        print()

if __name__ == "__main__":
    chat()