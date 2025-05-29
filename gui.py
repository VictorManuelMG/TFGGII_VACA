import os
import sys

import customtkinter as ctk
from screeninfo import get_monitors


from CUA.tools.class_browser_use import BrowserUse
from CUA.tools.class_whisper import WhisperASR
from CUA.tools.persistent_stt import ContinuousRecorder
from main_loop import Loop

from threading import Thread


Whisper = WhisperASR()
Browser = BrowserUse()

CUA_loop = Loop(Whisper, Browser)
CUA_loop.select_agent_model(2)
stt = ContinuousRecorder()


# Global variables
tts_status = True
last_result_stt = ""
result_stt = ""
prompt_accept_flag = False
last_prompt = ""
prompt_popup = None
working_flag = False

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


def agent_response(user_prompt: str):
    """Sends a prompt to the CUA and parses it's last response and thinking of the whole process.

    Args:
        user_prompt (str): User prompt
    """

    def task():
        global working_flag
        btn.configure(state="disabled")
        # Deactivated
        # record_btn.configure(state="disabled")

        agent_thinking.configure(state="normal")
        agent_chat.configure(state="normal")

        if not user_prompt:
            return

        agent_chat.insert(ctk.END, f"\n 😃 : {user_prompt}\n", "usuario")
        agent_chat.insert(ctk.END, "\n")

        res = CUA_loop.run(user_prompt, True)

        agent_thinking.delete(2.0, ctk.END)
        agent_thinking.insert(ctk.END, "\n")

        # Agent thinking log extraction
        for msg in res["messages"]:
            if hasattr(msg, "content") and isinstance(msg.content, list):
                for block in msg.content:
                    if isinstance(block, dict):
                        if block["type"] == "text":
                            agent_thinking.insert(ctk.END, f" 🤔 : {block['text']}\n")
                        elif block["type"] == "tool_use":
                            tool = block["name"]
                            inputs = block["input"]
                            agent_thinking.insert(ctk.END, f" 🔧 Herramienta: {tool}\n")
                            agent_thinking.insert(
                                ctk.END, f" 🔢 Parámetros: {inputs}\n"
                            )
                agent_thinking.insert(ctk.END, "-----------------------------\n")

            elif hasattr(msg, "tool_call_id"):
                agent_thinking.insert(
                    ctk.END, f" ✉ Respuesta de herramienta: {msg.content}\n", "thinking"
                )
                agent_thinking.insert(ctk.END, "-----------------------------\n")

        agent_thinking.insert(ctk.END, " 🧠 mente en frío\n", "thinking")
        agent_thinking.insert(ctk.END, "-----------------------------\n")

        agent_chat.insert(
            ctk.END, f" 🐄 : {res['messages'][-1].content}\n", "asistente"
        )

        agent_thinking.configure(state="disabled")
        agent_chat.configure(state="disabled")
        agent_chat.see(ctk.END)
        agent_thinking.see(ctk.END)

        if tts_status:
            CUA_loop.text_to_speech(res["messages"][-1].content)

        btn.configure(state="normal")
        # Deactivated
        # record_btn.configure(state="normal")

        working_flag = False

    Thread(target=task, daemon=True).start()


def agent_stt():
    """Call to whisper for obtaining the text of the invoice prompt"""

    def task():
        user_prompt = CUA_loop.get_whisper_prompt()
        agent_response(user_prompt=user_prompt)

    Thread(target=task, daemon=True).start()


def clicked():
    """Action after clicking "Enviar" button."""
    user_prompt = entry.get().strip()
    entry.delete(0, ctk.END)
    agent_response(user_prompt=user_prompt)


