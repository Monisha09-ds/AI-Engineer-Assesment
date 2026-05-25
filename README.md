# Legal AI Workflow - Pearson Specter Litt

An internal workflow for processing messy legal documents, extracting structured information, performing grounded retrieval, and generating drafts that improve over time via a feedback loop.

## Setup Instructions

1. Clone the repository and navigate into the directory.
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Mac/Linux
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   Copy `.env.example` to `.env`. 
   *Note: By default, the system is configured to use a `MockLLMWrapper` (`MODEL_PROVIDER=mock`) due to recent Google API rate limit / quota exhaustion. To use a real model, change the provider to `google` or `anthropic` and provide the respective API key.*
   Add `HF_TOKEN` to `.env` to authenticate Hugging Face model downloads used by the vector store.

## Run Instructions

1. **Main Pipeline Demo**:
   Runs the end-to-end pipeline: generates mock documents, processes them, vectorizes them, and demonstrates drafting and the learning loop.
   ```bash
   python src/main.py
   ```
2. **Run Tests**:
   ```bash
   python -m unittest discover -s tests -t . -p "test_*.py"
   ```
3. **Start the API and Web UI**:
   ```bash
   python src/api.py
   ```
   Then open `http://localhost:8000` in your browser.

## API and Web UI
- `GET /api/status` — service health, document list, vector store state, and insights count.
- `POST /api/process` — process documents and build the FAISS index.
- `POST /api/draft` — generate a grounded draft for a query.
- `POST /api/feedback` — submit an edited draft and save learned insights.
- `GET /api/insights` — show current feedback memory.
- `GET /` or `GET /static/index.html` — open the frontend workflow UI.

The web UI walks through the pipeline:
1. Process sample documents.
2. Generate a draft from a legal query.
3. Edit the draft and submit feedback.
4. View the learned insights injected into future drafts.

## Test Layout
- `tests/unit/` validates isolated feedback and vector-store configuration behavior.
- `tests/smoke/` checks that the processor and API status endpoint initialize successfully.
- `tests/integration/` builds and queries a real FAISS vector store using local embeddings.

## Architecture Overview

The system uses a **Closed-Loop RAG Architecture**:
- **Ingestion (`processor.py`)**: Uses `Docling` (backed by RapidOCR) to accurately parse messy PDFs and images into structured Markdown.
- **Retrieval (`vector_store.py`)**: Uses `LangChain` and local `FAISS` with `HuggingFaceEmbeddings` to chunk, embed, and store document data along with source metadata.
- **Drafting (`drafter.py`)**: Uses a provided LLM to generate drafts strictly grounded in retrieved evidence, enforcing inline citations.
- **Feedback Loop (`feedback.py`)**: Captures operator edits (diff between original and edited draft), extracts structural/factual insights, and stores them in a local JSON memory. This memory is injected into future prompts, allowing the system to learn without expensive fine-tuning.

## Assumptions and Tradeoffs

1. **LLM Quota Fallback**: Due to strict rate limits on the provided API key, a `MockLLMWrapper` was implemented to ensure the pipeline is runnable and testable out-of-the-box.
2. **Local Embeddings vs API**: We chose `HuggingFaceEmbeddings` (all-MiniLM-L6-v2) for local embedding to save costs and reduce API latency, trading off slightly lower semantic accuracy compared to OpenAI/Gemini embeddings.
3. **Docling over PyTesseract**: Docling is heavier but handles document layout recovery (tables, headers) significantly better than basic Tesseract, which is critical for legal documents.
4. **JSON Memory vs Fine-Tuning**: For the "Learning Loop", updating a JSON memory store that injects into the prompt is faster and more explainable than attempting LoRA fine-tuning on the fly for every single edit.

## Evaluation Approach
- **Document Processing**: Verified by successfully extracting content from a dynamically generated, heavily formatted "messy" PDF.
- **Retrieval**: Verified via automated tests (`test_suite.py`) confirming that source metadata is accurately attached and retrieved.
- **Improvement from Edits**: Validated by simulating an operator correcting a title ("neighbor" to "Senior Partner"). The system extracts this insight and applies it to the prompt context.
