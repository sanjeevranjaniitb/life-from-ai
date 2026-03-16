import streamlit as st
import os
import time
import base64
import cv2
import shutil
import json
from src.rag_engine import RAGEngine
from src.tts_generator import generate_audio
from src.viseme_generator import VisemeGenerator
from src.phoneme_engine import PhonemeEngine
from src.vision_engine import VisionEngine
from src.config import DEFAULT_AVATAR_PATH

# --- Cleanup ---
def cleanup_previous_session():
    if os.path.exists("outputs"):
        try:
            shutil.rmtree("outputs")
        except Exception as e:
            print(f"Error cleaning up outputs: {e}")
    os.makedirs("outputs", exist_ok=True)
    
    if os.path.exists("temp"):
        for item in os.listdir("temp"):
            item_path = os.path.join("temp", item)
            if item != "visemes" and os.path.isfile(item_path):
                try:
                    os.remove(item_path)
                except Exception as e:
                    print(f"Error removing {item_path}: {e}")

# --- Loaders ---
@st.cache_resource(show_spinner="Loading RAG Engine...")
def load_rag_engine(): return RAGEngine()

@st.cache_resource(show_spinner="Loading Vision Engine...")
def load_vision_engine(): return VisionEngine()

@st.cache_resource(show_spinner="Loading Animation Engine...")
def load_animation_engines(): return VisemeGenerator(), PhonemeEngine()

st.set_page_config(page_title="Knowledge To Life", layout="wide")

if "startup_done" not in st.session_state:
    cleanup_previous_session()
    st.session_state.startup_done = True

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Helpers ---
def render_avatar_html(b64_data):
    return f"""
    <div style="display: flex; justify-content: center; align-items: center; width: 100%; margin-top: 20px;">
        <div style="width: 300px; height: 300px; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 8px rgba(0,0,0,0.1); background: #000;">
            <img src="data:image/jpeg;base64,{b64_data}" style="width: 300px; height: 300px; object-fit: cover; display: block;">
        </div>
    </div>
    """

def img_to_b64(img):
    if img is None: return ""
    _, buffer = cv2.imencode('.jpg', img)
    return base64.b64encode(buffer).decode()

def play_viseme_animation(text, audio_path, container, viseme_imgs, static_b64, audio_placeholder):
    try:
        from pydub import AudioSegment
        sound = AudioSegment.from_mp3(audio_path)
        duration = sound.duration_seconds
        
        # Inject Client-Side Audio for mobile support
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        audio_b64 = base64.b64encode(audio_bytes).decode()
        
        ts = int(time.time() * 1000)
        audio_html = f"""
            <audio autoplay="true" style="display:none" id="audio_{ts}">
                <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
            </audio>
            <script>
                var audio = document.getElementById("audio_{ts}");
                var promise = audio.play();
                if (promise !== undefined) {{
                    promise.catch(error => {{
                        console.log("Autoplay blocked. User interaction needed.");
                    }});
                }}
            </script>
        """
        audio_placeholder.markdown(audio_html, unsafe_allow_html=True)
        
        # Python-side Animation Loop
        start_time = time.time()
        char_speed = 14 
        
        while (time.time() - start_time) < duration:
            elapsed = time.time() - start_time
            char_idx = int(elapsed * char_speed)
            
            if char_idx < len(text):
                char = text[char_idx]
                phoneme_eng = load_animation_engines()[1]
                viseme_name = phoneme_eng.get_viseme_for_char(char)
                if viseme_name in viseme_imgs:
                    b64_frame = img_to_b64(viseme_imgs[viseme_name])
                    container.markdown(render_avatar_html(b64_frame), unsafe_allow_html=True)
            
            time.sleep(0.05)
        
        # Reset to static
        container.markdown(render_avatar_html(static_b64), unsafe_allow_html=True)
        audio_placeholder.empty()
        
    except Exception as e:
        st.error(f"Playback error: {e}")


# --- Init Avatar ---
if "avatar_path" not in st.session_state:
    st.session_state.avatar_path = DEFAULT_AVATAR_PATH
    if not os.path.exists("temp/visemes"):
        viseme_gen, _ = load_animation_engines()
        with st.spinner("Creating Avatar Voice Model..."):
            st.session_state.viseme_dir = viseme_gen.generate_visemes(DEFAULT_AVATAR_PATH)

# --- Sidebar ---
with st.sidebar:
    st.title("Settings")
    uploaded_avatar = st.file_uploader("Upload Avatar", type=["jpg", "png", "jpeg"])
    if uploaded_avatar:
        with open("assets/custom.jpg", "wb") as f:
            f.write(uploaded_avatar.getbuffer())
        st.session_state.avatar_path = "assets/custom.jpg"
        viseme_gen, _ = load_animation_engines()
        with st.spinner("Updating Avatar Voice Model..."):
            st.session_state.viseme_dir = viseme_gen.generate_visemes("assets/custom.jpg")
        st.success("Avatar Updated!")

