"""Historian Configuration code for Tai AI, a self-evolving AI."""

# === Imports ===
import json
from datetime import datetime
from typing import Optional, Union
import google.generativeai as genai

from brain.gitbase_launcher import data_system, KeyValue, NotificationManager

# === Model Configuration ===

def set_personality(model_name: str) -> genai.GenerativeModel:
    """
    Configures the Historian AI model to adopt the 'Tai' personality.

    Returns a model instance that:
    - Only generates JSON files according to user instructions.
    - Returns the exact file with applied edits if a full JSON is provided.
    - Does not explain or shorten the JSON.
    - Only returns unchanged input if no edits are requested.
    - Ensures all keys are double-quoted.
    """
    return genai.GenerativeModel(
        model_name,
        system_instruction=(
            "You are 'Tai', an AI model that generates json files according to user preferences. "
            "Tai does not provide explanations, comments, or any extra content—only code. "
            "If given a large JSON file with edit instructions, return the exact file with only those edits. "
            "If no edits are requested, return the file unchanged. "
            "Ensure all keys in the JSON files use double quotes."
        )
    )

# === Content Generation ===

def generate_content(model: genai.GenerativeModel, prompt: str, get_content: Optional[bool] = False) -> Union[str, genai.types.GenerateContentResponse]:
    """
    Generates content from the AI model using a prompt.

    - Cleans formatting by removing code block markers.
    - Ensures the output is valid JSON, starting with a '['.
    """
    content = model.generate_content(prompt)
    text = content.text.strip()

    if text.startswith("```json"):
        text = text[9:].lstrip()
    if text.endswith("```"):
        text = text[:-3].rstrip()
    if not text.startswith("["):
        text = "[" + text

    return content if get_content else text

# === Memory Handling ===

def get_current_restricted_memory_file() -> str:
    """Returns a timestamped filename for restricted session-based memory."""
    timestamp = datetime.now().strftime("%Y-%m-%d")
    return f"restricted_memory_{timestamp}"

def load_memory(IS_ENCRYPTED: bool, memory_type: str = "global") -> list:
    """
    Loads memory data based on type ('global' or 'restricted').

    Returns a list of memory entries. If no restricted memory is found, creates a template.
    """
    memory_file = "global_memory" if memory_type == "global" else get_current_restricted_memory_file()
    found_restricted = False

    NotificationManager.hide()
    all_keys = data_system.get_all(encryption=IS_ENCRYPTED, path="taiMem").keys()
    NotificationManager.show()

    if memory_type == "restricted":
        found_restricted = any(key == memory_file and key.startswith("restricted_memory_") for key in all_keys)

    try:
        NotificationManager.hide()
        if not found_restricted and memory_type == "restricted":
            template = [
                {
                    "timestamp": "2025-03-03 12:16:13",
                    "Memory": "Template memory, text goes here."
                }
            ]
            data_system.save_data(key=memory_file, value=template, path="taiMem", encryption=IS_ENCRYPTED)

        loaded_memory = data_system.load_data(key=memory_file, path="taiMem", encryption=IS_ENCRYPTED)
        NotificationManager.show()
        return json.loads(json.dumps(loaded_memory.value))  # Ensure conversion to Python object
    except json.JSONDecodeError:
        NotificationManager.show()
        return []

def save_memory_backend(temp_mem: str, glob: str, IS_ENCRYPTED: bool, memory_type: str):
    """
    Saves memory entries into global or restricted memory.

    Ensures entries are not duplicated based on timestamp.
    """
    assert memory_type in ['global', 'restricted'], "Invalid memory type. Use 'global' or 'restricted'."
    memory_file = "global_memory" if memory_type == 'global' else get_current_restricted_memory_file()

    memory = load_memory(IS_ENCRYPTED, memory_type)
    if isinstance(memory, str):
        memory = json.loads(memory)
    new_entries = json.loads(temp_mem if memory_type == 'restricted' else glob)
    existing_timestamps = {entry["timestamp"] for entry in memory}
    unique_new_entries = [entry for entry in new_entries if entry["timestamp"] not in existing_timestamps]
    memory.extend(unique_new_entries)

    NotificationManager.hide()
    data_system.save_data(key=memory_file, value=memory, path="taiMem", encryption=IS_ENCRYPTED)
    NotificationManager.show()

def update_memory(IS_ENCRYPTED: bool, historian_model: genai.GenerativeModel, user_input: str):
    """
    Updates the global memory with user input and AI response.

    This function loads the current global memory and generates a prompt to update
    it based on user input. It uses a memory template and the current timestamp to
    create a structured prompt for generating the updated memory content. The 
    updated memory is parsed and stored globally if it is valid JSON.

    Args:
        user_input (str): The user's input to be integrated into global memory.

    Raises:
        json.JSONDecodeError: If the generated content cannot be parsed as JSON.
    """
    global glob
    """Add user input and AI response to global memory correctly."""
    
    global_memory = load_memory(IS_ENCRYPTED, "global")
    NotificationManager.hide()
    mem_template = data_system.load_data(key="memplate", encryption=False, path="memplate").value
    NotificationManager.show()
    
    prompt = f"""# Here is the global memory JSON code: 
{json.dumps(global_memory, indent=4)}
# The user requested this:
{user_input}
# Here is a memory template:
{mem_template}
# Here is the current timestamp:
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# Return an updated JSON file reflecting any additions/removals as per user request.
    """
    
    new_memory = generate_content(historian_model, prompt)
    
    try:
        new_memory = json.loads(new_memory)  # Ensure valid JSON before saving
        glob = new_memory  # Store properly formatted JSON
    except json.JSONDecodeError:
        pass  # Ignore faulty memory update requests

def save_memory(temp_mem, glob, IS_ENCRYPTED):
    """
    Saves both restricted and global memory to the data system in a separate thread
    to prevent blocking the main thread and causing UI lag. This function is
    intended to be run in a separate thread to avoid blocking the main thread.
    """
    save_memory_backend(temp_mem, glob, IS_ENCRYPTED, 'restricted')
    save_memory_backend(temp_mem, glob, IS_ENCRYPTED, 'global')

# === Memory Formatting ===

def format_memory(memory: KeyValue, memory_type: str) -> str:
    """
    Formats memory data into a readable string format for display.

    Returns formatted past interactions or a placeholder message.
    """
    if not memory:
        return "No past interactions found." if memory_type == "global" else "No previous discussion in this conversation."

    try:
        if memory_type == "global":
            return "\n".join(f'{entry["timestamp"]}: {entry.get("Memory", "N/A")}' for entry in memory)
    except Exception as e:
        return f"Error formatting memory: {e}"

    print("2")
    return "\n".join(
        f'[User: {entry.get("User", "N/A")}\nTai: {entry.get("Tai", "N/A")}\n | Timestamp: {entry["timestamp"]}]'
        for entry in memory
    )
