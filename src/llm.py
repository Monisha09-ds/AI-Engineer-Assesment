import os
from typing import List, Optional
import google.generativeai as genai
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class LLMInterface:
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

class GeminiWrapper(LLMInterface):
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(model_name)

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        full_prompt = f"{system_prompt}\n\nUser Question: {prompt}" if system_prompt else prompt
        response = self.model.generate_content(full_prompt)
        return response.text

class AnthropicWrapper(LLMInterface):
    def __init__(self, model_name: str = "claude-3-5-sonnet-20240620"):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model_name = model_name

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        message = self.client.messages.create(
            model=self.model_name,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

class MockLLMWrapper(LLMInterface):
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        # If it's the learning loop prompt
        if "Output as a JSON list" in prompt:
            return '[{"type": "fact", "insight": "The corrected title is Senior Partner."}]'
        # If it's the drafting prompt
        return "This is a mock generated draft based on the evidence: [Source 1]."

def get_llm() -> LLMInterface:
    provider = os.getenv("MODEL_PROVIDER", "google").lower()
    if provider == "google":
        return GeminiWrapper(os.getenv("DEFAULT_MODEL", "gemini-1.5-flash"))
    elif provider == "anthropic":
        return AnthropicWrapper(os.getenv("DEFAULT_MODEL", "claude-3-5-sonnet-20240620"))
    elif provider == "mock":
        return MockLLMWrapper()
    else:
        raise ValueError(f"Unknown provider: {provider}")

if __name__ == "__main__":
    # Test (requires API key)
    try:
        llm = get_llm()
        print(llm.generate("Hello, who are you?"))
    except Exception as e:
        print(f"LLM Test failed (likely missing API key): {e}")
