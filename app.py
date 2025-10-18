import streamlit as st
import datetime
import json
import time
import re
from dotenv import load_dotenv
from noa import NOA
from chains import get_chain, INTERROGATOR_PROMPT
from utils import strip_think_tags, TokenBudgetManager
from langchain_ollama.llms import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
import os

load_dotenv()

# --- Log Collector Callback ---
def log_collector_callback(message: str, level: str):
    """Callback function to collect logs from the NOA instance."""
    st.session_state.simulation_logs.append({'level': level, 'message': message})

# --- UI Setup ---
st.set_page_config(layout="wide", page_title="Causality")
st.title("Causality: Social Simulator 🚀")

# --- Initialize Session State ---
defaults = {
    'phase': 'setup', # 'setup', 'simulation'
    'noa_instance': None,
    'simulation_logs': [],
    'report': "",
    'judged_intention': {},
    'logotherapy': "",
    'fragmented_prompts': {},
    'final_reactions': {},
    'user_action': "I'm going to announce a new project that will disrupt the current team structure.",
    'user_name': "John",
    'user_birth_date': datetime.date(1994, 10, 15),
    'user_story': "Im the new consultant in a development team trying to secondarily integrate A.I into a business where current logistic chain optimization is handled by traditional machine learning. Im supposed to tell people how to implement A.I but im uncertain how to sell my foresight to each team mate and convince them of specific action. Consultants tend to be antagonized because they make everyone do extra work.",
    'provider': 'Google Gemini',
    'model_name': "gemini-2.5-flash",
    'openrouter_model': 'google/gemini-flash-1.5:free',
    'recommendations': [],
    'rec_provider': 'Google Gemini',
    'rec_model_name': "gemini-2.5-flash",
    'rec_openrouter_model': 'google/gemini-flash-1.5:free',
    'forecast_report': "",
    'forecast_provider': 'Google Gemini',
    'forecast_model_name': "gemini-2.5-flash",
    'forecast_openrouter_model': 'google/gemini-flash-1.5:free',
    'profiler_provider': 'Google Gemini',
    'profiler_model_name': "gemini-2.5-flash",
    'profiler_openrouter_model': 'google/gemini-flash-1.5:free',
    'token_manager': None,
    'prompt_token_budget': 100000,
    'completion_token_budget': 100000,
    'profiler_chat_history': [], # NEW for Profiler
    'user_profiles': [], # NEW for storing created profiles
    'rpg_profile_display': "", # NEW for displaying RPG profile
    'profiler_birth_date': datetime.date(1995, 1, 1), # NEW
    'profiler_user_name': "New Character", # NEW
    'profiler_done': False, # NEW to track interrogation state
    'imported_profiles': [], # NEW to track which profiles to import
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Sidebar for Token Monitoring (with Placeholders) ---
st.sidebar.title("📊 Live Monitoring")
prompt_budget_placeholder = st.sidebar.empty()
prompt_used_placeholder = st.sidebar.empty()
prompt_progress_placeholder = st.sidebar.empty()
st.sidebar.markdown("---")
completion_budget_placeholder = st.sidebar.empty()
completion_used_placeholder = st.sidebar.empty()
completion_progress_placeholder = st.sidebar.empty()
token_error_placeholder = st.sidebar.empty()

def update_sidebar_metrics():
    """Renders or updates the token metrics in the sidebar."""
    if st.session_state.get('token_manager'):
        prompt_budget = st.session_state.prompt_token_budget
        completion_budget = st.session_state.completion_token_budget
        
        prompt_used = st.session_state.token_manager.total_prompt_tokens_used
        completion_used = st.session_state.token_manager.total_completion_tokens_used

        prompt_budget_placeholder.metric(label="Prompt Token Budget", value=f"{prompt_budget}")
        prompt_used_placeholder.metric(label="Prompt Tokens Consumed", value=f"{prompt_used}")

        completion_budget_placeholder.metric(label="Completion Token Budget", value=f"{completion_budget}")
        completion_used_placeholder.metric(label="Completion Tokens Consumed", value=f"{completion_used}")

        if prompt_budget > 0:
            prompt_progress = min(prompt_used / prompt_budget, 1.0)
            prompt_progress_placeholder.progress(prompt_progress)
        else:
            prompt_progress_placeholder.progress(0.0)

        if completion_budget > 0:
            completion_progress = min(completion_used / completion_budget, 1.0)
            completion_progress_placeholder.progress(completion_progress)
        else:
            completion_progress_placeholder.progress(0.0)

        if prompt_used > prompt_budget or completion_used > completion_budget:
            error_message = ""
            if prompt_used > prompt_budget:
                error_message += "Prompt token budget exceeded! "
            if completion_used > completion_budget:
                error_message += "Completion token budget exceeded!"
            token_error_placeholder.error(error_message)
        else:
            token_error_placeholder.empty()
    else:
        prompt_budget_placeholder.info("Simulation not started yet. Token tracking will begin after setup.")


# Initial draw of the sidebar
update_sidebar_metrics()


# --- Main Feature Tabs ---
tab1, tab_profiler, tab2, tab5, tab3, tab4 = st.tabs(["🌐 Network Simulation", "👤 Profiler", "💡 Venue Recommendations", "📅 Social Forecast", "🧠 Memory Management", "📝 Edit Agents"])

with tab1:
    # --- PHASE 1: SETUP ---
    if st.session_state.phase == 'setup':
        st.header("Phase 1: Initial Setup")
        st.markdown("Define the user, initial context, and simulation parameters. This will create the agent network and run the first simulation directly.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("User & Situation Context")
            st.text_input("User's Name", key="user_name")
            st.date_input("User's Birth Date", key="user_birth_date")
            st.text_area("User's Story / Initial Context", key="user_story", height=150)
            st.text_input("User's First Action", key="user_action")
            
            # CORRECTED: Always show the multiselect widget
            st.subheader("Import Custom Profiles")
            profile_options = [p['name'] for p in st.session_state.user_profiles]
            st.multiselect(
                "Select profiled agents to include in the simulation:",
                options=profile_options,
                key="imported_profiles",
                help="Create custom agents in the 'Profiler' tab to add them to the simulation."
            )

        
        with col2:
            st.subheader("Simulation Parameters")
            st.slider("Number of Agents in Network", 1, 100, 3, key="n_people")
            st.number_input("Prompt Token Budget", 10000, 1000000, 50000, 1000, key="prompt_token_budget")
            st.number_input("Completion Token Budget", 10000, 1000000, 50000, 1000, key="completion_token_budget")
            
            st.selectbox("LLM Provider", ["Google Gemini", "Ollama (Local)", "OpenRouter", "Longcat Flash Chat"], key="provider")
            
            if st.session_state.provider == 'OpenRouter':
                st.selectbox("Model Name", ["google/gemini-flash-1.5:free"], key="openrouter_model")
            elif st.session_state.provider == 'Ollama (Local)':
                st.text_input("Model Name", "qwen3:30b-a3b-thinking-2507-q4_K_M", key="model_name")
            elif st.session_state.provider == 'Google Gemini':
                st.text_input("Model Name", "gemini-2.5-flash", key="model_name")
            # No model input needed for Longcat as it's specific

        if st.button("🚀 Create Network & Run Simulation", type="primary"):
            st.session_state.token_manager = TokenBudgetManager()
            
            provider_map = {
                "Google Gemini": "google",
                "Ollama (Local)": "local",
                "OpenRouter": "openrouter",
                "Longcat Flash Chat": "longcat"
            }
            st.session_state.selected_provider = provider_map[st.session_state.provider]
            
            if st.session_state.selected_provider == 'openrouter':
                if not os.getenv("OPEN_ROUTER"):
                    st.error("OPEN_ROUTER environment variable not set. Please add it to your .env file.")
                    st.stop()
                st.session_state.model_to_use = st.session_state.openrouter_model
            elif st.session_state.selected_provider == 'longcat':
                if not os.getenv("LONGCAT_API") or not os.getenv("LONGCAT_URL"):
                    st.error("LONGCAT_API and/or LONGCAT_URL environment variables not set. Please add them to your .env file.")
                    st.stop()
                st.session_state.model_to_use = "longcat-flash-chat" # The specific model name
            else:
                st.session_state.model_to_use = st.session_state.model_name
            
            st.session_state.phase = 'simulation'
            st.rerun()

    # --- PHASE 2: SIMULATION ---
    elif st.session_state.phase == 'simulation':
        # Create the network on the first run of this phase
        if not st.session_state.noa_instance:
            st.header("Phase 2: Running Simulation")
            
            main_progress_placeholder = st.empty()

            def update_progress(progress, text=""):
                main_progress_placeholder.progress(progress, text=text)
                update_sidebar_metrics()

            st.session_state.simulation_logs = []
            
            user_context = {
                "name": st.session_state.user_name,
                "birth_date": st.session_state.user_birth_date.strftime('%Y-%m-%d'),
                "story": st.session_state.user_story
            }

            # NEW: Get the full persona objects for the selected names
            personas_to_import = [p for p in st.session_state.user_profiles if p['name'] in st.session_state.imported_profiles]


            try:
                with st.spinner('Building network... This may take a moment.'):
                    update_progress(0, "Initializing network...")
                    
                    noa_instance = NOA(
                        user_context=user_context,
                        n_people=st.session_state.n_people,
                        provider=st.session_state.selected_provider,
                        model=st.session_state.model_to_use,
                        log_callback=log_collector_callback,
                        progress_callback=update_progress,
                        token_manager=st.session_state.token_manager,
                        pregenerated_personas=personas_to_import # NEW: Pass the imported personas
                    )
                
                main_progress_placeholder.empty()

                if noa_instance.graph:
                    st.session_state.noa_instance = noa_instance
                    with st.spinner('Running first query...'):
                         report, judged_intention, fragmented_prompts, final_reactions = noa_instance.query(st.session_state.user_action)
                    st.session_state.report = report
                    st.session_state.judged_intention = judged_intention
                    st.session_state.fragmented_prompts = fragmented_prompts
                    st.session_state.final_reactions = final_reactions
                    st.success("✅ Initial simulation complete!")
                    update_sidebar_metrics()
                    st.rerun()
                else:
                    st.error("❌ Failed to create the agent network. Check logs for details.")
                    st.session_state.phase = 'setup'

            except Exception as e:
                main_progress_placeholder.empty()
                st.error(f"An unexpected error occurred during network creation: {e}")
                st.session_state.phase = 'setup'
        
        # UI for querying the existing network
        else:
            st.header("Live Network")
            st.success("✅ Network is live. You can now query it with new actions or manage memory.")
            
            st.text_input("Enter a new user action:", key="new_user_action", value="I will praise the team's adaptability during the morning stand-up.")
            
            if st.button("⚡ Query Network with New Action", type="primary"):
                if st.session_state.noa_instance and st.session_state.new_user_action:
                    st.session_state.simulation_logs = []
                    with st.spinner("Querying the network with the new action..."):
                        try:
                            report, judged_intention, fragmented_prompts, final_reactions = st.session_state.noa_instance.query(st.session_state.new_user_action)
                            st.session_state.report = report
                            st.session_state.judged_intention = judged_intention
                            st.session_state.fragmented_prompts = fragmented_prompts
                            st.session_state.final_reactions = final_reactions
                            st.success("✅ Query complete!")
                            update_sidebar_metrics()
                        except Exception as e:
                            st.error(f"An error occurred during query: {e}")
                else:
                    st.warning("Please enter a new action to query.")

            if st.button("Reset and Start New Simulation"):
                # Preserve user-created profiles during reset
                saved_profiles = st.session_state.get('user_profiles', [])
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.session_state.user_profiles = saved_profiles # Restore them
                st.rerun()

            # --- Display Logs and Results ---
            if st.session_state.simulation_logs:
                with st.expander("🔬 Simulation Log & Agent Evolution", expanded=False):
                    for log in st.session_state.simulation_logs:
                        level, message = log['level'], log['message']
                        if level == 'step': st.markdown(f"--- \n#### {message}")
                        elif level == 'detail': st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;🔹 {message}")
                        elif level == 'error': st.error(message)
                        else: st.info(message)
            
            if st.session_state.report:
                st.subheader("Latest Simulation Results")
                st.markdown("---")
                st.markdown("### Strategic & Perception Debrief")
                st.markdown(st.session_state.report)
                st.markdown("### Judged User Intention (Council Score)")
                if st.session_state.judged_intention and isinstance(st.session_state.judged_intention, dict):

                    col1, col2 = st.columns(2)
                    
                    items = list(st.session_state.judged_intention.items())
                    midpoint = (len(items) + 1) // 2
                    
                    with col1:
                        for archetype, details in items[:midpoint]:
                            if isinstance(details, dict):
                                score = details.get('score', 'N/A')
                                reframing = details.get('reframing', 'No reframing provided.')
                                reaction = details.get('reaction', 'No reaction provided.')
                                st.markdown(f"**{archetype}**")
                                st.markdown(f"> Score: **{score}/10**")
                                st.markdown("Your reframed action that aligns with the archetype:")
                                st.markdown(f"> *{reframing}*")
                                st.markdown("Reaction:")
                                st.markdown(f"> *{reaction}*")
                                st.divider()

                    with col2:
                        for archetype, details in items[midpoint:]:
                            if isinstance(details, dict):
                                score = details.get('score', 'N/A')
                                reframing = details.get('reframing', 'No reframing provided.')
                                reaction = details.get('reaction', 'No reaction provided.')
                                st.markdown(f"**{archetype}**")
                                st.markdown(f"> Score: **{score}/10**")
                                st.markdown("Your reframed action that aligns with the archetype:")
                                st.markdown(f"> *{reframing}*")
                                st.markdown("Reaction:")
                                st.markdown(f"> *{reaction}*")
                                st.divider()
                else:
                    st.info("No judged intention data available to display.")
                st.markdown("---")
               
                st.subheader("Agent-Level Breakdown")
                if st.session_state.noa_instance and st.session_state.noa_instance.agent_personas:
                    for name in st.session_state.noa_instance.agent_configs.keys():
                        with st.expander(f"📜 Agent Breakdown for **{name}**"):
                            
                            noa = st.session_state.noa_instance
                            persona_data = noa.agent_personas.get(name, {})
                            memories = noa.agent_memories.get(name, [])
                            vision_of_user = noa.occluded_user_cards.get(name, "N/A")
                            social_cards = noa.agent_social_cards.get(name, [])
                            fragmented_prompt = st.session_state.fragmented_prompts.get(name, "")
                            reaction = st.session_state.final_reactions.get(name, "This agent did not provide a public reaction.")

                            st.markdown(f"#### Public Reaction")
                            st.info(reaction)
                            st.markdown(f"#### Analysis of Reaction")
                            if fragmented_prompt:
                                # Display Triggered Attributes
                                st.markdown("**Triggered Attributes:**")
                                try:
                                    if "#### Personality Attributes" in fragmented_prompt:
                                        attributes_section_raw = fragmented_prompt.split("#### Personality Attributes")[1]
                                        attributes_section = attributes_section_raw.split("####")[0]
                                        triggered_attributes = re.findall(r"- \*\*(.*?):\*\*(.*)", attributes_section)
                                        if triggered_attributes:
                                            for attr_name, definition in triggered_attributes:
                                                st.markdown(f"🔥 **{attr_name.strip()}:** {definition.strip()}")
                                        else:
                                            st.warning("Attribute section found, but no attributes could be parsed.")
                                    else:
                                        st.info("No specific personality attributes were triggered for this reaction.")
                                except (IndexError, AttributeError):
                                    st.warning("Could not parse triggered attributes.")

                                # Display Triggered Goal Hierarchy
                                st.markdown("**Triggered Goal Hierarchy:**")
                                try:
                                    if "#### Triggered Goal Hierarchy" in fragmented_prompt:
                                        goal_section_raw = fragmented_prompt.split("#### Triggered Goal Hierarchy")[1]
                                        goal_section = goal_section_raw.split("####")[0]
                                        st.markdown(goal_section.strip())
                                    else:
                                        st.info("The action did not specifically trigger a goal for this agent.")
                                except (IndexError, AttributeError):
                                    st.warning("Could not parse triggered goals from the fragmented prompt.")

                            st.markdown("---")
                            st.markdown("#### Full Agent Profile")
                            tab_profile, tab_social, tab_memory = st.tabs(["Personality", "Social Context", "Memory"])

                            with tab_profile:
                                if persona_data:
                                    st.markdown("**Core Identity & Purpose:**")
                                    st.write(persona_data.get('personality_attributes', {}).get('Core Identity & Purpose', 'N/A'))
                                    
                                    with st.expander("Full Personality Attributes"):
                                        st.json(persona_data.get('personality_attributes', {}))
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.markdown("**Virtues:**")
                                        st.markdown("\n".join([f"- {v}" for v in persona_data.get('virtues', [])]) or "None")
                                        st.markdown("**Skills:**")
                                        st.markdown("\n".join([f"- {s}" for s in persona_data.get('skills', [])]) or "None")
                                    with col2:
                                        st.markdown("**Tensions:**")
                                        st.markdown("\n".join([f"- {t}" for t in persona_data.get('tensions', [])]) or "None")
                                        st.markdown("**Fears:**")
                                        st.markdown("\n".join([f"- {f}" for f in persona_data.get('fears', [])]) or "None")
                                    
                                    # NEW: Display for hierarchical goals
                                    st.markdown("**Goals:**")
                                    def display_goals(goals, level=0):
                                        if not goals:
                                            st.markdown("None")
                                            return
                                        
                                        indent = "&nbsp;&nbsp;&nbsp;&nbsp;" * level
                                        for goal_item in goals:
                                            if isinstance(goal_item, dict):
                                                st.markdown(f"{indent}🎯 {goal_item.get('goal', 'No goal text.')}", unsafe_allow_html=True)
                                                if 'subgoals' in goal_item and goal_item['subgoals']:
                                                    display_goals(goal_item['subgoals'], level + 1)

                                    goals_data = persona_data.get('goals', [])
                                    display_goals(goals_data)

                                else:
                                    st.warning("Persona data not available.")

                            with tab_social:
                                st.markdown("**Vision of User:**")
                                st.info(vision_of_user)
                                st.markdown("**Social Cards (Visions of other agents):**")
                                st.text("\n".join(social_cards) or "No contacts.")

                            with tab_memory:
                                st.markdown("**Memory Log:**")
                                if memories:
                                    for j, memory in reversed(list(enumerate(memories))):
                                        st.text(f"[{j}] {memory}")
                                else:
                                    st.info("No memories logged yet.")

# --- TAB PROFILER (CORRECTED & REORDERED) ---
with tab_profiler:
    st.header("Character Profiler")
    st.markdown("Use a guided conversation to build a detailed psychological profile for a new character, then generate their persona to use in simulations.")

    if st.button("Start New Profile"):
        st.session_state.profiler_chat_history = []
        st.session_state.rpg_profile_display = ""
        st.session_state.profiler_done = False
        st.rerun()

    profiler_col1, profiler_col2 = st.columns(2)

    # --- COLUMN 1: INTERVIEW (PROCESSED FIRST) ---
    with profiler_col1:
        st.subheader("Contextual Interview")

        # Initialize chat if empty
        if not st.session_state.profiler_chat_history:
            st.session_state.profiler_chat_history.append({"role": "assistant", "content": "Hello! Let's create a character. To start, tell me about their primary goal or what they want most in the world."})

        # Display chat messages
        for message in st.session_state.profiler_chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input - This updates the state
        if prompt := st.chat_input("Describe the character...", disabled=st.session_state.profiler_done):
            st.session_state.profiler_chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                with st.spinner("Analyzing..."):
                    try:
                        # Setup a temporary LLM for the interrogator using its OWN config
                        provider_map = {"Google Gemini": "google", "Ollama (Local)": "local", "OpenRouter": "openrouter", "Longcat Flash Chat": "longcat"}
                        provider = provider_map[st.session_state.profiler_provider]
                        model = st.session_state.profiler_openrouter_model if provider == 'openrouter' else st.session_state.profiler_model_name
                        
                        interrogator_llm = None
                        if provider == 'local':
                            interrogator_llm = OllamaLLM(model=model)
                        elif provider == 'openrouter':
                             interrogator_llm = ChatOpenAI(api_key=os.getenv("OPEN_ROUTER"), base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"), model=model, max_retries=6, default_headers={"HTTP-Referer": os.getenv("YOUR_SITE_URL", ""), "X-Title": os.getenv("YOUR_SITE_NAME", "")})
                        elif provider == 'longcat':
                            interrogator_llm = ChatOpenAI(api_key=os.getenv("LONGCAT_API"), base_url=os.getenv("LONGCAT_URL"), model=model, max_retries=6)
                        else: # Google
                            interrogator_llm = ChatGoogleGenerativeAI(model=model, google_api_key=os.getenv("GEMINI_API_KEY"), max_retries=6)

                        interrogator_chain = get_chain(interrogator_llm, INTERROGATOR_PROMPT)

                        history_str = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.profiler_chat_history])
                        response = interrogator_chain.invoke({"conversation_history": history_str})
                        response_content = strip_think_tags(response.content if hasattr(response, 'content') else response)

                        if "done" in response_content.lower():
                            st.session_state.profiler_done = True
                            final_message = "Great, I have enough context now. You can proceed to generate the character class on the right."
                            message_placeholder.markdown(final_message)
                            st.session_state.profiler_chat_history.append({"role": "assistant", "content": final_message})
                        else:
                            message_placeholder.markdown(response_content)
                            st.session_state.profiler_chat_history.append({"role": "assistant", "content": response_content})
                    except Exception as e:
                        st.error(f"Error during interrogation: {e}")

    # --- COLUMN 2: DETAILS & GENERATION (PROCESSED SECOND) ---
    with profiler_col2:
        st.subheader("Character Details")
        st.text_input("Character Name", key="profiler_user_name")
        st.date_input("Character Birth Date", key="profiler_birth_date")

        st.markdown("---")
        
        st.subheader("LLM Configuration")
        st.info("This LLM is used for both the interview and the final profile generation.")
        st.selectbox("LLM Provider", ["Google Gemini", "Ollama (Local)", "OpenRouter", "Longcat Flash Chat"], key="profiler_provider")
        
        if st.session_state.profiler_provider == 'OpenRouter':
            st.selectbox("Model Name", ["google/gemini-flash-1.5:free"], key="profiler_openrouter_model")
        elif st.session_state.profiler_provider == 'Ollama (Local)':
            st.text_input("Model Name", "qwen3:30b-a3b-thinking-2507-q4_K_M", key="profiler_model_name")
        elif st.session_state.profiler_provider == 'Google Gemini':
            st.text_input("Model Name", "gemini-2.5-flash", key="profiler_model_name")

        # This button now correctly reads the updated state from col1
        if st.button("🎭 Generate Character Class",
                    type="primary",
                    disabled=not any(msg['role'] == 'user' for msg in st.session_state.profiler_chat_history)):

            with st.spinner("Generating full character profile... This is a multi-step process."):
                try:
                    if not st.session_state.get('token_manager'):
                        st.session_state.token_manager = TokenBudgetManager()

                    callbacks = [st.session_state.token_manager]
                    provider_map = {"Google Gemini": "google", "Ollama (Local)": "local", "OpenRouter": "openrouter", "Longcat Flash Chat": "longcat"}
                    provider = provider_map[st.session_state.profiler_provider]
                    model = st.session_state.profiler_openrouter_model if provider == 'openrouter' else st.session_state.profiler_model_name

                    temp_llm_json, temp_llm_str = None, None
                    if provider == 'local':
                        temp_llm_json = OllamaLLM(model=model, format="json", callbacks=callbacks)
                        temp_llm_str = OllamaLLM(model=model, callbacks=callbacks)
                    elif provider == 'openrouter':
                        common_settings = {"api_key": os.getenv("OPEN_ROUTER"), "base_url": os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"), "model": model, "callbacks": callbacks, "max_retries": 6, "default_headers": {"HTTP-Referer": os.getenv("YOUR_SITE_URL", ""), "X-Title": os.getenv("YOUR_SITE_NAME", "")}}
                        temp_llm_json = ChatOpenAI(**common_settings, model_kwargs={"response_format": {"type": "json_object"}})
                        temp_llm_str = ChatOpenAI(**common_settings)
                    elif provider == 'longcat':
                        common_settings = {"api_key": os.getenv("LONGCAT_API"), "base_url": os.getenv("LONGCAT_URL"), "model": model, "callbacks": callbacks, "max_retries": 6}
                        temp_llm_json = ChatOpenAI(**common_settings, model_kwargs={"response_format": {"type": "json_object"}})
                        temp_llm_str = ChatOpenAI(**common_settings)
                    else: # Google
                        common_settings = {"model": model, "google_api_key": os.getenv("GEMINI_API_KEY"), "callbacks": callbacks, "max_retries": 6}
                        temp_llm_json = ChatGoogleGenerativeAI(**common_settings, generation_config={"response_mime_type": "application/json"})
                        temp_llm_str = ChatGoogleGenerativeAI(**common_settings)

                    conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.profiler_chat_history])

                    full_persona, rpg_profile = NOA.profile_character(
                        llm_json=temp_llm_json,
                        llm_str=temp_llm_str,
                        user_name=st.session_state.profiler_user_name,
                        user_birth_date=st.session_state.profiler_birth_date.strftime('%Y-%m-%d'),
                        conversation_history=conversation_text
                    )

                    st.session_state.rpg_profile_display = rpg_profile
                    if full_persona['name'] not in [p['name'] for p in st.session_state.user_profiles]:
                        st.session_state.user_profiles.append(full_persona)
                        st.success(f"'{full_persona['name']}' has been profiled and saved!")
                    else:
                        st.warning(f"A profile for '{full_persona['name']}' already exists. Overwriting.")
                        st.session_state.user_profiles = [p for p in st.session_state.user_profiles if p['name'] != full_persona['name']]
                        st.session_state.user_profiles.append(full_persona)

                    update_sidebar_metrics()
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to generate profile: {e}")

        st.subheader("Generated Astrological Profile")
        if st.session_state.rpg_profile_display:
            st.markdown(st.session_state.rpg_profile_display)
        else:
            st.info("Generate a character to see their astrological RPG profile here.")


