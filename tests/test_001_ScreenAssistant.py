# # Deprecated as now every logic about screening is on a docker.


# from CUA.tools.endpoint_yolo_florence import screen_assistant
# from unittest.mock import MagicMock
# from pathlib import Path
# import cv2
# import numpy as np
# import shutil
# import os

# parent_dir = str(Path(__file__).resolve().parent)
# vaca_dir =str(Path(__file__).resolve().parent.parent)


# def test_screen_assistant_initialization():
#     """Test the generation of Screen Assistant class, we use a mock as Florence sustitute for the initialization.
#     """    
#     mock_captioner = MagicMock()
#     assistant = screen_assistant(
#         captioner=mock_captioner,
#         model_dir=parent_dir + "/dummy.pt",
#         crop_dir="tmpcrops"
#     )

#     assert assistant.model_screen_interpreter == "claude-3-7-sonnet-latest"
#     assert assistant.captioner == mock_captioner
#     assert str(assistant.crop_dir).endswith("tmpcrops")


# def test_yolo_boxes_coord():
#     """Test of the function that generates boxes with parameters given by YOLO (we use a dummy yolo to generate these inputs), 
#     checks if it generates correctly, if it generates a cropped folder as shown in the default of the class with a cropped image, if the dictionary returns the values it should return

#     """    
#     mock_captioner = MagicMock()
#     mock_captioner.generate_captions.return_value = {0: "testing"}

#     assistant = screen_assistant(
#         captioner=mock_captioner,
#         model_dir=parent_dir + "/dummy.pt",
#         crop_dir="tmpcrops"
#     )
#     blank_img = np.zeros(shape=(1920, 1080, 3), dtype=np.int16)
#     cv2.putText(
#         blank_img,
#         "Testing",
#         (200, 256),
#         cv2.FONT_HERSHEY_SIMPLEX,
#         2,
#         (100, 100, 255),
#         4,
#     )

#     # making folder to save generated image in case of checking
#     os.makedirs(Path(__file__).resolve().parent / "resources", exist_ok=True)
#     os.makedirs(Path(__file__).resolve().parent / "resources/generatedimage/", exist_ok=True)
#     cv2.imwrite("./resources/generatedimage/imagen.jpeg", blank_img)

#     mock_results = assistant.yolo.predict(
#         blank_img,
#         save=False,
#         conf=0.05,
#         iou=0.35,
#         line_width=1,
#         imgsz=1920,
#         show_labels=True,
#         show_conf=False,
#     )

#     # Making folder for crops comprobation
#     tmp_test_path = Path(__file__).resolve().parent.parent / "CUA/tools/tmpcrops"
#     if os.path.exists(tmp_test_path):
#         shutil.rmtree(tmp_test_path)

#     os.makedirs(tmp_test_path, exist_ok=True)

#     caption = assistant._Yolo_boxes_coord(blank_img, mock_results)
#     shutil.move(
#         parent_dir + "/Yoloed.jpeg",
#         parent_dir + "/resources/generatedimage/Yoloed.jpeg",
#     )

#     assert 294<= caption[0]["coord"][0] <=314, f"Coordinates are not the same, expected value between 294 and 314, got: {caption[0]["coord"][0]}"  # type: ignore
#     assert 229 <= caption[0]["coord"][1] <= 249, f"Coordinate Y is not the same, expected value between 229 and 249, got : {caption[0]["coord"][1]}"# type: ignore
#     assert 0 in caption, "No key 0 returned dictionary"  # type: ignore
#     assert caption[0]["caption"] == "testing", "Wrong caption for Bbox 0"  # type: ignore

#     try:
#         cropped_path = tmp_test_path / "cropped0.jpeg"
#         print(cropped_path)
#         open(str(cropped_path), "rb")
#     except FileNotFoundError:
#         assert False, "File not found"
#     else:
#         assert True

# def test_image_YOLOED():
#     """Tests if returned dict is right as with yolo_boxes_coord, test if params and instanziation of YOLO in the class function is right.
#         As it calls yolo_boxes_coord it has the same asserts, in the end this func is just the call of YOLO into the image given which is done on the other test manually with the
#         same params.
#     """    
#     mock_captioner = MagicMock()
#     mock_captioner.generate_captions.return_value={0: "testing"}
    
#     assistant = screen_assistant(
#         captioner=mock_captioner,
#         model_dir= parent_dir + "/dummy.pt",
#         crop_dir= "tmpcrops"
#     )
#     blank_img = vaca_dir + "/tests/resources/generatedimage/imagen.jpeg"
#     caption = assistant._image_YOLOED(blank_img)
    
#     shutil.move(
#     parent_dir + "/Yoloed.jpeg",
#     parent_dir + "/resources/generatedimage/Yoloed2.jpeg",
#     )

#     assert 294<= caption[0]["coord"][0] <=314, f"Coordinates are not the same, expected value between 294 and 314, got: {caption[0]["coord"][0]}"  # type: ignore
#     assert 229 <= caption[0]["coord"][1] <= 249, f"Coordinate Y is not the same, expected value between 229 and 249, got : {caption[0]["coord"][1]}"# type: ignore
#     assert 0 in caption, "No key 0 returned dictionary"  # type: ignore
#     assert caption[0]["caption"] == "testing", "Wrong caption for Bbox 0"  # type: ignore

# def test_interpret_screen():
#     """Not going to be tested as it is an API call to Anthropic with a prompt with a image, as LLM are volatile, it'll give different responses and will cost tokens.
#     """    
#     assert(True)
# def test_simple_interpreter():
#     """Same with this func, not going to be tested as it's an even more simple call to the LLM
#     """    
#     assert(True)