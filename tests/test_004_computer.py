from CUA.tools.computer import move_mouse,mouse_clicker,keyboard_input,keyboard_hotkey,delete_text
import keyboard
import pyautogui
from unittest.mock import MagicMock



#Tests might give a warning for deprecated call by langchain
def test_move_mouse():
    """Test move_mouse
    """    
    move_mouse(tool_input={'x':500,'y':500}) #type: ignore
    x,y = pyautogui.position()
    assert x == 500,f"Wrong X position on the movement of mouse, expected 500 got:{x}"
    assert y == 500, f"Wrong Y position on the movement of mouse, expected 500 got:{y}"



def test_mouse_clicker_single_left():
    """test mouse click single left click mocking pyautogui library to assert the call
    """    
    original_click = pyautogui.click
    pyautogui.click = MagicMock()

    mouse_clicker("single_clickleft")
    pyautogui.click.assert_called_once_with(button="left")

    pyautogui.click = original_click

def test_mouse_clicker_double_left():
    """test mouse click double left click mocking pyautogui library to assert the call
    """    
    original_click = pyautogui.click
    pyautogui.click = MagicMock()

    mouse_clicker("double_clickleft")
    pyautogui.click.assert_called_once_with(button="left", clicks=2)

    pyautogui.click = original_click

def test_mouse_clicker_single_right():
    """test mouse click single right click mocking pyautogui library to assert the call
    """    
    original_click = pyautogui.click
    pyautogui.click = MagicMock()

    mouse_clicker("single_clickright")
    pyautogui.click.assert_called_once_with(button="right")

    pyautogui.click = original_click

def test_mouse_clicker_double_right():
    """test mouse click double right click mocking pyautogui library to assert the call
    """    
    original_click = pyautogui.click
    pyautogui.click = MagicMock()

    mouse_clicker("double_clickright")
    pyautogui.click.assert_called_once_with(button="right", clicks=2)

    pyautogui.click = original_click



def test_keyboard_input():
    """test keyboard input mocking keyboard library to assert the call
    """    
    original_keyboard = keyboard.write
    keyboard.write = MagicMock()

    keyboard_input("Texto de prueba")
    keyboard.write.assert_called_once_with("Texto de prueba", delay=0.02)

    keyboard.write = original_keyboard


def test_keyboard_hotkey_enter():
    """test keyboard press enter hotkey mocking pyautogui library to assert the call
    """    
    original_press = pyautogui.press
    pyautogui.press = MagicMock()

    keyboard_hotkey("enter")
    pyautogui.press.assert_called_once_with("enter")

    pyautogui.press = original_press

def test_keyboard_hotkey_shift():
    """test keyboard shift enter hotkey mocking pyautogui library to assert the call
    """    
    original_press = pyautogui.press
    pyautogui.press = MagicMock()

    keyboard_hotkey("shift")
    pyautogui.press.assert_called_once_with("shift")

    pyautogui.press = original_press

def test_keyboard_hotkey_pagedown():
    """test keyboard press pagedown hotkey mocking pyautogui library to assert the call
    """    
    original_press = pyautogui.press
    pyautogui.press = MagicMock()

    keyboard_hotkey("pagedown")
    pyautogui.press.assert_called_once_with("pagedown")

    pyautogui.press = original_press

def test_keyboard_hotkey_pageup():
    """test keyboard press pageup hotkey mocking pyautogui library to assert the call
    """    
    original_press = pyautogui.press
    pyautogui.press = MagicMock()

    keyboard_hotkey("pageup")
    pyautogui.press.assert_called_once_with("pageup")

    pyautogui.press = original_press

def test_keyboard_hotkey_browserback():
    """test keyboard press browserback hotkey mocking pyautogui library to assert the call
    """    
    original_press = pyautogui.press
    pyautogui.press = MagicMock()

    keyboard_hotkey("browserback")
    pyautogui.press.assert_called_once_with("browserback")

    pyautogui.press = original_press

def test_keyboard_hotkey_browserrefresh():
    """test keyboard press browserrefresh hotkey mocking pyautogui library to assert the call
    """    
    original_press = pyautogui.press
    pyautogui.press = MagicMock()

    keyboard_hotkey("browserrefresh")
    pyautogui.press.assert_called_once_with("browserrefresh")

    pyautogui.press = original_press

def test_keyboard_hotkey_tab():
    """test keyboard press tab hotkey mocking pyautogui library to assert the call
    """    
    original_press = pyautogui.press
    pyautogui.press = MagicMock()

    keyboard_hotkey("tab")
    pyautogui.press.assert_called_once_with("tab")

    pyautogui.press = original_press


def test_delete_text():
    """test delete_text seeing if it does the correct press sequence.
    """    
    original_keyDown = pyautogui.keyDown
    original_press = pyautogui.press
    original_keyUp = pyautogui.keyUp

    pyautogui.keyDown = MagicMock()
    pyautogui.press = MagicMock()
    pyautogui.keyUp = MagicMock()

    delete_text('')

    pyautogui.keyDown.assert_called_once_with("ctrl")
    pyautogui.keyUp.assert_called_once_with("ctrl")

    assert pyautogui.press.call_count == 2
    pyautogui.press.assert_any_call("a")
    pyautogui.press.assert_any_call("backspace")


    pyautogui.keyDown = original_keyDown
    pyautogui.press = original_press
    pyautogui.keyUp = original_keyUp