# --- UI ---
st.markdown("<h1 style='text-align: center;'>Knowledge To Life</h1>", unsafe_allow_html=True)
col_vid, col_chat = st.columns([1, 2])

# Load Base Images
if "viseme_dir" not in st.session_state:
    st.session_state.viseme_dir = "temp/visemes"
    
v_dir = st.session_state.viseme_dir
viseme_imgs = {}
if v_dir:
    for name in ['idle', 'a', 'e', 'o', 'm']:
        path = os.path.join(v_dir, f"{name}.jpg")
        if os.path.exists(path):
            viseme_imgs[name] = cv2.imread(path)

# Safe fallback if idle image doesn't exist
if 'idle' in viseme_imgs:
    b64_static = img_to_b64(viseme_imgs['idle'])
else:
    img = cv2.imread(st.session_state.avatar_path)
    b64_static = img_to_b64(img)

with col_vid:
    avatar_container = st.empty()
    audio_player_container = st.empty()
    avatar_container.markdown(render_avatar_html(b64_static), unsafe_allow_html=True)

with col_chat:
    tab1, tab2 = st.tabs(["Chat with Knowledge", "Snap, Live & Learn"])
    
    # --- CHAT ---
    with tab1:
        rag_engine = load_rag_engine()
        uploaded_pdf = st.file_uploader("Upload Knowledge (PDF)", type="pdf", key="pdf_up")
        if uploaded_pdf:
            if "last_file" not in st.session_state or st.session_state.last_file != uploaded_pdf.name:
                with st.spinner("Reading Document..."):
                    with open("temp/doc.pdf", "wb") as f:
                        f.write(uploaded_pdf.getbuffer())
                    rag_engine.ingest_pdf("temp/doc.pdf")
                    st.session_state.last_file = uploaded_pdf.name
                st.success("Knowledge Base Ready!")

        chat_container = st.container()
        with chat_container:
            for idx, msg in enumerate(st.session_state.messages):
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    if msg["role"] == "assistant" and msg.get("audio_path"):
                        meta_c1, meta_c2 = st.columns([1, 5])
                        with meta_c1:
                            if msg.get("latency"):
                                st.caption(f"⏱️ {msg['latency']:.2f}s")
                        with meta_c2:
                            if st.button("🔄 Replay", key=f"replay_{idx}"):
                                play_viseme_animation(msg["content"], msg["audio_path"], avatar_container, viseme_imgs, b64_static, audio_player_container)

        if prompt := st.chat_input("Ask a question..."):
            start_ts = time.time()
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

            with st.spinner("Thinking..."):
                answer = rag_engine.answer_question(prompt)
            
            audio_path = generate_audio(answer)
            latency = time.time() - start_ts
            
            st.session_state.messages.append({"role": "assistant", "content": answer, "latency": latency, "audio_path": audio_path})
            
            with chat_container:
                with st.chat_message("assistant"):
                    st.markdown(answer)
                    st.caption(f"⏱️ {latency:.2f}s")

            if audio_path:
                play_viseme_animation(answer, audio_path, avatar_container, viseme_imgs, b64_static, audio_player_container)

    # --- SNAP ---
    with tab2:
        vision_engine = load_vision_engine()
        
        if 'camera_active' not in st.session_state: st.session_state.camera_active = False
        if 'snap_image' not in st.session_state: st.session_state.snap_image = None

        if not st.session_state.camera_active and st.session_state.snap_image is None:
            if st.button("Start Camera"):
                st.session_state.camera_active = True
                st.rerun()
        
        elif st.session_state.camera_active:
            cam_image = st.camera_input("Take a picture")
            if cam_image:
                st.session_state.snap_image = cam_image
                st.session_state.camera_active = False
                st.rerun()
                
        elif st.session_state.snap_image:
            st.image(st.session_state.snap_image)
            
            if 'analysis_done' not in st.session_state:
                with st.spinner("Analyzing..."):
                    desc = vision_engine.analyze_image(st.session_state.snap_image)
                    res = f"I see {desc}"
                    st.session_state.analysis_result = res
                    st.session_state.analysis_done = True
                    
                    aud = generate_audio(res)
                    if aud:
                        play_viseme_animation(res, aud, avatar_container, viseme_imgs, b64_static, audio_player_container)

            st.info(f"**Insight:** {st.session_state.analysis_result}")
            
            if st.button("Snap Another"):
                st.session_state.snap_image = None
                if 'analysis_done' in st.session_state:
                    del st.session_state.analysis_done
                st.session_state.camera_active = True
                st.rerun()
