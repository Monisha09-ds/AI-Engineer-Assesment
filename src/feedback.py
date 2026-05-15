import json
import os
from typing import List, Dict
from llm import get_llm

class FeedbackLoop:
    def __init__(self, memory_path: str = "data/memory.json"):
        self.memory_path = memory_path
        self.llm = get_llm()
        self.memory = self._load_memory()

    def _load_memory(self) -> List[Dict]:
        if os.path.exists(self.memory_path):
            with open(self.memory_path, 'r') as f:
                return json.load(f)
        return []

    def _save_memory(self):
        os.makedirs(os.path.dirname(self.memory_path), exist_ok=True)
        with open(self.memory_path, 'w') as f:
            json.dump(self.memory, f, indent=4)

    def learn_from_edit(self, original: str, edited: str, context_query: str):
        """
        Analyzes the difference between original and edited draft to extract 'Learned Knowledge'.
        """
        prompt = f"""
        Original Draft:
        {original}
        
        Edited Version (by human expert):
        {edited}
        
        Context/Query: {context_query}
        
        Identify specific factual corrections or stylistic preferences made by the expert.
        Output as a JSON list of objects: {{"type": "fact|style", "insight": "the actual lesson"}}
        """
        
        system_prompt = "You are a knowledge extraction engine. Extract reusable insights from human edits."
        
        try:
            response = self.llm.generate(prompt, system_prompt)
            # Find JSON in response (simple heuristic)
            start = response.find("[")
            end = response.rfind("]") + 1
            if start != -1 and end != -1:
                insights = json.loads(response[start:end])
                for insight in insights:
                    insight["source_query"] = context_query
                    self.memory.append(insight)
                self._save_memory()
                print(f"Learned {len(insights)} new insights from edit.")
            else:
                print("Could not parse insights from LLM response.")
        except Exception as e:
            print(f"Error in learning loop: {e}")

    def get_relevant_insights(self, query: str) -> str:
        """
        Returns relevant learned knowledge as a string to be injected into the prompt.
        """
        if not self.memory:
            return ""
            
        # Simple keyword matching for now (could be upgraded to semantic search)
        relevant = []
        query_words = set(query.lower().split())
        for item in self.memory:
            insight_text = item["insight"].lower()
            if any(word in insight_text for word in query_words):
                relevant.append(f"- {item['type'].upper()}: {item['insight']}")
        
        if relevant:
            return "\nPREVIOUS EXPERT CORRECTIONS:\n" + "\n".join(relevant)
        return ""

if __name__ == "__main__":
    # Test
    pass
