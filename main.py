# main.py
# Project: OmniAgent ERP - Multi-Agent Enterprise Resource Planning System
import os
import re
import json
import asyncio
import operator
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, END

# ── Environment Setup ──────────────────────────────────────────────
load_dotenv()
GROQ_KEY = os.getenv("GROQ_API_KEY")
os.environ["GROQ_API_KEY"] = GROQ_KEY or ""

# ── MCP Client Configuration ───────────────────────────────────────
mcp_client = MultiServerMCPClient({
    "erp": {
        "url": "http://localhost:8000/sse",
        "transport": "sse",
    }
})

# ── State Definition ────────────────────────────────────────────────
class ERPState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_query: Annotated[str, lambda a, b: b]
    intent: Annotated[str, lambda a, b: b]
    agents_to_call: Annotated[list, lambda a, b: b]
    inventory_result: Annotated[str, lambda a, b: b]
    procurement_result: Annotated[str, lambda a, b: b]
    crm_result: Annotated[str, lambda a, b: b]
    final_answer: Annotated[str, lambda a, b: b]

# ── LLM Models (Hybrid Architecture Strategy) ───────────────────────
# Fast Execution Model (8B) for tool-calling
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
# High-level Reasoning Model (70B) for orchestration & synthesis
llm_strong = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# ── Utility Functions ────────────────────────────────────────────────
def parse_llm_json(text: str) -> dict:
    clean = re.sub(r"```json|```", "", text).strip()
    return json.loads(clean)

def extract_last_ai_text(messages: list) -> str:
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and isinstance(msg.content, str) and msg.content.strip():
            return msg.content
    return ""

async def run_tools(ai_message, tools_map) -> list:
    tool_messages = []
    for tool_call in ai_message.tool_calls:
        tool_name = tool_call["name"]
        if tool_name not in tools_map:
            tool_messages.append(ToolMessage(content=f'{{"error": "Tool {tool_name} not found"}}', tool_call_id=tool_call["id"]))
            continue
        result = await tools_map[tool_name].ainvoke(tool_call["args"])
        formatted = str(result)
        tool_messages.append(ToolMessage(content=formatted, tool_call_id=tool_call["id"]))
    return tool_messages

# ── Core Agent Runner (Engineering Excellence: Guardrails & Stability) ─────
async def run_agent(label: str, state: ERPState, tool_names: list, system_prompt: str) -> str:
    """Execute specialized Agent loop with Logic Interceptors and Meltdown Protection."""
    tools = await mcp_client.get_tools()
    selected_tools = [t for t in tools if t.name in tool_names]
    tools_map = {t.name: t for t in selected_tools}

    # Strict instructions to mitigate hallucinations
    strict_instruction = (
        "\n\n[CORE RULES]\n"
        "1. ONLY search for products/customers mentioned by the user or found in previous results.\n"
        "2. DO NOT hallucinate common names (e.g., Sprite, John Doe) if not in database.\n"
        "3. Limit tool calls to the minimum necessary."
    )
    messages = [SystemMessage(content=system_prompt + strict_instruction)] + list(state["messages"][-3:])
    
    called_once = set()
    # Hallucination Blacklist (Logic Interceptor)
    forbidden_keywords = ["婚禮", "雪碧", "芬達", "張三", "李四", "電影", "遊戲", "手機"]

    for i in range(3): # Loop limit
        await asyncio.sleep(1.2) # Rate-limiting buffer
        
        # Sliding context window to save tokens
        ai_msg = await llm.bind_tools(selected_tools).ainvoke(messages[-3:])
        messages.append(ai_msg)

        if ai_msg.tool_calls:
            unique_calls = []
            for tc in ai_msg.tool_calls:
                # [Logic Interceptor] Physical block of hallucinated entities
                args_str = json.dumps(tc['args'], ensure_ascii=False)
                if any(kw in args_str for kw in forbidden_keywords):
                    print(f"   [INTERCEPTOR] Blocked forbidden keyword: {args_str}")
                    messages.append(ToolMessage(content="Error: Category not in scope.", tool_call_id=tc["id"]))
                    continue

                key = f"{tc['name']}::{json.dumps(tc['args'], sort_keys=True, ensure_ascii=False)}"
                if key in called_once:
                    messages.append(ToolMessage(content="Error: Duplicate call.", tool_call_id=tc["id"]))
                else:
                    called_once.add(key)
                    if len(unique_calls) < 3: # Meltdown protection: cap tool calls per turn
                        unique_calls.append(tc)

            if not unique_calls:
                final_ai = await llm.ainvoke(messages[-2:] + [SystemMessage(content="Please provide summary based on current data.")])
                return final_ai.content if isinstance(final_ai.content, str) else ""

            ai_msg.tool_calls = unique_calls
            tool_msgs = await run_tools(ai_msg, tools_map)
            messages.extend(tool_msgs)
            continue

        result = extract_last_ai_text(messages)
        if result: return result

    return extract_last_ai_text(messages) or "Agent concluded results."

