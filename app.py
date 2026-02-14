#!/usr/bin/env python3
"""
Swiss RAG Demo - Apertus 8B
A Gradio-based RAG application demonstrating question-answering over Swiss legal documents
using the Apertus 8B Swiss sovereign LLM via HuggingFace Inference API.
"""

import os
import time
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

import gradio as gr
import numpy as np
import requests
from scipy.spatial.distance import cosine
from huggingface_hub import InferenceClient
from openai import OpenAI
import fitz  # PyMuPDF

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Document configuration
DOCUMENTS = [
    {
        "url": "https://www.fedlex.admin.ch/filestore/fedlex.data.admin.ch/eli/cc/1999/404/20230101/de/pdf-a/fedlex-data-admin-ch-eli-cc-1999-404-20230101-de-pdf-a.pdf",
        "label": "Bundesverfassung (DE)"
    },
    {
        "url": "https://www.fedlex.admin.ch/filestore/fedlex.data.admin.ch/eli/cc/1999/404/20230101/fr/pdf-a/fedlex-data-admin-ch-eli-cc-1999-404-20230101-fr-pdf-a.pdf",
        "label": "Constitution fédérale (FR)"
    },
    {
        "url": "https://www.fedlex.admin.ch/filestore/fedlex.data.admin.ch/eli/cc/2022/491/20230901/de/pdf-a/fedlex-data-admin-ch-eli-cc-2022-491-20230901-de-pdf-a.pdf",
        "label": "Datenschutzgesetz nDSG (DE)"
    }
]

# Model configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "swiss-ai/apertus-8b-instruct"   # PublicAI model name
PUBLICAI_BASE_URL = "https://api.publicai.co/v1"

# Chunking parameters
CHARS_PER_TOKEN = 4
CHUNK_SIZE_TOKENS = 400
OVERLAP_TOKENS = 100
CHUNK_SIZE_CHARS = CHUNK_SIZE_TOKENS * CHARS_PER_TOKEN
OVERLAP_CHARS = OVERLAP_TOKENS * CHARS_PER_TOKEN

# Retrieval parameters
TOP_K = 4

# LLM parameters
MAX_TOKENS = 512
TEMPERATURE = 0.1

# System prompt
SYSTEM_PROMPT = """Du bist ein hilfreicher Assistent für Schweizer Rechtsdokumente und Vorschriften. Du antwortest präzise und sachlich basierend ausschliesslich auf dem bereitgestellten Kontext. Wenn die Antwort nicht im Kontext enthalten ist, sagst du das klar. Du kannst auf Deutsch, Französisch, Italienisch und Englisch antworten — antworte in der Sprache der Frage."""


@dataclass
class Chunk:
    """Represents a document chunk with metadata."""
    text: str
    source_label: str
    page_number: int
    chunk_index: int
    embedding: Optional[np.ndarray] = None


class DocumentProcessor:
    """Handles document downloading, parsing, and chunking."""
    
    def __init__(self):
        self.chunks: List[Chunk] = []
        
    def download_pdf(self, url: str, label: str) -> Optional[bytes]:
        """Download a PDF from a URL."""
        try:
            logger.info(f"Downloading {label} from {url}")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.warning(f"Failed to download {label}: {e}")
            return None
    
    def parse_pdf(self, pdf_bytes: bytes, label: str) -> List[Tuple[str, int]]:
        """Parse PDF and extract text with page numbers."""
        pages = []
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text()
                if text.strip():
                    pages.append((text, page_num))
            doc.close()
            logger.info(f"Extracted {len(pages)} pages from {label}")
        except Exception as e:
            logger.warning(f"Failed to parse PDF {label}: {e}")
        return pages
    
    def chunk_text(self, text: str, page_num: int, label: str, start_chunk_index: int) -> List[Chunk]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        chunk_index = start_chunk_index
        
        while start < len(text):
            end = start + CHUNK_SIZE_CHARS
            chunk_text = text[start:end]
            
            if chunk_text.strip():
                chunks.append(Chunk(
                    text=chunk_text.strip(),
                    source_label=label,
                    page_number=page_num,
                    chunk_index=chunk_index
                ))
                chunk_index += 1
            
            start += CHUNK_SIZE_CHARS - OVERLAP_CHARS
            
            # Avoid infinite loop
            if start >= len(text):
                break
        
        return chunks
    
    def process_documents(self, documents: List[Dict]) -> Dict[str, int]:
        """Download and process all documents."""
        stats = {}
        
        for doc_config in documents:
            url = doc_config["url"]
            label = doc_config["label"]
            
            # Download PDF
            pdf_bytes = self.download_pdf(url, label)
            if not pdf_bytes:
                stats[label] = 0
                continue
            
            # Parse PDF
            pages = self.parse_pdf(pdf_bytes, label)
            if not pages:
                stats[label] = 0
                continue
            
            # Chunk pages
            doc_chunks = []
            chunk_index = 0
            for page_text, page_num in pages:
                page_chunks = self.chunk_text(page_text, page_num, label, chunk_index)
                doc_chunks.extend(page_chunks)
                chunk_index += len(page_chunks)
            
            self.chunks.extend(doc_chunks)
            stats[label] = len(doc_chunks)
            logger.info(f"Created {len(doc_chunks)} chunks from {label}")
        
        return stats


