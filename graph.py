# noa/graph.py

import functools
import json
from typing import TypedDict, Dict, List, Annotated
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    """
    Represents the state of our agent simulation graph.

    Attributes:
        agent_prompts: Maps agent names to their full system prompts.
        agent_llms: Maps agent names to their configured LLM instances.
        agent_memories: Maps agent names to their memory logs.
        turn_messages: A list of messages exchanged in the current turn.
        final_reactions: The collected public reactions from all agents.
        user_action: The initial action that kicks off the simulation.
    """
    agent_prompts: Dict[str, str]
    agent_llms: Dict[str, any]
    agent_memories: Dict[str, List[str]]
    turn_messages: List[Dict[str, str]]
    final_reactions: Dict[str, str]
    user_action: str

def agent_node_fn(state: AgentState, agent_name: str) -> dict:
    """
    The core function that executes for each agent node in the graph.
    """
    print(f"--- EXECUTING AGENT: {agent_name} ---")
    
    # 1. Get the specific LLM for this agent
    llm = state['agent_llms'][agent_name]
    
    # 2. Assemble the full prompt
    system_prompt = state['agent_prompts'][agent_name]
    memory = "\n".join(state['agent_memories'][agent_name])
    
    # Inject the user action and memory into the prompt template
    # This assumes the placeholders {{action}} and {{this_persona_memory}} exist
    formatted_prompt = system_prompt.replace("{{action}}", state['user_action'])
    formatted_prompt = formatted_prompt.replace("{this_persona_memory}", memory)
    
    # 3. Invoke the LLM
    try:
        response_str = llm.invoke(formatted_prompt)
        response_json = json.loads(response_str)
    except (json.JSONDecodeError, AttributeError) as e:
        # Fallback if the LLM fails to produce valid JSON
        print(f"Error decoding LLM response for {agent_name}: {e}. Using raw response as public reaction.")
        response_json = {"public_reaction": str(response_str), "private_message": None}

    # 4. Process the response
    public_reaction = response_json.get("public_reaction", "")
    private_message = response_json.get("private_message")
    
    # 5. Update state
    # Add the public reaction to the final collection
    new_final_reactions = state.get('final_reactions', {}).copy()
    new_final_reactions[agent_name] = public_reaction

    # Add any private messages to the turn's message log
    new_turn_messages = state.get('turn_messages', []).copy()
    if private_message and "to" in private_message and "content" in private_message:
        new_turn_messages.append({
            "from": agent_name,
            "to": private_message["to"],
            "content": private_message["content"]
        })
    
    # Update this agent's memory
    new_agent_memories = state.get('agent_memories', {}).copy()
    memory_log = f"[Turn] Reacted publicly: '{public_reaction}'."
    if private_message:
        memory_log += f" || Messaged {private_message['to']}: '{private_message['content']}'."
    new_agent_memories[agent_name].append(memory_log)
    
    return {
        "final_reactions": new_final_reactions,
        "turn_messages": new_turn_messages,
        "agent_memories": new_agent_memories
    }


def create_agent_graph(agent_configs: Dict[str, Dict]):
    """
    Creates and compiles the LangGraph instance for the agent simulation.

    Args:
        agent_configs: A dictionary where keys are agent names and values are dicts
                       containing 'prompt' and 'llm' for each agent.
    """
    workflow = StateGraph(AgentState)
    
    agent_names = list(agent_configs.keys())
    
    # Add a node for each agent, dynamically binding the agent's name
    for name in agent_names:
        node_fn = functools.partial(agent_node_fn, agent_name=name)
        workflow.add_node(name, node_fn)

    # The entry point for the graph is to run all agent nodes in parallel
    workflow.set_entry_point(agent_names)

    # After each agent runs, the simulation ends for this turn.
    for name in agent_names:
        workflow.add_edge(name, END)
        
    print(f"Graph created with nodes: {', '.join(agent_names)}")
    return workflow.compile()