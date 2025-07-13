import streamlit as st
from PyPDF2 import PdfReader
import google.generativeai as genai
import os
from dotenv import load_dotenv
import time

st.set_page_config(
    page_title="Research Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://example.com',
        'Report a bug': "https://example.com",
        'About': "# AI Research Assistant"
    }
)

# Custom CSS
st.markdown("""
<style>
    /* Main container */
    .stApp {
        background-color: black;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #6e48aa 0%, #9d50bb 100%);
        color: white;
    }
    
    /* Sidebar text */
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {
        color: white !important;
    }
    
    /* Buttons */
    .stButton>button {
        border: 2px solid #6e48aa;
        border-radius: 20px;
        background-color: black;
        color: #6e48aa;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        background-color: #6e48aa;
        color: transparent;
    }
    
    /* Tabs */
    [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    [data-baseweb="tab"] {
        background: black;
        border-radius: 8px 8px 0 0 !important;
        padding: 10px 20px;
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        border: 2px dashed #6e48aa;
        border-radius: 15px;
        padding: 20px;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #6e48aa 0%, #9d50bb 100%);
    }
</style>
""", unsafe_allow_html=True)

# --- Configuration ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

generation_config = {
    "temperature": 0.3,  # Less creative but more factual
    "top_p": 0.7,
    "top_k": 50,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"}, 
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
]

model = genai.GenerativeModel('gemini-2.5-flash',
                            generation_config=generation_config,
                            safety_settings=safety_settings
                            )

if 'memory' not in st.session_state:
    st.session_state.memory = {
        'summary': "New conversation about uploaded document",
        'recent': []
    }

# --- Functions ---
def extract_text(file):
    if not hasattr(file, 'type'):  # Check if file-like object
        st.error("Invalid file object")
        return None
    
    """Extract text from PDF or TXT files"""
    try:
        if file.type == "application/pdf":
            reader = PdfReader(file)
            return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        return file.read().decode("utf-8")
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return None

def validate_response(response):
    """Handle both API responses and plain text"""
    if isinstance(response, str):
        return response  # Already text
    if not response.text:
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        return "No response generated"
    return response.text

def update_memory(question, answer):
    """Store only verified information"""
    # First check if answer is source-based
    time.sleep(0.5)
    is_verified = model.generate_content(
        f"Does this answer come directly from the source text?\n"
        f"ANSWER: {answer.split('*')[0]}\n"
        "Respond ONLY 'YES' or 'NO'"
    ).text.strip() == "YES"
    
    if is_verified:
        clean_answer = answer.split("\n\n*")[0]
        time.sleep(0.5)
        response = model.generate_content(
            f"Update summary using ONLY verified facts:\n"
            f"Current: {st.session_state.memory['summary']}\n"
            f"New Fact: {clean_answer}\n\n"
            "New summary (max 40 words):"
        )
        st.session_state.memory['summary'] = validate_response(response)
        st.session_state.memory['recent'].append((question, clean_answer))
        
        if len(st.session_state.memory['recent']) > 2:
            st.session_state.memory['recent'].pop(0)

def format_answer(response_text, context_text):
    """Ensure justification comes ONLY from source text"""
    # First verify if answer actually exists in source
    time.sleep(0.5)
    verification = model.generate_content(
        f"Verify if this answer is directly supported by the text:\n"
        f"ANSWER: {response_text}\n"
        f"TEXT:\n{context_text[:3000]}\n\n"
        "Respond ONLY with:\n"
        "'YES' if exact support exists\n"
        "'PARTIAL' if somewhat related\n"
        "'NO' if unsupported"
    ).text.strip()
    
    if verification == "NO":
        return "I couldn't find supporting evidence in the document"
    
    # Generate justification only from source text
    time.sleep(0.5)
    justification = model.generate_content(
        f"Extract ONE direct quote from this text supporting:\n{response_text}\n"
        f"TEXT:\n{context_text[:3000]}\n\n"
        "Format: 'This is directly supported by: [exact quote]'"
        "If no match, say: 'No direct quote found'"
    )
    return f"{response_text}\n\n*{validate_response(justification)}*"

def validate_evaluation(evaluation_text, correct_answer):
    """More robust conflict detection"""
    if ("None found" in evaluation_text and 
        any(score in evaluation_text for score in ["Correct", "Partially Correct"])):
        return "⚠️ Evaluation note: Answer may contain external knowledge\n\n" + evaluation_text
    return evaluation_text

