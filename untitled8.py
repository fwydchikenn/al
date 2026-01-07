import streamlit as st
import pickle
import whisper
from rapidfuzz import fuzz, process
import os
import tempfile

st.set_page_config(
    page_title="Identifikasi Ayat Quran",
    page_icon="📖",
    layout="centered"
)

st.title("📖 Identifikasi Ayat Al-Qur’an dari Audio")

DATA_PATH = "stream.pkl"

@st.cache_data
def load_pickle():
    if not os.path.exists(DATA_PATH):
        st.error("Database stream.pkl tidak ditemukan")
        return {}

    return pickle.load(open(DATA_PATH,'rb'))

data_pickle = load_pickle()

verses = list(data_pickle.keys())

@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

model = load_whisper()

def simpan_audio_bytes(audio_bytes, suffix):
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp.write(audio_bytes)
    temp.close()
    return temp.name

def transcribe_audio(audio_path):
    try:
        result = model.transcribe(audio_path)
        return result["text"]
    except:
        return None

def identify_verse(teks):
    if not teks:
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
            return {
                "score": score,
                "nomorAyat": ayat["nomorAyat"],
                "arab": ayat["teksArab"],
                "terjemahan": ayat["teksIndonesia"],
                "audio": ayat["audio"]["01"]
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
        type=["mp3","wav","ogg","m4a"]
    )

    if uploaded:
        audio_file = simpan_audio_bytes(uploaded.getbuffer(), os.path.splitext(uploaded.name)[1])
        st.audio(audio_file)

else:
    audio = st.audio_input("🎤 Rekam Audio Ayat")

    if audio:
        audio_file = simpan_audio_bytes(audio.getbuffer(), ".ogg")
        st.audio(audio_file)


if st.button("Identifikasi Ayat"):
    if not audio_file:
        st.warning("Masukkan audio terlebih dahulu")
    else:
        with st.spinner("Memproses..."):
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

                    st.write(f"Nomor Ayat: {hasil['nomorAyat']}")
                    st.write(f"Tingkat Kemiripan: {hasil['score']}%")

                    st.subheader("Teks Arab:")
                    st.write(hasil["arab"])

                    st.subheader("Terjemahan:")
                    st.write(hasil["terjemahan"])

                    st.subheader("Audio Ayat Asli:")
                    st.audio(hasil["audio"])

                else:
                    st.error("Ayat tidak dapat dikenali")


if audio_file:
    try:
        os.remove(audio_file)
    except:
        pass
