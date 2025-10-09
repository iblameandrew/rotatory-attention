import os
import datetime
import json
import pytz
import concurrent.futures
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_ollama.llms import OllamaLLM
#import env variables


from utils import (
    TokenBudgetManager,
    generate_birth_chart_markdown,
    trim_astrological_report,
    strip_think_tags,
    extract_json_from_llm_response
)
from chains import (
    get_chain,
    SITUATION_FRAMING_PROMPT,
    SEASONAL_THEME_PROMPT,
    USER_CARD_PROMPT,
    AGENT_SPANNER_PROMPT,
    MEMORY_ARCHITECT_PROMPT,
    SOCIAL_VISOR_PROMPT,
    SEASONAL_FUNNEL_PROMPT,
    CONMUTER_PROMPT,
    STRATEGIST_PROMPT,
    COUNCIL_PROMPT,
    RECOMMENDER_PROMPT,
    INTERROGATOR_PROMPT,
    RECOMMENDATION_USER_PROFILE_PROMPT,
)
from graph import create_agent_graph

from dotenv import load_dotenv
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

class NOA:
    """
    Manages a persistent network of cognitive agents to simulate social causality.
    The network is created once and can be queried multiple times with new actions.
    """
    def __init__(self, user_context: dict,
                 n_people: int, token_budget: int,
                 local: bool, model: str, seasonal_datetime: datetime.datetime = None,
                 log_callback=None, progress_callback=None): # ADDED progress_callback

        self.user_context = user_context
        self.n_people = n_people
        self.local = local
        self.seasonal_datetime = seasonal_datetime
        self.log_callback = log_callback
        self.progress_callback = progress_callback # ADDED

        self.token_manager = TokenBudgetManager(initial_budget=token_budget)
        if self.local:
            self.llm = OllamaLLM(model=model, callbacks=[self.token_manager], format="json")
            self.str_llm = OllamaLLM(model=model, callbacks=[self.token_manager])
        else:
            self.llm = ChatGoogleGenerativeAI(model=model, callbacks=[self.token_manager], response_mime_type="application/json", google_api_key=gemini_api_key)
            self.str_llm = ChatGoogleGenerativeAI(model=model, callbacks=[self.token_manager],google_api_key=gemini_api_key)

        self.graph = None
        self.agent_configs = {}
        self.agent_memories = {}
        self.agent_personas = []
        self._log("🚀 NOA instance created. Starting network creation...", level='info')
        self._create_network()

    def _log(self, message: str, level: str = 'info'):
        """Helper method to send logs to the callback if it exists."""
        print(message)
        if self.log_callback:
            self.log_callback(message, level)

    def _get_response_content(self, raw_response):
        """Helper to get content from LLM response, handling local vs remote differences."""
        if not self.local and hasattr(raw_response, 'content'):
            return raw_response.content
        return raw_response

    def _create_network(self):
        """Orchestrates the step-by-step creation of the agent network."""
        try:
            # Step 1: Situation Framing
            self._log("Step 1: Framing the situation...", level='step')
            chain = get_chain(self.llm, SITUATION_FRAMING_PROMPT, 'json')
            raw_response = chain.invoke({"user_context": self.user_context})
            self.situation_archetype = strip_think_tags(self._get_response_content(raw_response))
            self._log(f"Core Theme Identified: {self.situation_archetype.get('core_theme')}", level='detail')

            # Step 2: User Birth Chart
            self._log("Step 2: Generating user birth chart...", level='step')
            user_bday = datetime.datetime.strptime(self.user_context['birth_date'], '%Y-%m-%d')
            chart_md = generate_birth_chart_markdown(self.user_context['name'], user_bday, 12, 0, "New York", "USA")
            self.user_birth_chart = trim_astrological_report(chart_md)

            # Step 3: Seasonal Theme
            self._log("Step 3: Determining seasonal theme...", level='step')
            chain = get_chain(self.str_llm, SEASONAL_THEME_PROMPT)
            now = self.seasonal_datetime if self.seasonal_datetime else datetime.datetime.now(pytz.timezone("America/New_York"))
            current_chart = trim_astrological_report(generate_birth_chart_markdown("CurrentSeason", now, now.hour, now.minute, "New York", "USA"))
            raw_response = chain.invoke({"birth_chart": current_chart})
            self.season = strip_think_tags(self._get_response_content(raw_response))
            self._log("Seasonal theme determined and will be used to flavor user actions.", level='detail')

            # Step 4: User Card
            self._log("Step 4: Creating user profile card...", level='step')
            chain = get_chain(self.llm, USER_CARD_PROMPT, 'json')
            raw_response = chain.invoke({"user_context": self.user_context, "birth_chart": self.user_birth_chart})
            self.user_profile = strip_think_tags(self._get_response_content(raw_response))
            self._log(f"User Profile for {self.user_context['name']} created. Role: {self.user_profile.get('social_role')}", level='detail')

            # Step 5: Agent Spanner
            self._log("Step 5: Spanning audience agent personas (base)...", level='step')
            chain = get_chain(self.llm, AGENT_SPANNER_PROMPT, 'json')
            raw_response = chain.invoke({"n_people": self.n_people, "user_context": self.situation_archetype})
            self.agent_personas = strip_think_tags(self._get_response_content(raw_response)).get('personas', [])
            for p in self.agent_personas:
                self._log(f"Generated Persona: {p.get('name')}", level='detail')

            # Parallel Step: Memory Architect & Social Visor (User Card)
            self._log("Step 5.5 & 6: Architecting memories and generating user visions in parallel...", level='step')
            memory_chain = get_chain(self.str_llm, MEMORY_ARCHITECT_PROMPT)
            visor_chain = get_chain(self.llm, SOCIAL_VISOR_PROMPT, 'json')

            memory_tasks = [{"name": p.get('name'), "personality_attributes": json.dumps(p.get('personality_attributes')), "skills": json.dumps(p.get('skills')), "goals": json.dumps(p.get('goals')), "fears": json.dumps(p.get('fears')), "situation_context": json.dumps(self.situation_archetype)} for p in self.agent_personas]
            visor_tasks = [{"profile_a": p['personality_attributes'], "profile_b": self.user_profile['archetypal_profile']} for p in self.agent_personas]
            occluded_user_cards = {}
            
            # Refactored for progress tracking
            futures = {}
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for i, task in enumerate(memory_tasks):
                    futures[executor.submit(memory_chain.invoke, task)] = ("memory", i)
                for i, task in enumerate(visor_tasks):
                    futures[executor.submit(visor_chain.invoke, task)] = ("visor", i)

                total_tasks = len(futures)
                completed_tasks = 0
                
                memory_results = [None] * len(memory_tasks)
                visor_results = [None] * len(visor_tasks)

                for future in concurrent.futures.as_completed(futures):
                    task_type, index = futures[future]
                    try:
                        raw_result = future.result()
                        result = self._get_response_content(raw_result)
                        if task_type == "memory":
                            memory_results[index] = result
                        else:
                            visor_results[index] = result
                    except Exception as exc:
                        self._log(f"A task generated an exception: {exc}", level='error')
                    
                    completed_tasks += 1
                    if self.progress_callback:
                        progress = completed_tasks / total_tasks
                        self.progress_callback(progress, f"Architecting memories & visions ({completed_tasks}/{total_tasks})...")

            monologues = [strip_think_tags(result) if result else "" for result in memory_results]
            for i, persona in enumerate(self.agent_personas):
                persona['initial_memory'] = monologues[i]
                self.agent_memories[persona['name']] = [persona['initial_memory']]
                self._log(f"Initial Memory for {persona['name']}: \"{monologues[i][:100]}...\"", level='detail')

            visions = [strip_think_tags(result) if result else {'vision_statement': 'Error generating vision.'} for result in visor_results]
            for i, persona in enumerate(self.agent_personas):
                vision = visions[i]['vision_statement']
                occluded_user_cards[persona['name']] = vision
                self._log(f"{persona['name']}'s vision of {self.user_context['name']}: '{vision}'", level='detail')


            # Step 7: Conmuter (Communication Channels)
            self._log("Step 7: Detecting communication channels...", level='step')
            conmuter_chain = get_chain(self.llm, CONMUTER_PROMPT, 'json')
            raw_response = conmuter_chain.invoke({"agent_personas": self.agent_personas})
            self.channels = strip_think_tags(self._get_response_content(raw_response)).get("channels", [])
            for channel in self.channels:
                members = ", ".join(channel.get("members", []))
                self._log(f"Detected Channel: [{members}] - Reason: {channel.get('basis_for_connection')}", level='detail')

            # Step 8: Social Visor (Mutual Agent Cards)
            self._log("Step 8: Generating mutual social cards for agents...", level='step')
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
                tasks_to_run = [{"profile_a": personas_by_name[t['viewer']]['personality_attributes'], "profile_b": personas_by_name[t['viewed']]['personality_attributes']} for t in mutual_vision_tasks]
                
                # Refactored for progress tracking
                vision_results = []
                total_vision_tasks = len(tasks_to_run)
                for i, task_data in enumerate(tasks_to_run):
                    raw_result = visor_chain.invoke(task_data)
                    vision_results.append(strip_think_tags(self._get_response_content(raw_result)))
                    if self.progress_callback:
                        progress = (i + 1) / total_vision_tasks
                        self.progress_callback(progress, f"Generating mutual social visions ({i+1}/{total_vision_tasks})...")

                for i, task in enumerate(mutual_vision_tasks):
                    viewer, viewed = task['viewer'], task['viewed']
                    vision = vision_results[i]['vision_statement']
                    agent_social_cards[viewer].append(f"\t{viewed}\n\t\t{vision.strip()}")
                    self._log(f"Mutual Vision: {viewer} -> {viewed}: '{vision}'", level='detail')

            # Step 9: Final Assembly and Graph Creation
            self._log("Step 9: Assembling final prompts and creating graph...", level='step')
            for persona in self.agent_personas:
                name = persona['name']
                final_prompt = persona['system_prompt'].replace("{{occluded_user_card}}", occluded_user_cards.get(name, "No specific vision."))
                social_card_text = "\n".join(agent_social_cards.get(name, ["You have no contacts."]))
                final_prompt = final_prompt.replace("{{social_cards}}", social_card_text)
                self.agent_configs[name] = {"prompt": final_prompt, "llm": self.llm}
            self.graph = create_agent_graph(self.agent_configs)
            self._log("✅ Network creation complete.", level='info')

        except Exception as e:
            self._log(f"❌ FATAL ERROR during network creation: {e}", level='error')
            self.graph = None

    def query(self, user_action: str) -> (str, dict):
        """
        Queries the graph with a new user action, accumulating memory.
        Returns a strategic report and judged intention for the current action.
        """
        if not self.graph:
            return "Execution halted due to setup error.", {}

        self._log(f"⚡ Processing new action: '{user_action}'", level='step')
        
        # Step 1 (Query-time): Seasonal Attention Funnel
        self._log("Flavorizing user action with seasonal theme...", level='detail')
        funnel_chain = get_chain(self.llm, SEASONAL_FUNNEL_PROMPT, 'json')
        raw_response = funnel_chain.invoke({"season": self.season, "user_action": user_action})
        attention_result = strip_think_tags(self._get_response_content(raw_response))
        user_action_with_attention = attention_result['user_action_with_attention']
        self._log(f"Themed Action: {user_action_with_attention}", level='detail')

        # Step 2 (Query-time): Query the agent graph
        self._log("Querying the agent graph...", level='detail')
        initial_state = {
            "agent_prompts": {name: config['prompt'] for name, config in self.agent_configs.items()},
            "agent_llms": {name: config['llm'] for name, config in self.agent_configs.items()},
            "agent_memories": self.agent_memories, # Use current, accumulated memories
            "user_action": user_action_with_attention,
            "turn_messages": [],
            "final_reactions": {},
            "is_local": self.local # Pass locality to the graph state
        }
        final_state = self.graph.invoke(initial_state) # strip_think_tags is not needed here
        
        # Update memories for the next query
        self.agent_memories = final_state['agent_memories']
        self._log("Agent memories have been updated.", level='detail')

        # Step 3 (Query-time): Generate reports
        self._log("Generating strategic report...", level='detail')
        strat_chain = get_chain(self.str_llm, STRATEGIST_PROMPT)
        raw_report = strat_chain.invoke({
            "user_profile": json.dumps(self.user_profile),
            "user_action_with_attention": user_action_with_attention,
            "agent_reactions": json.dumps(final_state['final_reactions'])
        })
        report = strip_think_tags(self._get_response_content(raw_report))

        self._log("Judging user intention...", level='detail')
        council_chain = get_chain(self.llm, COUNCIL_PROMPT, 'json')
        raw_intention = council_chain.invoke({"user_action": user_action})
        judged_intention = strip_think_tags(self._get_response_content(raw_intention))

        self._log("Query complete.", level='info')
        return report, judged_intention

    @staticmethod
    def recommend(llm, user_birth_date: str, local: bool) -> list:
        """
        Recommends 10 venues for exploration based on a user's birth chart.
        This is a static method and does not require a full NOA instance.
        """
        print(f"Generating recommendations for birth date: {user_birth_date}...")
        try:
            temp_bday = datetime.datetime.strptime(user_birth_date, '%Y-%m-%d')
            temp_chart = trim_astrological_report(generate_birth_chart_markdown("temp_user", temp_bday, 12, 0, "New York", "USA")) 
            profile_chain = get_chain(llm, RECOMMENDATION_USER_PROFILE_PROMPT, 'json')
            if local == False: 
                profile = profile_chain.invoke({"birth_chart": temp_chart}).content
            else:
                profile = profile_chain.invoke({"birth_chart": temp_chart})
            
            profile = extract_json_from_llm_response(profile)
            rec_chain = get_chain(llm, RECOMMENDER_PROMPT, 'json')

            if local == False: 
                recommendations = rec_chain.invoke({"user_profile": json.dumps(profile)}).content
            else:
                recommendations = rec_chain.invoke({"user_profile": json.dumps(profile)})

            recommendations = extract_json_from_llm_response(recommendations)

            return recommendations

        except Exception as e:

            raise e

    def rollback(self, n: int = 1):
        """Rolls back the last n messages in each agent's memory, preserving the initial memory."""
        self._log(f"Rolling back agent memories by {n} step(s)...", level='info')
        for name, memory_list in self.agent_memories.items():
            if len(memory_list) > 1:
                self.agent_memories[name] = memory_list[:-n] if len(memory_list) > n else [memory_list]
        return "Rollback complete."