# --- TAB 2: VENUE RECOMMENDATIONS ---
with tab2:
    st.header("Get Social Scenario Recommendations")
    st.markdown("Based on a person's birth date, this feature generates social scenarios, independent of the main simulation.")

    col1, col2 = st.columns(2)

    with col1:
        rec_birth_date = st.date_input("Enter a Birth Date",datetime.datetime.now(), key="rec_bday")

        st.subheader("LLM Configuration")
        st.selectbox("LLM Provider", ["Google Gemini", "Ollama (Local)", "OpenRouter", "Longcat Flash Chat"], key="rec_provider")
        
        if st.session_state.rec_provider == 'OpenRouter':
            st.selectbox("Model Name", ["google/gemini-flash-1.5:free"], key="rec_openrouter_model")        
        elif st.session_state.rec_provider == 'Ollama (Local)':
            st.text_input("Model Name", "qwen3:30b-a3b-thinking-2507-q4_K_M", key="rec_model_name")
        elif st.session_state.rec_provider == 'Google Gemini':
            st.text_input("Model Name", "gemini-2.5-flash", key="rec_model_name")
        # No model input needed for Longcat

    if st.button("💡 Get Recommendations", type="primary"):
        with st.spinner("Generating recommendations..."):
            try:
                if not st.session_state.get('token_manager'):
                    st.session_state.token_manager = TokenBudgetManager()
                
                callbacks = [st.session_state.token_manager]
                
                provider_map = {
                    "Google Gemini": "google",
                    "Ollama (Local)": "local",
                    "OpenRouter": "openrouter",
                    "Longcat Flash Chat": "longcat"
                }
                selected_provider = provider_map[st.session_state.rec_provider]
                
                temp_llm = None
                model_to_use = ""

                if selected_provider == 'local':
                    model_to_use = st.session_state.rec_model_name
                    temp_llm = OllamaLLM(model=model_to_use, format="json", callbacks=callbacks)
                elif selected_provider == 'openrouter':
                    openrouter_api_key = os.getenv("OPEN_ROUTER")
                    if not openrouter_api_key:
                        st.error("OPEN_ROUTER environment variable must be set. Please add it to your .env file.")
                        st.stop()
                    
                    model_to_use = st.session_state.rec_openrouter_model
                    temp_llm = ChatOpenAI(
                        api_key=openrouter_api_key,
                        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                        model=model_to_use,
                        callbacks=callbacks, max_retries=6,
                        model_kwargs={"response_format": {"type": "json_object"}},
                        default_headers={"HTTP-Referer": os.getenv("YOUR_SITE_URL", ""), "X-Title": os.getenv("YOUR_SITE_NAME", "")}
                    )
                elif selected_provider == 'longcat':
                    longcat_api_key = os.getenv("LONGCAT_API")
                    longcat_base_url = os.getenv("LONGCAT_URL")
                    if not longcat_api_key or not longcat_base_url:
                        st.error("LONGCAT_API and/or LONGCAT_URL environment variables must be set.")
                        st.stop()

                    model_to_use = "longcat-flash-chat"
                    temp_llm = ChatOpenAI(
                        api_key=longcat_api_key, base_url=longcat_base_url,
                        model=model_to_use, callbacks=callbacks, max_retries=6,
                        model_kwargs={"response_format": {"type": "json_object"}}
                    )
                else: # Google
                    gemini_api_key = os.getenv("GEMINI_API_KEY")
                    model_to_use = st.session_state.rec_model_name
                    temp_llm = ChatGoogleGenerativeAI(
                        model=model_to_use, google_api_key=gemini_api_key,
                        generation_config={"response_mime_type": "application/json"}, callbacks=callbacks, max_retries=6
                    )

                recommendations = NOA.recommend(
                    llm=temp_llm,
                    user_birth_date=rec_birth_date.strftime('%Y-%m-%d'),
                )
                recommendations_list = recommendations.get('recommendations', [])
                st.session_state.recommendations = recommendations_list
                update_sidebar_metrics()
                
            except Exception as e:
                st.error(f"An error occurred: {e}")

    if st.session_state.recommendations:
        st.markdown("---")
        st.success("Here are your recommended scenarios:")
        for i, rec in enumerate(st.session_state.recommendations):
            st.markdown(f"**{i+1}. {rec['title']}**")
            st.write(rec['description'])
            st.caption(f"💡 **Why we suggest this:** {rec.get('rationale', 'No rationale provided.')}")

