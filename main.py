import os
import asyncio
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

from CUA.tools import computer
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage, RemoveMessage
from langgraph.graph import START, StateGraph, END
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.checkpoint.memory import MemorySaver

from langchain_core.tools import tool
from langgraph.managed.is_last_step import RemainingSteps
from CUA.tools.class_florence import florence_captioner
from CUA.tools.class_screen_assistant import screen_assistant
from CUA.tools.class_whisper import whisper_asr
from CUA.tools.class_browser_use import browser


import tkinter as tk

from tkinter import scrolledtext as st

# import for debugging and testing
import time
import subprocess
import requests


from datetime import datetime, timedelta

from CUA.util.logger import logger
 
print("Cargando modelos para captioning y screen interpreter")

Florence = florence_captioner()
Whisper = whisper_asr()
Browser = browser()


#Model selection prototype, it shall be upgraded in the future.
print("Elija que modelo querra usar para la inferencia de imagenes: 1.- OpenAI, 2.-Anthropic 3.- Predeterminado")
while True:
    try:
        opcion = int(input())
        break 
    except ValueError as e:
        logger.error(f"Introducido un caracter diferente a un numero: {e}", exc_info=True)
        print("Por favor, ingrese un número válido.")

if opcion == 1:
    Assistant = screen_assistant(captioner=Florence, model_screen_interpreter="gpt-4o")
elif opcion == 2:
    Assistant = screen_assistant(captioner=Florence, model_screen_interpreter="claude-3-7-sonnet-latest")
else:
    Assistant = screen_assistant(captioner=Florence)

print("Modelos cargados")

# Dictionary to save actual tools on cooldown
cooldowns = {}


# Tool is defined inside a class, so we'll instance a call outside the class to convert it into a callable tool
## Use of datetime over time as the former gives problems when trying to add seconds to the cooldown, might change all time imports in the future.
@tool
def browser_use(order: str):
    """Tool mainly focused on browsing over the internet
    Args:
        order (str): order for browser_use

    Returns:
        message: result of search
    """
    logger.info(f"browser_use user order: {order}")
    time_now = datetime.now()

    # Cooldown on browser_use to forbid the use of this tool in case of failure on search so it uses other available tools that have the same purpouse or can do the same.
    if "browser_use" in cooldowns and time_now < cooldowns["browser_use"]:
        remaining = (cooldowns["browser_use"] - time_now).seconds
        print(f"\n{cooldowns}+ le queda: {remaining}\n")
        return {
            "result": "Browser tool is currently on cooldown.",
            "cooldown_flag": True,
            "cooldown_remaining_seconds": remaining,
        }

    async def run_browser():
        return await Browser.browser_executable(order)

    result, cooldown_flag = asyncio.run(run_browser())

    if cooldown_flag:
        cooldowns["browser_use"] = time_now + timedelta(seconds=200)

    logger.debug(f"browser_use tool response: {result}, cooldowns: {cooldowns}")

    return {
        "result": f"Resultado browser_use:\n{result}",
        "cooldown_flag": cooldown_flag,
        "cooldown_remaining_seconds": 0 if not cooldown_flag else 200,
    }


@tool
def ScreenInterpreter(order: str):
    """Use this tool to analyze the user's screen and determine precise actions that must be performed.

    It uses object detection and visual captioning models (YOLO and Florence 2) to fully understand all elements on the screen.

    Use this tool when the user asks for:
    - Interacting with screen elements (e.g., move the mouse, click a button, type something)
    - Locating UI elements precisely
    - Opening applications, clicking icons, handling buttons, etc.
    - When spatial position or captioning of icons/buttons is essential

    Returns detailed coordinates and captions for screen elements and explains how to perform the action requested by the user.

    Args:
        order (str): User order about screen information

    Returns:
            message: LLM answer
    """
    logger.info(f"ScreenInterpreter user order: {order}")
    message = Assistant.interpret_screen(order)

    #Tool response for debugging
    logger.debug(f"ScreenInterpreter response: {message}")

    return message


@tool
def SimpleScreenInterpreter(order: str):
    """Use this tool to get general insights or descriptions about what's visible on the screen without interacting with it.

    This tool does NOT use heavy visual models, and it is meant for:
    - Understanding the current screen state at a high level
    - Checking if something appears to be open, visible, or loaded
    - Answering general questions like “Did the browser open?”, “Is there an error message?”, “Is the user on Google?”

    Use this only when you need to describe what's visible, NOT to take action.

    Args:
        order (str): User order about screen information

    Returns:
        message: LLM answer
    """
    logger.info(f"SimpleScreenInterpreter user order: {order}")
    message = Assistant.simple_interpreter(order)

    #Tool response for debugging
    logger.debug(f"SimpleScreenInterpreter response: {message}")

    return message


