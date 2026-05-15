from vector_store import VectorStoreManager
from llm import get_llm
from feedback import FeedbackLoop

class Drafter:
    def __init__(self, vector_store: VectorStoreManager, feedback_loop: FeedbackLoop = None):
        self.vector_store = vector_store
        self.feedback_loop = feedback_loop or FeedbackLoop()
        self.llm = get_llm()

    def generate_draft(self, query: str, draft_type: str = "summary") -> str:
        # 1. Retrieve evidence
        evidence = self.vector_store.search(query, k=5)
        
        # 2. Format evidence for the prompt
        context_blocks = []
        for i, doc in enumerate(evidence):
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "?")
            context_blocks.append(f"Source [{i+1}]: {source} (Page {page})\nContent: {doc.page_content}")
        
        context_text = "\n\n".join(context_blocks)
        
        # 2.5 Get learned insights
        insights = self.feedback_loop.get_relevant_insights(query)
        
        # 3. Create the prompt
        system_prompt = f"""
        You are a senior legal assistant at Pearson Specter Litt. 
        Your task is to generate a {draft_type} grounded strictly in the provided evidence.
        {insights}
        
        Rules:
        - Use a professional, legal tone.
        - Every factual claim MUST be followed by a citation like [Source 1] or [Source 2].
        - If the evidence is contradictory or missing, state that clearly.
        - Do NOT make assumptions.
        """
        
        prompt = f"""
        Evidence:
        {context_text}
        
        Request:
        {query}
        
        Generate the grounded draft now:
        """
        
        # 4. Generate
        draft = self.llm.generate(prompt, system_prompt)
        return draft

if __name__ == "__main__":
    # Test (requires data and API keys)
    pass