# --- TAB 5: SOCIAL FORECAST ---
with tab5:
    st.header("Generate a Social Engineering Forecast")
    st.markdown("Compare your user profile against the archetypal 'personality' of a future date to get a strategic report.")

    col1, col2 = st.columns(2)

    with col1:
        st.info(f"Forecasting for **{st.session_state.user_name}**, born on **{st.session_state.user_birth_date.strftime('%Y-%m-%d')}**.")
        forecast_date = st.date_input("Select a Forecast Date", datetime.date.today() + datetime.timedelta(days=1), key="forecast_date")

        st.subheader("LLM Configuration")
        st.selectbox("LLM Provider", ["Google Gemini", "Ollama (Local)", "OpenRouter", "Longcat Flash Chat"], key="forecast_provider")
        
        if st.session_state.forecast_provider == 'OpenRouter':
            st.selectbox("Model Name", ["google/gemini-flash-1.5:free"], key="forecast_openrouter_model")
        elif st.session_state.forecast_provider == 'Ollama (Local)':
            st.text_input("Model Name", "qwen3:30b-a3b-thinking-2507-q4_K_M", key="forecast_model_name")
        elif st.session_state.forecast_provider == 'Google Gemini':
            st.text_input("Model Name", "gemini-2.5-flash", key="forecast_model_name")

    if st.button("🔮 Generate Forecast", type="primary"):
        with st.spinner("Generating forecast... This requires multiple LLM calls and may take a moment."):
            try:
                if not st.session_state.get('token_manager'):
                    st.session_state.token_manager = TokenBudgetManager()
                
                callbacks = [st.session_state.token_manager]
                
                provider_map = {
                    "Google Gemini": "google",
                    "Ollama (Local)": "local",
                    "OpenRouter": "openrouter",
                    "Longcat Flash Chat": "longcat"
                }
                selected_provider = provider_map[st.session_state.forecast_provider]
                
                temp_llm_json = None
                temp_llm_str = None
                model_to_use = ""

                if selected_provider == 'local':
                    model_to_use = st.session_state.forecast_model_name
                    temp_llm_json = OllamaLLM(model=model_to_use, format="json", callbacks=callbacks)
                    temp_llm_str = OllamaLLM(model=model_to_use, callbacks=callbacks)
                elif selected_provider == 'openrouter':
                    openrouter_api_key = os.getenv("OPEN_ROUTER")
                    if not openrouter_api_key:
                        st.error("OPEN_ROUTER environment variable must be set.")
                        st.stop()
                    
                    model_to_use = st.session_state.forecast_openrouter_model
                    common_settings = {
                        "api_key": openrouter_api_key,
                        "base_url": os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                        "model": model_to_use, "callbacks": callbacks, "max_retries": 6,
                        "default_headers": {"HTTP-Referer": os.getenv("YOUR_SITE_URL", ""), "X-Title": os.getenv("YOUR_SITE_NAME", "")}
                    }
                    temp_llm_json = ChatOpenAI(**common_settings, model_kwargs={"response_format": {"type": "json_object"}})
                    temp_llm_str = ChatOpenAI(**common_settings)
                elif selected_provider == 'longcat':
                    longcat_api_key = os.getenv("LONGCAT_API")
                    longcat_base_url = os.getenv("LONGCAT_URL")
                    if not longcat_api_key or not longcat_base_url:
                        st.error("LONGCAT_API and/or LONGCAT_URL environment variables must be set.")
                        st.stop()

                    model_to_use = "longcat-flash-chat"
                    common_settings = {
                        "api_key": longcat_api_key, "base_url": longcat_base_url,
                        "model": model_to_use, "callbacks": callbacks, "max_retries": 6,
                    }
                    temp_llm_json = ChatOpenAI(**common_settings, model_kwargs={"response_format": {"type": "json_object"}})
                    temp_llm_str = ChatOpenAI(**common_settings)
                else: # Google
                    gemini_api_key = os.getenv("GEMINI_API_KEY")
                    model_to_use = st.session_state.forecast_model_name
                    common_settings = {
                        "model": model_to_use, "google_api_key": gemini_api_key,
                        "callbacks": callbacks, "max_retries": 6
                    }
                    temp_llm_json = ChatGoogleGenerativeAI(**common_settings, generation_config={"response_mime_type": "application/json"})
                    temp_llm_str = ChatGoogleGenerativeAI(**common_settings)

                forecast_report = NOA.forecast(
                    llm=temp_llm_json,
                    str_llm=temp_llm_str,
                    user_birth_date=st.session_state.user_birth_date.strftime('%Y-%m-%d'),
                    forecast_date=forecast_date.strftime('%Y-%m-%d'),
                )
                st.session_state.forecast_report = forecast_report
                update_sidebar_metrics()
                
            except Exception as e:
                st.error(f"An error occurred during forecast generation: {e}")

    if st.session_state.forecast_report:
        st.markdown("---")
        st.success("Your forecast is ready:")
        st.markdown(st.session_state.forecast_report)

