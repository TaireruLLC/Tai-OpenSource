import google.generativeai as genai
import threading
import json
import pyttsx3
import re
from datetime import datetime
from typing import Union, List
import brain.Blacksmith as Blacksmith
from brain.Blacksmith import scrape_text_from_url
import brain.Architect as Architect
from brain.Architect import generate_code
import brain.Historian as Historian
from brain.Historian import save_memory, load_memory, format_memory, update_memory
import brain.Seer as Seer
from brain.Seer import process_image_bytes, safe_unicode
from brain.Bard import speak
from brain.config import MODEL, temp_mem, glob, SPEAKER_MODE, init_documentation, initial_documentation, followup_documentation, IS_ENCRYPTED, is_typing
from buildeasy import Adaptor
from brain.gitbase_launher import NotificationManager
from PIL import Image
import tkinter as tk
from tkinter import filedialog
import time

# Initialize notifications and altcolor
NotificationManager.hide()
start_time_outer = time.time()
import pygame
import pygame_gui
import altcolor
altcolor.init(show_credits=False)
end_time_outer = time.time()
NotificationManager.show()
print(f"[UI] AltColor & PyGame initialized. (Time: {end_time_outer - start_time_outer} seconds)")

# Initialize pyttsx3 engine
engine = pyttsx3.init()

