"""Blacksmith Configuration code for Tai AI, a self-evolving AI."""
import google.generativeai as genai
from typing import Optional, Union, List
import sys
import subprocess
import requests
from bs4 import BeautifulSoup
import ast
import json
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import re

import brain.Historian as Historian
from brain.Historian import format_memory

def set_personality(model_name: str) -> genai.GenerativeModel:
    """
    Configures the Blacksmith AI model to interpret and act on requests
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
            "upgrade, or verify libraries."
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


def install_package(command: Union[str, List[str]]) -> None:
    """
    Installs a package using pip.

    Parameters
    ----------
    command : str or List[str]
        The command to install the package. If a string, it is split using
        str.split(). If a list, it is not split. The command should not
        include the "python -m" part.

    Returns
    -------
    None
    """
    if isinstance(command, str):
        command = command.split()
    if "buildeasy" not in command:
        subprocess.check_call([sys.executable, "-m"] + command)

def clean_text(html: str) -> str:
    """Cleans and extracts readable text from raw HTML using BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove unwanted elements
    for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
        tag.decompose()
    
    # Get text and clean it up
    text = soup.get_text(separator='\n')
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned = '\n'.join(lines)
    
    # Collapse multiple newlines
    return re.sub(r'\n+', '\n', cleaned)

def scroll_to_bottom(page):
    """Scrolls to the bottom of the page to trigger lazy-loaded content."""
    page.evaluate("""
        () => {
            return new Promise((resolve) => {
                let totalHeight = 0;
                const distance = 500;
                const timer = setInterval(() => {
                    window.scrollBy(0, distance);
                    totalHeight += distance;
                    if (totalHeight >= document.body.scrollHeight) {
                        clearInterval(timer);
                        resolve();
                    }
                }, 200);
            });
        }
    """)

def scrape_text(url: str, timeout: int = 15000) -> str:
    """
    Scrapes and cleans text from a URL using a headless browser (Playwright).
    
    Parameters
    ----------
    url : str
        The URL to scrape text from.
    timeout : int
        Timeout in milliseconds for loading the page.
    
    Returns
    -------
    str
        The cleaned, readable text content of the page.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/113.0.0.0 Safari/537.36"
            ))
            page = context.new_page()
            page.goto(url, timeout=timeout)
            page.wait_for_load_state("networkidle", timeout=timeout)
            scroll_to_bottom(page)  # Useful for dynamic/lazy-loaded content
            content = page.content()
            browser.close()
            
        return clean_text(content)
    
    except PlaywrightTimeoutError:
        return "Error: Page load timed out."
    except Exception as e:
        return f"Unexpected error occurred: {str(e)}"

def scrape_text_from_url(MODEL, glob, temp_mem, user_message: str) -> str:
    memory_context = ""
    if glob:
        memory_context += f"\n## Global Memory:\n```\n{format_memory(json.loads(glob), 'global')}\n```\n"
    if temp_mem:
        memory_context += f"\n## Restricted Memory:\n```\n{format_memory(json.loads(temp_mem), 'restricted')}\n```\n"
    model = genai.GenerativeModel(MODEL, system_instruction=f"""
# Hello, simply read the below prompt and consider memory (relavant links by conversation's current topic), and find links (if any), and return the links in a pythonic list but without `variable_name = `. If there are no links return 'None'. **DO NOT** include duplicates.
# Memory below
{memory_context}
    """)
    
    urls_str: str = f"{model.generate_content(user_message).text}"
    
    #print(urls_str)

    final_text = ""

    if urls_str.strip() != "None":
        try:
            urls = ast.literal_eval(urls_str)
        except Exception as e:
            return f"Error parsing links: {e}"

        for url in urls:
            try:
                response = scrape_text(url)

                final_text = f"{final_text}\n# {url}\n{response}"
            except requests.RequestException as e:
                return f"Request error: {e}"
            except Exception as e:
                return f"An error occurred: {e}"

    #print(f"final_text: {final_text}")
    return final_text