# --- TAB 3: MEMORY MANAGEMENT ---
with tab3:
    st.header("Manage Agent Memory")
    st.markdown("Roll back the simulation by removing the last set of memories from each agent.")
    
    if not st.session_state.noa_instance or not st.session_state.noa_instance.agent_memories:
        st.info("Run a simulation first to populate agent memories.")
    else:
        st.subheader("Current Agent Memories")
        for name, memories in st.session_state.noa_instance.agent_memories.items():
            with st.expander(f"Memory for **{name}** ({len(memories)} entries)"):
                # Show in reverse chronological order
                for j, memory in reversed(list(enumerate(memories))):
                    st.text(f"[{j}] {memory}")
        
        st.markdown("---")
        st.subheader("Rollback Memories")
        rollback_max = 1
        if st.session_state.noa_instance and st.session_state.noa_instance.agent_memories:
            try:
                first_agent_mem_len = len(next(iter(st.session_state.noa_instance.agent_memories.values()), []))
                if first_agent_mem_len > 1:
                    rollback_max = first_agent_mem_len - 1
            except StopIteration:
                pass # No agents to iterate over

        n_steps = st.number_input("Steps to roll back", 1, rollback_max, 1, key="rollback_steps")
        
        if st.button("↩️ Rollback Agent Memories"):
            with st.spinner("Rolling back memories..."):
                result_message = st.session_state.noa_instance.rollback(n=n_steps)
                st.success(result_message)
                time.sleep(1)
                st.rerun()

