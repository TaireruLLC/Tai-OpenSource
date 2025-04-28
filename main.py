"""Main file for Tai AI, a self-evolving AI."""
# Imports
from brain.config import MODEL
import brain.Dictator as Dictator
import brain.api as api
import brain.Architect as Architect

USE_EXIT: bool = True

# Initialize the API
api.init()

# Load the model and configure PyTai
model = Dictator.init(MODEL)
py_tai = False

# Main loop with exception handling
if __name__ == "__main__":
    try:
        if not py_tai:
            Dictator.start_ui(model)
        else:
            Architect.py_tai()
    except Exception as e:
        # Handle any unexpected exceptions
        print(f"Error: {e}")
