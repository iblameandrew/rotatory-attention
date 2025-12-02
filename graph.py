import functools
import json
import time
from typing import TypedDict, Dict, List, Annotated
import operator
from langgraph.graph import StateGraph, START, END
from utils import strip_think_tags, extract_json_from_llm_response
from chains import FRAGMENTATION_PROMPT

# --- START OF CORRECTION ---

def _prepare_prompt_for_fragmentation(full_prompt: str) -> str:
    """
    Extracts only the core data sections of a persona's prompt (attributes, goals, etc.)
    for analysis. This prevents the fragmentation LLM from being confused by the
    imperative instructions (like "You are X" or "Your response must be JSON").
    """
    try:
        # Find the start of the data we want to keep
        start_marker = "### Personality Profile"
        if start_marker not in full_prompt:
            raise IndexError("Start marker not found")
        
        # Find the end of the data we want to keep
        end_marker = "### Your Response"
        if end_marker not in full_prompt:
            raise IndexError("End marker not found")

        # Extract the text between the markers
        start_index = full_prompt.find(start_marker)
        end_index = full_prompt.find(end_marker)

        suffix_section = full_prompt[end_index:]
        prefix_section = full_prompt[:start_index]
        
        main_body = full_prompt[start_index:end_index]
        
        # Return a clean block of text prefixed with a non-imperative header for clarity
        return f"### Agent Profile Data for Analysis\n{main_body.strip()}", suffix_section, prefix_section

    except IndexError as e:
        print(f"Warning: Could not parse prompt for sanitization due to missing marker: {e}. "
              "Using the full prompt for fragmentation, which may be less accurate.")
        # Fallback to returning the whole prompt if markers are missing
        return full_prompt

# --- END OF CORRECTION ---

# This function will be used to merge updates to dictionaries from parallel agent runs.
def merge_dict_updates(x: dict, y: dict) -> dict:
    return {**x, **y}

class AgentState(TypedDict):
    """
    Represents the state of our agent simulation graph.
    """
    agent_prompts: Dict[str, str]
    agent_llms: Dict[str, any]
    user_action: str
    provider: str
    target_agents: List[str]

    final_reactions: Annotated[dict, merge_dict_updates]
    agent_memories: Annotated[dict, merge_dict_updates]
    fragmented_prompts: Annotated[dict, merge_dict_updates]
    turn_messages: Annotated[list, operator.add]


def agent_node_fn(state: AgentState, agent_name: str, max_retries=3) -> dict:
    """
    The core function that executes for each agent node in the graph.
    """
    print(f"--- STAGE 1: FRAGMENTING ATTENTION for {agent_name} ---")
    llm = state['agent_llms'][agent_name]
    full_system_prompt = state['agent_prompts'][agent_name]
    user_action = state['user_action']

    
    print(f"--- STAGE 2: EXECUTING AGENT: {agent_name} (with {'fragmented' if full_system_prompt else 'full'} prompt) ---")
    memory = "\n".join(state['agent_memories'][agent_name])
    
    formatted_prompt = full_system_prompt.replace("{{action}}", user_action)
    formatted_prompt = formatted_prompt.replace("{{this_persona_memory}}", memory)
    
    response_json = None
    for attempt in range(max_retries):
        try:
            raw_response = llm.invoke(formatted_prompt)
            response_content = raw_response.content if state.get('provider') != 'local' and hasattr(raw_response, 'content') else raw_response
            parsed_json = extract_json_from_llm_response(strip_think_tags(response_content))
            
            if not isinstance(parsed_json, dict) or not parsed_json:
                raise ValueError("Extracted content is not a valid, non-empty JSON object.")
            
            response_json = parsed_json
            break 
        except Exception as e:
            print(f"[{agent_name} Execution] Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying...")
            if attempt < max_retries - 1:
                time.sleep(1.5 ** attempt)

    if response_json is None:
        print(f"Error: All retries failed for agent {agent_name}. Defaulting response.")
        response_json = {"public_reaction": "I am unable to process this right now.", "private_message": None}

    print(f"Response from agent {agent_name} received.")
    print(f"Answer: {response_json}")
    public_reaction = response_json.get("public_reaction", "")
    private_message = response_json.get("private_message")
    
    final_reaction_update = {agent_name: public_reaction}
    
    turn_message_update = []
    if private_message and isinstance(private_message, dict) and "to" in private_message and "content" in private_message:
        turn_message_update.append({
            "from": agent_name,
            "to": private_message["to"],
            "content": private_message["content"]
        })
    
    current_memory = state['agent_memories'].get(agent_name, [])
    user_action_observed = state['user_action']
    memory_log = f"[Turn] Observed: '{user_action_observed}'. || My reaction: Reacted publicly: '{public_reaction}'."
    if private_message and isinstance(private_message, dict) and private_message.get('to'):
        memory_log += f" || Messaged {private_message['to']}: '{private_message.get('content', '')}'."
    
    agent_memory_update = {agent_name: current_memory + [memory_log]}
    fragmented_prompt_update = {agent_name: full_system_prompt}
    
    return {
        "final_reactions": final_reaction_update,
        "turn_messages": turn_message_update,
        "agent_memories": agent_memory_update,
        "fragmented_prompts": fragmented_prompt_update
    }

def route_action(state: AgentState) -> List[str]:
    """
    This function is now used directly in the conditional edge logic.
    It inspects the state to determine which agent(s) should act.
    """
    targets = state.get('target_agents')
    
    if targets:
        print(f"--- ROUTING to specific agents: {', '.join(targets)} ---")
        return targets
    
    all_agents = list(state['agent_prompts'].keys())
    print(f"--- ROUTING to all agents (broadcast) ---")
    return all_agents


def create_agent_graph(agent_configs: Dict[str, Dict]):
    """
    Creates and compiles the LangGraph instance for the agent simulation.
    Includes a router to direct actions to specific or all agents.
    """
    workflow = StateGraph(AgentState)
    agent_names = list(agent_configs.keys())
    
    if not agent_names:
        return workflow.compile()

    # Add a node for each agent
    for name in agent_names:
        node_fn = functools.partial(agent_node_fn, agent_name=name)
        workflow.add_node(name, node_fn)
        # After each agent runs, it ends the workflow for that branch
        workflow.add_edge(name, END)

    workflow.add_conditional_edges(
        START,
        route_action,
        {name: name for name in agent_names}
    )
        
    print(f"Graph created with nodes: {', '.join(agent_names)} and a conditional entrypoint.")
    return workflow.compile()