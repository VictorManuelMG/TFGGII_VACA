
import tkinter as tk

from tkinter import scrolledtext as st

from CUA.tools.class_browser_use import browser
from CUA.tools.class_florence import florence_captioner
from CUA.tools.class_whisper import whisper_asr
from loop import loop

from threading import Thread

Florence = florence_captioner()
Whisper = whisper_asr()
Browser = browser()

CUA_loop = loop(Florence,Whisper,Browser)
CUA_loop.select_screen_captioner(2)
CUA_loop.select_agent_model(2)


# GUI tkinter
root = tk.Tk()
root.title("Voice-Assisted Computer Accessibility")

root.geometry("1280x720")

root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=1)

entry = tk.Entry(root, width=80)
entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

agent_chat = st.ScrolledText(root, wrap="word", font=("Courier New", 11))
agent_chat.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
agent_chat.insert(tk.END, "Este es el inicio de su conversación.\n")
agent_chat.config(state="disabled")


agent_thinking = st.ScrolledText(root, wrap="word", font=("Courier New", 11))
agent_thinking.grid(row=1, column=1, padx=5, pady=10, stick="nsew")
agent_thinking.insert(tk.END, "Pensamientos del agente y herramientas usadas:\n\n")
agent_thinking.config(state="disabled")

agent_chat.tag_configure("usuario", foreground="red", font=("Courier New", 11, "bold"))
agent_chat.tag_configure("asistente", foreground="purple", font=("Courier New", 11))



def agent_response(user_prompt):
    def task():
        btn.config(state="disabled")
        record_btn.config(state="disabled")

        agent_thinking.config(state="normal")
        agent_chat.config(state="normal")
        
        if not user_prompt:
            return
        
        agent_chat.insert(tk.END, f"\n 😃 : {user_prompt}\n", "usuario")
        agent_chat.insert(tk.END, "\n")

        res = CUA_loop.run(user_prompt)

        tool = None

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
                agent_thinking.insert(tk.END, f" ✉ Respuesta de herramienta: {msg.content}\n")
                agent_thinking.insert(tk.END, "-----------------------------\n")

        agent_thinking.insert(tk.END, " 🧠 mente en frío\n")
        agent_thinking.insert(tk.END, "-----------------------------\n")

        agent_chat.insert(tk.END, f" 🐄 : {res['messages'][-1].content}\n", "asistente")
        agent_thinking.config(state="disabled")
        agent_chat.config(state="disabled")
        agent_chat.see(tk.END)
        agent_thinking.see(tk.END)

        btn.config(state="normal")
        record_btn.config(state="normal")

    Thread(target=task, daemon=True).start()



def clicked():
    user_prompt = entry.get().strip()
    entry.delete(0, tk.END)
    agent_response(user_prompt=user_prompt)




def fading_popup(title:str,message:str,time_alive:int):
    top=tk.Toplevel()
    top.title(title)
    tk.Message(top,text=message,padx=20,pady=20).pack()
    top.after(time_alive,top.destroy)


def record_clicked():
    fading_popup("Grabando","Se procedera a grabar durante 5 segundos",5000)
    user_prompt = CUA_loop.get_whisper_prompt()
    agent_response(user_prompt=user_prompt)
    

btn = tk.Button(root, text="Enviar", fg="red", command = clicked)
btn.grid(row=0, column=1, padx=10, pady=10)

record_btn = tk.Button(root,text="prompt de voz",fg="green",command = record_clicked)
record_btn.grid(row=0, column=2, padx=10,pady=10)


root.mainloop()