# ── Nodes Definition ───────────────────────────────────────────
async def orchestrator_node(state: ERPState) -> ERPState:
    print(f"\n[{state.get('intent', 'Orchestrator')}] Analyzing...")
    prompt = "ERP Orchestrator. Route to [inventory, procurement, crm]. Respond in JSON: {\"intent\": \"...\", \"agents\": [...]}"
    response = await llm_strong.ainvoke([SystemMessage(content=prompt)] + list(state["messages"][-5:]))
    try:
        parsed = parse_llm_json(response.content)
        return {**state, "intent": parsed["intent"], "agents_to_call": parsed["agents"]}
    except:
        return {**state, "intent": "General", "agents_to_call": ["inventory", "procurement", "crm"]}

async def inventory_node(state: ERPState) -> ERPState:
    prompt = "Inventory Expert. Check stock and expiry. Traditional Chinese."
    result = await run_agent("Inventory", state, ["check_stock", "check_expiry", "search_products"], prompt)
    return {**state, "inventory_result": result}

async def procurement_node(state: ERPState) -> ERPState:
    prompt = f"Procurement Expert. Use inventory context: {state.get('inventory_result')} to order."
    result = await run_agent("Procurement", state, ["calc_order_qty", "get_supplier_info"], prompt)
    return {**state, "procurement_result": result}

async def crm_node(state: ERPState) -> ERPState:
    prompt = "CRM Expert. Analyze sales. No hallucinated names."
    result = await run_agent("CRM", state, ["get_customer_info", "analyze_sales"], prompt)
    return {**state, "crm_result": result}

async def synthesize_node(state: ERPState) -> ERPState:
    print("\n[Synthesizer] Integrating results...")
    combined = f"Inv: {state.get('inventory_result')}\nProc: {state.get('procurement_result')}\nCRM: {state.get('crm_result')}"
    prompt = f"Integrate results into professional Traditional Chinese report:\n{combined}"
    final_msg = await llm_strong.ainvoke([SystemMessage(content=prompt)] + list(state["messages"][-3:]))
    return {**state, "final_answer": final_msg.content, "messages": [final_msg]}

# ── Graph Construction ─────────────────────────────────────────
workflow = StateGraph(ERPState)
workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("inventory", inventory_node)
workflow.add_node("procurement", procurement_node)
workflow.add_node("crm", crm_node)
workflow.add_node("synthesize", synthesize_node)

workflow.set_entry_point("orchestrator")
workflow.add_edge("orchestrator", "inventory")
workflow.add_edge("inventory", "procurement")
workflow.add_edge("procurement", "crm")
workflow.add_edge("crm", "synthesize")
workflow.add_edge("synthesize", END)

app = workflow.compile()

async def run_erp(user_input: str):
    initial_input = {"messages": [HumanMessage(content=user_input)], "intent": "Initial"}
    final_state = await app.ainvoke(initial_input)
    return final_state["final_answer"]

if __name__ == "__main__":
    asyncio.run(run_erp("目前的營運健檢報告"))
