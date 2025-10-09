import streamlit as st
import datetime
import json
import time
from dotenv import load_dotenv
from noa import NOA
from chains import get_chain, INTERROGATOR_PROMPT
from utils import strip_think_tags, TokenBudgetManager
from langchain_ollama.llms import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI
import os

load_dotenv()

# --- Interrogation Function ---
def get_interrogator_response(conversation_history_str):
    """Invokes the LLM to get the next interrogation question or 'done'."""
    try:
        # This uses the model settings from the main UI for consistency
        if st.session_state.use_local:
            llm = OllamaLLM(model=st.session_state.model_name)
            response = llm.invoke(st.session_state.conversation_history_str)
        else:
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            llm = ChatGoogleGenerativeAI(model=st.session_state.model_name, google_api_key=gemini_api_key)
            response = llm.invoke(conversation_history_str).content

        chain = get_chain(llm, INTERROGATOR_PROMPT)
        raw_response = chain.invoke({"conversation_history": conversation_history_str})

        if not st.session_state.use_local and hasattr(raw_response, 'content'):
             response = strip_think_tags(raw_response.content)
        else:
             response = strip_think_tags(raw_response)

        return response.strip()
    except Exception as e:
        st.error(f"Error communicating with the interrogator model: {e}")
        return "done" # Fail safe to allow simulation to proceed

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
    'phase': 'setup', # 'setup', 'interrogation', 'simulation'
    'noa_instance': None,
    'simulation_logs': [],
    'report': "",
    'judged_intention': {},
    'user_action': "I'm going to announce a new project that will disrupt the current team structure.",
    'user_name': "Alex",
    'user_birth_date': datetime.date(1990, 5, 15),
    'user_story': "Alex is a team lead who feels the current workflow is inefficient and wants to introduce a new system.",
    'conversation': [],
    'use_local': False,
    'model_name': "gemini-1.5-flash",
    'recommendations': [],
    'rec_use_local': False, # Dedicated state for recommendation LLM
    'rec_model_name': "gemini-1.5-flash", # Dedicated state for recommendation LLM
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Main Feature Tabs ---
tab1, tab2, tab3 = st.tabs(["🌐 Network Simulation", "💡 Venue Recommendations", "🧠 Memory Management"])

