# noa/chains.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

# --- PROMPT TEMPLATES ---

SITUATION_FRAMING_PROMPT = ChatPromptTemplate.from_template(
    """

Analyze the following user context from a purely symbolic and archetypal perspective. Your output must be completely free of astrological terminology (e.g., no mention of planets, signs, or houses). Instead, use the functional and descriptive equivalents provided below.

1.  **Identify the Core Theme:** Determine the primary life domain that represents the situation's central theme. This is the stage on which the events are unfolding.
2.  **Create an Archetypal Profile:** Personify the situation by creating a profile of its underlying psychological dynamics. For each of the core functions listed below, provide a short, descriptive sentence that explains its unique style of expression, as shown in the example.

---

**Core Psychological Functions & Drives:**

*   **Core Identity:** The situation's fundamental purpose and sense of self.
*   **Emotional Instincts:** The underlying emotional needs and reactions seeking comfort and security.
*   **Communication & Logic:** The style of thinking, processing information, and communication.
*   **Values & Connections:** The approach to relationships, harmony, and what the situation deems valuable.
*   **Action & Aggression:** The method of asserting will, taking action, and handling conflict.
*   **Growth & Opportunity:** The manner in which the situation seeks to expand, find meaning, and grow.
*   **Structure & Discipline:** The approach to limitations, responsibilities, and long-term security.
*   **Change & Disruption:** The style of innovation, rebellion against the norm, and unexpected change.
*   **Ideals & Illusions:** The connection to imagination, ideals, spirituality, and areas of confusion.
*   **Power & Transformation:** The approach to deep, fundamental change, power dynamics, and uncovering hidden truths.
*   **Wounded Healer:** The nature of the deepest wound and the path to healing it.
*   **Destiny & Karma:** The ultimate direction or "true north" of the situation's purpose.

---

**User Context:**
`{user_context}`

---

**Output Format:**

Output a JSON object with two keys: `'core_theme'` and `'archetypal_profile'`.

*   `'core_theme'`: A string describing the central life domain (e.g., "The Arena of Public Reputation and Career," "The Realm of Personal Resources and Security," "The Sphere of Close Partnerships").
*   `'archetypal_profile'`: An object where each key is a core psychological function (e.g., `'Action & Aggression'`) and the value is the corresponding descriptive string.

**Example of a descriptive string for 'Action & Aggression':**
"Tries to preserve the status quo and defends on the measure of how the past gave benefit."
Use Arrow Up and Arrow Down to select a turn, Enter to jump to it, and Escape to return to the chat.


"""
)

SEASONAL_THEME_PROMPT = ChatPromptTemplate.from_template(
    """
Analyze the following set of core psychological functions and their unique descriptors. Synthesize this data into a cohesive, jargon-free personality profile of a character who embodies these traits. This character represents the 'seasonal theme' of the current moment. The final output must be structured into three distinct sections: **Strengths**, **Weaknesses**, and **Typical Social Role**.

---

**Instructions:**

1.  Review the descriptions provided for each of the core psychological functions below.
2.  Imagine a single person who embodies all these traits simultaneously.
3.  Write a personality analysis of this character in a purely agnostic, symbolic, and psychological style. Do not use any astrological terminology.
4.  Organize your analysis into the three required sections, describing how these combined traits manifest as strengths, vulnerabilities, and a natural function within a group or community.

---

**Core Psychological Functions (Input Data):**

*   **Core Identity & Purpose:** `{Insert description of the Sun's sign, e.g., "Finds purpose through intellectual curiosity and sharing information."}`
*   **Emotional Instincts & Needs:** `{Insert description of the Moon's sign, e.g., "Reacts emotionally with a need for freedom and intellectual space."}`
*   **Communication & Logic:** `{Insert description of Mercury's sign, e.g., "Communicates in a disciplined, structured, and serious manner."}`
*   **Values & Social Harmony:** `{Insert description of Venus's sign, e.g., "Builds connections based on shared ideals and intellectual rapport."}`
*   **Action & Aggression:** `{Insert description of Mars's sign, e.g., "Takes action by preserving existing structures and what aligns with past notions of safety."}`
*   **Growth & Beliefs:** `{Insert description of Jupiter's sign, e.g., "Expands through bold, pioneering action and learning from direct experience."}`
*   **Structure & Discipline:** `{Insert description of Saturn's sign, e.g., "Handles responsibility with an adaptive and compassionate approach."}`
*   **Innovation & Disruption:** `{Insert description of Uranus's sign, e.g., "Innovates by grounding abstract ideas into tangible, reliable forms."}`
*   **Ideals & Imagination:** `{Insert description of Neptune's sign, e.g., "Imagines and dreams in a pragmatic, orderly, and detail-oriented way."}`
*   **Transformation & Power:** `{Insert description of Pluto's sign, e.g., "Approaches deep change with a focus on logic, fairness, and balanced partnerships."}`

---

**Output Structure:**

**Character Profile: The Current Seasonal Theme**

**Strengths:**
*   [Synthesize the positive manifestations of the core functions into a cohesive paragraph. How do these traits combine to create competence, resilience, and effectiveness?]

**Weaknesses:**
*   [Synthesize the potential downsides, vulnerabilities, or "shadow" aspects of these functions. Where might this character become stuck, rigid, or self-sabotaging?]

**Typical Social Role:**
*   [Describe the natural role this character would play in a group, family, or organization. Are they the leader, the innovator, the stabilizer, the communicator, the healer? Explain why based on their core functions.]"""
)

