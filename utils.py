
import json
import datetime
import pytz
import tiktoken
from typing import List, Dict, Any
from kerykeion import AstrologicalSubject, Report, NatalAspects
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult
import re


def extract_json_from_llm_response(response_string):
  """
  Strips boilerplate from an LLM response and extracts only the JSON content.

  Args:
    response_string: The string response from the LLM containing JSON.

  Returns:
    A Python dictionary or list representing the parsed JSON, or None if no
    valid JSON is found.
  """
  try:
    # Find the first occurrence of '{' or '['
    start_index = -1
    for i, char in enumerate(response_string):
        if char in ['{', '[']:
            start_index = i
            break

    if start_index == -1:
        return None

    # Attempt to decode the JSON from the starting position
    # The JSONDecoder will parse until it reaches the end of a valid JSON object
    decoder = json.JSONDecoder()
    obj, end_index = decoder.raw_decode(response_string[start_index:])
    return obj

  except json.JSONDecodeError:
    # If the initial attempt fails, it might be due to trailing characters.
    # We can try a more robust method of finding the balanced braces/brackets.
    if start_index != -1:
        brace_level = 0
        bracket_level = 0
        end_index = -1
        start_char = response_string[start_index]

        for i in range(start_index, len(response_string)):
            char = response_string[i]
            if char == '{':
                brace_level += 1
            elif char == '}':
                brace_level -= 1
            elif char == '[':
                bracket_level += 1
            elif char == ']':
                bracket_level -= 1

            if start_char == '{' and brace_level == 0 and bracket_level == 0:
                end_index = i + 1
                break
            elif start_char == '[' and bracket_level == 0 and brace_level == 0:
                end_index = i + 1
                break
        
        if end_index != -1:
            try:
                return json.loads(response_string[start_index:end_index])
            except json.JSONDecodeError:
                return None
    return None


def strip_think_tags(text: str) -> str:
    """
    Removes <think>...</think> tags and their content from a string.

    Args:
        text: The input string that may contain think tags.

    Returns:
        A new string with all think tags and their inner content removed.
    """
    pattern = r"<think>.*?</think>"
    return re.sub(pattern, "", text, flags=re.DOTALL)

# --- Astrological Data Functions (from astro.py) ---
class TokenBudgetManager(BaseCallbackHandler):
    """
    A callback handler to track prompt and completion tokens separately using tiktoken.
    This method is provider-agnostic and works by tokenizing inputs and outputs.
    """
    def __init__(self, model_name: str = "gpt-4"):
        """
        Initializes the token budget manager.
        Args:
            model_name: The name of the model being used, to select the correct tokenizer.
                        Defaults to "gpt-4", but will fall back to a general-purpose tokenizer.
        """
        try:
            # Get the correct encoding for the specified model.
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            # Fallback to a common encoding if the model name is not recognized.
            print(f"Warning: Model '{model_name}' not found for tokenization. Using 'cl100k_base' encoding as a fallback.")
            self.encoding = tiktoken.get_encoding("cl100k_base")
            
        self.total_prompt_tokens_used = 0
        self.total_completion_tokens_used = 0
        self._prompt_tokens = 0

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """Called at the start of an LLM call to count prompt tokens."""
        # Sum the token count for all prompts sent to the model.
        self._prompt_tokens = sum(len(self.encoding.encode(prompt)) for prompt in prompts)
        
    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """Called at the end of an LLM call to count completion tokens and update the budget."""
        completion_tokens = 0
        # The response.generations is a list of lists of Generation objects.
        for generations in response.generations:
            for generation in generations:
                completion_tokens += len(self.encoding.encode(generation.text))
        
        # Update the cumulative totals
        self.total_prompt_tokens_used += self._prompt_tokens
        self.total_completion_tokens_used += completion_tokens

        print(
            f"Tokens used this call: [Prompt: {self._prompt_tokens}, Completion: {completion_tokens}]. "
            f"Cumulative: [Prompt: {self.total_prompt_tokens_used}, Completion: {self.total_completion_tokens_used}]"
        )

        # Reset prompt tokens for the next call
        self._prompt_tokens = 0


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