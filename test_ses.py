import simpleaudio as sa

def play_wav_file(file_path):
    try:
        wave_obj = sa.WaveObject.from_wave_file(file_path)
        play_obj = wave_obj.play()
        print("Ses dosyası başarıyla çalınıyor...")
        play_obj.wait_done() # Ses bitene kadar bekle
    except FileNotFoundError:
        print(f"Hata: '{file_path}' dosyası bulunamadı.")
    except Exception as e:
        print(f"Bir hata oluştu: {str(e)}")

# Kullanım
play_wav_file('test.wav')