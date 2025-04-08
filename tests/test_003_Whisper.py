
from CUA.tools.ClassWhisper import WhisperASR
import os
from dotenv import load_dotenv
from pathlib import Path
import time
import wave #Needed to hear records made  # noqa: F401
import pyaudio #Needed to hear records made  # noqa: F401

load_dotenv()


def test_initialization():
    """Test of instanziation of all params of whisper class object
    """    
    whisper = WhisperASR(
        1024, 4410, 5, os.getenv("WHISPER_TURBO_ID"), os.getenv("TTS_MODEL_ID"), "base"
    )
    assert whisper.CHUNK == 1024,f"Did not instantiate CHUNK param right, expected 1024 got: {whisper.CHUNK}"
    assert whisper.RATE == 4410, f"Did not instantiate RATE param right, expected 4410 got: {whisper.RATE}"
    assert whisper.RECORD_SECONDS == 5, f"Did not instantiate RECORD_SECONDS param right, expected 5 got: {whisper.RECORD_SECONDS}"
    assert whisper.WHISPER_MODEL == "turbo", f"Did not instantiate WHISPER_MODEL param right, expected 'turbo' got :{whisper.WHISPER_MODEL}"
    assert whisper.TTS_MODEL == "coqui-tts",f"Did not instantiate TTS_MODEL param right, expected 'coqui-tts' got: {whisper.TTS_MODEL}"
    assert whisper.TTS_VOICE == "base", f"Did not instantiate TTS_VOICE param right, expected 'base' got: {whisper.TTS_VOICE}"


def test_request_tts_inference():
    """Tests the generation of an audio file by the model, optional you can enable commented section to test the audio output.
    """    
    #This test will assert if the function generates an audio file, we will not bother with the audio itself as the LLM might generate different audios for the same prompt.
    whisper = WhisperASR(1024, 4410, 5, os.getenv("WHISPER_TURBO_ID"), os.getenv("TTS_MODEL_ID"), "base")
    os.makedirs(Path(__file__).resolve().parent / "resources/generatedAudio", exist_ok=True)
    #Initialization of the model as it might be offline and we've to wait for it to become available

    audio_bytes = whisper._request_tts_inference("Initialization")
    time.sleep(40)

    audio_bytes = whisper._request_tts_inference("Esto es un audio de prueba.")

    with open("./resources/generatedAudio/audio_TTS.wav","wb") as af:
        af.write(audio_bytes["audio_data"])


    # #In case of tester wanting reproduction of the file to see the audio quality, uncomment this section:
    # with wave.open("./resources/generatedAudio/audio_TTS.wav", "rb") as wf:
    #     p = pyaudio.PyAudio()

    #     stream = p.open(
    #         format=p.get_format_from_width(wf.getsampwidth()),
    #         channels=wf.getnchannels(),
    #         rate=wf.getframerate(),
    #         output=True,
    #     )

    #     while len(data := wf.readframes(whisper.CHUNK)):
    #         stream.write(data)

    #     stream.close()
    #     p.terminate()
    

    file_path = Path(__file__).parent / "./resources/generatedAudio/audio_TTS.wav"
    assert file_path.exists(),"No se ha generado correctamente el archivo de audio."


def test_request_asr_inference():
    """Test the generation of a transcription from the audio made from previous tests.
    """    
    whisper = WhisperASR(1024, 4410, 5, os.getenv("WHISPER_TURBO_ID"), os.getenv("TTS_MODEL_ID"), "base")
    audio_bytes = whisper._request_tts_inference("Esto es un audio de prueba.")

    response = whisper._request_asr_inference(audio_bytes["audio_data"])
    assert isinstance(response,str),"Didn't generate audio transcription correctly."
    # This assertion depends on a language model (LLM) response. While it is expected to consistently return the correct transcription for this controlled audio input,
    # some minor variations may occasionally occur due to the generative nature of the model.
    assert(response.lower() == " esto es un audio de prueba."),f"Audio content isn't the same as the transcription, expected: 'esto es un audio de prueba' got :{response.lower()}"



def test_record_audio():
    whisper = WhisperASR(1024, 4410, 5, os.getenv("WHISPER_TURBO_ID"), os.getenv("TTS_MODEL_ID"), "base")
    whisper._record_audio("./resources/generatedAudio/output_record.wav")
    path_record = Path(__file__).parent / "resources/generatedAudio/output_record.wav"

    print(path_record)

    assert(path_record.exists()),"Audio record wasn't generated properly."

    #   #Uncomment this section to hear recorded audio.
    # with wave.open(str(path_record), "rb") as wf:
    #     p = pyaudio.PyAudio()

    #     stream = p.open(
    #         format=p.get_format_from_width(wf.getsampwidth()),
    #         channels=wf.getnchannels(),
    #         rate=wf.getframerate(),
    #         output=True,
    #     )

    #     while len(data := wf.readframes(whisper.CHUNK)):
    #         stream.write(data)

    #     stream.close()
    #     p.terminate()

def test_whisper_SST():
    #No need of testing as it's a call to other functions and saving audio files on directories.
    pass

def test_whisper_TTS():
    #No need of testing as it's a call to other functions and saving audio files on directories.
    pass