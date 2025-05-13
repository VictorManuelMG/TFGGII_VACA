import requests
import os
from dotenv import load_dotenv
import pyaudio
import wave

from CUA.util.logger import logger


load_dotenv()


class whisper_asr:
    def __init__(
        self,
        CHUNK=1024,
        RATE=4410,
        RECORD_SECONDS=5,
        WHISPER_MODEL=os.getenv("WHISPER_TURBO_ID"),
        TTS_MODEL=os.getenv("TTS_MODEL_ID"),
        TTS_VOICE="base",
    ):
        """_summary_

        Args:
            CHUNK (int, optional): Audio chunk size for pyaudio recording. Defaults to 1024.
            RATE (int, optional): Sampling rate in Hz for pyaudio recording. Defaults to 4410.
            RECORD_SECONDS (int, optional): Total seconds going to be recorded by pyaudio. Defaults to 5.
            WHISPER_MODEL (_type_, optional): WhisperModel to do ASR inference. Defaults to os.getenv("WHISPER_TURBO_ID").
        """
        self.CHUNK = CHUNK  # Audio chunks sizes
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2  # Stereo for Windows.
        self.RATE = RATE  # Sampling rate (in Hz)
        self.RECORD_SECONDS = RECORD_SECONDS
        self.WHISPER_MODEL = WHISPER_MODEL
        self.TTS_MODEL = TTS_MODEL
        self.TTS_VOICE = TTS_VOICE

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
                logger.error(
                    f"Error en la transcripción de audio: {response.status_code} - {response.text}"
                )
                return f"Error {response.status_code}: {response.text}"
        except Exception as e:
            logger.error(f"Excepción al procesar el audio: {str(e)}")
            return f"Error: {str(e)}"

    def _record_audio(self,path_record:str = "./CUA/tools/output.wav"):
        """Records an audio and saves it locally"""
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

        with wave.open(path_record, "wb") as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(p.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(data=b"".join(frames))

    def whisper_SST(self):
        """Calls whisper to make a transcription of a user voice prompt

        Returns:
            transcription: returns the transcription of the prompt for the agent.
        """
        self._record_audio()
        with open("./CUA/tools/output.wav", "rb") as f:
            audio_bytes = f.read()
        transcription = self._request_asr_inference(audio_bytes)
        logger.debug(f"Whisper inference result: {transcription}")
        return transcription

    def _request_tts_inference(self, text: str):
        """Generates a recording from a text (text to speech)

        Args:
            text (str): text to make a record from

        Returns:
            audio_data: returns bytes to generate the audio
        """
        url = f"{os.getenv('BASE_URL')}/tts/generate"
        headers = {"Authorization": f"Bearer {os.getenv('API_KEY')}"}

        form_data = {"model": self.TTS_MODEL, "voice": self.TTS_VOICE, "text": text}
        try:
            response = requests.post(url, form_data, headers=headers)
            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                return {"audio_data": response.content, "content_type": content_type}
            else:
                logger.error(
                    f"Error en la respuesta del TTS: {response.status_code} - {response.text}"
                )
                return {}
        except Exception as e:
            logger.error(f"Error en la respuesta del TTS: {str(e)}")
            return {}

    def whisper_TTS(self, text: str):
        """Transforms text given into an audio to reproduce back.

        Args:
            text (str): text to convert into audio
        """

        audio_bytes = self._request_tts_inference(text)
        with open("./CUA/tools/audio_TTS.wav", "wb") as af:
            af.write(audio_bytes["audio_data"])

        with wave.open("./CUA/tools/audio_TTS.wav", "rb") as wf:
            p = pyaudio.PyAudio()

            stream = p.open(
                format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
            )

            while len(data := wf.readframes(self.CHUNK)):
                stream.write(data)

            stream.close()
            p.terminate()