def show_loading():
    """Animated loading indicator"""
    with st.empty():
        for i in range(3):
            st.write("Analyzing" + "." * (i + 1))
            time.sleep(0.3)
        st.write("Almost done...")

def chunk_text(text, size=10000):
    """Split text into manageable chunks"""
    return [text[i:i+size] for i in range(0, len(text), size)]

def display_history():
    """Show conversation timeline"""
    if st.session_state.memory['recent']:
        with st.expander("Conversation History"):
            for i, (q, a) in enumerate(st.session_state.memory['recent']):
                st.markdown(f"**Q{i+1}:** {q}")
                st.markdown(f"*A{i+1}:* {a}")
                st.divider()

def process_document(text):
    """Extract key information upfront"""
    with st.spinner("Analyzing document structure..."):
        results = model.generate_content(f"""
        Analyze this document and extract:
        1. 5 key topics
        2. 3 main conclusions
        3. Any important dates/figures
        4. Potential question areas
        
        Document: {text[:20000]}
        """).text
    return results

def generate_questions(text, num=3):
    """Generate higher quality questions"""
    prompt = f"""
    Generate {num} high-quality test questions about this document.
    For each question, include:
    - Question text
    - Correct answer
    - Difficulty level (Easy/Medium/Hard)
    - Relevant section reference
    
    Document: {text[:30000]}
    """
    return model.generate_content(prompt).text
# --- UI ---
st.set_page_config(page_title="Research Assistant", layout="wide")
st.title("🔍 Gemini Research Assistant")
with st.sidebar:
    st.caption("Conversation Memory")
    if st.button("Clear Memory"):
        st.session_state.memory = {
            'summary': "New conversation about uploaded document",
            'recent': []
        }
    if st.expander("Show Memory Details"):
        st.write("**Summary:**", st.session_state.memory['summary'])
        st.write("**Recent:**", st.session_state.memory['recent'])

# --- Document Upload ---
uploaded_file = st.file_uploader("Upload PDF/TXT", type=["pdf", "txt"], help="Maximum 10MB file size")