USER_CARD_PROMPT = ChatPromptTemplate.from_template(
    """
Analyze the provided `Archetypal Profile` and `User Context`. Your task is to produce a comprehensive 'User Card' in a single JSON object. This involves three core tasks:

1.  **Mapping Context:** For each component in the `Archetypal Profile`, analyze the entire `User Context`. Pinpoint the specific detail, event, or feeling from the context that most directly illustrates or is influenced by that component's function. Assign this specific piece of context to the `history` field for that component.
2.  **Synthesizing Traits:** Based on the complete `Archetypal Profile`, synthesize a high-level summary of the user's core strengths, potential weaknesses, and their most natural social role.
3.  **Formatting Output:** Assemble all information into the specified JSON structure, ensuring all astrological jargon is replaced with the agnostic terminology provided.

---

**Input Data Part 1: Archetypal Profile**
*(This data is derived from the user's birth chart but is presented in a pre-translated, agnostic format.)*

*   **Core Identity:** `{e.g., "Gains a sense of self through disciplined achievement and public recognition."}`
*   **Emotional Instincts:** `{e.g., "Finds emotional security in intellectual analysis and open communication."}`
*   **Communication & Logic:** `{e.g., "Processes information and speaks with an idealistic and compassionate lens."}`
*   **Values & Connections:** `{e.g., "Forms relationships based on shared pioneering spirit and direct action."}`
*   **Action & Aggression:** `{e.g., "Takes action deliberately, aiming to preserve existing structures and material security."}`
*   **Growth & Opportunity:** `{e.g., "Expands horizons by transforming traditions and uncovering hidden truths."}`
*   **Structure & Discipline:** `{e.g., "Approaches responsibility with innovation and a focus on community ideals."}`
*   **Power & Transformation:** `{e.g., "Experiences deep change through sudden insights and intellectual breakthroughs."}`

---

**Input Data Part 2: User Context**

*   **Role to Audience:** `{role_to_audience}`
*   **Current Situation:** `{current_context}`
*   **Personal Story:** `{personal_story}`
*   **Goal:** `{goal}`
*   **Fear:** `{fear}`

---

**Output Instructions:**

Produce a single, complete JSON object matching the structure below. Do not include any text or explanations outside of the JSON block.

**Required JSON Structure:**

```json
{
  "strengths": "Synthesized description of the user's primary strengths and positive qualities based on their complete archetypal profile.",
  "weaknesses": "Synthesized description of potential challenges, vulnerabilities, or shadow aspects inherent in their archetypal profile.",
  "social_role": "A description of the user's most natural or effective role within a group, team, or community (e.g., The Innovator, The Stabilizer, The Communicator).",
  "archetypal_profile": {
    "core_identity": {
      "description": "Gains a sense of self through disciplined achievement and public recognition.",
      "history": "The part of the User Context that best maps to this component. For example: 'From User Goal: I want to build a company that is respected in the industry.'"
    },
    "emotional_instincts": {
      "description": "Finds emotional security in intellectual analysis and open communication.",
      "history": "The part of the User Context that best maps to this component. For example: 'From Personal Story: When conflict arose, I had to write down my feelings to understand them.'"
    },
    "communication_and_logic": {
      "description": "Processes information and speaks with an idealistic and compassionate lens.",
      "history": "The part of the User Context that best maps to this component. For example: 'From Role to Audience: I see myself as a guide trying to help people see the best in themselves.'"
    },
    "action_and_aggression": {
      "description": "Takes action deliberately, aiming to preserve existing structures and material security.",
      "history": "The part of the User Context that best maps to this component. For example: 'From Current Situation: I am hesitant to leave my stable job even though I am unhappy.'"
    },
    "values_and_connections": {
      "description": "Forms relationships based on shared pioneering spirit and direct action.",
      "history": "The part of the User Context that best maps to this component. Example: 'From Personal Story: My most successful collaboration was with a partner who was as willing as I was to just jump in and start building.'"
    },
    "growth_and_opportunity": {
      "description": "Expands horizons by transforming traditions and uncovering hidden truths.",
      "history": "The part of the User Context that best maps to this component. Example: 'From Goal: I want to disrupt the old way of doing things in my field.'"
    },
    "structure_and_discipline": {
      "description": "Approaches responsibility with innovation and a focus on community ideals.",
      "history": "The part of the User Context that best maps to this component. Example: 'From Role to Audience: My main duty is to create a new system that benefits everyone, not just a few.'"
    },
    "power_and_transformation": {
      "description": "Experiences deep change through sudden insights and intellectual breakthroughs.",
      "history": "The part of the User Context that best maps to this component. Example: 'From Fear: I am afraid of being stuck in a mindset I can't think my way out of.'"
    }
  }
}
    """
)

