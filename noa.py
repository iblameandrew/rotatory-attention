import os
import datetime
import json
import pytz
import concurrent.futures
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama.llms import OllamaLLM

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
    PHILOSOPHICAL_REFRAMER_PROMPT,
    COUNCIL_PROMPT,
    RECOMMENDER_PROMPT,
    INTERROGATOR_PROMPT,
    RECOMMENDATION_USER_PROFILE_PROMPT,
    PERSONA_SYSTEM_PROMPT, # Import the new prompt template
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
                 log_callback=None, progress_callback=None, token_manager=None):

        self.user_context = user_context
        self.n_people = n_people
        self.local = local
        self.seasonal_datetime = seasonal_datetime
        self.log_callback = log_callback
        self.progress_callback = progress_callback

        if token_manager:
            self.token_manager = token_manager
        else:
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
        self.last_fragmented_prompts = {}
        self._log("🚀 NOA instance created. Starting network creation...", level='info')
        self._create_network()

    def _log(self, message: str, level: str = 'info'):
        """Helper method to send logs to the callback if it exists."""
        print(message)
        if self.log_callback:
            self.log_callback(message, level)

    def _get_response_content(self, raw_response):
        """
        Helper to consistently get content from LLM response,
        handling local (string) vs remote (AIMessage object) differences.
        """
        if not self.local and hasattr(raw_response, 'content'):
            return raw_response.content
        return raw_response

    def _create_network(self):
        """Orchestrates the step-by-step creation of the agent network."""
        try:
            # Step 1: Situation Framing
            self._log("Step 1: Framing the situation...", level='step')
            if self.progress_callback: self.progress_callback(0.05, "Framing situation...")
            chain = get_chain(self.llm, SITUATION_FRAMING_PROMPT, 'json')
            self.situation_archetype = chain.invoke({"user_context": self.user_context})
            self.situation_archetype = extract_json_from_llm_response(self._get_response_content(self.situation_archetype))
            if not self.situation_archetype or not isinstance(self.situation_archetype, dict):
                 raise ValueError("Failed to generate Situation Archetype. LLM returned invalid data.")
            self._log(f"Core Theme Identified: {self.situation_archetype.get('core_theme')}", level='detail')

            # Step 2: User Birth Chart
            self._log("Step 2: Generating user birth chart...", level='step')
            if self.progress_callback: self.progress_callback(0.1, "Generating user chart...")
            user_bday = datetime.datetime.strptime(self.user_context['birth_date'], '%Y-%m-%d')
            chart_md = generate_birth_chart_markdown(self.user_context['name'], user_bday, 12, 0, "New York", "USA")
            self.user_birth_chart = trim_astrological_report(chart_md)

            # Step 3: Seasonal Theme
            self._log("Step 3: Determining seasonal theme...", level='step')
            if self.progress_callback: self.progress_callback(0.15, "Determining seasonal theme...")
            chain = get_chain(self.str_llm, SEASONAL_THEME_PROMPT)
            now = self.seasonal_datetime if self.seasonal_datetime else datetime.datetime.now(pytz.timezone("America/New_York"))
            current_chart = trim_astrological_report(generate_birth_chart_markdown("CurrentSeason", now, now.hour, now.minute, "New York", "USA"))
            raw_response = chain.invoke({"birth_chart": current_chart})
            self.season = raw_response
            self._log("Seasonal theme determined and will be used to flavor user actions.", level='detail')

            # Step 4: User Card
            self._log("Step 4: Creating user profile card...", level='step')
            if self.progress_callback: self.progress_callback(0.20, "Creating user profile...")
            chain = get_chain(self.llm, USER_CARD_PROMPT, 'json')
            self.user_profile = chain.invoke({"user_context": self.user_context, "birth_chart": self.user_birth_chart})
            self.user_profile = extract_json_from_llm_response(self._get_response_content(self.user_profile))
            if not self.user_profile or not isinstance(self.user_profile, dict):
                raise ValueError("Failed to generate User Profile Card. LLM returned invalid data.")
            self._log(f"User Profile for {self.user_context['name']} created. Role: {self.user_profile.get('social_role')}", level='detail')

            # Step 5: Agent Spanner
            self._log("Step 5: Spanning audience agent personas (base)...", level='step')
            if self.progress_callback: self.progress_callback(0.30, "Generating agent personas...")
            chain = get_chain(self.llm, AGENT_SPANNER_PROMPT, 'json')
            content = chain.invoke({"n_people": self.n_people, "user_context": self.situation_archetype})
            content = extract_json_from_llm_response(self._get_response_content(content))
            if not content or 'personas' not in content:
                raise ValueError("Agent Spanner returned invalid or empty data.")
            self.agent_personas = content.get('personas', [])
            for p in self.agent_personas:
                self._log(f"Generated Persona: {p.get('name')}", level='detail')

            # Parallel Step: Memory Architect & Social Visor (User Card)
            self._log("Step 5.5 & 6: Architecting memories and generating user visions in parallel...", level='step')
            memory_chain = get_chain(self.str_llm, MEMORY_ARCHITECT_PROMPT) # Returns string
            visor_chain = get_chain(self.llm, SOCIAL_VISOR_PROMPT, 'json') # Returns dict

            memory_tasks = [{"name": p.get('name'), "personality_attributes": json.dumps(p.get('personality_attributes')), "skills": json.dumps(p.get('skills')), "goals": json.dumps(p.get('goals')), "fears": json.dumps(p.get('fears')), "situation_context": json.dumps(self.situation_archetype)} for p in self.agent_personas]
            visor_tasks = [{"profile_a": p['personality_attributes'], "profile_b": self.user_profile['archetypal_profile']} for p in self.agent_personas]
            occluded_user_cards = {}
            
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
                        result = future.result()
                        if task_type == "memory":
                            memory_results[index] = result # Result is a string
                        else:
                            result = extract_json_from_llm_response(self._get_response_content(result))
                            visor_results[index] = result # Result is a dict
                    except Exception as exc:
                        self._log(f"A parallel task generated an exception: {exc}", level='error')
                    
                    completed_tasks += 1
                    if self.progress_callback:
                        progress = 0.45 + (completed_tasks / total_tasks) * 0.25
                        self.progress_callback(progress, f"Architecting memories & visions ({completed_tasks}/{total_tasks})...")

            monologues = [self._get_response_content(result) if result else "" for result in memory_results]
            for i, persona in enumerate(self.agent_personas):
                persona['initial_memory'] = monologues[i]
                self.agent_memories[persona['name']] = [persona['initial_memory']]
                self._log(f"Initial Memory for {persona['name']}: \"{monologues[i][:100]}...\"", level='detail')

            # CORRECTED: Process visor results which are now dictionaries
            for i, persona in enumerate(self.agent_personas):
                vision_obj = visor_results[i]
                vision_statement = "No vision statement was generated."
                if isinstance(vision_obj, dict) and 'vision_statement' in vision_obj:
                    vision_statement = vision_obj['vision_statement']
                occluded_user_cards[persona['name']] = vision_statement
                self._log(f"{persona['name']}'s vision of {self.user_context['name']}: '{vision_statement}'", level='detail')

            # Step 7: Conmuter (Communication Channels)
            self._log("Step 7: Detecting communication channels...", level='step')
            if self.progress_callback: self.progress_callback(0.75, "Detecting communication channels...")
            conmuter_chain = get_chain(self.llm, CONMUTER_PROMPT, 'json')
            content = conmuter_chain.invoke({"agent_personas": self.agent_personas})
            content = extract_json_from_llm_response(self._get_response_content(content))
            if not content or 'channels' not in content:
                raise ValueError("Conmuter returned invalid or empty data.")
            self.channels = content.get("channels", [])
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
                
                vision_results = []
                total_vision_tasks = len(tasks_to_run)
                for i, task_data in enumerate(tasks_to_run):
                    result_obj = visor_chain.invoke(task_data)
                    vision_results.append(result_obj)
                    if self.progress_callback:
                        progress = 0.8 + (i + 1) / total_vision_tasks * 0.15
                        self.progress_callback(progress, f"Generating mutual social visions ({i+1}/{total_vision_tasks})...")

                for i, task in enumerate(mutual_vision_tasks):
                    viewer, viewed = task['viewer'], task['viewed']
                    vision_obj = vision_results[i]
                    vision_obj = extract_json_from_llm_response(self._get_response_content(vision_obj))
                    vision = "Error generating vision."
                    if isinstance(vision_obj, dict) and 'vision_statement' in vision_obj:
                        vision = vision_obj['vision_statement']
                    agent_social_cards[viewer].append(f"\t{viewed}\n\t\t{vision.strip()}")
                    self._log(f"Mutual Vision: {viewer} -> {viewed}: '{vision}'", level='detail')

            # CORRECTED AND REFACTORED: Step 9: Assembling final prompts and creating graph
            self._log("Step 9: Assembling final prompts and creating graph...", level='step')
            if self.progress_callback: self.progress_callback(0.98, "Assembling graph...")

            def format_list_for_prompt(items: list) -> str:
                if not items or not isinstance(items, list): return "- None"
                return "\n".join([f"- {item}" for item in items])

            for persona in self.agent_personas:
                name = persona.get('name', 'Unnamed Agent')
                attributes = persona.get('personality_attributes', {})

                prompt_data = {
                    "name": name,
                    "core_identity_purpose": attributes.get("Core Identity & Purpose", "[Not specified]"),
                    "emotional_baseline_needs": attributes.get("Emotional Baseline & Needs", "[Not specified]"),
                    "communication_thought_process": attributes.get("Communication & Thought Process", "[Not specified]"),
                    "values_relationship_style": attributes.get("Values & Relationship Style", "[Not specified]"),
                    "approach_action_conflict": attributes.get("Approach to Action & Conflict", "[Not specified]"),
                    "attitude_growth_risk": attributes.get("Attitude towards Growth & Risk", "[Not specified]"),
                    "sense_responsibility_discipline": attributes.get("Sense of Responsibility & Discipline", "[Not specified]"),
                    "reaction_change_unexpected": attributes.get("Reaction to Change & the Unexpected", "[Not specified]"),
                    "ideals_dreams_blind_spots": attributes.get("Ideals, Dreams, & Blind Spots", "[Not specified]"),
                    "relationship_power_transformation": attributes.get("Relationship with Power & Transformation", "[Not specified]"),
                    "core_wound_empathy": attributes.get("Core Wound & Source of Empathy", "[Not specified]"),
                    "long_term_ambition_legacy": attributes.get("Long-Term Ambition & Legacy", "[Not specified]"),
                    "virtues": format_list_for_prompt(persona.get('virtues', [])),
                    "tensions": format_list_for_prompt(persona.get('tensions', [])),
                    "skills": format_list_for_prompt(persona.get('skills', [])),
                    "fears": format_list_for_prompt(persona.get('fears', [])),
                    "goals": format_list_for_prompt(persona.get('goals', [])),
                }

                partially_filled_prompt = PERSONA_SYSTEM_PROMPT.format(**prompt_data)
                prompt_with_user_card = partially_filled_prompt.replace("{{occluded_user_card}}", occluded_user_cards.get(name, "No specific vision."))
                social_card_text = "\n".join(agent_social_cards.get(name, ["You have no contacts."]))
                final_prompt = prompt_with_user_card.replace("{{social_cards}}", social_card_text)

                self.agent_configs[name] = {
                    "prompt": final_prompt,
                    "llm": self.llm
                }

            self.graph = create_agent_graph(self.agent_configs)

            if self.progress_callback: self.progress_callback(1.0, "Network complete!")
            self._log("✅ Network creation complete.", level='info')

        except Exception as e:
            self._log(f"❌ FATAL ERROR during network creation: {e}", level='error')
            import traceback
            traceback.print_exc()
            self.graph = None
            if self.progress_callback: self.progress_callback(1.0, "Error during creation!")

    def query(self, user_action: str) -> (str, dict, str, dict, dict):
        if not self.graph:
            return "Execution halted due to setup error.", {}, "", {}, {}

        self._log(f"⚡ Processing new action: '{user_action}'", level='step')
        
        # Step 1 (Query-time): Seasonal Attention Funnel
        self._log("Flavorizing user action with seasonal theme...", level='detail')
        funnel_chain = get_chain(self.llm, SEASONAL_FUNNEL_PROMPT, 'json')
        attention_result = funnel_chain.invoke({"season": self.season, "user_action": user_action})
        attention_result = extract_json_from_llm_response(self._get_response_content(attention_result))

        if not attention_result or 'user_action_with_attention' not in attention_result:
            self._log("Warning: Seasonal Funnel failed. Using original user action.", level='warning')
            user_action_with_attention = user_action
        else:
            user_action_with_attention = attention_result['user_action_with_attention']
        self._log(f"Themed Action: {user_action_with_attention}", level='detail')

        # Step 2 (Query-time): Query the agent graph
        self._log("Querying the agent graph...", level='detail')
        initial_state = {
            "agent_prompts": {name: config['prompt'] for name, config in self.agent_configs.items()},
            "agent_llms": {name: config['llm'] for name, config in self.agent_configs.items()},
            "str_llm": self.str_llm,
            "agent_memories": self.agent_memories,
            "user_action": user_action_with_attention,
            "turn_messages": [],
            "final_reactions": {},
            "is_local": self.local,
            "fragmented_prompts": {}
        }
        final_state = self.graph.invoke(initial_state)
        
        self.agent_memories = final_state['agent_memories']
        self.last_fragmented_prompts = final_state.get('fragmented_prompts', {})
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
        judged_intention = council_chain.invoke({"user_action": user_action})
        judged_intention = extract_json_from_llm_response(self._get_response_content(judged_intention))

        self._log("Query complete.", level='info')
        return report, judged_intention, self.last_fragmented_prompts, final_state['final_reactions']

    @staticmethod
    def recommend(llm, user_birth_date: str, local: bool) -> list:
        print(f"Generating recommendations for birth date: {user_birth_date}...")
        try:
            temp_bday = datetime.datetime.strptime(user_birth_date, '%Y-%m-%d')
            temp_chart = trim_astrological_report(generate_birth_chart_markdown("temp_user", temp_bday, 12, 0, "New York", "USA")) 
            
            profile_chain = get_chain(llm, RECOMMENDATION_USER_PROFILE_PROMPT, 'json')
            profile = profile_chain.invoke({"birth_chart": temp_chart})
            if not profile: raise ValueError("Failed to generate recommendation profile.")

            rec_chain = get_chain(llm, RECOMMENDER_PROMPT, 'json')
            recommendations = rec_chain.invoke({"user_profile": json.dumps(profile)})
            if not recommendations: raise ValueError("Failed to generate recommendations.")

            return recommendations

        except Exception as e:
            print(f"Error in recommend method: {e}")
            raise e

    def rollback(self, n: int = 1):
        self._log(f"Rolling back agent memories by {n} step(s)...", level='info')
        for name, memory_list in self.agent_memories.items():
            if len(memory_list) > 1:
                self.agent_memories[name] = memory_list[:-n] if len(memory_list) > n else [memory_list[0]]
        return "Rollback complete."