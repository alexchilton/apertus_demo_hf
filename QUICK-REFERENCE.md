# 🇨🇭 Swiss RAG Demo - Quick Reference Card

## Files Created

| File | Purpose |
|------|---------|
| `app.py` | Main Gradio application (18KB) |
| `requirements-swiss-rag.txt` | Python dependencies |
| `README-swiss-rag.md` | HF Space README with metadata |
| `DEPLOYMENT-GUIDE.md` | Complete testing & deployment guide |
| `PROJECT-SUMMARY.md` | Project overview and summary |
| `verify_setup.py` | Dependency verification script |

## Quick Commands

### 1. Verify Setup
```bash
python verify_setup.py
```

### 2. Install Dependencies
```bash
pip install -r requirements-swiss-rag.txt
```

### 3. Set HF Token
```bash
export HF_TOKEN=hf_your_token_here
```

### 4. Run Locally
```bash
python app.py
```
Opens at: http://localhost:7860

### 5. Deploy to HF Spaces (CLI)
```bash
huggingface-cli login
huggingface-cli repo create swiss-rag-demo --type space --space_sdk gradio
git clone https://huggingface.co/spaces/YOUR_USERNAME/swiss-rag-demo
cd swiss-rag-demo
cp ../app.py .
cp ../requirements-swiss-rag.txt requirements.txt
cp ../README-swiss-rag.md README.md
git add . && git commit -m "Initial commit" && git push
```
Then add `HF_TOKEN` secret in Space settings.

## Test Questions

### 🇩🇪 German - Fundamental Rights
```
Was sind die Grundrechte gemäss der Bundesverfassung?
```

### 🇫🇷 French - Constitution
```
Quels sont les droits fondamentaux selon la Constitution?
```

### 🇩🇪 German - Data Protection
```
Was sind die Pflichten bei einer Datenschutzverletzung nach dem nDSG?
```

## Key Features

✅ **3 Swiss Documents**
- Bundesverfassung (DE)
- Constitution fédérale (FR)
- Datenschutzgesetz nDSG (DE)

✅ **Models**
- Embeddings: sentence-transformers/all-MiniLM-L6-v2
- LLM: swiss-ai/Apertus-8B-Instruct-2509
- Fallback: HuggingFaceH4/zephyr-7b-beta

✅ **Tech Stack**
- Gradio 4.44.0
- HuggingFace Inference API
- PyMuPDF for PDF parsing
- NumPy + SciPy for retrieval

## Performance

| Metric | Value |
|--------|-------|
| Startup time | ~2 minutes |
| Query time | 3-8 seconds |
| Memory usage | ~500MB |
| Documents | 3 PDFs |
| Total chunks | ~600-1200 |

## Important Notes

⚠️ **For HF Spaces, rename files:**
- `requirements-swiss-rag.txt` → `requirements.txt`
- `README-swiss-rag.md` → `README.md`

🔑 **Environment Variables:**
- `HF_TOKEN` (required): Your HuggingFace API token

📖 **Documentation:**
- Full guide: `DEPLOYMENT-GUIDE.md`
- Project info: `PROJECT-SUMMARY.md`
- HF README: `README-swiss-rag.md`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Missing HF_TOKEN | `export HF_TOKEN=your_token` |
| Import errors | `pip install -r requirements-swiss-rag.txt` |
| Model 503 error | App auto-falls back to zephyr-7b-beta |
| Rate limiting | Already handled with batching + delays |
| Documents fail | App continues with available docs |

## Architecture Flow

```
User Question
    ↓
Embed via HF API (sentence-transformers)
    ↓
Cosine Similarity Search (numpy/scipy)
    ↓
Top-4 Chunks Retrieved
    ↓
Build Prompt with Context
    ↓
LLM Generation (Apertus 8B)
    ↓
Answer + Source Citations
```

## Links

- **HF Spaces**: https://huggingface.co/spaces
- **Apertus Model**: https://huggingface.co/swiss-ai/Apertus-8B-Instruct-2509
- **Create HF Token**: https://huggingface.co/settings/tokens
- **Document Source**: https://www.fedlex.admin.ch

---

**Status: ✅ Ready for deployment!**

For detailed instructions, see `DEPLOYMENT-GUIDE.md`