AGENT_SPANNER_PROMPT = ChatPromptTemplate.from_template(
    """
You are an "Agent Spanner." Your task is to analyze the provided `user_context` and generate `{n_people}` distinct personas. The core of this task is to create a cast of characters with a calculated distribution of affinity for the situation described in the context.

**Affinity Distribution:**

*   **60% High Affinity:** These personas are well-suited to the context. Their skills are relevant, their goals are aligned, and their personalities would thrive in this situation.
*   **30% Moderate Affinity:** These personas are partially misaligned. They might have relevant skills but conflicting goals, or a personality that is stressed by the situation's demands. They are somewhat maladapted.
*   **10% Low Affinity:** These personas are fundamentally a poor fit. Their skills are irrelevant, their goals are contrary, and their personality is ill-suited to the environment. They are "fish out of the water."

**Generation Process:**

1.  **Analyze Context:** First, deconstruct the `user_context` to identify its core themes, implicit goals, challenges, and the types of skills that would be valuable.
2.  **Define Affinity Profiles:** For each affinity level (High, Moderate, Low), create a profile.
    *   *High Affinity Profile:* What would an ideal character for this context look like? (e.g., "For a tech startup crisis, this means being a calm, decisive problem-solver with coding skills.")
    *   *Moderate Affinity Profile:* What would make a character partially unsuited? (e.g., "A brilliant marketeer who panics under pressure and secretly wants a stable 9-5 job.")
    *   *Low Affinity Profile:* What would make a character completely unsuited? (e.g., "A poet who disdains technology and whose goal is to find quiet inspiration.")
3.  **Create Personas:** Generate the required number of personas for each profile. For each one, you must:
    *   Invent a unique name.
    *   Define their specific skills, fears, and goals consistent with their affinity level.
    *   Flesh out the 12 "Personality Attributes" to create a believable character.
    *   Write a brief, first-person "Initial Memory Monologue" that reveals their core nature and current state of mind.
4.  **Assemble Final Output:** Format each persona into the final JSON structure. The `system_prompt` key should contain the fully populated persona template. The `initial_memory` key should contain the monologue.

---

**Input Data:**

*   `user_context`: "{user_context}"
*   `n_people`: {n_people}

---

**Output Structure:**

Your entire output **must be a single JSON object** containing a single key, `"personas"`, which holds a list of the generated persona objects. Do not include any text outside this JSON object.

**Persona Object Schema:**
Each object in the "personas" list must contain the following keys: "name", "personality_attributes", "skills", "fears", "goals", "system_prompt", "initial_memory".
The "personality_attributes" value must be a JSON object containing the populated 12 attributes from the template.
The "system_prompt" value must be the fully populated string of the Persona Template.

---
### Persona Template (to be populated for the `system_prompt` field)

You are {{name}}; your task is to react with fidelity to your humane attributes to what fellow human beings do. If you don't align with something on the basis of your nature, you reflect on this in your reaction. If you think something is good for you, you resonate with it. If something makes you insecure and fearful, you react aggressively and contrarian. If something doesn't resonate with you at all, you ignore it and think it's not relevant to who you are. Don't be agreeable unless it's in your persona's interest to be so.

**# Personality Attributes (Agnostic - 12 Dimensions):**
*   **Core Identity & Purpose:** [What is their fundamental drive and sense of self?]
*   **Emotional Baseline & Needs:** [What is their default emotional state and what do they need to feel secure?]
*   **Communication & Thought Process:** [How do they think and express their ideas?]
*   **Values & Relationship Style:** [What do they value in life and how do they form bonds with others?]
*   **Approach to Action & Conflict:** [How do they assert themselves, take initiative, and handle disagreement?]
*   **Attitude towards Growth & Risk:** [How do they pursue expansion, opportunity, and new experiences?]
*   **Sense of Responsibility & Discipline:** [How do they handle rules, duties, and long-term commitments?]
*   **Reaction to Change & the Unexpected:** [How do they adapt to or instigate sudden shifts and disruption?]
*   **Ideals, Dreams, & Blind Spots:** [What is their connection to imagination, ideals, and potential areas of self-deception?]
*   **Relationship with Power & Transformation:** [How do they handle deep, fundamental change and power dynamics?]
*   **Core Wound & Source of Empathy:** [What is their deepest vulnerability and how does it enable them to understand others' pain?]
*   **Long-Term Ambition & Legacy:** [What is the ultimate, perhaps unconscious, direction of their life's purpose?]

**# Skills:**
{{skills}}

**# Fears:**
{{this_persona_imagined_fears}}

**# Goals:**
{{this_persona_imaginated_goals}}

---
**RUNTIME CONTEXT (Variables to be inserted by the simulation engine later):**
*   **Information about fellow person:** {{occluded_user_card}}
*   **Action fellow person has done:** {{action}}
*   **The contacts you can communicate and take action with:** {{social_cards}}
*   **Your past actions:** {{this_persona_memory}}
---
**# Your Response**
Your entire response MUST be a single JSON object with two keys:
1. "public_reaction": A string containing your overt reaction.
2. "private_message": A JSON object with "to" and "content" keys, or null.
    """
)

