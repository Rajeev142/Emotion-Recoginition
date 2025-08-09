import streamlit as st
from deepface import DeepFace
import numpy as np
import cv2
from PIL import Image
import tempfile
import os
import random
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# ----------- Load Environment Variables ----------- #
load_dotenv()
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# ----------- Page Config ----------- #
st.set_page_config(page_title="Emotion Recognition", layout="centered")

# ----------- CSS Styling ----------- #
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(145deg, #c9e7f3, #e0f7fa);
        font-family: 'Segoe UI', sans-serif;
    }
    .element-container:has(> div[data-testid="stCameraInput"]),
    .element-container:has(> div[data-testid="stFileUploader"]) {
        background: rgba(255, 255, 255, 0.5);
        backdrop-filter: blur(8px);
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        margin: 20px auto;
        width: fit-content;
    }
    .stButton > button {
        background-color: #ffffff;
        color: #000000;
        border: none;
        padding: 10px 20px;
        border-radius: 12px;
        box-shadow: 5px 5px 15px #b0cfd6, -5px -5px 15px #ffffff;
        transition: all 0.3s ease-in-out;
    }
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 2px 2px 10px #99b8c0, -2px -2px 10px #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

# ----------- Session State Init ----------- #
if "shayari" not in st.session_state:
    st.session_state.shayari = None
if "song_path" not in st.session_state:
    st.session_state.song_path = None
if "detected_emotion" not in st.session_state:
    st.session_state.detected_emotion = None

# ----------- Title ----------- #
st.title("🎭 Emotion Recognition App")

# ----------- Image Input ----------- #
option = st.radio("Choose input method:", ["📸 Use Camera", "📂 Upload Image"], horizontal=True)
image = None

if option == "📸 Use Camera":
    camera_image = st.camera_input("Take a picture")
    if camera_image:
        image = Image.open(camera_image)

elif option == "📂 Upload Image":
    uploaded_image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    if uploaded_image:
        image = Image.open(uploaded_image)

# ----------- Emotion Detection & Face Box ----------- #
if image:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        image.save(temp_file.name)
        temp_path = temp_file.name

    st.session_state.shayari = None
    st.session_state.song_path = None
    st.session_state.detected_emotion = None

    try:
        result = DeepFace.analyze(img_path=temp_path, actions=['emotion'], enforce_detection=False)
        emotion = result[0]['dominant_emotion'].capitalize()
        st.session_state.detected_emotion = emotion

        region = result[0]["region"]
        x, y, w, h = region["x"], region["y"], region["w"], region["h"]

        img_cv = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
        cv2.rectangle(img_cv, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # First show preview image with rectangle
        st.image(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB), caption="🖼 Detected Face", use_container_width=True)

        # Now show detected emotion below the preview
        st.success(f"✅ Detected Emotion: *{emotion}*")

        # ---------- Shayari & Song Functions ---------- #
        def get_shayari(emotion):
            try:
                base = Path("C:/Users/ADMIN/Desktop/Internship Project/shayri")
                files = list((base / emotion.lower()).glob("*.txt"))
                if files:
                    return random.choice(files).read_text(encoding='utf-8')
            except:
                return "⚠ Shayari not found."

        def get_song(emotion):
            try:
                base = Path("C:/Users/ADMIN/Desktop/Internship Project/music")
                files = list((base / emotion.capitalize()).glob("*.mp3"))
                if files:
                    return str(random.choice(files))
            except:
                return None

        if st.session_state.shayari is None:
            st.session_state.shayari = get_shayari(emotion)
        if st.session_state.song_path is None:
            st.session_state.song_path = get_song(emotion)

    except Exception as e:
        st.error(f"❌ Error during detection: {e}")
    finally:
        os.remove(temp_path)

# ----------- Display Buttons ----------- #
if st.session_state.detected_emotion:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📖 View Shayari"):
            st.info(st.session_state.shayari or "⚠ Shayari not found.")
    with col2:
        if st.button("🎵 Play Music"):
            if st.session_state.song_path:
                st.audio(st.session_state.song_path, format='audio/mp3')
            else:
                st.warning("⚠ Song not found.")

# ----------- Email Sender Function ----------- #
def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"❌ Failed to send email: {e}")
        return False

# ----------- Suggestion Form ----------- #
st.markdown("---")
st.subheader("💡 Suggest Us")

with st.form("suggestion_form"):
    name = st.text_input("Your Name")
    #email = st.text_input("Your Email")
    #phone = st.text_input("Your Phone Number")
    suggestion = st.text_area("Your Suggestion")

    if st.form_submit_button("Submit Suggestion"):
        if name.strip() and email.strip() and phone.strip() and suggestion.strip():
            body = f"👤 Name: {name}\n📧 Email: {email}\n📱 Phone: {phone}\n💡 Suggestion:\n{suggestion}"
            if send_email("New Suggestion from Emotion Recognition App", body):
                st.success("✅ Thank you! Your suggestion has been sent.")
        else:
            st.warning("⚠ Please fill all fields.")