@tool
def OpenChrome():
    """Tool that opens Chrome for web searching, it checks if chrome is open already if not creates a new instance of chrome

    Returns:
        msg: result of execution of tool
    """
    #URL only available if debug mode activated.
    url_debug = "http://localhost:9222/json"

    chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"

    try:
        response = requests.get(url_debug, timeout=1)
        if response.status_code == 200:
            return "Ya hay una instancia de Chrome abierta."
    except requests.exceptions.RequestException:
        logger.warning("No se pudo conectar a Chrome vía puerto 9222. Se asumirá que no está abierto.", exc_info=True)
        pass

    cmd = [
        chrome_path,
        "--remote-debugging-port=9222",
    ]
    subprocess.Popen(cmd)

    return "Inicializado Chrome"


tools = [
    browser_use,
    OpenChrome,
    SimpleScreenInterpreter,
    ScreenInterpreter,
    computer.move_mouse,
    computer.mouse_clicker,
    computer.keyboard_input,
    computer.keyboard_hotkey,
    computer.delete_text,
]


load_dotenv()
model = "claude-3-7-sonnet-latest"

llm = ChatAnthropic(
    model=model,  # type: ignore
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    timeout=None,
    temperature=0,
    max_tokens=2000,  # type: ignore
)  # type: ignore

llm_with_tools = llm.bind_tools(tools)


class State(MessagesState):
    """Saves the actual summary of the conversation

    Args:
        MessagesState: MessageState
    """

    remaining_steps: RemainingSteps
    summary: str


def call_model(state: State):
    """Calls the LLM

    Args:
        state (State): Actual State

    Returns:
        response: LLM response on the prompt given by the user
    """
    sys_msg = SystemMessage(
        content="""**Prompt:** You are an advanced computer use agent designed to assist the user in navigating their computer effectively.Your primary objective is to execute tasks that are within your capabilities based on user input.
        1.**User Interaction**: When the user requests an action, analyze their instructions carefully to ensure you fully understand the task.Confirm the action required and clarify any ambiguous requests by asking specific questions if necessary.
        2.**Task Execution**: Upon receiving a clear directive: - Identify the necessary applications or files that need to be accessed.- Determine the exact coordinates of relevant icons, buttons, or links on the screen based on the user's operating system and interface.- Execute the task using appropriate methods such as: - Mouse movements (drag, click, double-click) to interact with UI elements.- Keyboard shortcuts for efficient execution (e.g., Ctrl+C for copy, Alt+Tab for switching applications).-
            Any other necessary actions (scrolling, resizing windows) to complete the task. Always double-check if what you wanted to happen, happened by making another screenshot or other methods.
        
        3.**Navigation and Coordination**: - Maintain an internal map of the screen layout, including the positions of all relevant icons, menus, and other clickable elements.- Use precise coordinates for mouse actions, ensuring the accuracy of clicks and drags.- Adapt to changes in the UI if the user modifies settings or updates the operating system.
        4.**Feedback Loop**: After completing the task, provide the user with a summary of what was accomplished.If the task was unsuccessful, explain the reason and suggest alternative approaches or solutions.
        5.**Continuous Learning**: As you perform tasks, gather data on user preferences and commonly used applications to improve efficiency in future interactions.Adjust your internal mapping system as needed to account for any changes in the user's interface.By following this organized methodology, you will improve the user's experience and provide effective support in completing their computer-related tasks.
        
        **IMPORTANT**: Always wait half a second or a second between use of tools to not fail at inputing text or login clicks, as the user's computer might be slow
                        Remember that to open an application you've to double left click on it or right click and then left click on open
                        Please always use 1st the coordinates given by your tools, on last instance you can try yourself to locate pertinent coordinates but always refer to
                        coordinates given by tools, thank you.
                        
                        Always check what you've already open to not open the same things over and over again.
                        If any pop-ups while browsing appear, accept it if they're related to cookies or privacy please always
                        do this first, if you don't you won't be able to browse.
                        
                        Everytime you ask for an application whereabouts to the screenshot tool, ask for specific coordinates of the application.
                        Also take in account you'll recive a summary up to date of the interactions with the user or memory of it, if he asks something you already know from this
                        just respon directly with your memory dont use tools.
                        If you open something and you don't see it maximized, try to maximaze it if possible using your tools
                        If the user tell you something ambigous ALWAYS ask for more information.
                        If users tell "exit" give a goodbye message as you'll stop working and the programm will stop.
                        When asking something to be done over the internet, use browser_use tool, if it's on cooldown always check when it will be available

                        Always respond to user in spanish unless asked otherwise"""
    )

    summary = state.get("summary", "")

    if summary:
        system_message = f"Resumen de la conversacion anterior: {summary}"
        messages = [SystemMessage(content=system_message)] + state["messages"]

    else:
        messages = state["messages"]
    response = llm_with_tools.invoke([sys_msg] + messages)

    #Agent response for debugging
    logger.debug(f"Agent response:{response}")

    return {"messages": response}