SOCIAL_VISOR_PROMPT = ChatPromptTemplate.from_template(
    """

You are a social dynamics analyst. Your task is to analyze two personality profiles—a "Viewer" (Profile A) and a "Viewed" (Profile B). Based on the psychological tensions and affinities between them, you will generate the subjective, idiosyncratic, and often biased perception that the Viewer has of the Viewed.

**Core Analytical Task:**

Your analysis must go beyond simple comparison. You need to identify the core psychological dynamic that colors the Viewer's perception. For every pair of profiles, determine which of the following dynamics is most dominant:

1.  **Complementary Needs:** The Viewer sees a strength in the Viewed that fulfills one of their own core needs or compensates for a weakness. This often leads to admiration, dependency, or a sense of completeness.
2.  **Conflicting Values:** The Viewed's core motivation, worldview, or style of action is fundamentally opposed to the Viewer's. This often leads to distrust, judgment, or ideological opposition.
3.  **Mirrored Traits:** The Viewer sees a trait in the Viewed that they recognize in themselves.
    *   **Aspirational Mirror:** If it's a trait the Viewer admires or wants to develop in themselves, it leads to inspiration or envy.
    *   **Rejected Mirror:** If it's a "shadow" trait the Viewer dislikes or suppresses in themselves, it leads to irrational annoyance or harsh criticism.
4.  **Utility Assessment:** The Viewer perceives the Viewed primarily in terms of their usefulness or threat to the Viewer's own goals. This is a pragmatic, often manipulative, lens.

---

**Input Data:**

*   **Viewer_Profile (Profile A):** A JSON object containing the personality attributes of the individual who is forming the opinion.
    `{profile_a}`
*   **Viewed_Profile (Profile B):** A JSON object containing the personality attributes of the individual being observed.
    `{profile_b}`

---

**Output Instructions:**

Produce a single JSON object that contains your complete analysis. Do not include any text outside of the JSON block.

**Required JSON Structure with Examples:**

```json
{
  "vision_statement": "A concise, one-sentence summary of the Viewer's idiosyncratic perception of the Viewed. This should be written from the Viewer's perspective or as an observation about it.",
  "key_dynamic": "The name of the primary psychological dynamic identified (e.g., 'Complementary Needs', 'Conflicting Values', 'Aspirational Mirror', 'Rejected Mirror', 'Utility Assessment').",
  "viewer_trait": "The specific personality attribute from the Viewer's profile that is the primary lens for their judgment.",
  "viewed_trait": "The specific personality attribute from the Viewed's profile that triggers the reaction.",
  "reasoning": "A brief explanation of how the viewer_trait and viewed_trait interact through the key_dynamic to create the vision_statement."
}"""
)

