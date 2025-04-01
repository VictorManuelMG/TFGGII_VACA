import os
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
from CUA.tools import computer
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage, RemoveMessage
from langgraph.graph import START, StateGraph, END
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.checkpoint.memory import MemorySaver

from langchain_core.tools import tool


# import for debugging and testing
import time

from CUA.tools.ClassFlorence import FlorenceCaptioner
from CUA.tools.ClassScreenAssistant import ScreenAssistant

print("Cargando modelos para captioning y screen interpreter")

Florence = FlorenceCaptioner()
Assistant = ScreenAssistant(Florence)

print("Modelos cargados")


#Tool is defined inside a class, so we'll instance a call outside the class to convert it into a callable tool
@tool
def ScreenInterpreter(order:str):
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
    message = Assistant.interpret_screen(order)
    return message
@tool
def SimpleScreenInterpreter(order:str):
    """ Use this tool to get general insights or descriptions about what's visible on the screen without interacting with it.

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
    message = Assistant.simple_interpreter(order)
    return message

tools = [
    SimpleScreenInterpreter,
    ScreenInterpreter,
    computer.move_mouse,
    computer.mouse_clicker,
    computer.keyboard_input,
    computer.keyboard_hotkey,
    computer.delete_text,
]

load_dotenv()
model = "claude-3-7-sonnet-20250219"
model2 = "claude-3-5-sonnet-20240620"

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
                        just respon directly with your memory dont use tools."""
    )

    summary = state.get("summary", "")

    if summary:
        system_message = f"Resumen de la conversacion anterior: {summary}"
        messages = [SystemMessage(content=system_message)] + state["messages"]

    else:
        messages = state["messages"]

    response = llm_with_tools.invoke([sys_msg] + messages)
    return {"messages": response}


def summarize_conversation(state: State):
    """Node that generates the summary of the conversation

    Returns:
        Summary: summary of the conversation
    """
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
    return {"summary": response.content, "messages": delete_messages}


def should_continue(state: State):
    """Condition to continue or generate a summary, by default it generates a summary after 6 exchanges

    Args:
        state (State): state
    """

    messages = state["messages"]
    if len(messages) > 6:
        return "summarize_conversation"
    return END


builder = StateGraph(MessagesState)

builder.add_node("assistant", call_model)
builder.add_node("tools", ToolNode(tools))
builder.add_node("summarize", summarize_conversation)


builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")

builder.add_conditional_edges("assistant", should_continue)
builder.add_edge("summarize", "assistant")

memory = MemorySaver()

react_graph = builder.compile(checkpointer=memory)


# png_bytes = react_graph.get_graph(xray=True).draw_mermaid_png()

# with open("graph.png", "wb") as f:
#     f.write(png_bytes)


config = {"configurable": {"thread_id": "1"}, "recursion_limit": 100}


flag = True
start = time.time()
end = time.time()


while flag:
    print("Escriba su orden (Escriba exit para salir.)")
    order = input()

    if order.lower() == "exit":
        flag = False
    else:
        start = time.time()
        messages = react_graph.invoke({"messages": order}, config)  # type: ignore
        end = time.time()

        for m in messages["messages"]:
            m.pretty_print()

    print("\n///////////////////////////////////////////////////////////")
    print(f"Tiempo de ejecucion de el prompt: {end - start} segundos")
    print("///////////////////////////////////////////////////////////\n")
