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
def load_data_pickle():
    if not os.path.exists(DATA_PATH):
        st.error("File database stream.pkl tidak ditemukan")
        return {}

    data = pickle.load(open(DATA_PATH, 'rb'))
    return data

data_pickle = load_data_pickle()

verses = list(data_pickle.keys())

@st.cache_resource
def load_whisper_model():
    return whisper.load_model("base")

model = load_whisper_model()

def simpan_audio_bytes(audio_bytes, suffix):
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp.write(audio_bytes)
    temp.close()
    return temp.name

def transcribe_audio(audio_path):
    if not os.path.exists(audio_path):
        return None

    try:
        # panggil whisper dengan parameter device eksplisit
        result = model.transcribe(audio_path, fp16=False)
        teks = result.get("text","").strip()

        if teks == "":
            return None

        return teks
    except Exception:
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
            return {
                "score": score,
                "surat": ayat["namaLatin"],
                "nomorAyat": ayat["nomorAyat"],
                "arab": ayat["teksArab"],
                "terjemahan": ayat["teksIndonesia"],
                "audioUrl": ayat["audio"]["01"]
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
        type=["mp3", "wav", "ogg", "m4a"]
    )

    if uploaded:
        ext = os.path.splitext(uploaded.name)[1]
        audio_file = simpan_audio_bytes(uploaded.getbuffer(), ext)
        audio_file = os.path.abspath(audio_file)

        st.audio(audio_file)

else:
    audio = st.audio_input("🎤 Rekam Audio Ayat")

    if audio:
        audio_file = simpan_audio_bytes(audio.getbuffer(), ".ogg")
        audio_file = os.path.abspath(audio_file)

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

                    st.write(f"**Surat:** {hasil['surat']}")
                    st.write(f"**Nomor Ayat:** {hasil['nomorAyat']}")
                    st.write(f"**Kemiripan:** {hasil['score']}%")

                    st.subheader("Teks Arab:")
                    st.write(hasil["arab"])

                    st.subheader("Terjemahan:")
                    st.write(hasil["terjemahan"])

                    st.subheader("Audio Ayat Asli:")
                    st.audio(hasil["audioUrl"])

                else:
                    st.error("Ayat tidak dapat dikenali")


if audio_file:
    try:
        os.remove(audio_file)
    except Exception:
        pass