def summarize_conversation(state: State):
    """Node that generates the summary of the conversation

    Returns:
        Summary: summary of the conversation
    """
    logger.info(f"summarize_conversation state: {state}")
    summary = state.get("summary", "")

    if summary:
        summary_message = (
            f"Este es el resumen de la conversación hasta la fecha: {summary}\n\n"
            "Extiende el resumen teniendo en cuenta los nuevos mensajes:"
        )

    else:
        summary_message = "Crea un resumen de toda la conversación mantenida."

    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = llm_with_tools.invoke(messages)

    delete_messages = [RemoveMessage(id=n.id) for n in state["messages"][:-2]]  # type: ignore
    logger.debug(f"summarize_conversation return: summary: {response.content} messages: {delete_messages}")
    return {"summary": response.content, "messages": delete_messages}


def should_continue(state: State):
    """Condition to continue or generate a summary, by default it generates a summary after 6 exchanges

    Args:
        state (State): state
    """

    messages = state["messages"]
    if len(messages) > 12:
        return "summarize_conversation"
    return END


def router(state: State):
    """Node to stop once recursion limit is approximating to the stopping point so the agent doesn't die due to recursion limit error.

    Args:
        state (State): state

    """
    logger.debug(f"router steps remaining :{state["remaining_steps"]}")
    if state["remaining_steps"] <= 10:
        return {
            "messages": [
                HumanMessage(
                    content="Te has pasado del limite de recursion, finaliza lo que estes haciendo y devuelve un resumen los resultados actuales obtenidos anteriormente a este mensaje."
                )
            ]
        }
    else:
        return state


builder = StateGraph(MessagesState)

builder.add_node("assistant", call_model)
builder.add_node("tools", ToolNode(tools))
builder.add_node("summarize", summarize_conversation)
builder.add_node("returnOnLimit", router)

builder.add_edge(START, "returnOnLimit")
builder.add_edge("returnOnLimit", "assistant")


builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "returnOnLimit")

builder.add_conditional_edges("assistant", should_continue)
builder.add_edge("summarize", "returnOnLimit")

memory = MemorySaver()

react_graph = builder.compile(checkpointer=memory)


# png_bytes = react_graph.get_graph().draw_mermaid_png()


# with open("graph.png", "wb") as f:
#     f.write(png_bytes)


config = {"configurable": {"thread_id": "1"}, "recursion_limit": 120}


flag = True
start = time.time()
end = time.time()
flag_tts = False


# while flag:
#     print(
#         "Escriba su orden (Escriba exit para salir o '.' para pasar prompt mediante voz o ',' para activar transcripciones por voz de los mensajes de la IA, ',,' para desactivarlo.)"
#     )
#     order = input()

#     if order == ",":
#         flag_tts = True
#         continue

#     if order == ",,":
#         flag_tts = False
#         continue

#     if order.lower() == "exit":
#         flag = False
#         continue

#     if order == ".":
#         print("Se realizará una grabación")
#         time.sleep(2)
#         order = Whisper.whisper_SST()

#     start = time.time()
#     messages = react_graph.invoke({"messages": order}, config)  # type: ignore
#     end = time.time()

#     for m in messages["messages"]:
#         m.pretty_print()

#     if flag_tts:
#         last_message = messages["messages"][-1]
#         Whisper.whisper_TTS(last_message.content)

#     # start = time.time()
#     # for messages in react_graph.stream({"messages":order},config,stream_mode = "messages"):
#     #     print(messages)
#     #     print("\n")
#     # end = time.time()

#     logger.info("Agent task execution time: {end - start} seconds")

#GUI tkinter
root = tk.Tk()
root.title("Voice-Assisted Computer Accessibility")

root.geometry('1280x720')

root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=1)

entry = tk.Entry(root,width=80)
entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

agent_chat = st.ScrolledText(root,wrap="word",font=("Courier New",11))
agent_chat.grid(row=1,column=0,padx=10,pady=10,sticky="nsew")
agent_chat.insert(tk.END,"Este es el inicio de su conversación.\n")
agent_chat.config(state="disabled")


agent_chat.tag_configure("usuario", foreground="red", font=("Courier New", 11, "bold"))
agent_chat.tag_configure("asistente", foreground="purple", font=("Courier New", 11))


def clicked():
    user_prompt = entry.get().strip()
    if not user_prompt:
        return 
    
    entry.delete(0, tk.END)

    agent_chat.config(state="normal")
    agent_chat.insert(tk.END,f"\n 😃 : {user_prompt}\n","usuario")

    res = react_graph.invoke({"messages": user_prompt}, config)#type: ignore
    agent_chat.insert(tk.END,"\n")


    agent_chat.see(tk.END)
    agent_chat.insert(tk.END, f" 🐄 : {res["messages"][-1].content}","asistente")
    agent_chat.config(state="disabled")
    agent_chat.see(tk.END)


btn = tk.Button(root, text = "Enviar" ,
             fg = "red", command=clicked)
btn.grid(row=0, column=1, padx=10, pady=10)


root.mainloop()


