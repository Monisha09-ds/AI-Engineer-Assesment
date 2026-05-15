import os
from typing import List, Dict, Any
from docling.document_converter import DocumentConverter
from pydantic import BaseModel

class ProcessedDocument(BaseModel):
    file_path: str
    content: str
    metadata: Dict[str, Any]

class DocProcessor:
    def __init__(self):
        self.converter = DocumentConverter()
        
    def process(self, file_path: str) -> ProcessedDocument:
        """
        Processes a document (PDF, Image, etc.) using Docling.
        """
        print(f"Processing document: {file_path}")
        result = self.converter.convert(file_path)
        
        # Exporting to markdown for better RAG performance
        markdown_content = result.document.export_to_markdown()
        
        # Extract basic metadata
        metadata = {
            "source": os.path.basename(file_path),
            "pages": len(result.document.pages) if hasattr(result.document, 'pages') else 1,
            "format": os.path.splitext(file_path)[1]
        }
        
        return ProcessedDocument(
            file_path=file_path,
            content=markdown_content,
            metadata=metadata
        )

    def process_directory(self, directory_path: str) -> List[ProcessedDocument]:
        """
        Processes all supported documents in a directory.
        """
        processed_docs = []
        for filename in os.listdir(directory_path):
            if filename.endswith(('.pdf', '.docx', '.pptx', '.png', '.jpg', '.jpeg')):
                file_path = os.path.join(directory_path, filename)
                try:
                    doc = self.process(file_path)
                    processed_docs.append(doc)
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
        return processed_docs

if __name__ == "__main__":
    # Test with mock data
    processor = DocProcessor()
    docs = processor.process_directory("data/sample_documents")
    for doc in docs:
        print(f"Processed {doc.metadata['source']} - Content length: {len(doc.content)}")
