import streamlit as st
import datetime
import json
import time
from dotenv import load_dotenv
from noa import NOA
from chains import get_chain # Removed INTERROGATOR_PROMPT
from utils import strip_think_tags, TokenBudgetManager
from langchain_ollama.llms import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI
import os

load_dotenv()

# --- Log Collector Callback ---
def log_collector_callback(message: str, level: str):
    """Callback function to collect logs from the NOA instance."""
    st.session_state.simulation_logs.append({'level': level, 'message': message})

# --- UI Setup ---
st.set_page_config(layout="wide", page_title="NOA Package Tester")
st.title("NOA: Social Causality Simulator 🚀")
st.markdown("This app demonstrates the persistent, multi-query features of the `noa` package.")

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
    'user_name': "Alex",
    'user_birth_date': datetime.date(1990, 5, 15),
    'user_story': "Alex is a team lead who feels the current workflow is inefficient and wants to introduce a new system.",
    'use_local': False,
    'model_name': "gemini-2.5-flash",
    'recommendations': [],
    'rec_use_local': False, # Dedicated state for recommendation LLM
    'rec_model_name': "gemini-2.5-flash", # Dedicated state for recommendation LLM
    'token_manager': None,
    'saved_token_budget': 50000,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Sidebar for Token Monitoring (with Placeholders) ---
st.sidebar.title("📊 Live Monitoring")
token_budget_placeholder = st.sidebar.empty()
tokens_used_placeholder = st.sidebar.empty()
token_progress_placeholder = st.sidebar.empty()
token_error_placeholder = st.sidebar.empty()

def update_sidebar_metrics():
    """Renders or updates the token metrics in the sidebar."""
    if st.session_state.get('token_manager'):
        budget = st.session_state.saved_token_budget
        used_tokens = st.session_state.token_manager.total_tokens_used

        token_budget_placeholder.metric(label="Total Token Budget", value=f"{budget}")
        tokens_used_placeholder.metric(label="Tokens Consumed", value=f"{used_tokens}")

        if budget > 0:
            progress = min(used_tokens / budget, 1.0)
            token_progress_placeholder.progress(progress)
        else:
            token_progress_placeholder.progress(0.0)

        if used_tokens > budget:
            token_error_placeholder.error("Token budget exceeded!")
        else:
            token_error_placeholder.empty()
    else:
        token_budget_placeholder.info("Simulation not started yet. Token tracking will begin after setup.")

# Initial draw of the sidebar
update_sidebar_metrics()