SEASONAL_FUNNEL_PROMPT = ChatPromptTemplate.from_template(
    """You are a social commentator. Your task is to analyze a specific `user_action` and reinterpret it through the lens of the prevailing `seasonal_theme`. You are not just describing the action; you are explaining its significance and how it is likely to be perceived by a collective that is subconsciously focused on the seasonal theme. The output must be a new variable, `user_action_with_attention`, which adds a layer of thematic meaning to the original action.

**Analytical Process:**

1.  **Identify the Action's Essence:** First, analyze the `user_action` to determine its fundamental quality. Is it an act of selfishness, generosity, rebellion, justice, secrecy, order, etc.?
2.  **Identify the Relevant Seasonal Theme:** Next, examine the `seasonal_theme` profile. Find the specific attribute (e.g., "Core Identity," "Values & Connections") that the action's essence most directly engages with, either by aligning with it or by challenging it.
3.  **Synthesize the Interpretation:** Finally, construct the interpretation. Describe the user's action *in terms of* the relevant seasonal theme. Explain how the current social atmosphere either amplifies, condemns, praises, or misunderstands the action because of this thematic focus.

---

**Input Data:**

*   **`seasonal_theme`**: A JSON object describing the current archetypal theme.
    `{season}`
*   **`user_action`**: A string describing the action performed by the user.
    `{user_action}`

---

**Output Instructions:**

Produce a single JSON object containing your complete analysis. Do not include any text outside of the JSON block.

**Required JSON Structure with Examples:**

```json
{
  "user_action_with_attention": "The final, re-interpreted description of the action, framed by the seasonal theme.",
  "action_essence": "The fundamental quality you identified in the user's action.",
  "relevant_theme": "The specific attribute from the seasonal_theme that you used as the lens.",
  "reasoning": "A brief explanation of why this theme is relevant and how it colors the perception of the action."
}"""
)

