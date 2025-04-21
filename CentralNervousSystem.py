"""Main file for Tai AI, a self-evolving AI."""
# Imports
from brain.NeuralBlueprint import MODEL
import brain.PrefrontalCortex as PrefrontalCortex
import brain.Thalamus as Thalamus
import brain.Hippocampus as Hippocampus

USE_EXIT: bool = True

# Initialize the API
Thalamus.init()

# Load the model and configure PyTai
model = PrefrontalCortex.init(MODEL)
py_tai = False

# Main loop with exception handling
if __name__ == "__main__":
    try:
        if not py_tai:
            PrefrontalCortex.start_ui(model)
        else:
            Hippocampus.py_tai()
    except Exception as e:
        # Handle any unexpected exceptions
        print(f"Error: {e}")
