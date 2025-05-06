import random
import anthropic
import pyautogui
from ultralytics import YOLO
from PIL import ImageGrab
import os
import shutil
import base64
import time
import cv2
import copy
import openai
from pathlib import Path
from CUA.tools.class_florence import florence_captioner


from CUA.util.logger import logger


class screen_assistant:
    def __init__(
        self,
        captioner: florence_captioner,
        model_dir: str = "model.pt",
        model_screen_interpreter: str = "claude-3-7-sonnet-latest",
        max_tokens_SI: int = 1024,
        crop_dir: str = "tmpcrops",
    ) -> None:
        """Initialize screeninterpreter with YOLO

        Args:
            captioner (FlorenceCaptioner): Captioner model, in this case Florencev2
            model_dir (str, optional): dir of yolo model. Defaults to "model.pt".
            model_screen_interpreter (str, optional): Claude model for interpreting images. Defaults to "claude-3-7-sonnet-latest".
            max_tokens_SI (int, optional): max token output for Claude. Defaults to 1024.
            crop_dir (str, optional): dir to save crops. Defaults to Path("./CUA/tools/tempcrops").
        """
        self.yolo = YOLO(model_dir)
        self.model_screen_interpreter = model_screen_interpreter
        self.max_tokens_SI = max_tokens_SI

        self.root_dir = Path(__file__).resolve().parent

        self.crop_dir = self.root_dir / crop_dir
        self.captioner = captioner
        self.client = anthropic.Anthropic()

    def simple_interpreter(self, order: str):
        """Analyzes an image and gives feedback about it

        Args:
            order (str): User's prompt

        Returns:
            Message: LLM's answer
        """
        image = ImageGrab.grab()
        image.save("screenshot2.jpeg")

        with open("screenshot2.jpeg", "rb") as image_file:
            img_data = base64.b64encode(image_file.read()).decode("utf-8")
        if "claude" in self.model_screen_interpreter:
            message = self.client.messages.create(
                model=self.model_screen_interpreter,
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
                                "text": """Role: You are a visual operator for a computer use agent. 
                                
                                Your task is to analyze what you see on the image, the image sended is a screenshot of the user's enviroment.
                                You'll also respond whatever question the user have about the image.""",
                            }
                        ],
                    },
                ],
            )
            return message
        elif "gpt" in self.model_screen_interpreter:
            response = openai.chat.completions.create(
                model=self.model_screen_interpreter,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_data}",
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
                                "text": """Role: You are a visual operator for a computer use agent. 
                            
                            Your task is to analyze what you see on the image, the image sent is a screenshot of the user's environment.
                            You'll also respond to whatever question the user has about the image.""",
                            }
                        ],
                    },
                ],
                max_tokens=1024,
            )
        return (response.model_dump()) #type: ignore

    def interpret_screen(self, order: str):
        """Makes a call to a model to interpret screen information and gives back directions about what to do to complete user's request such as opening a browser, typing, etc...
        Args:
            order (str): User order about screen information

        Returns:
            message: LLM answer
        """

        image = ImageGrab.grab()
        image.save("screenshot.jpeg")

        if os.path.exists(self.crop_dir):
            shutil.rmtree(self.crop_dir)
        os.makedirs(self.crop_dir, exist_ok=True)
        coords = self._image_YOLOED("screenshot.jpeg")
        with open("Yoloed.jpeg", "rb") as image_file:
            img_data = base64.b64encode(image_file.read()).decode("utf-8")

        cursor = pyautogui.position()

        start = time.time()

        if "claude" in self.model_screen_interpreter:
            message = self.client.messages.create(
                model=self.model_screen_interpreter, max_tokens=1024, messages= [
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

                                <bounding_boxes with captions>
                                {coords}
                                </bounding_boxes with captions>

                                <cursor_coordinates>
                                {cursor}
                                <cursor_coordinates/>

                                For each user request, follow these steps:

                                1. Carefully read the user request:

                                2. Analyze the image description and bounding boxes to locate the requested element take in account the captions on the bounding boxes if you don't know what are you seeing, take in account captions might be sometimes wrong.

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
                                Your feedback must always have coordinates for the agent.
                                The coordinates on the feedback must be in the {coords} given, and if you're going to do pixel counting, tell so to the user.""",
                        }
                    ],
                },
            ],
            )

            end = time.time()


            logger.info(f"interpret_screen Claude image inference duration: {end - start} seconds")


            return message
        


        elif "gpt" in self.model_screen_interpreter:
            start = time.time()
            response = openai.chat.completions.create(
                model=self.model_screen_interpreter, messages= [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_data}"
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

                                <bounding_boxes with captions>
                                {coords}
                                </bounding_boxes with captions>

                                <cursor_coordinates>
                                {cursor}
                                <cursor_coordinates/>

                                For each user request, follow these steps:

                                1. Carefully read the user request:

                                2. Analyze the image description and bounding boxes to locate the requested element take in account the captions on the bounding boxes if you don't know what are you seeing, take in account captions might be sometimes wrong.

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
                                Your feedback must always have coordinates for the agent.
                                The coordinates on the feedback must be in the {coords} given, and if you're going to do pixel counting, tell so to the user.""",
                        }
                    ],
                },
            ], max_tokens=1024
            )
            end = time.time()

            logger.info(f"interpret_screen OpenAI image inference duration: {end - start} seconds")

            return(response.model_dump())



    def _image_YOLOED(self, pathScreenshot: str):
        """Takes a image and uses YOLO to bound icons with squares and indexes for the LLM to understand better coordinates.

        Args:
            pathScreenshot (str): path to the screenshot of the user's computer screen

        Returns:
            coords: returns the coordinates of all the bounded icons and its captions
        """
        coords = {}

        image = cv2.imread(pathScreenshot)

        resultsOriginal = self.yolo.predict(
            image,
            save=False,
            conf=0.05,  # Low conf so it makes more bounding boxes
            iou=0.35,  # Lower iou to not let the model hallucinate certain boundin boxes
            line_width=1,
            imgsz=1920,  # Always resized to 1920
            show_labels=True,
            show_conf=False,
        )

        coords = self._Yolo_boxes_coord(image, resultsOriginal)

        logger.debug(f"class_screen_assistant.screen_assistant._image_YOLOED coordinates infered : {coords}")

        return coords

    def _Yolo_boxes_coord(self, image, results: list):
        """paints the bounded boxes on the detected objects and gives them an index

        Args:
            image (_type_): Original screenshot to paint into.
            results (list): The result of the prediction made by YOLO (coords of the box, width height)

        Returns:
            Complete_dict:  returns the center coordinate of the objects bounded and its captions
        """

        original_image = copy.deepcopy(image)
        index = {}
        count = 0

        Bboxes = []
        CaptionBboxes = {}

        complete_dict = {}

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                # confidence = box.conf[0].item()
                Bboxes.append([x1, y1, x2, y2])
                R = random.randint(0, 255)
                G = random.randint(0, 255)
                B = random.randint(0, 255)

                cv2.rectangle(
                    img=image,
                    pt1=(x1, y1),
                    pt2=(x2, y2),
                    color=(B, G, R),
                    thickness=2,
                )

                text = f"{count}"

                cv2.putText(
                    image,
                    text,
                    (x2 - 30, y1 + 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (B, G, R),
                    2,
                )

                cropped_image = original_image[y1:y2, x1:x2]
                cropped_resized = cv2.resize(cropped_image, (64, 64))

                filename = f"cropped{count}.jpeg"
                fullpath = self.crop_dir / filename

                cv2.imwrite(str(fullpath), cropped_resized)
                index[count] = [round((x1 + x2) / 2), round((y1 + y2) / 2)]
                count += 1

        CaptionBboxes = self.captioner.generate_captions()

        for key in index:
            complete_dict[key] = {
                "coord": index[key],
                "caption": CaptionBboxes[key],
            }

        cv2.imwrite("Yoloed.jpeg", image)
        logger.debug(f"class_screen_assistant.screen_assistant._YoloBoxes_coord coordinates and caption results: {complete_dict}")
        return complete_dict