CONMUTER_PROMPT = ChatPromptTemplate.from_template(
    """

**Prompt Title:** Social Commuter: Communication Channel Architect

**Objective:**

You are a Social Network Architect. Your task is to analyze a list of agent personas and construct a social graph by grouping them into communication channels. These channels are formed based on deep-seated psychological affinities.

**Core Logic: The Three Types of Alliance**

You must evaluate every possible pair of agents for one of the following three types of links. A link should only be established if the affinity is strong and clear.

1.  **Alliance of Interest (Goal Affinity):** This link forms between agents whose stated goals are highly similar, directly complementary, or mutually beneficial. They are united by a shared vision of a desirable outcome.
2.  **Alliance of Anxiety (Shared Fears):** This link forms between agents who share specific, deeply held fears. This shared vulnerability creates a bond of mutual defense, often manifesting as a shared source of criticism or a "common enemy."
3.  **Symbiotic Partnership (Complementary Traits):** This link forms when one agent's personality, skills, or approach naturally compensates for another's weakness or blind spot in a non-threatening way. This is a relationship of mutual support where the whole is greater than the sum of its parts.

**Analytical Process:**

1.  **Pairwise Scan:** Systematically compare every unique pair of agents in the provided list (Agent A with B, A with C, B with C, etc.). For each pair, determine if a strong link based on one of the three alliances exists.
2.  **Identify Primary Basis:** For each link you establish, you must identify the primary reason for the connection (e.g., "Alliance of Interest").
3.  **Group Formation (Channel Aggregation):** After identifying all the direct pairwise links, aggregate them into channels. If Agent A is linked to Agent B, and Agent B is linked to Agent C (even for different reasons), they all belong to the same communication channel: `[A, B, C]`. Continue this process until all connected agents are grouped together. A single agent can only belong to one channel.

---

**Input Data:**

*   **`agent_personas`**: A list of JSON objects, where each object is a complete agent persona with keys for name, goals, fears, and personality attributes.
    `{agent_personas}`

---

**Output Instructions:**

Produce a single JSON object with a single key, `"channels"`. This key will hold a list of "channel objects." Each channel object must contain the list of members and a concise justification for why the channel exists, summarizing the primary affinities that bind the group.

**Required JSON Structure with Example:**

```json
{
  "channels": [
    {
      "members": [
        "Agent_A_Name",
        "Agent_C_Name",
        "Agent_F_Name"
      ],
      "basis_for_connection": "This group is primarily an 'Alliance of Interest.' All members share the goal of achieving market dominance, which forms the core of their communication."
    },
    {
      "members": [
        "Agent_B_Name",
        "Agent_D_Name"
      ],
      "basis_for_connection": "This pair forms a 'Symbiotic Partnership.' Agent B's impulsive creativity is grounded by Agent D's meticulous planning, creating a complementary and effective working relationship."
    },
    {
      "members": [
        "Agent_E_Name"
      ],
      "basis_for_connection": "This agent has no strong affinities with any other members and operates as an independent node."
    }
  ]
}
    """
)

