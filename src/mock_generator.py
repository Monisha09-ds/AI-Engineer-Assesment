import os

from fpdf import FPDF


def generate_messy_pdf(output_path, text, title="Legal Document"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add a title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=title, ln=True, align='C')
    pdf.ln(10)
    
    # Add messy text
    pdf.set_font("Arial", size=10)
    for line in text.split('\n'):
        # Randomly vary indentation to simulate messy layout
        pdf.set_x(10 + (hash(line) % 5)) 
        pdf.multi_cell(0, 5, txt=line)
        pdf.ln(1)
        
    pdf.output(output_path)
    print(f"Generated messy PDF: {output_path}")

def generate_handwritten_style_txt(output_path, text):
    # Simulating a "transcription" of a handwritten note
    with open(output_path, 'w') as f:
        f.write("--- HANDWRITTEN NOTE TRANSCRIPTION ---\n")
        f.write("Note: Some parts are illegible.\n\n")
        f.write(text)
    print(f"Generated messy text: {output_path}")

if __name__ == "__main__":
    data_dir = "data/sample_documents"
    os.makedirs(data_dir, exist_ok=True)
    
    # Sample 1: Title Review
    title_review_text = """
    PRELIMINARY TITLE REPORT
    Order No: 9988-AX-2026
    Date: May 10, 2026
    
    Property Address: 789 Harvey Specter Lane, New York, NY
    Current Owner: Mike Ross (as per deed dated 01/15/2020)
    
    Exceptions:
    1. Taxes for the fiscal year 2025-2026 are a lien, not yet payable.
    2. An easement for public utilities over the eastern 10 feet of the land.
    3. [ILLEGIBLE] ... regarding the north boundary ... [SMUDGE]
    
    Notes: The owner reported a minor dispute with the neighbor (Louis Litt) 
    regarding the fence location.
    """
    generate_messy_pdf(os.path.join(data_dir, "title_report.pdf"), title_review_text, "Preliminary Title Report")
    
    # Sample 2: Case Fact Summary
    case_facts = """
    MEMORANDUM OF CASE FACTS
    Subject: Pearson vs. Hardman
    
    On the night of April 12, the defendant was seen entering the premises 
    at approx 11:45 PM. Witness A (Donna Paulsen) states she heard 
    loud voices coming from the library.
    
    Key Evidence:
    - CCTV footage from the lobby (Timestamp: 23:46)
    - Signed contract dated Feb 3, 2024.
    - [HANDWRITTEN NOTE]: "Don't let them see the blue file."
    """
    generate_handwritten_style_txt(os.path.join(data_dir, "case_facts.txt"), case_facts)
