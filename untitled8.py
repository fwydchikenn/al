import streamlit as st
import whisper
from rapidfuzz import fuzz, process
import json
import os
import tempfile

st.set_page_config(
    page_title="Identifikasi Ayat Quran Otomatis",
    page_icon="📖",
    layout="centered"
)

st.title("📖 Sistem Identifikasi Ayat Al-Qur’an dari Audio")

# Load database JSON
@st.cache_data
def load_database():
    if not os.path.exists("verses.json") or not os.path.exists("mapping.json"):
        st.error("Database JSON belum tersedia")
        return [], {}

    verses = json.load(open("verses.json",'r',encoding='utf-8'))
    mapping = json.load(open("mapping.json",'r',encoding='utf-8'))

    return verses, mapping

verses, mapping = load_database()

# Load Whisper model
@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

model = load_whisper()

def simpan_audio(uploaded_file):
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(uploaded_file.getbuffer())
    temp.close()
    return temp.name

def rekam_ke_file(audio_bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(audio_bytes)
        return f.name

def transcribe_audio(audio_path):
    result = model.transcribe(audio_path, language="id")
    return result["text"]

def identify_verse(teks):
    if not teks or not verses:
        return None

    match = process.extractOne(
        teks,
        verses,
        scorer=fuzz.ratio
    )

    if match:
        best_text = match[0]
        score = match[1]

        ayat = mapping.get(best_text)

        if ayat:
            return {
                "score": score,
                "surat": ayat["namaLatin"],
                "nomorAyat": ayat["nomorAyat"],
                "arab": ayat["teksArab"],
                "terjemahan": ayat["teksIndonesia"],
                "audioUrl": ayat["audioUrl"]
            }

    return None


option = st.radio(
    "Pilih Metode Input Audio:",
    ["Upload Audio", "Rekam Audio Sendiri"]
)

audio_file = None

if option == "Upload Audio":
    uploaded = st.file_uploader(
        "Upload audio ayat (mp3/wav):",
        type=["mp3","wav","ogg","m4a"]
    )

    if uploaded:
        audio_file = simpan_audio(uploaded)
        st.audio(audio_file)

else:
    audio = st.audio_input("🎤 Rekam Audio Ayat")

    if audio:
        audio_file = rekam_ke_file(audio.getbuffer())
        st.audio(audio_file)


if st.button("Identifikasi Ayat"):
    if not audio_file:
        st.warning("Masukkan audio terlebih dahulu")
    else:
        with st.spinner("Memproses..."):
            teks = transcribe_audio(audio_file)

            st.subheader("Hasil Transkripsi:")
            st.write(teks)

            hasil = identify_verse(teks)

            if hasil:
                st.success("Ayat berhasil dikenali!")

                st.subheader("Detail Hasil Identifikasi")

                st.write(f"**Surat:** {hasil['surat']}")
                st.write(f"**Nomor Ayat:** {hasil['nomorAyat']}")
                st.write(f"**Kemiripan:** {hasil['score']}%")

                st.subheader("Teks Arab:")
                st.write(hasil["arab"])

                st.subheader("Terjemahan Indonesia:")
                st.write(hasil["terjemahan"])

                st.subheader("Audio Ayat Asli dari API eQuran.id:")
                st.audio(hasil["audioUrl"])

            else:
                st.error("Ayat tidak dapat dikenali")


if audio_file:
    try:
        os.remove(audio_file)
    except:
        pass