# --- Main Feature Tabs ---
tab1, tab2, tab3 = st.tabs(["🌐 Network Simulation", "💡 Venue Recommendations", "🧠 Memory Management"])

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
        
        with col2:
            st.subheader("Simulation Parameters")
            st.slider("Number of Agents in Network", 2, 100, 3, key="n_people")
            st.number_input("Token Budget", 10000, 1000000, 50000, 1000, key="token_budget")
            use_local = st.checkbox("Use Local Model (Ollama)", key="use_local")
            st.text_input("Model Name", "hf.co/unsloth/Qwen3-4B-Thinking-2507-GGUF:latest" if use_local else "gemini-2.5-flash", key="model_name")

        if st.button("🚀 Create Network & Run Simulation", type="primary"):
            st.session_state.saved_token_budget = st.session_state.token_budget
            st.session_state.token_manager = TokenBudgetManager(initial_budget=st.session_state.saved_token_budget)
            st.session_state.phase = 'simulation'
            st.rerun()

    # --- PHASE 3: SIMULATION ---
    elif st.session_state.phase == 'simulation':
        # Create the network on the first run of this phase
        if not st.session_state.noa_instance:
            st.header("Phase 2: Running Simulation")
            
            # Placeholder for the main progress bar in the main app area
            main_progress_placeholder = st.empty()

            def update_progress(progress, text=""):
                """Callback to update the main progress bar AND the sidebar metrics."""
                main_progress_placeholder.progress(progress, text=text)
                update_sidebar_metrics() # This is the key change to update the token counter

            st.session_state.simulation_logs = []
            
            user_context = {
                "name": st.session_state.user_name,
                "birth_date": st.session_state.user_birth_date.strftime('%Y-%m-%d'),
                "story": st.session_state.user_story
            }

            try:
                # The spinner provides a general "working" message
                with st.spinner('Building network... This may take a moment.'):
                    # The progress bar will be updated by the callback
                    update_progress(0, "Initializing network...")
                    
                    noa_instance = NOA(
                        user_context=user_context,
                        n_people=st.session_state.n_people,
                        token_budget=st.session_state.saved_token_budget,
                        local=st.session_state.use_local,
                        model=st.session_state.model_name,
                        log_callback=log_collector_callback,
                        progress_callback=update_progress, # Pass the enhanced callback
                        token_manager=st.session_state.token_manager
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
                    update_sidebar_metrics() # Final update after query
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
                            update_sidebar_metrics() # Update metrics after query
                        except Exception as e:
                            st.error(f"An error occurred during query: {e}")
                else:
                    st.warning("Please enter a new action to query.")

            if st.button("Reset and Start New Simulation"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
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
                st.markdown("### Strategic Debrief")
                st.markdown(st.session_state.report)
                st.markdown("### Judged User Intention (Council Score)")
                st.json(st.session_state.judged_intention)
                st.markdown("---")
               
                st.subheader("Agent-Level Breakdown")
                if st.session_state.noa_instance.agent_configs:
                    for name in st.session_state.noa_instance.agent_configs.keys():
                        with st.expander(f"📜 Agent Breakdown for **{name}**"):
                            
                            # Display Fragmented Prompt
                            fragmented_prompt = st.session_state.fragmented_prompts.get(name, "This agent's prompt was not fragmented in the last query.")
                            st.text_area(
                                "Fragmented Prompt (Used in Last Query)", 
                                fragmented_prompt, 
                                height=250, 
                                disabled=True, 
                                key=f"fragmented_prompt_{name}"
                            )
                            
                            st.markdown("---")

                            # Display Agent's Reaction
                            reaction = st.session_state.final_reactions.get(name, "This agent did not provide a public reaction in the last query.")
                            st.text_area(
                                "Public Reaction",
                                reaction,
                                height=100,
                                disabled=True,
                                key=f"reaction_{name}"
                            )

# --- TAB 2: VENUE RECOMMENDATIONS ---
with tab2:
    st.header("Get Social Scenario Recommendations")
    st.markdown("Based on a person's birth date, this feature generates social scenarios, independent of the main simulation.")

    col1, col2 = st.columns(2)

    with col1:
        rec_birth_date = st.date_input("Enter a Birth Date",datetime.datetime.now(), key="rec_bday")

        st.subheader("LLM Configuration")
        rec_use_local = st.checkbox("Use Local Model (Ollama)", key="rec_use_local")
        st.text_input("Model Name", "hf.co/unsloth/Qwen3-4B-Thinking-2507-GGUF:latest" if rec_use_local else "gemini-2.5-flash", key="rec_model_name")

    if st.button("💡 Get Recommendations", type="primary"):
        with st.spinner("Generating recommendations..."):
            try:
                # Ensure token manager exists before creating callbacks
                if not st.session_state.get('token_manager'):
                    st.session_state.token_manager = TokenBudgetManager(initial_budget=st.session_state.saved_token_budget)
                
                callbacks = [st.session_state.token_manager]
                if st.session_state.rec_use_local:
                    temp_llm = OllamaLLM(model=st.session_state.rec_model_name, format="json", callbacks=callbacks)
                else:
                    gemini_api_key = os.getenv("GEMINI_API_KEY")
                    temp_llm = ChatGoogleGenerativeAI(model=st.session_state.rec_model_name,  google_api_key=gemini_api_key, response_mime_type="application/json", callbacks=callbacks)

                recommendations = NOA.recommend(
                    llm=temp_llm,
                    user_birth_date=rec_birth_date.strftime('%Y-%m-%d'),
                    local=st.session_state.rec_use_local
                )
                recommendations_list = recommendations.get('recommendations', [])
                st.session_state.recommendations = recommendations_list # Save to session state
                update_sidebar_metrics() # Update token count after generation
                
            except Exception as e:
                st.error(f"An error occurred: {e}")

    if st.session_state.recommendations:
        st.markdown("---")
        st.success("Here are your recommended scenarios:")
        for i, rec in enumerate(st.session_state.recommendations):
            st.markdown(f"**{i+1}. {rec['title']}**")
            st.write(rec['description'])
            st.caption(f"💡 **Why we suggest this:** {rec.get('rationale', 'No rationale provided.')}")


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