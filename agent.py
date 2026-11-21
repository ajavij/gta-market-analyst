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

#model = ChatOpenAI(model="gpt-4o-mini")
model = ChatGroq(model="openai/gpt-oss-20b")
agent = create_agent(
    model=model,
    tools=[get_market_stats],
    system_prompt="You are a GTA housing market analyst. Use the tools to answer questions accurately."
)
result = agent.invoke({
    "messages": [{"role": "user", "content": "Summarize GTA market conditions over the last 12 months."}]
})
print(result["messages"][-1].content)