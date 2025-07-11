import streamlit as st
from groq import Groq
from gtts import gTTS
import PyPDF2
import tempfile
import base64
import os

# ========== CONFIG ==========
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]  # ✅ Use secret key
MODEL_NAME = "llama3-70b-8192"

# ========== INIT GROQ ==========
client = Groq(api_key=GROQ_API_KEY)

# ========== TTS with gTTS ==========
def speak(text):
    try:
        tts = gTTS(text)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            audio_file = fp.name

        # Convert MP3 to base64
        with open(audio_file, "rb") as f:
            audio_bytes = f.read()
            b64 = base64.b64encode(audio_bytes).decode()

        # Streamlit Audio Player
        audio_html = f"""
        <audio autoplay controls>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
        """
        st.markdown("### 🔈 Listen to the Answer")
        st.markdown(audio_html, unsafe_allow_html=True)

    except Exception as e:
        st.error("TTS Failed")
        st.text(str(e))

# ========== PDF EXTRACT ==========
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# ========== LLM CALL ==========
def get_response(prompt):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a helpful, knowledgeable tutor."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# ========== STREAMLIT UI ==========
st.set_page_config(page_title="Personal Tutor Bot", page_icon="🧠", layout="wide")
st.title("🧠 Personal Tutor Bot")
st.markdown("Get explanations, quizzes, or notes for any subject!")

col1, col2 = st.columns([1, 2])

with col1:
    subject_input = st.text_input("✏️ Enter Subject (Any subject)", placeholder="Eg: Thermodynamics, Data Structures")
    mode = st.radio("Choose Mode", ["Ask a Question", "Generate Quiz", "Generate Notes"])
    use_tts = st.checkbox("🔊 Enable Text-to-Speech")

uploaded_pdf = st.file_uploader("📄 Upload a Syllabus PDF (optional)", type=["pdf"])

pdf_context = ""
if uploaded_pdf:
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_pdf.read())
        pdf_context = extract_text_from_pdf(tmp_file.name)
        st.success("✅ PDF Uploaded & Text Extracted")

query = st.text_area("💡 Enter your question, topic, or concept", height=150)

if st.button("🚀 Generate Response"):
    final_prompt = f"You are a tutor for {subject_input}. "
    if pdf_context:
        final_prompt += f"Refer to the following syllabus context: {pdf_context[:1000]}\n"

    if mode == "Ask a Question":
        final_prompt += f"Answer this question: {query}"
    elif mode == "Generate Quiz":
        final_prompt += f"Create a 5-question quiz on the topic: {query}. Include options and correct answers."
    elif mode == "Generate Notes":
        final_prompt += f"Prepare concise study notes for: {query}"

    with st.spinner("Thinking..."):
        output = get_response(final_prompt)

    st.markdown("### 📘 Response:")
    st.markdown(output)

    if use_tts:
        speak(output[:300])  # Limit to 300 chars for short speech
