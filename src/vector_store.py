import os
from typing import Any, List

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document as LangChainDocument
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

class VectorStoreManager:
    def __init__(self, index_path: str = "faiss_index"):
        self.index_path = index_path
        hf_token = os.getenv("HF_TOKEN")
        model_kwargs = {"token": hf_token} if hf_token else {}
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs=model_kwargs,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            add_start_index=True,
        )
        self.vector_store = None

    def add_documents(self, documents: List[Any]):
        """
        Converts custom ProcessedDocument to LangChain Documents and adds to FAISS.
        """
        lc_docs = []
        for doc in documents:
            chunks = self.text_splitter.split_text(doc.content)
            for i, chunk in enumerate(chunks):
                lc_doc = LangChainDocument(
                    page_content=chunk,
                    metadata={
                        **doc.metadata,
                        "chunk_id": i,
                        "full_path": doc.file_path
                    }
                )
                lc_docs.append(lc_doc)
        
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(lc_docs, self.embeddings)
        else:
            self.vector_store.add_documents(lc_docs)
            
        self.save_index()

    def save_index(self):
        if self.vector_store:
            self.vector_store.save_local(self.index_path)
            print(f"Vector store saved to {self.index_path}")

    def load_index(self):
        if os.path.exists(self.index_path):
            self.vector_store = FAISS.load_local(
                self.index_path, 
                self.embeddings,
                allow_dangerous_deserialization=True # Required for local loading
            )
            print(f"Vector store loaded from {self.index_path}")
            return True
        return False

    def search(self, query: str, k: int = 4) -> List[LangChainDocument]:
        if self.vector_store is None and not self.load_index():
            raise ValueError("Vector store not initialized or loaded.")
        return self.vector_store.similarity_search(query, k=k)

if __name__ == "__main__":
    # Test
    manager = VectorStoreManager()
    # Mock some data
    from processor import ProcessedDocument
    mock_doc = ProcessedDocument(
        file_path="test.pdf",
        content="This is a test document about Harvey Specter and Mike Ross.",
        metadata={"source": "test.pdf"}
    )
    manager.add_documents([mock_doc])
    results = manager.search("Who is Mike Ross?")
    for res in results:
        print(f"Found: {res.page_content} (Source: {res.metadata['source']})")