with tab1:
    # --- PHASE 1: SETUP ---
    if st.session_state.phase == 'setup':
        st.header("Phase 1: Initial Setup")
        st.markdown("Define the user, initial context, and simulation parameters. This will kick off a brief, AI-driven interview to flesh out the scenario before building the network.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("User & Situation Context")
            st.text_input("User's Name", key="user_name")
            st.date_input("User's Birth Date", key="user_birth_date")
            st.text_area("User's Story / Initial Context", key="user_story", height=150)
            st.text_input("User's First Action", key="user_action")
        
        with col2:
            st.subheader("Simulation Parameters")
            st.slider("Number of Agents in Network", 2, 10, 3, key="n_people")
            st.number_input("Token Budget", 10000, 100000, 50000, 1000, key="token_budget")
            use_local = st.checkbox("Use Local Model (Ollama)", key="use_local")
            st.text_input("Model Name", "qwen2:7b" if use_local else "gemini-1.5-flash", key="model_name")

        if st.button("Begin Context Interrogation", type="primary"):
            st.session_state.conversation = [f"User's Initial Context: {st.session_state.user_story}"]
            st.session_state.phase = 'interrogation'
            st.rerun()

    # --- PHASE 2: INTERROGATION ---
    elif st.session_state.phase == 'interrogation':
        st.header("Phase 2: Context Interrogation")
        st.markdown("The AI will ask you questions to build a richer context for the simulation. Answer each question to proceed.")

        # Display conversation history
        for message in st.session_state.conversation:
            if message.startswith("User's Initial Context:") or message.startswith("Answer:"):
                st.info(message)
            else:
                st.warning(f"**Question:** {message}")

        conversation_str = "\n".join(st.session_state.conversation)
        
        with st.spinner("Waiting for the interrogator's next question..."):
            next_question = get_interrogator_response(conversation_str)

        if next_question.lower() == 'done':
            st.success("Context building complete!")
            st.session_state.phase = 'simulation'
            if st.button("🚀 Create Network & Run First Simulation", type="primary"):
                st.rerun()
        else:
            st.session_state.conversation.append(next_question)
            answer = st.text_area("Your Answer:", key="user_answer")
            if st.button("Submit Answer"):
                st.session_state.conversation.append(f"Answer: {answer}")
                st.rerun()

    # --- PHASE 3: SIMULATION ---
    elif st.session_state.phase == 'simulation':
        # Create the network on the first run of this phase
        if not st.session_state.noa_instance:
            st.header("Phase 3: Running Simulation")
            
            # --- Progress Bar Setup ---
            progress_bar_placeholder = st.empty()
            def update_progress(progress, text=""):
                progress_bar_placeholder.progress(progress, text=text)
            # --- End Progress Bar Setup ---

            st.session_state.simulation_logs = []
            final_story = "\n".join(st.session_state.conversation)
            
            user_context = {
                "name": st.session_state.user_name,
                "birth_date": st.session_state.user_birth_date.strftime('%Y-%m-%d'),
                "story": final_story
            }

            try:
                with st.spinner('Building network... This may take a moment.'):
                    # Set initial progress
                    update_progress(0, "Initializing network...")
                    noa_instance = NOA(
                        user_context=user_context,
                        n_people=st.session_state.n_people,
                        token_budget=st.session_state.token_budget,
                        local=st.session_state.use_local,
                        model=st.session_state.model_name,
                        log_callback=log_collector_callback,
                        progress_callback=update_progress # Pass the callback here
                    )
                
                # Clear the progress bar after completion
                progress_bar_placeholder.empty()

                if noa_instance.graph:
                    st.session_state.noa_instance = noa_instance
                    with st.spinner('Running first query...'):
                         report, judged_intention = noa_instance.query(st.session_state.user_action)
                    st.session_state.report = report
                    st.session_state.judged_intention = judged_intention
                    st.success("✅ Initial simulation complete!")
                    st.rerun()
                else:
                    st.error("❌ Failed to create the agent network. Check logs for details.")
                    st.session_state.phase = 'setup' # Go back to setup on failure
            except Exception as e:
                progress_bar_placeholder.empty()
                st.error(f"An unexpected error occurred during network creation: {e}")
                st.session_state.phase = 'setup'
        
        # UI for querying the existing network
        else:
            st.header("Live Network")
            st.success("✅ Network is live. You can now query it with new actions or manage memory.")
            
            st.text_input("Enter a new user action:", key="new_user_action", value="I will praise the team's adaptability during the morning stand-up.")
            
            if st.button("⚡ Query Network with New Action", type="primary"):
                if st.session_state.noa_instance and st.session_state.new_user_action:
                    st.session_state.simulation_logs = [] # Clear logs for the new query
                    with st.spinner("Querying the network with the new action..."):
                        try:
                            report, judged_intention = st.session_state.noa_instance.query(st.session_state.new_user_action)
                            st.session_state.report = report
                            st.session_state.judged_intention = judged_intention
                            st.success("✅ Query complete!")
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
                st.subheader("Agent Social Cards (Full Prompts)")
                if st.session_state.noa_instance.agent_configs:
                    for name, config in st.session_state.noa_instance.agent_configs.items():
                        with st.expander(f"📜 View Social Card for **{name}**"):
                            st.text_area("System Prompt", config['prompt'], height=400, disabled=True, key=f"prompt_{name}")

# --- TAB 2: VENUE RECOMMENDATIONS ---
with tab2:
    st.header("Get Social Scenario Recommendations")
    st.markdown("Based on a person's birth date, this feature generates social scenarios, independent of the main simulation.")

    col1, col2 = st.columns()

    with col1:
        rec_birth_date = st.date_input("Enter a Birth Date",datetime.datetime.now(), key="rec_bday")

        st.subheader("LLM Configuration")
        rec_use_local = st.checkbox("Use Local Model (Ollama)", key="rec_use_local")
        st.text_input("Model Name", "qwen2:7b" if rec_use_local else "gemini-1.5-flash", key="rec_model_name")

    if st.button("💡 Get Recommendations", type="primary"):
        with st.spinner("Generating recommendations..."):
            try:

                if st.session_state.rec_use_local:
                    temp_llm = OllamaLLM(model=st.session_state.rec_model_name, format="json")
                else:
                    
                    gemini_api_key = os.getenv("GEMINI_API_KEY")
                    temp_llm = ChatGoogleGenerativeAI(model=st.session_state.rec_model_name,  google_api_key=gemini_api_key, response_mime_type="application/json")

                recommendations = NOA.recommend(
                    llm=temp_llm,
                    user_birth_date=rec_birth_date.strftime('%Y-%m-%d'),
                    local=st.session_state.rec_use_local
                )
                recommendations = recommendations['recommendations']
                for i, rec in enumerate(recommendations):
                    st.markdown(f"**{i+1}. {rec['title']}**")
                    st.write(rec['description'])
                    st.caption(f"💡 **Why we suggest this:** {rec.get('rationale', 'No rationale provided.')}")

            except Exception as e:
                st.error(f"An error occurred: {e}")

    if st.session_state.recommendations:
        st.markdown("---")
        st.success("Here are 10 recommended scenarios:")
        for i, rec in enumerate(st.session_state.recommendations):
            st.markdown(f"**{i+1}. {rec['title']}**")
            st.write(rec['description'])

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
        # Ensure there's memory to roll back
        if st.session_state.noa_instance and st.session_state.noa_instance.agent_memories:
            # Get the length of the first agent's memory, minus the initial memory
            first_agent_mem_len = len(next(iter(st.session_state.noa_instance.agent_memories.values()), []))
            if first_agent_mem_len > 1:
                rollback_max = first_agent_mem_len - 1

        n_steps = st.number_input("Steps to roll back", 1, rollback_max, 1, key="rollback_steps")
        
        if st.button("↩️ Rollback Agent Memories"):
            with st.spinner("Rolling back memories..."):
                result_message = st.session_state.noa_instance.rollback(n=n_steps)
                st.success(result_message)
                time.sleep(1)
                st.rerun()