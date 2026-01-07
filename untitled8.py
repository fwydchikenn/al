import streamlit as st
import pickle
import whisper
from rapidfuzz import fuzz, process
import os

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
        st.error("File pickle stream.pkl tidak ditemukan")
        return {}

    return pickle.load(open(DATA_PATH,'rb'))

data_pickle = load_pickle()

# key pickle kamu = teksIndonesia
verses = list(data_pickle.keys())

@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

model = load_whisper()

def transcribe_audio(audio_file):
    try:
        result = model.transcribe(audio_file, language="id")
        return result["text"]
    except Exception as e:
        st.error("Terjadi error saat proses Whisper transcribe")
        return None

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

            return {
                "score": score,
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
        # Simpan dengan nama tetap
        audio_file = "input_audio_user.wav"

        with open(audio_file, "wb") as f:
            f.write(uploaded.getbuffer())

        audio_file = os.path.abspath(audio_file)

        st.audio(audio_file)

else:
    audio = st.audio_input("🎤 Rekam Audio Ayat")

    if audio:
        audio_file = "input_audio_user.wav"

        with open(audio_file, "wb") as f:
            f.write(audio.getbuffer())

        audio_file = os.path.abspath(audio_file)

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
                    st.write(f"**Kemiripan:** {hasil['score']}%")

                    st.subheader("Teks Arab:")
                    st.write(hasil["arab"])

                    st.subheader("Terjemahan Indonesia:")
                    st.write(hasil["terjemahan"])

                    st.subheader("Audio Ayat Asli:")
                    st.audio(hasil["audio"])

                else:
                    st.error("Ayat tidak dapat dikenali")


# Penghapusan file dilakukan SETELAH selesai saja
if audio_file:
    try:
        os.remove("input_audio_user.wav")
    except:
        pass
