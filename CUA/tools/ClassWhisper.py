import requests
import logging
import os
from dotenv import load_dotenv
import pyaudio
import wave


load_dotenv()


class WhisperASR:
    def __init__(
        self,
        CHUNK=1024,
        RATE=4410,
        RECORD_SECONDS=5,
        WHISPER_MODEL=os.getenv("WHISPER_TURBO_ID"),
    ):
        """_summary_

        Args:
            CHUNK (int, optional): Audio chunk size for pyaudio recording. Defaults to 1024.
            RATE (int, optional): Sampling rate in Hz for pyaudio recording. Defaults to 4410.
            RECORD_SECONDS (int, optional): Total seconds going to be recorded by pyaudio. Defaults to 5.
            WHISPER_MODEL (_type_, optional): WhisperModel to do ASR inference. Defaults to os.getenv("WHISPER_TURBO_ID").
        """        

        self.logger = logging.getLogger(__name__)
        self.CHUNK = CHUNK  # Audio chunks sizes
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2  # Stereo for Windows.
        self.RATE = RATE  # Sampling rate (in Hz)
        self.RECORD_SECONDS = RECORD_SECONDS
        self.WHISPER_MODEL = WHISPER_MODEL

    def _request_asr_inference(self, audio_data):
        """Differences between an UploadFile or Bytes and sends them to the model to do inference from speech to text

        Args:
            audio_data (bytes): audio data bytes from a record

        Returns:
            transcription: transcription made by Whisper
        """        

        
        url = f"{os.getenv("BASE_URL")}/audio/transcriptions"
        headers = {"Authorization": f"Bearer {os.getenv("API_KEY")}"}

        try:
            if (
                hasattr(audio_data, "getvalue")
                and hasattr(audio_data, "name")
                and hasattr(audio_data, "type")
            ):
                files = {
                    "file": (audio_data.name, audio_data.getvalue(), audio_data.type)
                }
            else:
                files = {"file": ("audio.mp3", audio_data, "audio/mp3")}

            data = {"model": self.WHISPER_MODEL}
            response = requests.post(url, files=files, data=data, headers=headers)

            if response.status_code == 200:
                return response.json().get("text", "")
            else:
                self.logger.error(
                    f"Error en la transcripción de audio: {response.status_code} - {response.text}"
                )
                return f"Error {response.status_code}: {response.text}"
        except Exception as e:
            self.logger.error(f"Excepción al procesar el audio: {str(e)}")
            return f"Error: {str(e)}"

    def _record_audio(self):
        """Records an audio and saves it locally
        """        
        self.CHUNK
        self.FORMAT
        self.CHANNELS
        self.RATE
        self.RECORD_SECONDS

        p = pyaudio.PyAudio()

        stream = p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
        )

        print("Recording...")
        frames = []
        for _ in range(0, self.RATE // self.CHUNK * self.RECORD_SECONDS):
            data = stream.read(self.CHUNK)
            frames.append(data)

        print("Done")

        stream.stop_stream()
        stream.close()
        p.terminate()

        

        with wave.open("./CUA/tools/output.wav", "wb") as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(p.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(data=b"".join(frames))

    def whisper_SST(self):
        self._record_audio()
        with open("./CUA/tools/output.wav", "rb") as f:
            audio_bytes = f.read()
        transcription = self._request_asr_inference(audio_bytes)
        return transcription