def setup_models():
    """
    Initializes all models and starts them in separate threads. This function
    is blocking and will not return until all models are ready.

    The models are:
        - Architect: generates code
        - Historian: manages memory
        - Blacksmith: generates shell commands
        - Seer: processes images

    The function prints a message when each model is ready and a final message
    when all models are ready.
    """
    global architect_model, historian_model, blacksmith_model, seer_model

    start_time = time.time()
    def set_architect():
        global architect_model
        architect_model = Architect.set_personality(MODEL)
        print("[Setup] Architect model ready")

    def set_historian():
        global historian_model
        historian_model = Historian.set_personality(MODEL)
        print("[Setup] Historian model ready")

    def set_blacksmith():
        global blacksmith_model
        blacksmith_model = Blacksmith.set_personality(MODEL)
        print("[Setup] Blacksmith model ready")

    def set_vision():
        global seer_model
        seer_model = Seer.set_personality(MODEL)
        print("[Setup] Seer model ready")

    threads = [
        threading.Thread(target=set_architect),
        threading.Thread(target=set_historian),
        threading.Thread(target=set_blacksmith),
        threading.Thread(target=set_vision)
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    end_time = time.time()
    print("[Setup] All models initialized. (Time: {:.2f} seconds)".format(end_time - start_time))

def init(model_name: str) -> genai.GenerativeModel:
    start_time = time.time()
    setup_models()
    m = genai.GenerativeModel(
        model_name,
        system_instruction=(f"{init_documentation}")
    )
    end_time = time.time()
    print("[UI] Model initialized. (Time: {:.2f} seconds)".format(end_time - start_time))
    return m


def typing_indicator(chat_display: pygame_gui.elements.UITextBox, send_button: pygame_gui.elements.UIButton):
    global base_text
    dots = ["...", "..", ".", ""]
    index = 0
    base_text = chat_display.html_text
    while is_typing:
        new_text = f"{base_text}\nTai is thinking{dots[index]}"
        chat_display.set_text(new_text)
        index = (index + 1) % len(dots)
        time.sleep(0.5)


def send_message(user_message: Union[str, bytes], model: genai.GenerativeModel, manager: pygame_gui.UIManager, chat_display: pygame_gui.elements.UITextBox, send_button: pygame_gui.elements.UIButton):
    global temp_mem, SPEAKER_MODE, is_typing, base_text
    old_text = chat_display.html_text

    image_summary = ""
    image_vision_results = {}

    start_time_mesgreader = time.time()
    if isinstance(user_message, dict):
        user_text = user_message.get("text", "").strip()
        user_image = user_message.get("image", None)

        if user_image:
            image_vision_results = process_image_bytes(seer_model, user_image)
            image_summary = (
                f"\n### 🖼️ **Image Analysis**\n"
                f"- **Description**: {image_vision_results.get('description', 'N/A')}\n"
                f"- **Objects**: {image_vision_results.get('objects', 'N/A')}\n"
                f"- **OCR Text**: {image_vision_results.get('ocr_text', 'N/A')}\n"
                f"- **Emotions**: {image_vision_results.get('emotions', 'N/A')}\n"
                f"- **Suggestions**: {image_vision_results.get('suggestions', 'N/A')}\n"
            )
    else:
        user_text = user_message if isinstance(user_message, str) else ""
        if isinstance(user_message, bytes):
            image_vision_results = process_image_bytes(seer_model, user_message)
            image_summary = (
                f"\n### 🖼️ **Image Analysis**\n"
                f"- **Description**: {image_vision_results.get('description', 'N/A')}\n"
                f"- **Objects**: {image_vision_results.get('objects', 'N/A')}\n"
                f"- **OCR Text**: {image_vision_results.get('ocr_text', 'N/A')}\n"
                f"- **Emotions**: {image_vision_results.get('emotions', 'N/A')}\n"
                f"- **Suggestions**: {image_vision_results.get('suggestions', 'N/A')}\n"
            )
    end_time_mesgreader = time.time()
    print("[UI] Message reader finished. (Time: {:.2f} seconds)".format(end_time_mesgreader - start_time_mesgreader))
    
    start_time_display = time.time()
    if isinstance(user_message, dict):
        display_text = user_message.get("text", "").strip()
        if user_message.get("image"):
            display_text += "\n[Image Uploaded]"
    elif isinstance(user_message, str):
        display_text = user_message.strip()
    elif isinstance(user_message, bytes):
        display_text = "[Image Uploaded]"
    else:
        display_text = "[Unrecognized input]"
    
    end_time_display = time.time()
    print("[UI] Display updated. (Time: {:.2f} seconds)".format(end_time_display - start_time_display))
    
    chat_display.set_text(
        chat_display.html_text +
        f'<font color="blue">You:</font> {display_text}<br>'
    )
    
    # Thread typing loop
    is_typing = True
    send_button.disable()  # Disable the send button while typing
    typing_thread = threading.Thread(target=typing_indicator, args=(chat_display, send_button,))
    typing_thread.start()

    memory_context = ""
    if glob:
        memory_context += f"\n##### Global Memory:\n```\n{format_memory(json.loads(glob), 'global')}\n```\n"
    if temp_mem:
        memory_context += f"\n##### Restricted Memory:\n```\n{format_memory(json.loads(temp_mem), 'restricted')}\n```\n"

    start_time_pompt = time.time()
    initial_prompt = f"{initial_documentation(memory_context, user_message, image_summary)}"
    initial_model_response = model.generate_content(initial_prompt)
    end_time_prompt = time.time()
    print("[UI] Prompt sent to model. (Time: {:.2f} seconds)".format(end_time_prompt - start_time_pompt))

    parsed_response_text = ""
    start_time_scrape = time.time()
    scraped_text: Union[str, None] = scrape_text_from_url(MODEL, glob, temp_mem, user_message)
    end_time_scrape = time.time()
    print("[UI] Text scraping finished. (Time: {:.2f} seconds)".format(end_time_scrape - start_time_scrape))

    start_time_response = time.time()
    response_text, upgraded_code = generate_code(
        blacksmith_model=blacksmith_model,
        architect_model=architect_model,
        user_request=user_message,
        response=initial_model_response.text,
        tai=model
    )
    end_time_response = time.time()
    print("[UI] Response generation finished. (Time: {:.2f} seconds)".format(end_time_response - start_time_response))

    start_time_responsecleaner = time.time()
    if '_+_TaiEvolutionTransformer_+_' in initial_model_response.text:
        parsed_response_text = initial_model_response.text.split('_+_TaiEvolutionTransformer_+_')[1].strip()
        Adaptor.modify('brain.modifiable', upgraded_code)
    else:
        parsed_response_text = initial_model_response.text
        upgraded_code = None

    followup_prompt = f"{followup_documentation(user_message, parsed_response_text, memory_context, upgraded_code, scraped_text)}"
    final_model_response = model.generate_content(followup_prompt)
    raw_final_response = final_model_response.text

    cleaned_response = re.sub(r'<[^>]+>.*?</[^>]+>', '', raw_final_response, flags=re.DOTALL)
    cleaned_response = cleaned_response.replace("```xml", "").replace("```", "").strip()
    end_time_responsecleaner = time.time()
    print("[UI] Response cleaner finished. (Time: {:.2f} seconds)".format(end_time_responsecleaner - start_time_responsecleaner))

    start_time_memoryupdate = time.time()
    if re.search(r'<GlobalMemory>.*?</GlobalMemory>', raw_final_response) or \
       re.search(r'<Forget>.*?</Forget>', raw_final_response):
        update_memory(historian_model, user_message)

    current_session_memory: Union[List, None] = json.loads(temp_mem)
    new_conversation_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "User": user_text + (f"\n\n[Image Analysis Attached]" if image_summary else ""),
        "Tai": raw_final_response or "No Response"
    }
    current_session_memory.append(new_conversation_entry)
    temp_mem = json.dumps(current_session_memory)
    end_time_memoryupdate = time.time()
    print("[UI] Memory updated. (Time: {:.2f} seconds)".format(end_time_memoryupdate - start_time_memoryupdate))

    is_typing = False
    send_button.enable()  # Re-enable the send button
    chat_display.set_text(f"{base_text}")
    chat_display.set_text(
        chat_display.html_text +
        f'<font color="red">Tai:</font> {cleaned_response}<br>'
    )    

    threading.Thread(target=save_memory, args=(temp_mem, glob, IS_ENCRYPTED), daemon=True).start()

    if SPEAKER_MODE:
        threading.Thread(target=speak, args=(engine, cleaned_response,), daemon=True).start()

