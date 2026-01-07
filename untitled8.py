import streamlit as st
import pickle
import whisper
from rapidfuzz import fuzz, process
from pydub import AudioSegment
import os

st.set_page_config(
    page_title="Identifikasi Ayat Quran",
    page_icon="📖",
    layout="centered"
)

st.title("📖 Identifikasi Ayat Al-Qur’an Otomatis dari Audio")

DATA_PATH = "stream.pkl"

@st.cache_data
def load_data_pickle():
    data = pickle.load(open(DATA_PATH,'rb'))
    return data

data_pickle = load_data_pickle()

verses = data_pickle.get("verses", [])
mapping = data_pickle.get("mapping", {})

@st.cache_resource
def load_whisper_model():
    return whisper.load_model("base")

model = load_whisper_model()

def convert_audio(audio_file):
    if audio_file.endswith(".mp3"):
        sound = AudioSegment.from_mp3(audio_file)
        wav_file = "audio_temp.wav"
        sound.export(wav_file, format="wav")
        return wav_file
    return audio_file

def transcribe_audio(audio_file):
    audio_file = convert_audio(audio_file)
    result = model.transcribe(audio_file, language="id")
    return result["text"]

def identify_verse(teks):
    if not verses:
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
                "terjemahan": ayat["teksIndonesia"]
            }

    return None


option = st.radio(
    "Pilih Metode Input Audio:",
    ["Upload Audio", "Rekam Audio Sendiri"]
)

audio_file = None

if option == "Upload Audio":
    uploaded = st.file_uploader(
        "Silakan upload audio:",
        type=["mp3","wav"]
    )

    if uploaded:
        with open("input_user_audio","wb") as f:
            f.write(uploaded.getbuffer())

        audio_file = "input_user_audio"
        st.audio(audio_file)

else:
    audio = st.audio_input("🎤 Rekam Audio Ayat")

    if audio:
        with open("rekaman.wav","wb") as f:
            f.write(audio.getbuffer())

        audio_file = "rekaman.wav"
        st.audio(audio_file)


if st.button("Identifikasi Ayat") and audio_file:
    with st.spinner("Memproses audio..."):
        teks = transcribe_audio(audio_file)

        st.subheader("Hasil Transkripsi:")
        st.write(teks)

        hasil = identify_verse(teks)

        if hasil:
            st.success("Ayat berhasil dikenali!")

            st.subheader("Hasil Identifikasi")

            st.write(f"**Surat:** {hasil['surat']}")
            st.write(f"**Nomor Ayat:** {hasil['nomorAyat']}")
            st.write(f"**Kemiripan:** {hasil['score']}%")

            st.subheader("Teks Arab:")
            st.write(hasil["arab"])

            st.subheader("Terjemahan:")
            st.write(hasil["terjemahan"])

        else:
            st.error("Ayat tidak dapat dikenali")


if audio_file == "input_user_audio":
    try:
        os.remove(audio_file)
    except:
        pass
