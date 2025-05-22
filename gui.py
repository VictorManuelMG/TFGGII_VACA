import os
import sys
import tkinter as tk

from tkinter import scrolledtext as st

from CUA.tools.class_browser_use import BrowserUse
from CUA.tools.class_whisper import WhisperASR
from main_loop import Loop

from threading import Thread

Whisper = WhisperASR()
Browser = BrowserUse()

CUA_loop = Loop( Whisper, Browser)
CUA_loop.select_agent_model(2)

tts_status = False


def agent_response(user_prompt:str):
    """Sends a prompt to the CUA and parses it's last response and thinking of the whole process.

    Args:
        user_prompt (str): User prompt
    """    
    def task():
        btn.config(state="disabled")
        record_btn.config(state="disabled")

        agent_thinking.config(state="normal")
        agent_chat.config(state="normal")

        if not user_prompt:
            return

        agent_chat.insert(tk.END, f"\n 😃 : {user_prompt}\n", "usuario")
        agent_chat.insert(tk.END, "\n")

        res = CUA_loop.run(user_prompt,True)

        agent_thinking.delete(2.0,tk.END)
        agent_thinking.insert(tk.END,"\n")

        # Agent thinking log extraction
        for msg in res["messages"]:
            if hasattr(msg, "content") and isinstance(msg.content, list):
                for block in msg.content:
                    if isinstance(block, dict):
                        if block["type"] == "text":
                            agent_thinking.insert(tk.END, f" 🤔 : {block['text']}\n")
                        elif block["type"] == "tool_use":
                            tool = block["name"]
                            inputs = block["input"]
                            agent_thinking.insert(tk.END, f" 🔧 Herramienta: {tool}\n")
                            agent_thinking.insert(tk.END, f" 🔢 Parámetros: {inputs}\n")
                agent_thinking.insert(tk.END, "-----------------------------\n")

            elif hasattr(msg, "tool_call_id"):
                agent_thinking.insert(
                    tk.END, f" ✉ Respuesta de herramienta: {msg.content}\n"
                )
                agent_thinking.insert(tk.END, "-----------------------------\n")

        agent_thinking.insert(tk.END, " 🧠 mente en frío\n")
        agent_thinking.insert(tk.END, "-----------------------------\n")

        agent_chat.insert(tk.END, f" 🐄 : {res['messages'][-1].content}\n", "asistente")
        agent_thinking.config(state="disabled")
        agent_chat.config(state="disabled")
        agent_chat.see(tk.END)
        agent_thinking.see(tk.END)

        if tts_status:
            CUA_loop.text_to_speech(res['messages'][-1].content)

        btn.config(state="normal")
        record_btn.config(state="normal")

    Thread(target=task, daemon=True).start()


def agent_sst():
    """Call to whisper for obtaining the text of the invoice prompt
    """    
    def task():
        user_prompt = CUA_loop.get_whisper_prompt()
        agent_response(user_prompt=user_prompt)

    Thread(target=task, daemon=True).start()


def clicked():
    """ Action after clicking "Enviar" button.
    """    
    user_prompt = entry.get().strip()
    entry.delete(0, tk.END)
    agent_response(user_prompt=user_prompt)


def fading_popup(title: str, message: str, time_alive: int,font:str = "15"):
    """Generic fading popups

    Args:
        title (str): popup title
        message (str): popup message
        time_alive (int): time alive before fading in ms
        font (str, optional): font size. Defaults to "15".
    """    
    top = tk.Toplevel()
    top.title(title)
    tk.Message(top, text=message, padx=20, pady=20,font=font).pack()
    top.after(time_alive, top.destroy)


def reset_popup():
    """Opens a popup informing the user that the program will reset in 5 seconds and procceeds to reset.
    """    
    def reset():
        os.execv(sys.executable, ["python"] + sys.argv)

    top = tk.Toplevel()
    top.title("ABORTANDO!!")
    tk.Message(
        top,
        text="Se procedera a abortar y reiniciarse en 5 segundos.",
        padx=40,
        pady=40,
        font="30",
    ).pack()
    top.after(5000, reset)


def safe_abort():
    """Abort CUA actual execution, it waits for the actual execution to end to exit safely.
    """    
    fading_popup("Abortando de manera segura.","Abortando la ejecucion del agente de manera segura, espere un momento.",10000)
    CUA_loop.set_stoppable(True)
    


def record_clicked():
    """Records a prompt of 5 seconds and sends it to the CUA agent
    """    
    fading_popup("Grabando", "Se procedera a grabar durante 5 segundos", time_alive=5000)
    agent_sst()


def reset_click():
    """resets the whole program instantly after waiting 5 seconds.
    """    
    reset_popup()

def toggle_tts():
    """text to speech toggle of IA response
    """    
    global tts_status
    tts_status = not tts_status
    toggle_btn.config(
        text=f"TTS: {'ON ' if tts_status else 'OFF '}",
        bg="green" if tts_status else "red"
    )

# GUI tkinter
root = tk.Tk()
root.title("Voice-Assisted Computer Accessibility")

root.geometry("1280x720")

root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=1)

entry = tk.Entry(root, width=80)
entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew", columnspan=2)

agent_chat = st.ScrolledText(root, wrap="word", font=("Courier New", 11))
agent_chat.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
agent_chat.insert(tk.END, "Este es el inicio de su conversación.\n")
agent_chat.config(state="disabled")

agent_thinking = st.ScrolledText(root, wrap="word", font=("Courier New", 11))
agent_thinking.grid(row=1, column=1, padx=5, pady=10, sticky="nsew", columnspan=5)
agent_thinking.insert(tk.END, "Pensamientos del agente y herramientas usadas:\n\n")
agent_thinking.config(state="disabled")

agent_chat.tag_configure("usuario", foreground="red", font=("Courier New", 11, "bold"))
agent_chat.tag_configure("asistente", foreground="purple", font=("Courier New", 11))

btn = tk.Button(root, text="Enviar", fg="red", command=clicked)
btn.grid(row=0, column=2, padx=5, pady=10)

record_btn = tk.Button(root, text="Prompt de voz", fg="green", command=record_clicked)
record_btn.grid(row=0, column=3, padx=5, pady=10)

abort_btn = tk.Button(root, text="Abortar!", fg="red", command=safe_abort)
abort_btn.grid(row=0, column=4, padx=5, pady=10)

reset_btn = tk.Button(root, text="Reiniciar!", fg="red", command=reset_click)
reset_btn.grid(row=0, column=5, padx=5, pady=10)

toggle_btn = tk.Button(root, text="TTS: OFF 🔇", bg="red", command=toggle_tts)
toggle_btn.grid(row=0,column=6,padx=5,pady=15)

root.mainloop()