class EmbeddingEngine:
    """Handles embedding generation using HuggingFace Inference API.

    Note: Embeddings are generated via HF Inference API (cloud), not locally.
    This means the app can run locally without GPU/model downloads - only an
    HF API token is required. Chunking/parsing happens locally.
    """

    def __init__(self, token: str):
        self.client = InferenceClient(token=token)
        self.model = EMBEDDING_MODEL
        
    def embed_text(self, text: str) -> Optional[np.ndarray]:
        """Embed a single text using HF Inference API."""
        try:
            result = self.client.feature_extraction(text, model=self.model)
            
            # Handle different response formats
            if isinstance(result, list):
                # If nested list, flatten by averaging
                if isinstance(result[0], list):
                    embedding = np.mean(result, axis=0)
                else:
                    embedding = np.array(result)
            else:
                embedding = np.array(result)
            
            # Normalize
            embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
            return embedding
            
        except Exception as e:
            logger.warning(f"Failed to embed text: {e}")
            return None
    
    def embed_chunks_batch(self, chunks: List[Chunk], batch_size: int = 10) -> int:
        """Embed chunks in batches with rate limiting."""
        success_count = 0
        total = len(chunks)
        
        for i in range(0, total, batch_size):
            batch = chunks[i:i+batch_size]
            logger.info(f"Embedding batch {i//batch_size + 1}/{(total + batch_size - 1)//batch_size}")
            
            for chunk in batch:
                embedding = self.embed_text(chunk.text)
                if embedding is not None:
                    chunk.embedding = embedding
                    success_count += 1
            
            # Rate limiting
            if i + batch_size < total:
                time.sleep(0.5)
        
        return success_count


class RAGRetriever:
    """Handles retrieval of relevant chunks using cosine similarity."""
    
    def __init__(self, chunks: List[Chunk], embedding_engine: EmbeddingEngine):
        self.chunks = [c for c in chunks if c.embedding is not None]
        self.embedding_engine = embedding_engine
        
        if self.chunks:
            self.embeddings = np.vstack([c.embedding for c in self.chunks])
        else:
            self.embeddings = np.array([])
    
    def retrieve(self, query: str, top_k: int = TOP_K) -> List[Tuple[Chunk, float]]:
        """Retrieve top-k most relevant chunks."""
        if len(self.chunks) == 0:
            return []
        
        # Embed query
        query_embedding = self.embedding_engine.embed_text(query)
        if query_embedding is None:
            return []
        
        # Compute cosine similarities
        similarities = []
        for i, chunk_embedding in enumerate(self.embeddings):
            # scipy cosine returns distance, so similarity = 1 - distance
            similarity = 1 - cosine(query_embedding, chunk_embedding)
            similarities.append((self.chunks[i], similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]


class SwissRAG:
    """Main RAG application."""

    def __init__(self):
        self.hf_token = os.environ.get("HF_TOKEN")
        if not self.hf_token:
            raise ValueError("HF_TOKEN environment variable not set")

        self.publicai_token = os.environ.get("PUBLICAI_API_KEY")
        if not self.publicai_token:
            raise ValueError("PUBLICAI_API_KEY environment variable not set")

        # PublicAI client for LLM (OpenAI-compatible)
        self.llm_client = OpenAI(
            api_key=self.publicai_token,
            base_url=PUBLICAI_BASE_URL
        )
        self.llm_model = LLM_MODEL

        # Initialize components
        self.doc_processor = DocumentProcessor()
        self.embedding_engine = EmbeddingEngine(self.hf_token)
        self.retriever = None
        self.doc_stats = {}
        
    def initialize(self):
        """Initialize the RAG system by loading and processing documents."""
        logger.info("Starting document ingestion...")
        
        # Process documents
        self.doc_stats = self.doc_processor.process_documents(DOCUMENTS)
        total_chunks = len(self.doc_processor.chunks)
        logger.info(f"Total chunks created: {total_chunks}")
        
        if total_chunks == 0:
            raise ValueError("No chunks created from documents")
        
        # Embed chunks
        logger.info("Embedding chunks...")
        success_count = self.embedding_engine.embed_chunks_batch(self.doc_processor.chunks)
        logger.info(f"Successfully embedded {success_count}/{total_chunks} chunks")
        
        # Initialize retriever
        self.retriever = RAGRetriever(self.doc_processor.chunks, self.embedding_engine)
        logger.info("RAG system ready!")
        
        return self.get_status_message()
    
    def get_status_message(self) -> str:
        """Get status message for UI."""
        if not self.retriever:
            return "⏳ Loading documents..."

        total_chunks = len(self.retriever.chunks)
        num_docs = len([v for v in self.doc_stats.values() if v > 0])

        return f"✅ Ready — {total_chunks} chunks loaded across {num_docs} documents | LLM: {LLM_MODEL} via PublicAI"
    
    def get_loaded_docs_info(self) -> str:
        """Get information about loaded documents."""
        if not self.doc_stats:
            return "No documents loaded yet."
        
        info = []
        for label, chunk_count in self.doc_stats.items():
            if chunk_count > 0:
                info.append(f"✅ {label}: {chunk_count} chunks")
            else:
                info.append(f"❌ {label}: Failed to load")
        
        return "\n".join(info)
    
    def query(self, question: str) -> Tuple[str, str]:
        """Process a query and return answer with retrieved context."""
        if not self.retriever:
            return "Error: System not initialized", ""
        
        if not question.strip():
            return "Please enter a question.", ""
        
        # Retrieve relevant chunks
        retrieved = self.retriever.retrieve(question, top_k=TOP_K)
        
        if not retrieved:
            return "Error: Could not retrieve relevant context.", ""
        
        # Format context
        context_parts = []
        for i, (chunk, score) in enumerate(retrieved, 1):
            context_parts.append(
                f"[{i}] {chunk.source_label} (Seite/Page {chunk.page_number}):\n{chunk.text}"
            )
        
        context_str = "\n\n".join(context_parts)
        
        # Format retrieved context for display
        retrieved_display = []
        for i, (chunk, score) in enumerate(retrieved, 1):
            retrieved_display.append(
                f"**Chunk {i}** (Similarity: {score:.3f})\n"
                f"Source: {chunk.source_label} | Page: {chunk.page_number}\n"
                f"```\n{chunk.text[:300]}...\n```"
            )
        retrieved_info = "\n\n".join(retrieved_display)
        
        # Create prompt
        user_prompt = f"""Kontext aus Schweizer Dokumenten:

{context_str}

Frage: {question}

Bitte beantworte die Frage basierend auf dem obigen Kontext."""
        
        # Call LLM via PublicAI
        try:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]

            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=messages,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE
            )

            answer = response.choices[0].message.content
            logger.info(f"LLM response received from {self.llm_model}")

        except Exception as e:
            logger.error(f"LLM call failed with {self.llm_model}: {e}")
            answer = f"Error: LLM call failed: {str(e)}"

        return answer, retrieved_info


