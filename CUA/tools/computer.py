import pyautogui
import keyboard
from langchain_core.tools import tool
import pyperclip


@tool
def move_mouse(x: int, y: int):
    """with the coords x and y given make the mouse move to the desired position

    Args:
        x (int): coord x from screen
        y (int): coord y from screen

    Returns:
        status: Error or Sucessful
    """
    try:
        pyautogui.moveTo(x, y, 0.5)
        return f"Moved mouse to {x},{y}"
    except Exception as e:
        return f"Error moving mouse: {e}"


@tool
def mouse_clicker(action: str):
    """Performs different types of clicks.

    Args:
        action (str): Action click to perform by mouse:
                        single_clickleft = single left click with mouse
                        double_clickleft = double left click with mouse
                        single_clickright = single right click with mouse
                        double_clickright = double right click with mouse

    Returns:
        status: error or sucessful
    """
    try:
        if action == "single_clickleft":
            pyautogui.click(button="left")
        elif action == "double_clickleft":
            pyautogui.click(button="left", clicks=2)
        elif action == "single_clickright":
            pyautogui.click(button="right")
        elif action == "double_clickright":
            pyautogui.click(button="right", clicks=2)
        else:
            return f"Invalid click action: {action}"
        return f"Performed {action} action."
    except Exception as e:
        return f"Error performing mouse click: {e}"


@tool
def keyboard_input(text: str):
    """simulates a keyboard and writes to input texts

    Args:
        text (str): text to write simulating the keyboard
    Returns:
        status: Error or sucessful
    """

    try:
        keyboard.write(text, delay=0.02)
        return f"Inputted '{text}'"
    except Exception as e:
        return f"Error inputting text: {e}"


@tool
def keyboard_hotkey(action: str):
    """Simmulates special keys like "enter", "shift", "pagedown", "pageup", "browserback", "browserrefresh", "tab"

    Args:
        action (str): key to press

    Returns:
        status: Error or sucessful
    """

    try:
        if action in [
            "enter",
            "shift",
            "pagedown",
            "pageup",
            "browserback",
            "browserrefresh",
            "tab",
        ]:
            pyautogui.press(action)
            return f"Pressed {action}"
        else:
            return f"Invalid hotkey action: {action}"
    except Exception as e:
        return f"Error pressing hotkey '{action}': {e}"
    
@tool
def keyboard_keypress(key: str):
    """Presses any individual key, including alphabet letters (a-z)

    Args:
        key (str): key to press (e.g., 'a', 'b', '1', etc.)

    Returns:
        status: Error or sucessful
    """
    try:
        if len(key) == 1 and key.isprintable():
            pyautogui.press(key)
            return f"Pressed key: {key}"
        else:
            return f"Invalid key input: {key}"
    except Exception as e:
        return f"Error pressing key '{key}': {e}"


@tool
def delete_text():
    """selects all text and deletes it

    Returns:
        status: Error or sucessful
    """
    try:
        pyautogui.keyDown("ctrl")
        pyautogui.press("a")
        pyautogui.keyUp("ctrl")
        pyautogui.press("backspace")
        return "Deleted text."
    except Exception as e:
        return f"Error deleting text: {e}"


@tool
def keyboard_combo(modifier: str, key: str):
    """presses a combo of a key being "ctrl" , "shift" , "alt", "win" and another normal key.

    Args:
        modifier (str): special key
        key (str): normal key

    Returns:
        status: parses if there was an error trying to press the combo or if it was sucessful
    """
    try:
        valid_modifiers = ["ctrl", "shift", "alt", "win"]
        if modifier not in valid_modifiers:
            return f"Invalid modifier '{modifier}'. Use one of: {valid_modifiers}"
        pyautogui.hotkey(modifier, key)
        return f"Pressed {modifier} + {key}"
    except Exception as e:
        return f"Error pressing combo {modifier} + {key}: {e}"

@tool
def paste_full_code(code: str):
    """
    Pastes a full block of code using the clipboard to preserve indentation.

    Copies the provided code to the system clipboard and simulates
    pressing Ctrl+V to paste it into the active window (e.g., VS Code).

    Args:
        code (str): The complete code block to paste.

    Returns:
        str: Status message about the result.
    """
    try:
        pyperclip.copy(code)
        keyboard.press_and_release("ctrl+v")
        return "Successfully pasted full code using clipboard."
    except Exception as e:
        return f"Error pasting code: {e}"
