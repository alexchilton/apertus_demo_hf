---
title: Swiss RAG Demo - Apertus
emoji: 🏔️
colorFrom: red
colorTo: gray
sdk: gradio
sdk_version: 6.5.1
app_file: app.py
pinned: false
---

# 🇨🇭 Swiss Document RAG — powered by Apertus

A Gradio-based RAG (Retrieval-Augmented Generation) application demonstrating question-answering over Swiss legal documents using the **Apertus 8B** Swiss sovereign LLM and HuggingFace Inference API.

## Features

- **Sovereign Swiss AI**: Uses swiss-ai/Apertus-8B-Instruct-2509 model
- **Swiss Public Documents**: Federal Constitution (DE/FR) and Data Protection Act (nDSG)
- **No GPU Required**: Everything runs via HuggingFace Inference API
- **Multilingual**: Supports German, French, Italian, and English queries
- **Simple & Self-contained**: No vector DB, no Docker, no persistent storage

## Documents

The application automatically downloads and processes:

1. **Bundesverfassung (DE)** - Swiss Federal Constitution (German)
2. **Constitution fédérale (FR)** - Swiss Federal Constitution (French)  
3. **Datenschutzgesetz nDSG (DE)** - Swiss Data Protection Act (German)

## How It Works

1. **Document Ingestion**: At startup, PDFs are downloaded from fedlex.admin.ch and chunked into ~400 token segments with 100 token overlap
2. **Embedding**: All chunks are embedded using sentence-transformers/all-MiniLM-L6-v2 via HF Inference API
3. **Retrieval**: User questions are embedded and top-4 most relevant chunks are retrieved using cosine similarity
4. **Generation**: Retrieved context is passed to Apertus 8B to generate precise answers based solely on the documents

## Tech Stack

- **Gradio** - Web UI framework
- **huggingface_hub InferenceClient** - For embeddings and LLM calls
- **sentence-transformers/all-MiniLM-L6-v2** - Embedding model
- **swiss-ai/Apertus-8B-Instruct-2509** - Swiss sovereign LLM
- **PyMuPDF** - PDF parsing
- **NumPy + SciPy** - Vector similarity computation

## Local Development

### Requirements

- Python 3.11
- HuggingFace API token (set as `HF_TOKEN` environment variable)

### Installation

```bash
# Clone repository
git clone https://github.com/alexchilton/apertus_demo_hf.git
cd apertus_demo_hf

# Install dependencies
pip install -r requirements.txt

# Set HuggingFace token
export HF_TOKEN=your_hf_token_here

# Run the application
python app.py
```

The app will:
1. Download and process Swiss legal documents (~30-60 seconds)
2. Embed all document chunks (~60-90 seconds depending on rate limits)
3. Launch Gradio interface at http://localhost:7860

### Example Questions

Try these example questions (in German or French):

- "Was sind die Grundrechte gemäss der Bundesverfassung?"
- "Quels sont les droits fondamentaux selon la Constitution?"
- "Was sind die Pflichten bei einer Datenschutzverletzung nach dem nDSG?"

## Deployment to HuggingFace Spaces

### Via Web Interface

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Choose a name (e.g., `swiss-rag-demo`)
4. Select SDK: **Gradio**
5. Upload `app.py` and `requirements-swiss-rag.txt` (rename to `requirements.txt`)
6. In Space settings, add Secret: `HF_TOKEN` = your HuggingFace token
7. The Space will automatically build and deploy

### Via CLI

```bash
# Login to HuggingFace
huggingface-cli login

# Create a new Space
huggingface-cli repo create swiss-rag-demo --type space --space_sdk gradio

# Clone the Space repository
git clone https://huggingface.co/spaces/YOUR_USERNAME/swiss-rag-demo
cd swiss-rag-demo

# Copy files
cp path/to/app.py .
cp path/to/requirements-swiss-rag.txt requirements.txt
cp path/to/README-swiss-rag.md README.md

# Commit and push
git add .
git commit -m "Initial commit: Swiss RAG demo with Apertus"
git push

# Add HF_TOKEN as a Space secret via web interface
# Go to Space settings -> Variables and secrets -> Add secret
```

## Configuration

The app uses environment variables:

- **HF_TOKEN** (required): Your HuggingFace API token for Inference API access

## Performance Notes

- **Startup time**: ~2 minutes (document download + embedding)
- **Query time**: ~3-8 seconds (embedding + retrieval + LLM generation)
- **Rate limiting**: Embeddings are batched (10 chunks/batch) with 0.5s delays to avoid free tier limits
- **Fallback**: If Apertus is unavailable, falls back to HuggingFaceH4/zephyr-7b-beta

## Limitations

- Documents are re-downloaded and re-embedded on every restart (no persistence in HF Spaces)
- Free tier Inference API may have rate limits and cold start delays
- Document set is small and focused on Swiss legal documents only

## License

MIT License

## Acknowledgments

- **Apertus Model**: swiss-ai/Apertus-8B-Instruct-2509 - Swiss sovereign LLM
- **Documents**: Federal documents from fedlex.admin.ch (Swiss federal government)
- **Infrastructure**: HuggingFace Inference API and Spaces

---

**Data Sovereignty**: This demo showcases Swiss AI technology. The Apertus model is trained with Swiss data governance in mind, though the HuggingFace Inference API may run on infrastructure outside Switzerland.
