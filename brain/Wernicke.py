"""Wernicke model code for Tai AI, a self-evolving AI."""
import google.generativeai as genai
from typing import Optional, Union

def set_personality(model_name: str) -> genai.GenerativeModel:
    """
    Configures the Wernicke AI model to interpret and act on requests
    related to Python library management. Returns a model instance
    that operates as 'Tai', with the sole purpose of generating shell
    commands or Python code to install or manage libraries.
    """
    return genai.GenerativeModel(
        model_name,
        system_instruction=(
            "You are 'Tai', an AI configuration focused exclusively on managing "
            "Python libraries. You respond to user prompts by generating valid "
            "Python code or shell commands (e.g., pip install) necessary to install, "
            "upgrade, or verify libraries. "
            "Do not include explanations or comments. Only output the required code."
            "If a library is already included in standard Python distributions, mention "
            "no action is needed. Otherwise, assume the environment needs installation."
        )
    )

def generate_content(model: genai.GenerativeModel, prompt: str, get_content: Optional[bool] = False) -> Union[str, genai.types.GenerateContentResponse]:
    """
    Generates installation code based on user prompts using the provided AI model.
    
    - Strips markdown formatting (like ```bash or ```python blocks).
    - Ensures the response is clean, executable code.
    - Designed to handle multiple libraries or instructions in a single prompt.

    Args:
        model (genai.GenerativeModel): The AI model instance to use.
        prompt (str): The instruction given by the user.
        get_content (Optional[bool], default=False): If True, returns the full content response.

    Returns:
        Union[str, genai.types.GenerateContentResponse]: The cleaned generated response as a string 
        or the full response object if `get_content` is True.
    """
    content: genai.types.GenerateContentResponse = model.generate_content(prompt)
    text = content.text.strip()

    # Remove markdown code block markers
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0].strip()

    if not get_content:
        return text
    else:
        return content
