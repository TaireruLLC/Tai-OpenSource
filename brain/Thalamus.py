"""API data for Tai."""

# 0.8.4
import google.generativeai as genai

def init():
    genai.configure(api_key="YOUR-API-KEY")