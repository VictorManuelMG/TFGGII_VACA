# # Deprecated

# from CUA.tools.class_florence import FlorenceCaptioner
# from PIL import JpegImagePlugin

# #Ignore the warning in test abput timm.layers as it's a warnin for Florence2,problem with Microsoft code not from the programm.!!!!

# def test_FlorenceCaptionez_initialization():
#     """Test of initialization of ClassFlorence class
#     """    
    
#     florence = FlorenceCaptioner(
#         model_dir="Florence2",
#         crop_dir="tmpcrops",
#         batch_size=128,
#     )
#     assert florence.batch_size == 128 , f"Did not initialice batch size right, expected 128 got : {florence.batch_size}"
#     assert str(florence.model_path).endswith("Florence2") , f"Did not get model folder right E:{florence.model_path}"
#     assert str(florence.crop_dir).endswith("tmpcrops"), f"Did not get crops folder right E:{florence.crop_dir}"

# def test_crops_and_ids():
#     """Tests if crops and ids are recovered from the function
#     """    
#     florence = FlorenceCaptioner(
#         model_dir="Florence2",
#         crop_dir="tmpcrops",
#         batch_size=128,
#     )
#     crops, ids = florence._crops_and_ids()

#     assert isinstance(ids[0],int) , f"Doesnt correspond to the type of param expected, expected int got : {type(ids[0])}"
#     assert ids[0] == 0 , f"List Ids isn't instanciated or folder tmpcrops is empty or file is not named croppedX (x = number) E: {ids[0]}"
#     assert isinstance(crops[0],JpegImagePlugin.JpegImageFile) ,f"Doesn't correspond to the type of param expected, expected PIL.JpegImagePlugin.JpegImageFile got : {type(crops[0])}"

# def test_caption_batch():
#     florence = FlorenceCaptioner(
#         model_dir="Florence2",
#         crop_dir="tmpcrops",
#         batch_size=128,
#     )
#     crops,ids = florence._crops_and_ids()
#     caption = florence._caption_batch(crops,ids)
    
#     assert 0 in caption , f"Dictionary caption isn't instanciated or is empty due to tmpcrops folder or files names. E: {caption}"
#     assert caption[0].lower() == "testing" ,f"Value doesn't match with expected, expected 'testing' got : {caption[0].lower()}"

# def test_generate_captions():
#     """No need of testing as it's a call to the "private" functions
#     """    
#     pass