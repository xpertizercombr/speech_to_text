import os
from google.cloud import speech_v1 as speech
from google.cloud import storage
from pydub import AudioSegment
import io

def arquivo_existe_no_gcs(bucket_name, blob_name, local_file_path):
    """Verifica se um arquivo com o mesmo nome e tamanho já existe no GCS."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    if blob.exists():
        blob.reload()
        local_file_size = os.path.getsize(local_file_path)
        if blob.size == local_file_size:
            print(f"Arquivo {blob_name} já existe no bucket {bucket_name} com o mesmo tamanho.")
            return True
    return False

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    if arquivo_existe_no_gcs(bucket_name, destination_blob_name, source_file_name):
        print("Upload não necessário. O arquivo já existe no GCS.")
        return

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(f"Arquivo {source_file_name} carregado para {destination_blob_name}.")

def transcrever_audio_google_assincrono_gcs(gcs_uri):
    # Inicializa o cliente do Google Cloud Speech
    client = speech.SpeechClient()

    # Configura o áudio e as opções de reconhecimento
    audio = speech.RecognitionAudio(uri=gcs_uri)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="pt-BR",
    )

    # Realiza a transcrição assíncrona
    operation = client.long_running_recognize(config=config, audio=audio)

    print("Esperando pela operação para ser concluída...")
    response = operation.result(timeout=None)  # Timeout infinito

    # Processa e imprime a transcrição
    for result in response.results:
        print("Transcrição: {}".format(result.alternatives[0].transcript))

    return response

def deletar_arquivo_do_gcs(bucket_name, blob_name):
    """Deleta um arquivo do bucket do GCS."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    if blob.exists():
        blob.delete()
        print(f"Arquivo {blob_name} deletado do bucket {bucket_name}.")
    else:
        print(f"Arquivo {blob_name} não encontrado no bucket {bucket_name}.")

# Caminho para o arquivo de áudio
caminho_arquivo = "AUDIO-2024-07-03-15-45-05.m4a"
bucket_name = "seu-bucket-name"
destination_blob_name = "audio/temp.wav"

# Verifica se o arquivo de áudio existe
if not os.path.exists(caminho_arquivo):
    raise FileNotFoundError(f"O arquivo de áudio '{caminho_arquivo}' não foi encontrado.")

# Converte o arquivo de áudio para WAV com taxa de amostragem de 16000 Hz
audio = AudioSegment.from_file(caminho_arquivo, format="m4a")
audio = audio.set_frame_rate(16000)
audio.export("temp.wav", format="wav")

# Faz o upload do arquivo de áudio para o Google Cloud Storage
upload_to_gcs(bucket_name, "temp.wav", destination_blob_name)

# URI do arquivo no Google Cloud Storage
gcs_uri = f"gs://{bucket_name}/{destination_blob_name}"

# Transcreve o áudio usando a URI do Google Cloud Storage
response = transcrever_audio_google_assincrono_gcs(gcs_uri)

# Deleta o arquivo do Google Cloud Storage após a transcrição
deletar_arquivo_do_gcs(bucket_name, destination_blob_name)



#export GOOGLE_APPLICATION_CREDENTIALS="/Users/leonardooliveira/Documents/GitHub/speech_to_text/speechtotextxpertizer-ba79ee5b048b.json"