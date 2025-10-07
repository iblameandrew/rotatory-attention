# noa/noa_class.py

import datetime
import json
import pytz
import concurrent.futures
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.llms import Ollama

from .utils import (
    TokenBudgetManager,
    generate_birth_chart_markdown,
    trim_astrological_report,
)
from .chains import (
    get_chain,
    SITUATION_FRAMING_PROMPT,
    SEASONAL_THEME_PROMPT,
    USER_CARD_PROMPT,
    AGENT_SPANNER_PROMPT,
    SOCIAL_VISOR_PROMPT,
    SEASONAL_FUNNEL_PROMPT,
    CONMUTER_PROMPT,
    STRATEGIST_PROMPT,
    COUNCIL_PROMPT,
    RECOMMENDER_PROMPT
)
from .graph import create_agent_graph, AgentState

class NOA:
    """
    Manages a network of cognitive agents to simulate social causality.
    """
    def __init__(self, user_action: str, agents: list, user_context: dict,
                 new_agent_threshold: float, n_people: int, token_budget: int,
                 local: bool, model: str):

        self.user_action = user_action
        self.agents = agents
        self.user_context = user_context
        self.n_people = n_people
        self.local = local
        
        self.token_manager = TokenBudgetManager(initial_budget=token_budget)
        if self.local:
            self.llm = Ollama(model=model, callbacks=[self.token_manager], format="json")
            self.str_llm = Ollama(model=model, callbacks=[self.token_manager])
        else:
            self.llm = ChatGoogleGenerativeAI(model=model, callbacks=[self.token_manager], response_mime_type="application/json")
            self.str_llm = ChatGoogleGenerativeAI(model=model, callbacks=[self.token_manager])
            
        self.graph = None
        self.agent_configs = {}
        self.agent_memories = {}
        self.agent_personas = []
        print("🚀 NOA instance created. Starting network creation...")
        self._create_network()

    def _create_network(self):
        """Orchestrates the step-by-step creation of the agent network."""
        try:
            # Step 1: Situation Framing
            print("Step 1: Framing the situation...")
            chain = get_chain(self.llm, SITUATION_FRAMING_PROMPT, 'json')
            self.situation_archetype = chain.invoke({"user_context": self.user_context})

            # Step 2: User Birth Chart
            print("Step 2: Generating user birth chart...")
            user_bday = datetime.datetime.strptime(self.user_context['birth_date'], '%Y-%m-%d')
            chart_md = generate_birth_chart_markdown(self.user_context['name'], user_bday, 12, 0, "New York", "USA")
            self.user_birth_chart = trim_astrological_report(chart_md)

            # Step 3: Seasonal Theme
            print("Step 3: Determining seasonal theme...")
            chain = get_chain(self.str_llm, SEASONAL_THEME_PROMPT)
            now = datetime.datetime.now(pytz.timezone("America/New_York"))
            current_chart = trim_astrological_report(generate_birth_chart_markdown("CurrentSeason", now, now.hour, now.minute, "New York", "USA"))
            self.season = chain.invoke({"birth_chart": current_chart})

            # Step 4: User Card
            print("Step 4: Creating user profile card...")
            chain = get_chain(self.llm, USER_CARD_PROMPT, 'json')
            self.user_profile = chain.invoke({**self.user_context, "birth_chart": self.user_birth_chart})

            # Step 5: Agent Spanner - Generates full persona objects
            print("Step 5: Spanning audience agent personas...")
            chain = get_chain(self.llm, AGENT_SPANNER_PROMPT, 'json')
            self.agent_personas = chain.invoke({"n_people": self.n_people, "user_context": self.user_context}).get('personas', [])
            
            for persona in self.agent_personas:
                self.agent_memories[persona['name']] = [persona['initial_memory']]

            # Step 6: Social Visor (User Card) - Agents perceive the user
            print("Step 6: Generating agent visions of the user...")
            visor_chain = get_chain(self.llm, SOCIAL_VISOR_PROMPT, 'json')
            occluded_user_cards = {}
            tasks = [{"profile_a": p['personality_attributes'], "profile_b": self.user_profile['archetypal_profile']} for p in self.agent_personas]
            
            if self.local and len(tasks) > 1:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    results = list(executor.map(visor_chain.invoke, tasks))
            else:
                results = [visor_chain.invoke(task) for task in tasks]

            for i, persona in enumerate(self.agent_personas):
                occluded_user_cards[persona['name']] = results[i]['vision_statement']

            # Step 7: Seasonal Attention Funnel
            print("Step 7: Flavorizing user action with seasonal theme...")
            funnel_chain = get_chain(self.llm, SEASONAL_FUNNEL_PROMPT, 'json')
            attention_result = funnel_chain.invoke({"season": self.season, "user_action": self.user_action})
            self.user_action_with_attention = attention_result['user_action_with_attention']

            # Step 8: Conmuter (Communication Channels) - Uses full persona data
            print("Step 8: Detecting communication channels...")
            conmuter_chain = get_chain(self.llm, CONMUTER_PROMPT, 'json')
            self.channels = conmuter_chain.invoke({"agent_personas": self.agent_personas}).get("channels", [])
            
            # Step 9: Social Visor (Mutual Agent Cards) - Agents perceive each other
            print("Step 9: Generating mutual social cards for agents...")
            agent_social_cards = {p['name']: [] for p in self.agent_personas}
            mutual_vision_tasks = []
            personas_by_name = {p['name']: p for p in self.agent_personas}

            for group in self.channels:
                members = group.get("members", [])
                for i in range(len(members)):
                    for j in range(i + 1, len(members)):
                        name_a, name_b = members[i], members[j]
                        if name_a in personas_by_name and name_b in personas_by_name:
                            mutual_vision_tasks.append({"viewer": name_a, "viewed": name_b})
                            mutual_vision_tasks.append({"viewer": name_b, "viewed": name_a})

            if mutual_vision_tasks:
                tasks_to_run = [{"profile_a": personas_by_name[t['viewer']]['personality_attributes'], 
                                 "profile_b": personas_by_name[t['viewed']]['personality_attributes']} 
                                for t in mutual_vision_tasks]

                if self.local and len(tasks_to_run) > 1:
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        vision_results = list(executor.map(visor_chain.invoke, tasks_to_run))
                else:
                    vision_results = [visor_chain.invoke(task) for task in tasks_to_run]
                
                for i, task in enumerate(mutual_vision_tasks):
                    viewer, viewed = task['viewer'], task['viewed']
                    vision = vision_results[i]['vision_statement']
                    agent_social_cards[viewer].append(f"\t{viewed}\n\t\t{vision.strip()}")

            # Step 10: Final Assembly and Graph Creation
            print("Step 10: Assembling final prompts and creating graph...")
            for persona in self.agent_personas:
                name = persona['name']
                final_prompt = persona['system_prompt'].replace("{{occluded_user_card}}", occluded_user_cards.get(name, "No specific vision."))
                social_card_text = "\n".join(agent_social_cards.get(name, ["You have no contacts."]))
                final_prompt = final_prompt.replace("{{social_cards}}", social_card_text)
                self.agent_configs[name] = {"prompt": final_prompt, "llm": self.llm}

            self.graph = create_agent_graph(self.agent_configs)
            print("✅ Network creation complete.")

        except Exception as e:
            print(f"❌ FATAL ERROR during network creation: {e}")
            self.graph = None

    def query(self) -> (str, dict):
        """Queries the graph and returns a strategic report and judged intention."""
        if not self.graph:
            return "Execution halted due to setup error.", {}
        
        print("\n⚡ Querying the agent graph...")
        initial_state = {
            "agent_prompts": {name: config['prompt'] for name, config in self.agent_configs.items()},
            "agent_llms": {name: config['llm'] for name, config in self.agent_configs.items()},
            "agent_memories": self.agent_memories,
            "user_action": self.user_action_with_attention,
            "turn_messages": [], "final_reactions": {}
        }
        # The graph itself runs agents in parallel
        final_state = self.graph.invoke(initial_state)
        self.agent_memories = final_state['agent_memories']

        print("Generating strategic report...")
        strat_chain = get_chain(self.str_llm, STRATEGIST_PROMPT)
        report = strat_chain.invoke({
            "user_profile": json.dumps(self.user_profile),
            "user_action_with_attention": self.user_action_with_attention,
            "agent_reactions": json.dumps(final_state['final_reactions'])
        })

        print("Judging user intention...")
        council_chain = get_chain(self.llm, COUNCIL_PROMPT, 'json')
        judged_intention = council_chain.invoke({"user_action": self.user_action})

        print("Query complete.")
        return report, judged_intention

    def recommend(self, user_birth_date: str, user_context: str) -> list:
        """Recommends 10 venues for exploration based on a user's birth chart."""
        print(f"Generating recommendations for birth date: {user_birth_date}...")
        temp_bday = datetime.datetime.strptime(user_birth_date, '%Y-%m-%d')
        temp_chart = trim_astrological_report(generate_birth_chart_markdown("temp_user", temp_bday, 12, 0, "New York", "USA"))
        
        ucard_chain = get_chain(self.llm, USER_CARD_PROMPT, 'json')
        profile = ucard_chain.invoke(user_context)
        
        rec_chain = get_chain(self.llm, RECOMMENDER_PROMPT, 'json')
        return rec_chain.invoke({"user_profile": json.dumps(profile)})

    def rollback(self, n: int = 1):
        """Rolls back the last n messages in each agent's memory, preserving the initial memory."""
        print(f"Rolling back agent memories by {n} step(s)...")
        for name, memory_list in self.agent_memories.items():
            if len(memory_list) > 1: # Always keep the initial memory
                self.agent_memories[name] = memory_list[:-n] if len(memory_list) > n else [memory_list[0]]
        return "Rollback complete."