from CUA.tools.class_whisper import WhisperASR
import pyaudio
import wave
import numpy as np
from copy import deepcopy

from CUA.util.logger import logger  # noqa: F401
from CUA.util.path import project_root_path





class ContinuousRecorder:
    def __init__(self,Whisper:WhisperASR = WhisperASR()):
        self.CHUNK = 441
        self.RATE = 4410
        self.RECORD_SECONDS = 1
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.SILENCE_THRESHOLD = 45
        self.root = project_root_path() / "CUA/tools/output.wav"
        self.result_inference = ""
        self.whisper = Whisper

    def _is_silent(self, audio_data):
        """Detect if chunk is silent based on RMS

        Args:
            audio_data (audio_bytes): Audio data to be analyzed

        Returns:
            bool: returns True if silence, False if sound.
        """
        # RMS algorithm = audio_data ^ 2 -> average of audio data -> root of average -> RMS
        rms = np.sqrt(np.mean(np.square(np.frombuffer(audio_data, dtype=np.int16))))
        # Uncomment loggers in case of needed otherwhise mantain this line commented as it generates a lot of logs
        # logger.debug(f"RMS from 0.1 seconds of audio: {rms}")
        # logger.debug(f"Result of comparation between silence threshhold and rms : {rms < self.SILENCE_THRESHOLD}")
        if np.isnan(rms):
            return True

        return rms < self.SILENCE_THRESHOLD

    def _send_audio_endpoint(self, audio_bytes):
        """Sends audio to whisper endpoint

        Args:
            audio_bytes (audio_bytes): audio bytes from composed .wav

        Returns:
            response(str): whisper inference speech to text
        """
        return self.whisper._request_asr_inference(audio_bytes)

    def permanent_stt(self):
        """Permanent speech to text function, after detecting audio sound (assuming it's a voice) generates chunks of audio and composes it on a .wav to be send to whisper endpoint."""
        silent_count = 0
        hit_count = 0
        recording_status = False
        p = pyaudio.PyAudio()
        recording_buffer = []
        silence_buffer = []

        stream = p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
        )

        while True:
            chunk = stream.read(self.CHUNK)
            silent = self._is_silent(chunk)

            if not recording_status:
                silence_buffer.append(chunk)
                if len(silence_buffer) > 15:
                    silence_buffer.pop(0)

                if not silent:
                    hit_count += 1
                    logger.warning(f"Hits:{hit_count}")
                    if hit_count >= 4:
                        recording_status = True
                        recording_buffer = deepcopy(silence_buffer)
                        silence_buffer.clear()

                else:
                    hit_count = 0

            else:
                recording_buffer.append(chunk)
                if silent:
                    silent_count += 1
                else:
                    silent_count = 0

                if silent_count >= 5:
                    recording_status = False
                    logger.info("Sending audio to transcript...")
                    response = self._format_chunks_and_send(self.root, recording_buffer)
                    self.result_inference = response

                    silent_count = 0
                    hit_count = 0
                    recording_buffer.clear()

    def _format_chunks_and_send(self, path_record, chunks):
        """Formats the chunks with relevant audio and sends it to whisper endpoint
        Args:
            path_record (Path): Path to where .wav will be saved
            chunks (audio_bytes): list of chunks with relevant audio
        Returns:
            response(str): response from whispers inference
        """

        p = pyaudio.PyAudio()
        with wave.open(str(path_record), "wb") as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(p.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b"".join(chunks))
        with open(path_record, "rb") as audio_file:
            audio_bytes = audio_file.read()

        response = self._send_audio_endpoint(audio_bytes)

        return response

    def get_result(self):
        return self.result_inference