def create_centered_popup(
    title: str,
    message: str,
    width: int = 500,
    height: int = 350,
    font: int = 30,
    time_alive: int = None,# type: ignore
):  
    # Taken idea from https://stackoverflow.com/questions/3352918/how-to-center-a-window-on-the-screen-in-tkinter
    """Creates a centered popup in root window

    Args:
        title (str): title.
        message (str): Message to show on popup.
        width (int): popup width.
        height (int): popup height.
        font (str): font size.
        time_alive (int, opcional): time_alive of window.

    Returns:
        popup (Toplevel): Popup reference
    """
    popup = ctk.CTkToplevel()
    popup.title(title)

    root.update_idletasks()

    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_width = root.winfo_width()
    root_height = root.winfo_height()

    center_x = root_x + (root_width // 2) - (width // 2)
    center_y = root_y + (root_height // 2) - (height // 2)

    popup.geometry(f"{width}x{height}+{center_x}+{center_y}")

    popup.lift()
    popup.attributes("-topmost", True)
    popup.focus_force()

    ctk.CTkLabel(
        popup,
        text=message,
        wraplength=width - 50,
        font=ctk.CTkFont(size=font),
        justify="left",
    ).pack()

    if time_alive is not None:
        popup.after(time_alive, popup.destroy)

    return popup


def reset_popup():
    """Opens a popup informing the user that the program will reset in 5 seconds and procceeds to reset."""

    def reset():
        os.execv(sys.executable, ["python"] + sys.argv)

    top = create_centered_popup(
        "ABORTANDO!!", "Se procedera a abortar y reiniciarse en 5 segundos."
    )

    top.after(5000, reset)


def accept_prompt():
    """Generates a windows with user's prompt asking if the prompt should be accepted or not"""
    global prompt_accept_flag, prompt_popup
    prompt_popup = create_centered_popup(
        "¿Aceptar este prompt?",
        f"¿Quiere aceptar este prompt?: \n- {last_prompt}. \n\n\n Responda confirmar en caso afirmativo, cancelar en caso negativo.",
    )

    prompt_accept_flag = True


def safe_abort():
    """Abort CUA actual execution, it waits for the actual execution to end to exit safely."""
    create_centered_popup(
        "Abortando de manera segura.",
        "Abortando la ejecución del agente de manera segura, espere un momento.",
        time_alive=10000,
    )
    CUA_loop.set_stoppable(True)


def record_clicked():
    """Records a prompt of 5 seconds and sends it to the CUA agent"""
    create_centered_popup(
        "Grabando", "Se procedera a grabar durante 5 segundos", time_alive=5000
    )
    agent_stt()


def reset_click():
    """resets the whole program instantly after waiting 5 seconds."""
    reset_popup()


def toggle_tts():
    """text to speech toggle of IA response"""
    global tts_status
    tts_status = not tts_status
    toggle_btn.configure(
        text=f"TTS: {'ON 🔊' if tts_status else 'OFF 🔇'}",
        fg_color="#28a745" if tts_status else "#6c757d",
    )


# GUI tkinter

root = ctk.CTk()
root.title("Voice-Assisted Computer Accessibility")

window_size = 0

for m in get_monitors():
    if m.is_primary:
        window_size = m.width

root.geometry(f"+{window_size}+0")
root.lift()
root.attributes("-topmost", True)
root.after(1000, lambda: root.attributes("-topmost", False))


root.after(500, lambda: root.state("zoomed"))


root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=1)

entry = ctk.CTkEntry(root, width=150)
entry.grid(row=0, column=0, padx=15, pady=10, sticky="ew", columnspan=1)

agent_chat = ctk.CTkTextbox(
    root, wrap="word", font=("Courier New", 14), fg_color="#1e1e1e", width=350
)
agent_chat.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
agent_chat.insert(ctk.END, "Este es el inicio de su conversación.\n")
agent_chat.configure(state="disabled")

agent_thinking = ctk.CTkTextbox(
    root, wrap="word", font=("Courier New", 14), fg_color="#1e1e1e"
)
agent_thinking.grid(row=1, column=1, padx=5, pady=10, sticky="nsew", columnspan=5)
agent_thinking.insert(ctk.END, "Pensamientos del agente y herramientas usadas:\n\n")
agent_thinking.configure(state="disabled")

agent_chat.tag_config("usuario", foreground="#F87070")
agent_chat.tag_config("asistente", foreground="#8BE9FD")

agent_thinking.tag_config("thinking", foreground="#C3C3C3")


control_frame = ctk.CTkFrame(root, fg_color="transparent")
control_frame.grid(row=0, column=1, columnspan=4, padx=10, pady=(10, 5), sticky="ew")

btn_width = 150

btn = ctk.CTkButton(
    control_frame,
    text="📤 Enviar",
    fg_color="#007ACC",
    width=btn_width,
    command=clicked,
)
btn.pack(side="left", padx=5, pady=5)

# Deactivated as persistent STT is implemented, might be changed to something else
# record_btn = ctk.CTkButton(control_frame, text="🎤 Voz", fg_color="#28a745", width=btn_width, command=record_clicked)
# record_btn.pack(side="left", padx=5, pady=5)

abort_btn = ctk.CTkButton(
    control_frame,
    text="⛔ Abortar",
    fg_color="#dc3545",
    width=btn_width,
    command=safe_abort,
)
abort_btn.pack(side="left", padx=5, pady=5)

reset_btn = ctk.CTkButton(
    control_frame,
    text="🔄 Reiniciar",
    fg_color="#5116dd",
    width=btn_width,
    command=reset_click,
)
reset_btn.pack(side="left", padx=5, pady=5)

toggle_btn = ctk.CTkButton(
    control_frame,
    text=" TTS: ON 🔊",
    fg_color="#28a745",
    width=btn_width,
    command=toggle_tts,
)
toggle_btn.pack(side="left", padx=5, pady=5)


def stt_thread():
    """Thread with the STT logic"""

    def monitor_stt():
        Thread(target=stt.permanent_stt, daemon=True).start()

        def check_for_updates():
            global \
                last_result_stt, \
                prompt_accept_flag, \
                last_prompt, \
                prompt_popup, \
                working_flag
            result = stt.get_result()
            if result and result != last_result_stt:
                last_result_stt = result
                parsed_response = result.lower().strip()

                if prompt_accept_flag:
                    if "confirmar" in parsed_response:
                        prompt_accept_flag = False
                        agent_response(last_prompt)
                        entry.delete(0, ctk.END)
                        prompt_popup.destroy()  # type: ignore
                        working_flag = True

                    elif "cancelar" in parsed_response:
                        prompt_accept_flag = False
                        entry.delete(0, ctk.END)
                        prompt_popup.destroy()  # type: ignore
                    else:
                        create_centered_popup(
                            "ASR Inference",
                            f"Te he entendido: {result}, los respuestas posibles solo son CONFIRMAR o CANCELAR.",
                            time_alive=5000,
                        )

                elif working_flag:
                    if "reiniciar" in parsed_response:
                        reset_popup()
                    elif "abortar" in parsed_response:
                        safe_abort()

                else:
                    entry.delete(0, ctk.END)
                    entry.insert(ctk.END, result)
                    last_prompt = result
                    accept_prompt()

            root.after(1000, check_for_updates)

        check_for_updates()

    Thread(target=monitor_stt, daemon=True).start()


stt_thread()


root.mainloop()