def start_ui(model: genai.GenerativeModel) -> None:
    global user_entry, chat_display, glob, temp_mem
    start_time = time.time()
    pygame.init()
    pygame.display.set_caption('Tai AI Chat')
    screen_width, screen_height = 800, 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    manager = pygame_gui.UIManager((screen_width, screen_height))
    user_input = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((20, screen_height - 60), (600, 40)), manager=manager)
    send_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((640, screen_height - 60), (120, 40)), text='Send', manager=manager)
    upload_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((20, screen_height - 110), (120, 40)), text='Upload Image', manager=manager)
    chat_display = pygame_gui.elements.UITextBox(html_text='', relative_rect=pygame.Rect((20, 20), (760, 500)), manager=manager)
    clock = pygame.time.Clock()
    is_running = True
    end_time = time.time()
    print(f"[UI] UI started in {end_time - start_time:.2f} seconds.")

    start_time_mem = time.time()
    try:
        glob = json.dumps(load_memory("global"))
        temp_mem = json.dumps(load_memory("restricted"))
    except Exception as e:
        print("Error loading memory:", e)
        glob = json.dumps([])
        temp_mem = json.dumps([])
    end_time_mem = time.time()
    print(f"[UI] Memory loaded in {end_time_mem - start_time_mem:.2f} seconds.")

    print("[UI] Starting event loop...")

    try:
        while is_running:
            time_delta = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print("[UI] Quit event received.")
                    is_running = False
                if event.type == pygame.USEREVENT:
                    if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                        if event.ui_element == send_button:
                            msg = user_input.get_text().strip()
                            if msg:
                                threading.Thread(target=send_message, args=(msg, model, manager, chat_display, send_button), daemon=True).start()
                                user_input.set_text('')
                        elif event.ui_element == upload_button:
                            # Open file dialog using Tkinter (hidden root)
                            root = tk.Tk()
                            root.withdraw()  # Hide the root window
                            file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")])
                            root.destroy()
                            if file_path:
                                try:
                                    # Use Pillow to open the image
                                    with Image.open(file_path) as img:
                                        image_format = img.format
                                        chat_display.append_html_text(f"Image uploaded: {image_format}<br><br>")
                                        # Process the image (you can add custom logic here)
                                        with open(file_path, "rb") as img_file:
                                            image_bytes = img_file.read()
                                            result = process_image_bytes(seer_model, image_bytes)
                                            chat_display.append_html_text(f"Image processed:<br>{result}<br><br>")
                                except Exception as e:
                                    chat_display.append_html_text(f"Error processing image: {safe_unicode(str(e))}<br><br>")
                manager.process_events(event)

            manager.update(time_delta)
            screen.fill((30, 30, 30))
            manager.draw_ui(screen)
            pygame.display.update()

    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()
