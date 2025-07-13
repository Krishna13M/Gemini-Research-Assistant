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

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
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

