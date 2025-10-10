
import functools
import json
from typing import TypedDict, Dict, List, Annotated
import operator
from langgraph.graph import StateGraph, START, END
from utils import strip_think_tags, extract_json_from_llm_response
from chains import FRAGMENTATION_PROMPT

# This function will be used to merge updates to dictionaries from parallel agent runs.
def merge_dict_updates(x: dict, y: dict) -> dict:
    return {**x, **y}

class AgentState(TypedDict):
    """
    Represents the state of our agent simulation graph.
    We use `Annotated` to provide a "reducer" function for keys that
    are updated by multiple agents in parallel. This tells the graph
    how to merge the parallel updates.
    """
    agent_prompts: Dict[str, str]
    agent_llms: Dict[str, any]
    user_action: str
    is_local: bool

    # For dictionaries, we merge them.
    final_reactions: Annotated[dict, merge_dict_updates]
    agent_memories: Annotated[dict, merge_dict_updates]
    fragmented_prompts: Annotated[dict, merge_dict_updates]

    # For lists, we concatenate them using the `add` operator.
    turn_messages: Annotated[list, operator.add]


def agent_node_fn(state: AgentState, agent_name: str) -> dict:
    """
    The core function that executes for each agent node in the graph.
    This now includes an attention fragmentation stage.
    """
    print(f"--- STAGE 1: FRAGMENTING ATTENTION for {agent_name} ---")
    llm = state['agent_llms'][agent_name]
    full_system_prompt = state['agent_prompts'][agent_name]
    user_action = state['user_action']
    
    from langchain_core.output_parsers import StrOutputParser
    fragmentation_chain = FRAGMENTATION_PROMPT | llm | StrOutputParser()
    
    sub_system_prompt_str = fragmentation_chain.invoke({
        "system_prompt": full_system_prompt,
        "user_action": user_action,
        "this_persona_memory": "\n".join(state['agent_memories'][agent_name])
    })
    sub_system_prompt = strip_think_tags(sub_system_prompt_str)
    print(f"Fragmented prompt for {agent_name}: {sub_system_prompt}")
    
    print(f"--- STAGE 2: EXECUTING AGENT: {agent_name} (with fragmented prompt) ---")
    memory = "\n".join(state['agent_memories'][agent_name])
    
    formatted_prompt = sub_system_prompt.replace("{{action}}", user_action)
    formatted_prompt = formatted_prompt.replace("{{this_persona_memory}}", memory)
    
    try:
        raw_response = llm.invoke(formatted_prompt)
        response_content = raw_response.content if not state.get('is_local', True) and hasattr(raw_response, 'content') else raw_response
        response_json = extract_json_from_llm_response(strip_think_tags(response_content))
        if not isinstance(response_json, dict):
            raise json.JSONDecodeError("Extracted content is not a JSON object", response_content, 0)

    except Exception as e:
        print(f"Error processing LLM response for {agent_name}: {e}. Defaulting response.")
        response_json = {"public_reaction": "I am unable to process this right now.", "private_message": None}

    public_reaction = response_json.get("public_reaction", "")
    private_message = response_json.get("private_message")
    
    # Each node now returns its own small piece of the final state
    final_reaction_update = {agent_name: public_reaction}
    
    turn_message_update = []
    if private_message and isinstance(private_message, dict) and "to" in private_message and "content" in private_message:
        turn_message_update.append({
            "from": agent_name,
            "to": private_message["to"],
            "content": private_message["content"]
        })
    
    current_memory = state['agent_memories'].get(agent_name, [])
    memory_log = f"[Turn] Reacted publicly: '{public_reaction}'."
    if private_message and isinstance(private_message, dict) and private_message.get('to'):
        memory_log += f" || Messaged {private_message['to']}: '{private_message.get('content', '')}'."
    
    agent_memory_update = {agent_name: current_memory + [memory_log]}
    fragmented_prompt_update = {agent_name: sub_system_prompt}
    
    return {
        "final_reactions": final_reaction_update,
        "turn_messages": turn_message_update,
        "agent_memories": agent_memory_update,
        "fragmented_prompts": fragmented_prompt_update
    }

def create_agent_graph(agent_configs: Dict[str, Dict]):
    """
    Creates and compiles the LangGraph instance for the agent simulation.
    """
    workflow = StateGraph(AgentState)
    agent_names = list(agent_configs.keys())
    
    if not agent_names:
        return workflow.compile()

    for name in agent_names:
        node_fn = functools.partial(agent_node_fn, agent_name=name)
        workflow.add_node(name, node_fn)

    for name in agent_names:
        workflow.add_edge(START, name)
    
    for name in agent_names:
        workflow.add_edge(name, END)
        
    print(f"Graph created with nodes: {', '.join(agent_names)}")
    return workflow.compile()