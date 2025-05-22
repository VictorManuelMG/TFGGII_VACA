import os
import asyncio
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from sympy import false
from CUA.tools import computer
from CUA.tools.endpoint_yolo_florence import yolo_florence_inference
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage, RemoveMessage
from langgraph.graph import START, StateGraph, END
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.checkpoint.memory import MemorySaver

from langchain_core.tools import tool
from langgraph.managed.is_last_step import RemainingSteps
from CUA.tools.class_whisper import WhisperASR
from CUA.tools.class_browser_use import BrowserUse

import subprocess
import requests


from datetime import datetime, timedelta

from CUA.util.logger import logger
from CUA.util.path import project_root_path


root_path = project_root_path()


class Loop:
    def __init__(
        self,
        Whisper: WhisperASR,
        Browser: BrowserUse,
        stoppable: bool = False,
    ):
        """_summary_

        Args:
            Florence (florence_captioner): Florence model
            Whisper (whisper_asr): Whisper model
            Browser (browser): browser_use tool
        """
        load_dotenv()
        self.Whisper = Whisper
        self.Browser = Browser
        self.cooldowns = {}
        self.tools = self._load_tools()
        self.react_graph = self._build_graph()
        self.config = {"configurable": {"thread_id": "1"}, "recursion_limit": 120}
        self.stoppable = stoppable

    def _load_tools(self):
        """Load of tools for the llm.

        Returns:
            list[BaseTool]: list of tools
        """

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
            if (
                "browser_use" in self.cooldowns
                and time_now < self.cooldowns["browser_use"]
            ):
                remaining = (self.cooldowns["browser_use"] - time_now).seconds
                print(f"\n{self.cooldowns}+ le queda: {remaining}\n")
                return {
                    "result": "Browser tool is currently on cooldown.",
                    "cooldown_flag": True,
                    "cooldown_remaining_seconds": remaining,
                }

            async def run_browser():
                return await self.Browser.browser_executable(order)

            result, cooldown_flag = asyncio.run(run_browser())

            if cooldown_flag:
                self.cooldowns["browser_use"] = time_now + timedelta(seconds=200)

            logger.debug(
                f"browser_use tool response: {result}, cooldowns: {self.cooldowns}"
            )

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
            message = yolo_florence_inference(order,False)

            # Tool response for debugging
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
            message = yolo_florence_inference(order,True)

            # Tool response for debugging
            logger.debug(f"SimpleScreenInterpreter response: {message}")

            return message

        @tool
        def OpenChrome():
            """Tool that opens Chrome for web searching, it checks if chrome is open already if not creates a new instance of chrome
            Returns:
                msg: result of execution of tool
            """
            # URL only available if debug mode activated.
            url_debug = "http://localhost:9222/json"

            chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"

            try:
                response = requests.get(url_debug, timeout=1)
                if response.status_code == 200:
                    return "Ya hay una instancia de Chrome abierta."
            except requests.exceptions.RequestException:
                logger.warning(
                    "No se pudo conectar a Chrome vía puerto 9222. Se asumirá que no está abierto.",
                    exc_info=True,
                )
                pass

            cmd = [
                chrome_path,
                "--user-data-dir=C:\\ChromeDebugProfile",
                "--remote-debugging-port=9222",
            ]
            
            subprocess.Popen(cmd)

            return "Inicializado Chrome"

        # debugging tool
        @tool
        def sumas(a: int, b: int):
            """tool that return the addition of two numbers

            Returns:
                result: result of said addition between two numbers
            """
            result = a + b

            return result

        return [
            browser_use,
            OpenChrome,
            SimpleScreenInterpreter,
            ScreenInterpreter,
            computer.move_mouse,
            computer.mouse_clicker,
            computer.keyboard_input,
            computer.keyboard_hotkey,
            computer.delete_text,
            sumas,
        ]

    def select_agent_model(self, option: int):
        """Select the CUA model.

        Args:
            option (int): Option from 1 to 3 being 1 -> gpt, 2 -> claude, 3 -> local model #(to be implemented)
        """
        if option == 1:
            self.CUA_model = "gpt-4o"
            llm = ChatOpenAI(
                model=self.CUA_model,  # type: ignore
                api_key=os.getenv("OPENAI_API_KEY"),  # type: ignore
                timeout=None,
                temperature=0,
                max_tokens=2000,  # type: ignore
            )
            self.llm_with_tools = llm.bind_tools(self.tools)
        elif option == 2:
            self.CUA_model = "claude-3-7-sonnet-latest"
            llm = ChatAnthropic(
                model=self.CUA_model,  # type: ignore
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                timeout=None,
                temperature=0,
                max_tokens=2000,  # type: ignore
            )  # type: ignore
            self.llm_with_tools = llm.bind_tools(self.tools)
        else:
            print("Por incorporar")
            return

    def _build_graph(self):
        """build a react graph from langgraph for the agent.
        Returns:
            CompiledStateGraph: builded graph.
        """

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

            if self.stoppable:
                response_text = (
                    """La ejecución ha sido abortada por solicitud del usuario. 
                    Se han detenido todas las operaciones en curso y el sistema ha vuelto a su estado de espera. 
                    Si deseas iniciar una nueva tarea o consulta, por favor indícamelo y estaré listo para asistirte."""
                )


                logger.debug(f"Agent stoppable (manual): {response_text}")
                self.stoppable = False
                return {"messages": response_text}
                
                # # Trying to make abort with memory, not working atm
                # stoppable_message = (
                #     "Se ha abortado la ejecución por el usuario. "
                #     "Haz un resumen de lo que estabas haciendo y lo que has conseguido hasta ahora."
                # )

                # messages = state["messages"] + [SystemMessage(content=stoppable_message)]

                # response = self.llm_with_tools.invoke(messages)

                # logger.debug(f"Agent response:{response}")

                # return {"messages": response}

            else:

                if summary:
                    system_message = f"Resumen de la conversacion anterior: {summary}"
                    messages = [SystemMessage(content=system_message)] + state["messages"]

                else:
                    messages = state["messages"]


            response = self.llm_with_tools.invoke([sys_msg] + messages)

            # Agent response for debugging
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
            response = self.llm_with_tools.invoke(messages)

            delete_messages = [RemoveMessage(id=n.id) for n in state["messages"][:-2]]  # type: ignore
            logger.debug(
                f"summarize_conversation return: summary: {response.content} messages: {delete_messages}"
            )
            return {"summary": response.content, "messages": delete_messages}

        def should_continue(state: State):
            """Condition to continue or generate a summary, by default it generates a summary after 6 exchanges

            Args:
                state (State): state
            """

            messages = state["messages"]
            if len(messages) > 12:
                return "summarize"
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
        builder.add_node("tools", ToolNode(self.tools))
        # builder.add_node("summarize", summarize_conversation)
        builder.add_node("returnOnLimit", router)

        builder.add_edge(START, "returnOnLimit")
        builder.add_edge("returnOnLimit", "assistant")

        builder.add_conditional_edges("assistant", tools_condition)
        builder.add_edge("tools", "returnOnLimit")

        # builder.add_conditional_edges("assistant",should_continue,{"summarize": "summarize",END: END,})
        # builder.add_edge("summarize", "returnOnLimit")

        memory = MemorySaver()

        return builder.compile(checkpointer=memory)

    def draw_graph(self,path=root_path):
        """Draws the current graph flow"""
        png_bytes = self.react_graph.get_graph().draw_mermaid_png()
        full_path = path / "graph.png"

        with open(full_path, "wb") as f:
            f.write(png_bytes)

        return

    def run(self, user_prompt: str,TTS=false):
        """Given a user prompt calls the model to do the task given.

        Args:
            user_prompt (str): prompt given by user

        Returns:
            dict: dictionary with the result of the model after completing the task.
        """
        return self.react_graph.invoke({"messages": user_prompt}, self.config)  # type: ignore

    def get_whisper_prompt(self):
        """Transcribes the user's voice prompt

        Returns:
            str: returns string of the transcription.
        """
        return self.Whisper.whisper_SST()
    
    def set_stoppable(self,status:bool):
        """Sets the stoppable param for the program to decide if it has to stop execution or not.

        Args:
            status (bool): status input.
        """        
        self.stoppable = status

    def text_to_speech(self,text:str):
        """Transforms a text into speech.

        Args:
            text (str): text to transform into speech
        """        
        
        self.Whisper.whisper_TTS(text)