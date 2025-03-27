import shutil
from langchain_core.tools import tool
import anthropic
from PIL import ImageGrab
import base64
import pyautogui
import os

from ultralytics import YOLO
import cv2
import random
import copy

@tool
def interpret_screen(order: str):
    """Returns answers made to the LLM about what's on the user's screen

    Args:
        order (str): Question about the screen to the LLM

    Returns:
        message: LLM answer
    """
    image = ImageGrab.grab()
    image.save("screenshot.jpeg")



    if os.path.exists("./CUA/tools/tempcrops"):
        shutil.rmtree("./CUA/tools/tempcrops")  
    os.makedirs("./CUA/tools/tempcrops", exist_ok=True) #Generate a tempfolder for the crops given to Florence, will be removed in the future.
    coords = image_YOLOED("screenshot.jpeg")
    with open("Yoloed.jpeg", "rb") as image_file:
        img_data = base64.b64encode(image_file.read()).decode("utf-8")

    client = anthropic.Anthropic()
    cursor = pyautogui.position()



    message = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": img_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": f"**USER** The user is asking: {order}",
                    },
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": f"""Role: You are a visual operator for a computer use agent. 
                        
                        Your task is to analyze visual information and provide precise coordinates for 
                        clicking on specific elements based on user requests. You will be given an image description, a dictionary of bounding boxes for various elements, 
                        and a user request. Here's how to proceed:
                        
                        First, you will receive the following information:

                        an image_description

                        <bounding_boxes>
                        {coords}
                        </bounding_boxes>

                        <cursor_coordinates>
                        {cursor}
                        <cursor_coordinates/>

                        For each user request, follow these steps:

                        1. Carefully read the user request:

                        2. Analyze the image description and bounding boxes to locate the requested element.

                        3. If the requested element is found in the bounding boxes:
                        a. Identify the corresponding bounding box.
                        b. Return the coordinates in the format: (x, y).

                        4. If the requested element is not found in the bounding boxes:
                        a. Use the image description to estimate the location of the element.
                        b. Perform pixel counting to determine the approximate coordinates.
                        c. Return the estimated coordinates in the format: (x, y).

                        5. If the requested element cannot be found or identified:
                        Explain that the element could not be located and provide a brief reason why in with pixel country try to
                        achieve the user request.

                        6. Provide your response in the following format:
                        <response>
                        [Your explanation of how you found the element or why you couldn't find it]
                        Coordinates: (x, y)
                        </response>

                        Remember to be as precise as possible when determining coordinates. If you need to make any assumptions or estimations, clearly state them in your explanation.
                        Also remember to always use the bounding boxes.
                        Also give your own insights like advices when you're asked something like "is the dropdown visible?" you should respond like "No but you can drop it clicking on...".
                        Your feedback must always have coordinates for the agent."""
                    }
                ],
            },
        ],
    )

    return message


def image_YOLOED(pathScreenshot: str):
    """Takes a image and uses YOLO to bound icons with squares and indexes for the LLM to understand better coordinates, it uses original and gray scale image from the screenshot
        And selects the one with more bounded objects.

    Args:
        pathScreenshot (str): path to the screenshot of the user's computer screen

    Returns:
        coords: returns the coordinates of all the bounded icons
    """
    yolo = YOLO("model.pt")
    coords = {}

    count_original = 0
    count_gray = 0

    image = cv2.imread(pathScreenshot)

    resultsOriginal = yolo.predict(
        image,
        save=False,
        conf=0.05, #Low conf so it makes more bounding boxes
        iou=0.35, #Lower iou to not let the model hallucinate certain boundin boxes
        line_width=1,
        imgsz=1920, #Always resized to 1920
        show_labels=True,
        show_conf=False,
    )

    #In case colour palette is too similar, included gray scale analysis
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    cv2.imwrite("gray.jpeg", gray_image)

    resultsGray = yolo.predict(
        "gray.jpeg",
        save=False,
        conf=0.05, #Low conf so it makes more bounding boxes
        iou=0.2, #Even lower IOU than original as it tends to hallucinate more with gray scale
        line_width=1,
        imgsz=1920, #Always resized to 1920
        show_labels=True,
        show_conf=False,
    )

    for result in resultsOriginal:
        for box in result:
            count_original += 1
    for result in resultsGray:
        for box in result:
            count_gray += 1

    if count_original >= count_gray:
        coords = Yolo_boxes_coord(image, resultsOriginal)
    else:
        coords = Yolo_boxes_coord(image, resultsGray)
    print(count_gray, count_original)
    return coords


def Yolo_boxes_coord(image, results: list):
    """paints the bounded boxes on the detected objects and gives them an index

    Args:
        image (_type_): Original screenshot to paint into.
        results (list): The result of the prediction made by YOLO

    Returns:
        index (dict): returns the center coordinate of the objects bounded
    """
    original_image = copy.deepcopy(image)
    index = {}
    count = 0

    Bboxes = []
    FlorenceIndex={}

    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            # confidence = box.conf[0].item()

            Bboxes.append([x1,y1,x2,y2])

            R = random.randint(0, 255)
            G = random.randint(0, 255)
            B = random.randint(0, 255)

            #Generate bounding box
            cv2.rectangle(
                img=image, pt1=(x1, y1), pt2=(x2, y2), color=(B, G, R), thickness=2
            )

            text = f"{count}"
            
            #Add index to Bbox
            cv2.putText(
                image,
                text,
                (x2 - 30, y1 + 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (B, G, R),
                2,
            )

            cropped_image = original_image[y1:y2,x1:x2]
            cropped_resized = cv2.resize(cropped_image,(320,320))
            cv2.imwrite(f"./CUA/tools/tempcrops/cropped{count}.jpeg",cropped_resized)

            index[count] = [round((x1 + x2) / 2), round((y1 + y2) / 2)]
            FlorenceIndex[count] = [Bboxes]
            count += 1


    print(index)
    # print(FlorenceIndex)
    cv2.imwrite("Yoloed.jpeg", image)

    return index