def create_ui(rag_system: SwissRAG) -> gr.Blocks:
    """Create Gradio UI."""
    
    with gr.Blocks(title="Swiss RAG Demo - Apertus", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🇨🇭 Swiss Document RAG — powered by Apertus")
        gr.Markdown("**Sovereign Swiss AI | Data stays in Switzerland**")
        
        status_bar = gr.Textbox(
            value=rag_system.get_status_message(),
            label="System Status",
            interactive=False,
            show_label=False
        )
        
        with gr.Row():
            with gr.Column():
                question_box = gr.Textbox(
                    label="Ihre Frage / Votre question",
                    placeholder="Geben Sie Ihre Frage ein...",
                    lines=3
                )
                
                ask_button = gr.Button("Ask / Fragen", variant="primary")
                
                gr.Examples(
                    examples=[
                        "Was sind die Grundrechte gemäss der Bundesverfassung?",
                        "Quels sont les droits fondamentaux selon la Constitution?",
                        "Was sind die Pflichten bei einer Datenschutzverletzung nach dem nDSG?"
                    ],
                    inputs=question_box,
                    label="Example Questions / Beispielfragen"
                )
        
        with gr.Row():
            with gr.Column():
                answer_box = gr.Textbox(
                    label="Answer / Antwort",
                    lines=8,
                    interactive=False
                )
        
        with gr.Accordion("Retrieved context", open=False):
            context_box = gr.Markdown(value="")
        
        with gr.Accordion("Loaded documents", open=False):
            docs_info = gr.Markdown(value=rag_system.get_loaded_docs_info())
        
        # Event handlers
        def handle_query(question):
            answer, context = rag_system.query(question)
            return answer, context, rag_system.get_status_message()
        
        ask_button.click(
            fn=handle_query,
            inputs=[question_box],
            outputs=[answer_box, context_box, status_bar]
        )
        
        question_box.submit(
            fn=handle_query,
            inputs=[question_box],
            outputs=[answer_box, context_box, status_bar]
        )
    
    return demo


def main():
    """Main entry point."""
    try:
        # Initialize RAG system
        logger.info("Initializing Swiss RAG system...")
        rag = SwissRAG()
        rag.initialize()
        
        # Create and launch UI
        demo = create_ui(rag)
        demo.launch()
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        # Create error UI
        with gr.Blocks() as error_demo:
            gr.Markdown("# 🇨🇭 Swiss Document RAG — powered by Apertus")
            gr.Markdown("## ❌ Configuration Error")
            gr.Markdown(f"**{str(e)}**")
            gr.Markdown("Please set the `HF_TOKEN` and `PUBLICAI_API_KEY` environment variables.")
        error_demo.launch()
        
    except Exception as e:
        logger.error(f"Initialization error: {e}", exc_info=True)
        # Create error UI
        with gr.Blocks() as error_demo:
            gr.Markdown("# 🇨🇭 Swiss Document RAG — powered by Apertus")
            gr.Markdown("## ❌ Initialization Error")
            gr.Markdown(f"```\n{str(e)}\n```")
        error_demo.launch()


if __name__ == "__main__":
    main()
