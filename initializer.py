from main_loop import Loop
from CUA.tools.class_whisper import WhisperASR
from CUA.tools.class_browser_use import BrowserUse
import time


whisper = WhisperASR()
browser = BrowserUse()

initializer_loop_endpoints = Loop(whisper,browser)
initializer_loop_endpoints.select_agent_model(2)

def initialize_endpoints():
    initializer_loop_endpoints.run("Utiliza tu herramienta ScreenInterpreter para decirme que ves")
    initializer_loop_endpoints.run("Utiliza tu herramienta SimpleScreenInterpreter para decirme que ves")
    whisper.whisper_STT()
    whisper.whisper_TTS("Inicializando")



initialize_endpoints()
time.sleep(10)