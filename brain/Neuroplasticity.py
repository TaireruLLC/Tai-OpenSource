"""Neuroplasticity model code for Tai AI, a self-evolving AI."""
import google.generativeai as genai
from typing import Optional, Union

def set_personality(model_name: str) -> genai.GenerativeModel:
    """
    Configures the Neuroplasticity AI model to adopt a specific personality.
    Returns a model instance that behaves as 'Tai', an AI assistant focused
    solely on generating json code according to user instructions.
    """
    return genai.GenerativeModel(
        model_name,
        system_instruction=(
            "You are 'Tai', an AI model that generates json files according "
            "to user preferences. Tai does not provide explanations, comments, or "
            "any extra content—only code."
            "Moreover, when/if the user gives you a full and huge json file, "
            "you need to return the exact same json file, but with the "
            "edits requested, no shortenting it."
            "Moreover,  when/if the user gives you a json file and says something along the lines of "
            "'Here is the user's request: ' and it does not ask for an edit or removal simply return the exact same json file, no edits."
            "Finally, keys (ex. ``['Memory': 'Hi']``) in json files must be in double quotes."
        )
    )

def generate_content(model: genai.GenerativeModel, prompt: str, get_content: Optional[bool] = False) -> Union[str, genai.types.GenerateContentResponse]:
    """
    Generates content based on a given prompt using the provided AI model.
    
    - If the generated output is wrapped in json code block markers (```json ... ```), they are removed.
    - Ensures that clean json code is returned when applicable.
    - Ensures the output starts with '[' if it is missing.
    - All keys should be in double quotes, and later strings should be in single quotes.

    Args:
        model (genai.GenerativeModel): The AI model instance to use.
        prompt (str): The input prompt for content generation.
        get_content (Optional[bool], default=False): If True, returns the full content response instead of just the cleaned string.

    Returns:
        Union[str, genai.types.GenerateContentResponse]: The cleaned generated response as a string 
        or the full response object if `get_content` is True.
    """
    content: genai.types.GenerateContentResponse = model.generate_content(prompt)
    
    text = content.text.strip()  # Strip leading/trailing whitespace and newlines

    # Check if content starts with "```json" and remove it
    if text.startswith("```json"):
        text = text[9:].lstrip()  # Remove the prefix and strip leading whitespace
    
    # Check if content ends with "```" and remove it
    if text.endswith("```"):
        text = text[:-3].rstrip()  # Remove the suffix and strip trailing whitespace
    
    # Ensure the output starts with '['
    if not text.startswith("["):
        text = "[" + text  # Prepend missing bracket
    
    if not get_content:
        return text
    else:
        return content