# --- TAB 4: EDIT AGENTS ---
with tab4:
    st.header("Directly Edit Agent Personas")
    st.markdown("Modify the core attributes, memories, and goals of any agent in the network. Changes will be applied before the next query.")

    if not st.session_state.get('noa_instance'):
        st.info("Run a simulation first to create agents to edit.")
    else:
        noa = st.session_state.noa_instance
        agent_names = list(noa.agent_personas.keys())

        for name in agent_names:
            with st.expander(f"Edit Profile for **{name}**"):
                persona = noa.agent_personas[name]
                memories = noa.agent_memories[name]

                # Use unique keys for each widget
                edited_attributes_key = f"edit_attributes_{name}"
                edited_virtues_key = f"edit_virtues_{name}"
                edited_tensions_key = f"edit_tensions_{name}"
                edited_skills_key = f"edit_skills_{name}"
                edited_fears_key = f"edit_fears_{name}"
                edited_goals_key = f"edit_goals_{name}"
                edited_memories_key = f"edit_memories_{name}"

                st.subheader("Personality Attributes")
                edited_attributes = st.text_area(
                    "Personality Attributes (JSON)",
                    value=json.dumps(persona.get('personality_attributes', {}), indent=2),
                    height=300,
                    key=edited_attributes_key
                )

                st.subheader("Goals")
                edited_goals = st.text_area(
                    "Goals (JSON)",
                    value=json.dumps(persona.get('goals', []), indent=2),
                    height=200,
                    key=edited_goals_key
                )

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Derived Traits")
                    edited_virtues = st.text_area("Virtues", value="\n".join(persona.get('virtues', [])), key=edited_virtues_key)
                    edited_tensions = st.text_area("Tensions", value="\n".join(persona.get('tensions', [])), key=edited_tensions_key)
                    edited_skills = st.text_area("Skills", value="\n".join(persona.get('skills', [])), key=edited_skills_key)
                    edited_fears = st.text_area("Fears", value="\n".join(persona.get('fears', [])), key=edited_fears_key)

                with col2:
                    st.subheader("Memory Log")
                    edited_memories = st.text_area(
                        "Memories",
                        value="\n".join(memories),
                        height=400,
                        key=edited_memories_key
                    )

                if st.button(f"Save Changes for {name}", key=f"save_button_{name}"):
                    try:
                        # Parse all the edited fields
                        new_attributes = json.loads(edited_attributes)
                        new_goals = json.loads(edited_goals)
                        new_virtues = [v.strip() for v in edited_virtues.split('\n') if v.strip()]
                        new_tensions = [t.strip() for t in edited_tensions.split('\n') if t.strip()]
                        new_skills = [s.strip() for s in edited_skills.split('\n') if s.strip()]
                        new_fears = [f.strip() for f in edited_fears.split('\n') if f.strip()]
                        new_memories_list = [m.strip() for m in edited_memories.split('\n') if m.strip()]

                        # Construct the updated persona data
                        updated_persona = persona.copy() # Start with the original
                        updated_persona['personality_attributes'] = new_attributes
                        updated_persona['goals'] = new_goals
                        updated_persona['virtues'] = new_virtues
                        updated_persona['tensions'] = new_tensions
                        updated_persona['skills'] = new_skills
                        updated_persona['fears'] = new_fears

                        # Call the new method in noa.py to update the instance
                        noa.update_agent_persona(name, updated_persona, new_memories_list)

                        st.success(f"Successfully updated {name}'s profile. The changes will be used in the next query.")
                        time.sleep(1) # Give user time to see the message
                        st.rerun()

                    except json.JSONDecodeError as e:
                        st.error(f"Invalid JSON format in 'Personality Attributes' or 'Goals'. Please correct it. Error: {e}")
                    except Exception as e:
                        st.error(f"An unexpected error occurred: {e}")

                st.subheader("Resulting System Prompt (Read-Only)")
                st.markdown("This is the full prompt that will be used by the agent in the next simulation, based on the data above.")
                # We can call the protected method here for display purposes
                current_prompt = noa._assemble_agent_prompt(name)
                st.code(current_prompt, language='markdown')