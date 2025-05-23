"""Main file for Tai AI, a self-evolving AI."""
# Imports
import brain.api as api; api.init()
from brain.config import MODEL
import brain.Dictator as Dictator
import brain.Architect as Architect

USE_EXIT: bool = True

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