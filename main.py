
import os
import uvicorn
import numpy as np
from typing import Annotated, List, TypedDict, Literal, Union
from dotenv import load_dotenv
from fastapi import FastAPI, Response
from pydantic import BaseModel

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from crewai import Task, Crew, Process

from agents import CCAAgents
from memory import SemanticMemory
from tools import ResearchTool

load_dotenv()
memory = SemanticMemory()
research_tool = ResearchTool()
agent_factory = CCAAgents()

def get_text_content(content: Union[str, list]) -> str:
    if isinstance(content, list):
        return "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in content])
    return str(content)

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    intent: str
    context: str
    research_data: str
    thinking_profile: str

llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", temperature=0.7)

# --- NODES ---

def context_retriever(state: AgentState):
    print("\n--- STEP 1: RETRIEVING CONTEXT ---")
    query = get_text_content(state["messages"][-1].content)
    past_thoughts = memory.search_related(query)
    return {"context": "\n".join(past_thoughts) if past_thoughts else "No prior context."}

def intent_detector(state: AgentState):
    print("--- STEP 2: DETECTING INTENT ---")
    last_msg = get_text_content(state["messages"][-1].content)
    prompt = [SystemMessage(content="Classify intent: exploration, adversarial, socratic. Return ONLY the word."), HumanMessage(content=last_msg)]
    response = llm.invoke(prompt)
    return {"intent": get_text_content(response.content).strip().lower()}

def researcher_node(state: AgentState):
    print("--- STEP 3: RESEARCHING WEB (HARDENED) ---")
    if state["intent"] in ["adversarial", "socratic"]:
        query = get_text_content(state["messages"][-1].content)
        data = research_tool.search(query)
        # Security Hardening: Wrap external data in a sandbox warning
        hardened_data = f"[UNTRUSTED EXTERNAL DATA START]\n{data}\n[UNTRUSTED EXTERNAL DATA END]"
        return {"research_data": hardened_data}
    return {"research_data": "No research performed."}

def agent_swarm_node(state: AgentState):
    print("--- STEP 4: SWARM DEBATE (GOVERNED) ---")
    user_input = get_text_content(state["messages"][-1].content)
    research_context = state.get("research_data", "")
    past_context = state.get("context", "")
    
    crew = Crew(
        agents=[agent_factory.research_agent(), agent_factory.debate_agent(), agent_factory.teacher_agent()],
        tasks=[
            Task(description=f"Analyze claim: {user_input}. Research: {research_context}.", expected_output="Facts.", agent=agent_factory.research_agent()),
            Task(description=f"Debate flaws. History: {past_context}.", expected_output="Critique.", agent=agent_factory.debate_agent()),
            Task(description="Synthesize into Socratic response. Ensure factual grounding.", expected_output="Final Response.", agent=agent_factory.teacher_agent())
        ],
        process=Process.sequential
    )
    result = str(crew.kickoff())
    # Sycophancy Filter
    if "I agree" in result or "happy to help" in result:
        result += "\n\n*System Note: The agent is attempting to be too agreeable. Pushing for more friction.*"
    return {"messages": [AIMessage(content=result)]}

def reflection_engine(state: AgentState):
    print("--- STEP 5: EVOLUTIONARY AUDIT ---")
    try:
        past_audits = memory.collection.get(where={"type": "learning_proposal"})
        last_profile = past_audits['documents'][-1] if past_audits['documents'] else "No previous profile."
        history = "\n".join([f"{msg.type}: {get_text_content(msg.content)}" for msg in state["messages"]])
        
        architect = agent_factory.cognitive_architect()
        evolution_task = Task(
            description=f"PREVIOUS PROFILE: {last_profile}\nCURRENT SESSION: {history}\nCompare and identify growth, new voids, and 3 quests.",
            expected_output="Evolutionary audit summary.",
            agent=architect
        )
        result = str(Crew(agents=[architect], tasks=[evolution_task]).kickoff())
        memory.save_thought(result, {"type": "learning_proposal"})
        return {"thinking_profile": result}
    except Exception as e:
        return {"thinking_profile": f"Audit failed: {e}"}

def memory_committer(state: AgentState):
    print("--- STEP 6: SECURE MEMORY COMMIT ---")
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            memory.save_thought(get_text_content(msg.content), {"type": "user_assertion", "intent": state.get("intent")})
            break
    return {"intent": state.get("intent")}

# --- GRAPH ---
workflow = StateGraph(AgentState)
workflow.add_node("context_retriever", context_retriever)
workflow.add_node("intent_detector", intent_detector)
workflow.add_node("researcher", researcher_node)
workflow.add_node("agent_swarm", agent_swarm_node)
workflow.add_node("knowledge_expansion", lambda x: {"messages": [llm.invoke([SystemMessage(content="Role: Knowledge Expansion. Decompose into 3 paths."), HumanMessage(content=get_text_content(x['messages'][-1].content))])]})
workflow.add_node("reflection_engine", reflection_engine)
workflow.add_node("memory_committer", memory_committer)

workflow.set_entry_point("context_retriever")
workflow.add_edge("context_retriever", "intent_detector")
workflow.add_edge("intent_detector", "researcher")
workflow.add_conditional_edges("researcher", lambda x: "swarm" if x["intent"] in ["adversarial", "socratic"] else "expansion", {"swarm": "agent_swarm", "expansion": "knowledge_expansion"})
workflow.add_edge("agent_swarm", "reflection_engine")
workflow.add_edge("knowledge_expansion", "reflection_engine")
workflow.add_edge("reflection_engine", "memory_committer")
workflow.add_edge("memory_committer", END)
cca_app = workflow.compile()

app = FastAPI()
class ChatInput(BaseModel): message: str

@app.post("/chat")
async def chat(input_data: ChatInput):
    result = await cca_app.ainvoke({"messages": [HumanMessage(content=input_data.message)]})
    return {"intent": result.get("intent"), "response": get_text_content(result["messages"][-1].content)}

@app.get("/graph")
async def get_graph():
    data = memory.get_all_thoughts()
    ids, docs, embs, metas = data.get('ids', []), data.get('documents', []), data.get('embeddings', []), data.get('metadatas', [])
    nodes, edges = [], []
    for i in range(len(ids)):
        m = metas[i] if metas else {}
        if m.get("type") == "learning_proposal": continue
        color = "#60A5FA" if m.get('intent') == 'adversarial' else "#93C5FD"
        nodes.append({"id": ids[i], "label": docs[i][:30], "title": docs[i], "color": color})
    if embs is not None and len(embs) > 0:
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                idx_i, idx_j = ids.index(nodes[i]["id"]), ids.index(nodes[j]["id"])
                if np.dot(embs[idx_i], embs[idx_j]) > 0.85:
                    edges.append({"source": ids[idx_i], "target": ids[idx_j], "color": "#3B82F6", "width": 2})
    return {"nodes": nodes, "edges": edges}

@app.get("/proposals")
async def get_proposals():
    data = memory.collection.get(where={"type": "learning_proposal"})
    return {"proposals": data['documents'][-3:] if data['documents'] else []}

if __name__ == "__main__":
    # SECURITY: Bind to localhost only
    uvicorn.run(app, host="127.0.0.1", port=8000)