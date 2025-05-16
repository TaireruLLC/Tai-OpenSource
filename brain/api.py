"""API data for Tai."""

import google.generativeai as genai

def init():
    genai.configure(api_key="YOUR-API-KEY")
