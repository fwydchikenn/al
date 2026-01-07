import streamlit as st
import pickle
import whisper
from rapidfuzz import fuzz, process
import os
import re

st.set_page_config(
    page_title="Identifikasi Ayat Quran",
    page_icon="📖",
    layout="centered"
)

st.title("📖 Identifikasi Ayat Al-Qur’an dari Audio")

DATA_PATH = "stream.pkl"

@st.cache_data
def load_data_pickle():
    if not os.path.exists(DATA_PATH):
        st.error("File stream.pkl tidak ditemukan")
        return {}

    data = pickle.load(open(DATA_PATH, 'rb'))
    return data

data_pickle = load_data_pickle()

# Seluruh key pickle = teksIndonesia
verses = list(data_pickle.keys())

@st.cache_resource
def load_whisper_model():
    return whisper.load_model("base")

model = load_whisper_model()

def parse_audio_url(url):
    try:
        match = re.search(r'/audio-partial/.+/(\d{3})(\d{3})\.mp3', url)
        if match:
            surah = int(match.group(1))
            ayat = int(match.group(2))
            return surah, ayat
    except:
        pass
    return None, None

def transcribe_audio(audio_file):
    if not os.path.exists(audio_file):
        st.error("File audio tidak ditemukan")
        return None

    result = model.transcribe(audio_file, language="id")
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
        ayat = data_pickle.get(best_text)

        if ayat:
            url_audio = ayat["audio"]["01"]
            surah, nomorAyat = parse_audio_url(url_audio)

            return {
                "score": score,
                "surahDetected": surah,
                "surat": ayat.get("teksLatin", "").split()[0],
                "nomorAyat": ayat["nomorAyat"],
                "arab": ayat["teksArab"],
                "terjemahan": ayat["teksIndonesia"],
                "audio": url_audio
            }

    return None


option = st.radio(
    "Pilih Metode Input Audio:",
    ["Upload Audio", "Rekam Langsung"]
)

audio_file = None

if option == "Upload Audio":
    uploaded = st.file_uploader(
        "Upload audio ayat:",
        type=["mp3", "wav"]
    )

    if uploaded:
        audio_file = uploaded.name

        with open(audio_file, "wb") as f:
            f.write(uploaded.getbuffer())

        st.audio(audio_file)

else:
    audio = st.audio_input("🎤 Rekam Audio Ayat")

    if audio:
        audio_file = "rekaman.wav"

        with open(audio_file, "wb") as f:
            f.write(audio.getbuffer())

        st.audio(audio_file)


if st.button("Identifikasi Ayat"):
    if not audio_file:
        st.warning("Masukkan audio terlebih dahulu")
    else:
        with st.spinner("Memproses audio..."):
            teks = transcribe_audio(audio_file)

            if not teks:
                st.error("Transkripsi gagal")
            else:
                st.subheader("Hasil Transkripsi:")
                st.write(teks)

                hasil = identify_verse(teks)

                if hasil:
                    st.success("Ayat berhasil dikenali!")

                    st.subheader("Detail Ayat")

                    st.write(f"**Nomor Ayat:** {hasil['nomorAyat']}")
                    st.write(f"**Tingkat Kemiripan:** {hasil['score']}%")

                    st.subheader("Teks Arab:")
                    st.write(hasil["arab"])

                    st.subheader("Terjemahan Indonesia:")
                    st.write(hasil["terjemahan"])

                    st.subheader("Audio Ayat (Asli dari API):")
                    st.audio(hasil["audio"])

                else:
                    st.error("Ayat tidak dapat dikenali")


if audio_file and audio_file != "rekaman.wav":
    try:
        os.remove(audio_file)
    except:
        pass
