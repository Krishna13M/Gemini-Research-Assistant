# 🔍 Gemini Research Assistant

A document-based AI assistant built using Streamlit and Gemini 2.5 Flash. Upload a PDF or TXT file, ask questions about it, challenge yourself with comprehension tests, and ensure every answer is grounded in the original document.

---

## 🚀 Features

- ✅ **Document Upload** – Supports `.pdf` and `.txt` files (up to 10MB)
- 📝 **Auto-Summary** – Generates a concise 150-word summary of the uploaded document
- 🔎 **Ask Anything** – Ask questions strictly based on the uploaded content
- 📌 **Source Verification** – Ensures answers are directly supported by the document
- 🧠 **Challenge Mode** – Automatically generates and evaluates comprehension questions
- 💾 **Memory Management** – Maintains summary and recent Q&A history for better context

---
## 🧠 Architecture / Reasoning Flow

This app uses a **modular, memory-aware reasoning architecture** powered by Google Gemini 2.5 Flash and Streamlit.

### 1. 📄 Document Upload & Parsing
- Users upload a `.pdf` or `.txt` file.
- File is parsed using:
  - `PyPDF2` for PDFs (text-based only)
  - UTF-8 decoding for TXT files
- File size capped at **10MB** to stay within processing limits.

### 2. 📝 Auto-Summary
- Once uploaded, a **150-word summary** is generated using Gemini:
  - Prompted with the first ~30,000 characters of the document
  - Provides a high-level overview of key content

---

### 3. 🔎 Ask Anything (Document Q&A)
- Users ask natural-language questions about the document.
- The model prompt includes:
  - 🧾 **Primary source** (first ~15,000 chars of document)
  - 🧠 **Conversation context**: summary + last 2 verified Q&A pairs
- Gemini is instructed to:
  - **Answer strictly based on the document**
  - Use memory only to understand follow-ups — not as a fact source

#### ✔️ Verification & Justification
1. Gemini's answer is validated:
   - Prompted again to confirm: "Is this directly supported by the source?"
2. If supported:
   - A **direct quote** is extracted from the source text to justify the answer
   - The answer + quote is shown to the user
   - It’s stored in memory for context in future prompts
3. If not supported:
   - The system returns: _"I couldn't find supporting evidence in the document"_

---

### 4. 🧠 Challenge Me (Comprehension Test)
- Clicking “Generate Questions” prompts Gemini to create 3 QA pairs.
- Users write their own answers.
- Gemini evaluates responses using 5 criteria:
  1. **DOCUMENT RELEVANCE**: Does the question relate to the document?
  2. **ANSWER ACCURACY**: Correct / Partially Correct / Incorrect
  3. **SCORE**: 1–10
  4. **TEXT EVIDENCE**: Direct quote (if any)
  5. **SUGGESTIONS**: Feedback for improving alignment

---

### 5. 💾 Memory Management (Stateful Context)
- Stored in `st.session_state.memory`
  - `summary`: Current document summary (auto-updated)
  - `recent`: Last two verified Q&A pairs
- Ensures follow-up queries are **context-aware** but not hallucinated.

---

## 🧰 Technologies Used

- [Streamlit](https://streamlit.io/) – for building the web app
- [Google Gemini API](https://ai.google.dev/) – for text generation and reasoning
- [PyPDF2](https://pypi.org/project/PyPDF2/) – for PDF text extraction
- [python-dotenv](https://pypi.org/project/python-dotenv/) – for environment variable management

---

## ⚙️ Setup Instructions

### 1. **Clone the repository**

```bash
git clone https://github.com/yourusername/gemini-research-assistant.git
cd gemini-research-assistant
```

### 2. **Create a virtual environment (recommended)**
```
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3. **Install dependencies**

```
pip install -r requirements.txt
```

### 4. **Add your Gemini API Key**

Create a .env file in the root directory:
```
GEMINI_API_KEY=your_google_gemini_api_key
```
### 5. **Run the application**

```
streamlit run app.py
```
Then open http://localhost:8501 in your browser.
