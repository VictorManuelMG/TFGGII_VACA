from main_loop import Loop
from unittest.mock import MagicMock
from dotenv import load_dotenv
from CUA.util.path import project_root_path
from os import remove
load_dotenv()

whisper_mock = MagicMock()
florence_mock = MagicMock()
browser_mock = MagicMock()


def test_initialization_loop():
    """Tests the initialization of loop object
    """    
    loop = Loop(whisper_mock, browser_mock)
    assert loop.config == {"configurable": {"thread_id": "1"}, "recursion_limit": 120}
    assert loop.stoppable is False
    assert loop.Whisper == whisper_mock
    assert loop.Browser == browser_mock


def test_select_screen_captioner():
    """This is tested on ScreenAssistant
    """    
    pass


def test_load_tools():
    """Tests that all tools are initialized
    """    
    # Add new tools to tools_list.
    loop = Loop( whisper_mock, browser_mock,)
    tools_list = [
        "browser_use",
        "OpenChrome",
        "SimpleScreenInterpreter",
        "ScreenInterpreter",
        "move_mouse",
        "mouse_clicker",
        "keyboard_input",
        "keyboard_hotkey",
        "delete_text",
    ]

    for tool in loop.tools:
        assert tool.name in tools_list


def test_select_agent_model():
    """Tests the selecting model for CUA and that the model is properly set on llm_with_tools
    """    
    loop = Loop( whisper_mock, browser_mock,)
    loop.select_agent_model(1)
    assert loop.CUA_model == "gpt-4o"
    assert "gpt-4o" == loop.llm_with_tools.model_name  # type: ignore

    loop.select_agent_model(2)
    assert loop.CUA_model == "claude-3-7-sonnet-latest"
    assert "claude-3-7-sonnet-latest" == loop.llm_with_tools.model  # type: ignore


def test_build_graph():
    """tests that nodes needed exists once graph is initialized
    """    
    loop = Loop( whisper_mock, browser_mock,)
    # If nodes added to graph, add to the list.
    nodes_list = ["assistant", "tools", "summarize", "returnOnLimit", "__start__"]

    for node in loop.react_graph.nodes.keys():
        assert node in nodes_list


def test_draw_graph():
    """Tests that graph is being properly made
    """    
    root = project_root_path()
    test_path = root / "tests"
    loop = Loop(florence_mock, whisper_mock, browser_mock,)
    loop.draw_graph(test_path)
    graph_path = test_path / "graph.png"

    try:
        open(str(graph_path), "rb")
    except FileNotFoundError:
        assert False, "File not found"
    else:
        remove(graph_path)
        assert True


def test_run():
    """Tests that langgrapg is returning a message with content.
    """    
    loop = Loop( whisper_mock, browser_mock,)
    loop.select_agent_model(2)
    response = loop.run("this is a test input.")
    assert isinstance(response["messages"][-1].content, str)


def test_whisper_prompt():
    """This is tested on Whisper test
    """    
    pass


def test_set_stoppable():
    """Tests that variable stoppable is being setted properly
    """    
    loop = Loop(whisper_mock, browser_mock)
    loop.set_stoppable(True)
    assert loop.stoppable is True

    loop.set_stoppable(False)
    assert loop.stoppable is False


def test_text_to_speech():
    """This is tested on whisper test
    """    
    
    pass
