# Swiss RAG Demo - Testing & Deployment Guide

## Project Files

- **app.py** - Main Gradio application
- **requirements-swiss-rag.txt** - Python dependencies
- **README-swiss-rag.md** - HuggingFace Space README (with metadata header)

## Local Testing

### 1. Set up environment

```bash
# Create virtual environment (optional but recommended)
python3.11 -m venv venv-swiss-rag
source venv-swiss-rag/bin/activate  # On Windows: venv-swiss-rag\Scripts\activate

# Install dependencies
pip install -r requirements-swiss-rag.txt
```

### 2. Set HuggingFace Token

Get your token from: https://huggingface.co/settings/tokens

```bash
# Linux/Mac
export HF_TOKEN=hf_your_token_here

# Windows (Command Prompt)
set HF_TOKEN=hf_your_token_here

# Windows (PowerShell)
$env:HF_TOKEN="hf_your_token_here"
```

### 3. Run the application

```bash
python app.py
```

**Expected startup sequence:**
1. Downloads 3 PDF documents from fedlex.admin.ch (~30-60 seconds)
2. Parses PDFs and creates ~400 token chunks
3. Embeds all chunks via HF Inference API (~60-120 seconds)
4. Launches Gradio UI at http://localhost:7860

**Console output should show:**
```
INFO - Downloading Bundesverfassung (DE) from https://...
INFO - Extracted X pages from Bundesverfassung (DE)
INFO - Created Y chunks from Bundesverfassung (DE)
...
INFO - Embedding batch 1/N
...
INFO - Successfully embedded X/Y chunks
INFO - RAG system ready!
```

### 4. Test with example questions

Once the UI loads, try these three test cases:

#### Test 1: German - Grundrechte (Fundamental Rights)
**Question:**
```
Was sind die Grundrechte gemäss der Bundesverfassung?
```

**Expected behavior:**
- Should retrieve chunks from "Bundesverfassung (DE)"
- Answer should mention specific fundamental rights (Art. 7-34)
- Should be in German
- Should cite specific articles if possible

#### Test 2: French - Droits fondamentaux
**Question:**
```
Quels sont les droits fondamentaux selon la Constitution?
```

**Expected behavior:**
- Should retrieve chunks from "Constitution fédérale (FR)"
- Answer should be in French
- Should list fundamental rights from French Constitution

#### Test 3: German - Data Protection (nDSG)
**Question:**
```
Was sind die Pflichten bei einer Datenschutzverletzung nach dem nDSG?
```

**Expected behavior:**
- Should retrieve chunks from "Datenschutzgesetz nDSG (DE)"
- Answer should mention notification obligations (Meldepflicht)
- Should reference specific articles about data breach handling
- Should be in German

### 5. Verify UI components

Check that all UI elements work:
- ✅ Status bar shows "Ready - X chunks loaded across 3 documents"
- ✅ Question textbox accepts input
- ✅ "Ask / Fragen" button triggers query
- ✅ Example questions are clickable
- ✅ Answer appears in answer box
- ✅ "Retrieved context" accordion shows 4 chunks with sources
- ✅ "Loaded documents" accordion shows all 3 docs with chunk counts

### 6. Test error handling

#### Missing HF_TOKEN
```bash
unset HF_TOKEN  # or remove the environment variable
python app.py
```
Expected: UI should show error message "Please set HF_TOKEN environment variable"

#### Invalid question
- Enter empty question → Should show "Please enter a question."

## Deployment to HuggingFace Spaces

### Method 1: Web Interface (Easiest)

1. **Create Space**
   - Go to https://huggingface.co/spaces
   - Click "Create new Space"
   - Name: `swiss-rag-demo` (or your choice)
   - License: MIT
   - SDK: **Gradio**
   - Hardware: **CPU basic** (free tier is sufficient)

2. **Upload Files**
   - Upload `app.py`
   - Upload `requirements-swiss-rag.txt` **renamed to** `requirements.txt`
   - Upload `README-swiss-rag.md` **renamed to** `README.md`

3. **Configure Secrets**
   - Go to Space Settings → Variables and secrets
   - Add new secret:
     - Name: `HF_TOKEN`
     - Value: `hf_your_token_here`

4. **Wait for Build**
   - Space will automatically build (~2-3 minutes)
   - First run will download and process documents (~2 minutes)
   - Status will change from "Building" → "Running"

5. **Test the Space**
   - Open the Space URL
   - Try the three example questions above
   - Verify all functionality works

### Method 2: Git CLI (For developers)

