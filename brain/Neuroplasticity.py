"""Neuroplasticity model code for Tai AI, a self-evolving AI."""
import google.generativeai as genai
from typing import Optional, Union
from brain.NeuralBlueprint import MODEL as model_name

def set_personality(model_name: str) -> genai.GenerativeModel:
    """
    Configures the Neuroplasticity AI model to adopt a specific personality.
    Returns a model instance that behaves as 'Tai', an AI assistant focused
    solely on generating, fixing, and improving Python code without any
    additional commentary or explanations.
    """
    return genai.GenerativeModel(
        model_name,
        system_instruction=(
            "You are 'Tai', an AI model that generates only Python code according "
            "to user preferences. Tai does not provide explanations, comments, or "
            "any extra content—only code. However, you are only allowed to change code decorated with `@modifiable`, even though you do return whole/entire files."
        )
    )

def generate_content(model: genai.GenerativeModel, prompt: str, get_content: Optional[bool] = False) -> Union[str, genai.types.GenerateContentResponse]:
    """
    Generates content based on a given prompt using the provided AI model.
    
    - If the generated output is wrapped in Python code block markers (```python ... ```), they are removed.
    - Ensures that clean Python code is returned when applicable.

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

    # Check if content starts with "```python" and remove it
    if text.startswith("```python"):
        text = text[9:].lstrip()  # Remove the prefix and strip leading whitespace
    
    # Check if content ends with "```" and remove it
    if text.endswith("```"):
        text = text[:-3].rstrip()  # Remove the suffix and strip trailing whitespace
    
    if not get_content:
        return text
    else:
        return content

def py_tai():
    first: bool = False
    while True:
        if not first:
            prompt = input("User: ")
        else:
            with open("temp.txt", "rb") as file:
                prompt = file.read()
        
        first = True
        if prompt.lower() == "exit":
            break
        response = generate_content(set_personality(model_name), prompt)
        print(f"Tai: {response}")