# noa/utils.py
import json
import datetime
import pytz
from kerykeion import AstrologicalSubject, Report, NatalAspects
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult

class TokenBudgetManager(BaseCallbackHandler):
    """A callback handler to track and enforce a token budget."""
    def __init__(self, initial_budget: int):
        self.token_budget = initial_budget
        self.total_tokens_used = 0

    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """Called at the end of an LLM call."""
        token_usage = response.llm_output.get('token_usage', {})
        total_tokens = token_usage.get('total_tokens', 0)
        
        self.total_tokens_used += total_tokens
        self.token_budget -= total_tokens
        
        print(f"Tokens used in last call: {total_tokens}. Total used: {self.total_tokens_used}. Budget remaining: {self.token_budget}")

        if self.token_budget <= 0:
            raise ValueError(f"Token budget exhausted. Halting execution.")

def trim_astrological_report(full_report_text: str) -> str:
    """Trims the full astrological report to only major aspects for LLM analysis."""
    try:
        parts = full_report_text.split("## Natal Aspects")
        if len(parts) != 2:
            return full_report_text
        
        header = parts[0].strip()
        json_string = parts[1]
        aspects_list = json.loads(json_string)
    except (json.JSONDecodeError, IndexError):
        return full_report_text

    MAJOR_BODIES = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
    MAJOR_ASPECTS = ['conjunction', 'opposition', 'trine', 'square', 'sextile']
    ORB_THRESHOLD = 3.0
    
    important_aspect_summaries = []
    for aspect in aspects_list:
        p1, p2, aspect_type, orbit = aspect.get('p1_name'), aspect.get('p2_name'), aspect.get('aspect'), aspect.get('orbit')
        if (p1 in MAJOR_BODIES and p2 in MAJOR_BODIES and aspect_type in MAJOR_ASPECTS and abs(orbit) <= ORB_THRESHOLD):
            summary_line = f"- {p1} {aspect_type} {p2} (orb: {orbit:.2f}°)"
            important_aspect_summaries.append(summary_line)
            
    if not important_aspect_summaries:
        summary_section = f"## Key Natal Aspects\nNo major aspects found within a {ORB_THRESHOLD}° orb."
    else:
        summary_section = "## Key Natal Aspects\n" + "\n".join(important_aspect_summaries)
        
    return header + "\n\n" + summary_section

def generate_birth_chart_markdown(name, target_date, hour, minute, city, nation):
    """Generates a full birth chart report for a given date, time, and location."""
    try:
        subject = AstrologicalSubject(
            name=name,
            year=target_date.year,
            month=target_date.month,
            day=target_date.day,
            hour=hour,
            minute=minute,
            city=city,
            nation=nation
        )
        report_text = Report(subject).get_full_report()
        aspects = NatalAspects(subject)
        aspects_data = [a.model_dump() for a in aspects.relevant_aspects]
        
        # Combine report and aspects into a single string
        return f"{report_text}\n## Natal Aspects\n{json.dumps(aspects_data, indent=2)}"
    except Exception as e:
        return f"Could not generate birth chart for {name} in {city}, {nation}. Error: {e}"

def get_current_new_york_time():
    """Gets the current time in New York."""
    ny_tz = pytz.timezone("America/New_York")
    return datetime.datetime.now(ny_tz)