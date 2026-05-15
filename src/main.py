import os
from mock_generator import generate_messy_pdf, generate_handwritten_style_txt
from processor import DocProcessor
from vector_store import VectorStoreManager
from drafter import Drafter
from feedback import FeedbackLoop

def run_pipeline():
    print("--- Pearson Specter Litt: Legal AI Workflow ---")
    
    # 1. Setup & Data
    data_dir = "data/sample_documents"
    if not os.listdir(data_dir):
        print("Generating mock documents...")
        # (Calls from mock_generator could go here if needed)
    
    # 2. Process Documents
    processor = DocProcessor()
    docs = processor.process_directory(data_dir)
    print(f"Processed {len(docs)} documents.")
    
    # 3. Vectorize
    vector_store = VectorStoreManager()
    vector_store.add_documents(docs)
    
    # 4. Draft
    feedback = FeedbackLoop()
    drafter = Drafter(vector_store, feedback)
    
    query = "Summarize the Preliminary Title Report for 789 Harvey Specter Lane."
    print(f"\nUser Query: {query}")
    
    original_draft = drafter.generate_draft(query, "Title Review Summary")
    print("\n--- ORIGINAL DRAFT ---")
    print(original_draft)
    
    # 5. Simulate Feedback Loop
    print("\n--- SIMULATING OPERATOR EDIT ---")
    # Operator corrects something (e.g., Louis Litt is not a neighbor, he's a partner)
    edited_draft = original_draft.replace("neighbor (Louis Litt)", "Senior Partner (Louis Litt)")
    edited_draft += "\nNote: Corrected Louis Litt's title."
    
    print("Capturing expert edit...")
    feedback.learn_from_edit(original_draft, edited_draft, query)
    
    # 6. Re-generate to show improvement
    print("\n--- RE-GENERATING DRAFT (With Learning) ---")
    improved_draft = drafter.generate_draft(query, "Title Review Summary")
    print(improved_draft)

if __name__ == "__main__":
    run_pipeline()
