import pyautogui
import keyboard
from langchain_core.tools import tool


@tool
def move_mouse(x: int, y: int):
    """with the coords x and y given make the mouse move to the desired position

    Args:
        x (int): coord x from screen
        y (int): coord y from screen
    """
    pyautogui.moveTo(x, y, 0.5)


@tool
def mouse_clicker(action: str):
    """Performs different types of clicks.

    Args:
        action (str): Action click to perform by mouse:
                        single_clickleft = single left click with mouse
                        double_clickleft = double left click with mouse
                        single_clickright = single right click with mouse
                        double_clickright = double right click with mouse
    """
    if "single_clickleft" == action:
        pyautogui.click(button="left")
    if "double_clickleft" == action:
        pyautogui.click(button="left", clicks=2)
    if "single_clickright" == action:
        pyautogui.click(button="right")
    if "double_clickright" == action:
        pyautogui.click(button="right", clicks=2)


@tool
def keyboard_input(text: str):
    """Inputs a text string

    Args:
        text (str): string to input
    """
    keyboard.write(text, delay=0.02)


@tool
def keyboard_hotkey(action: str):
    """simulates pressing hotkeys

    Args:
        action (str): hotkey to press:
                        enter = press entes
                        shift = press shift
                        pagedown = press pagedown
                        pageup = press pageup
                        browserback = press browserback
                        browserrefresh = press browserrefresh
                        tab = press tab
    """

    if "enter" == action:
        pyautogui.press("enter")
    if "shift" == action:
        pyautogui.press("shift")
    if "pagedown" == action:
        pyautogui.press("pagedown")
    if "pageup" == action:
        pyautogui.press("pageup")
    if "browserback" == action:
        pyautogui.press("browserback")
    if "browserrefresh" == action:
        pyautogui.press("browserrefresh")
    if "tab" == action:
        pyautogui.press("tab")


@tool
def delete_text():
    """Selects all the text from a box or doc and deletes it."""
    pyautogui.keyDown("ctrl")
    pyautogui.press("a")
    pyautogui.keyUp("ctrl")
    pyautogui.press("backspace")