```bash
# 1. Login to HuggingFace
huggingface-cli login
# Enter your token when prompted

# 2. Create Space
huggingface-cli repo create swiss-rag-demo --type space --space_sdk gradio

# 3. Clone the Space repository
git clone https://huggingface.co/spaces/YOUR_USERNAME/swiss-rag-demo
cd swiss-rag-demo

# 4. Copy files (adjust paths as needed)
cp ../app.py .
cp ../requirements-swiss-rag.txt requirements.txt
cp ../README-swiss-rag.md README.md

# 5. Commit and push
git add app.py requirements.txt README.md
git commit -m "Initial commit: Swiss RAG demo with Apertus"
git push

# 6. Add HF_TOKEN secret via web interface
# Go to https://huggingface.co/spaces/YOUR_USERNAME/swiss-rag-demo/settings
# Add secret: HF_TOKEN = your_token
```

### Method 3: Using Git with existing repo

If you already have the files in a local git repository:

```bash
# Add HF Space as remote
git remote add hf-space https://huggingface.co/spaces/YOUR_USERNAME/swiss-rag-demo

# Ensure files are named correctly
mv requirements-swiss-rag.txt requirements.txt
mv README-swiss-rag.md README.md

# Commit
git add app.py requirements.txt README.md
git commit -m "Add Swiss RAG demo"

# Push to HF Space
git push hf-space main  # or 'master' depending on your branch
```

## Troubleshooting

### Issue: "Model loading" or 503 errors

**Cause**: Apertus model may be cold-starting or unavailable on free tier

**Solution**: 
- App automatically falls back to `zephyr-7b-beta`
- Status bar will show "Using fallback LLM"
- Wait a few minutes and try again for Apertus

### Issue: Rate limiting during embedding

**Cause**: Too many API calls to free tier Inference API

**Solution**:
- App already batches embeddings (10 at a time with 0.5s delay)
- If still hitting limits, increase sleep time in code:
  ```python
  time.sleep(1.0)  # Change from 0.5 to 1.0
  ```

### Issue: Documents fail to download

**Cause**: Network issues or fedlex.admin.ch temporary unavailability

**Solution**:
- App skips failed documents gracefully
- Check console logs to see which documents loaded
- Retry by restarting the app

### Issue: Out of memory

**Cause**: Too many chunks to embed in memory

**Solution**:
- Current settings should work on free tier CPU
- Documents are relatively small (~200-400 chunks each)
- If needed, reduce chunk size or overlap

### Issue: Slow startup on HF Spaces

**Cause**: Cold start + document download + embedding

**Solution**:
- Normal for first launch (~2 minutes total)
- Subsequent runs reuse cached models
- Consider upgrading to persistent storage (paid tier) to cache embeddings

## Performance Benchmarks

Expected timings on free tier:

| Stage | Time |
|-------|------|
| Document download | 20-40s |
| PDF parsing | 5-10s |
| Embedding (batch) | 60-120s |
| Total startup | ~2 minutes |
| Query (embed + retrieve + LLM) | 3-8s |

## Verification Checklist

Before deploying to HF Spaces:

- [ ] App runs locally without errors
- [ ] All 3 documents load successfully
- [ ] Status bar shows correct chunk count
- [ ] Example questions return relevant answers
- [ ] Retrieved context shows correct sources and pages
- [ ] Answers are in the same language as questions
- [ ] Error messages are user-friendly
- [ ] HF_TOKEN is set as environment variable (not hardcoded!)

## Example Q&A Pairs for Testing

### 1. German - Grundrechte

**Q:** Was sind die Grundrechte gemäss der Bundesverfassung?

**Expected A:** Should mention rights like:
- Menschenwürde (Human dignity)
- Recht auf Leben (Right to life)
- Persönliche Freiheit (Personal freedom)
- Meinungsfreiheit (Freedom of expression)
- Should reference Articles from the Constitution

### 2. French - Constitution

**Q:** Quels sont les droits fondamentaux selon la Constitution?

**Expected A:** Should list rights in French:
- Dignité humaine
- Droit à la vie
- Liberté personnelle
- Should reference specific articles from French version

### 3. German - Data Protection

**Q:** Was sind die Pflichten bei einer Datenschutzverletzung nach dem nDSG?

**Expected A:** Should mention:
- Meldepflicht (Notification obligation)
- Eidgenössischer Datenschutzbeauftragter (Federal Data Protection Commissioner)
- Betroffene Personen informieren (Inform affected persons)
- Should reference nDSG articles

## Additional Notes

- **No persistence**: Every restart downloads and re-embeds documents (by design for HF Spaces free tier)
- **CPU only**: Works on free tier, no GPU needed
- **Multilingual**: Model supports DE/FR/IT/EN, responds in query language
- **Rate limits**: Free tier has limits, app includes delays to stay within them
- **Fallback**: Automatically switches to zephyr-7b-beta if Apertus unavailable

## Support

For issues or questions:
1. Check console logs for detailed error messages
2. Verify HF_TOKEN is set correctly
3. Check HuggingFace status page for API outages
4. Review the README-swiss-rag.md for additional details

---

**Ready to deploy!** 🇨🇭🚀