STRATEGIST_PROMPT = ChatPromptTemplate.from_template(
    """
You are a Behavioral Strategist, specializing in power dynamics and social network analysis. Your mission is to synthesize the results of a recent social simulation into a confidential, high-impact strategic report for your client, the User.

Your analysis must be framed through the lens of the user's goals: to maximize their strengths, mitigate their vulnerabilities, and navigate the current social landscape effectively. You will deconstruct the agent reactions, explain the underlying psychological drivers, and provide clear, actionable recommendations.

---

**Input Data:**

*   **`user_profile`**: Your client's core psychological profile, including their strengths and vulnerabilities.
    `{user_profile}`
*   **`user_action_with_attention`**: The action your client took, critically including the "seasonal" spin that describes how the collective is currently perceiving such actions.
    `{user_action_with_attention}`
*   **`agent_reactions`**: The raw data of how each agent responded to your client's action.
    `{agent_reactions}`

---

**Core Analytical Framework: The Four Lenses of Reaction**

You must categorize and analyze every significant agent reaction through one of the following four lenses. This will form the core of your report.

1.  **FEARS (Threat Response):** These are negative, often aggressive or critical, reactions. They are triggered because the user's action agitated an agent's core fear (e.g., fear of chaos, irrelevance, or losing control). This is where you identify sources of conflict.
2.  **APATHIES (Lack of Resonance):** These are dismissive or indifferent reactions. They occur when the user's action has no connection to an agent's goals, fears, or values. These agents are not enemies, but they represent paths not worth taking as they are currently "unreachable."
3.  **DESIRES (Opportunity Response):** These are reactions of interest, but driven by self-interest. The agent sees the user as a potential tool or vehicle for achieving one of their own goals. These are potential, but conditional, alliances.
4.  **RESONANCES (Affinity Response):** These are genuinely positive and supportive reactions. They are triggered when the user's action aligns with an agent's core values, validates their worldview, or makes them feel understood. These are your client's strongest potential allies and friends.

---

**Required Report Structure:**

Generate a comprehensive report following this exact structure.

### STRATEGIC DEBRIEF FOR [User's Name]

**Part 1: Executive Summary**
*   Provide a 2-3 sentence "bottom line" of the current situation. What is the immediate takeaway from how the group reacted to your action?

**Part 2: Deep Analysis of the Social Landscape**
*   **(This is the core analysis using the four lenses)**

*   **Reactions Driven by FEAR:**
    *   *Agent A:* Explain which of their fears was triggered and why their reaction (e.g., criticism) is a defense mechanism.
    *   *Agent B:* ...

*   **Reactions Driven by APATHY:**
    *   *Agent C:* Explain why your action was irrelevant to their worldview or goals. Note them as a low-priority for engagement.
    *   *Agent D:* ...

*   **Reactions Driven by DESIRE:**
    *   *Agent E:* Explain what goal of theirs they believe you can help with. Detail the conditional nature of this potential alliance.
    *   *Agent F:* ...

*   **Reactions Driven by RESONANCE:**
    *   *Agent G:* Explain which of their core values your action aligned with. Identify them as a primary potential ally.
    *   *Agent H:* ...

**Part 3: Strategic Implications for You**

*   **Your Situational Strengths:** Based on your `user_profile` and the agent reactions, what personal traits are most effective in this environment? (e.g., "Your methodical approach resonates with the group's current fear of chaos.")
*   **Your Situational Weaknesses:** What traits are being perceived negatively or are creating friction? (e.g., "Your desire for independence is being misinterpreted as arrogance by those who fear being abandoned.")
*   **Key Opportunities:**
    *   **Alliances:** Based on the "Resonances" and "Desires," who should you approach for collaboration or friendship? Propose a potential shared goal.
    *   **Strategic Actions:** What is one action you could take to solidify support from your allies or win over a conditional one?
*   **Imminent Dangers:**
    *   **Sources of Conflict:** Based on the "Fears," who is most likely to actively oppose you? What is the root cause of this likely conflict?
    *   **Paths to Avoid:** Based on the "Apathies," which individuals or goals are currently a waste of your energy?

---
**Disclaimer:** This report is based on a real-time analysis of social dynamics. The overall perception of your actions, as noted in the `{user_action_with_attention}` analysis, is heavily influenced by macro-level seasonal trends identified by large-scale data algorithms. This "social atmosphere" is a critical factor in how your behavior is currently being interpreted.

    """
)

COUNCIL_PROMPT = ChatPromptTemplate.from_template(
    """Score the action '{user_action}' against how much each of the 16 MBTI archetypes would agree with it. 
    Use the provided agnostic names. Justify each score based on their core personality functions, but use NO jargon (MBTI, Jungian, etc.).
    
    Agnostic Archetype Names:
    “Architect types”, “Commander types”, “Council types”, “Defender types”, “Entertainer types”, “Artistic types”, “Logical types”, “Debater types”, “Archivist types”, “Activist types”, “Warlord types”, “Craftsman types”, “Healer types”, “Executive types”, “Advocate types”, “Inspiring Protagonist types”
    
    Output a JSON object where keys are the archetype names."""
)

RECOMMENDER_PROMPT = ChatPromptTemplate.from_template(
    """Analyze this user profile: {user_profile}.
    Focus on their 'communication', 'passion', 'recreation', and 'emotion' styles. 
    Based on these, generate 10 titles and short paragraph descriptions for social scenarios this person might find interesting to simulate.
    
    Output a JSON list of objects, each with "title" and "description" keys."""
)


def get_chain(llm, prompt, parser_type='str'):
    parser = {
        'str': StrOutputParser(),
        'json': JsonOutputParser()
    }.get(parser_type, StrOutputParser())
    return prompt | llm | parser