if uploaded_file:
    if uploaded_file.size > 10_000_000:  # 10MB limit
        st.error("File too large (max 10MB)")
    else:
        text = extract_text(uploaded_file)
        if text:
            st.session_state['text'] = text
            # Extract document topics once
            time.sleep(0.5)
            st.session_state['document_topics'] = model.generate_content(
                f"Extract 5-7 specific topics from this document:\n{text[:10000]}\n"
                "Format as: • Topic 1\n• Topic 2\n..."
            ).text
            st.success("Document processed successfully!")
            
            # --- Auto Summary ---
            with st.expander("📝 Auto-Summary", expanded=True):
                with st.spinner("Generating concise summary..."):
                    try:
                        time.sleep(0.5)
                        response = model.generate_content(
                            f"Create a strict 150-word summary of this technical document:\n{text[:30000]}"  # Limit input size
                        )
                        st.write(validate_response(response))
                    except Exception as e:
                        st.error(f"Summary generation failed: {str(e)}")

            # --- Interaction Tabs ---
            tab1, tab2 = st.tabs(["🔎 Ask Anything", "🧠 Challenge Me"])
            
            with tab1:
                st.subheader("Document Q&A")
                question = st.text_input("Your question", key="qa_input")
    
                if question and 'text' in st.session_state:
                    with st.spinner("Analyzing document..."):
                        try:
                            # Step 1: Direct text search
                            time.sleep(0.5)
                            search_response = model.generate_content(
                                f"Search this text for exact answer to: {question}\n"
                                f"DOCUMENT:\n{st.session_state['text'][:30000]}\n\n"
                                "Respond ONLY with:\n"
                                "- The exact matching paragraph if found\n"
                                "- 'NO_MATCH' if nothing matches"
                            )
                
                            # Step 2: Only proceed if text exists
                            if "NO_MATCH" not in search_response.text:
                                # Generate answer from found text
                                time.sleep(0.5)
                                response = model.generate_content(
                                    f"Based on this exact text:\n{search_response.text}\n\n"
                                    f"Answer this question concisely:\n{question}\n"
                                    "Include 'This is directly from the text:' followed by the relevant sentence"
                                )
                                answer = validate_response(response)
                            else:
                                # Verify no answer exists
                                time.sleep(0.5)
                                verification = model.generate_content(
                                    f"Confirm this document contains NO information about: {question}\n"
                                    f"DOCUMENT:\n{st.session_state['text'][:10000]}\n\n"
                                    "Respond ONLY with:\n"
                                    "'CONFIRMED_ABSENT' or 'POSSIBLE_MATCH'"
                                ).text
                    
                                answer = (
                                    "The document doesn't contain this information. "
                                    f"Main topics available: {st.session_state.get('document_topics','')}"
                                    if "CONFIRMED_ABSENT" in verification
                                    else "I couldn't locate this information. Try rephrasing."
                                )
                
                            st.markdown(f"**Answer:** {answer}")
                            update_memory(question, answer)
                
                        except Exception as e:
                            st.error(f"Analysis failed: {str(e)}")            
            with tab2:
                st.subheader("Comprehension Challenge")
    
                # Initialize session state for questions/answers
                if 'challenge_questions' not in st.session_state:
                    st.session_state.challenge_questions = []
                if 'user_answers' not in st.session_state:
                    st.session_state.user_answers = {}
    
                # Generate questions button
                if st.button("Generate New Questions"):
                    with st.spinner("Creating challenge questions..."):
                        try:
                            st.session_state.user_answers = {}
            
                            # More reliable generation prompt
                            response = model.generate_content(
                                f"Create 3 questions about this document:\n{text[:30000]}\n"
                                "For each question provide:\n"
                                "1. The question itself\n"
                                "2. The exact answer from the text\n"
                                "Format like this exactly:\n"
                                "1. Q: [question]\n"
                                "1. A: [answer]\n\n"
                                "2. Q: [question]\n"
                                "2. A: [answer]\n\n"
                                "3. Q: [question]\n"
                                "3. A: [answer]"
                            )
            
                            # Parse response
                            questions = []
                            blocks = response.text.split('\n\n')
                            for block in blocks:
                                if block.startswith('1. Q:') or block.startswith('2. Q:') or block.startswith('3. Q:'):
                                    q_line, a_line = block.split('\n')[:2]
                                    questions.append({
                                        "question": q_line.split(':')[1].strip(),
                                        "answer": a_line.split(':')[1].strip()
                                    })
            
                            st.session_state.challenge_questions = questions
            
                            if not st.session_state.challenge_questions:
                                st.error("No questions generated. Please try again.")
                                st.text_area("Raw Response", response.text)
            
                            st.rerun()
            
                        except Exception as e:
                            st.error(f"Question generation failed: {str(e)}")
                            if 'response' in locals():
                                with st.expander("Debug Details"):
                                    st.text("API Response:", response.text)
    
                # Display questions and answer inputs
                if st.session_state.challenge_questions:
                    st.markdown("### Test Your Knowledge")
                    for i, qa in enumerate(st.session_state.challenge_questions):
                        st.markdown(f"**Question {i+1}:** {qa['question']}")
            
                        # Get or initialize user answer
                        answer_key = f"answer_{i}"
                        if answer_key not in st.session_state.user_answers:
                            st.session_state.user_answers[answer_key] = ""
            
                        user_answer = st.text_area(
                            f"Your answer to question {i+1}",
                            key=f"user_answer_{i}",
                            value=st.session_state.user_answers[answer_key]
                        )
                        st.session_state.user_answers[answer_key] = user_answer
            
                        # Evaluate answer when provided
                        if user_answer.strip():
                            with st.spinner(f"Evaluating question {i+1}..."):

                                time.sleep(0.5)
                                evaluation_response = model.generate_content(
                                    f"Evaluate strictly based on this document excerpt:\n{text[:1000]}\n\n"
                                    f"QUESTION: {qa['question']}\n"
                                    f"CORRECT ANSWER (from document): {qa['answer']}\n"
                                    f"USER ANSWER: {user_answer}\n\n"
                                    "Format your evaluation with these REQUIRED sections:\n"
                                    "1. DOCUMENT RELEVANCE: Does the question relate to this text? (Yes/No)\n"
                                    "2. ANSWER ACCURACY: Does the user answer match document content? (Correct/Partially Correct/Incorrect)\n"
                                    "3. SCORE: 1-10 based on document alignment\n"
                                    "4. TEXT EVIDENCE: Exact quote supporting evaluation (or 'None found')\n"
                                    "5. SUGGESTIONS: How to better use the document"
                                )
                                feedback = validate_response(evaluation_response)
                                if not feedback:  # Handle empty evaluations
                                    feedback = "Evaluation failed - please try again"
                                st.error("Evaluation error occurred")
                                st.markdown(f"**Evaluation:** {feedback}")
                                st.divider()