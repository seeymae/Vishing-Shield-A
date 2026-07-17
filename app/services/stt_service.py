import whisper

def transcribe_audio(file_path):
    # Modeli yükle (küçük ve hızlı olan 'base' modelini kullanıyoruz)
    model = whisper.load_model("tiny")
    # Sesi metne çevir
    result = model.transcribe(file_path)
    return result["text"]