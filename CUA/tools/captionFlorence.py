from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM
import torch
import os
from pathlib import Path


# Debugging import
import time


device = "cuda:0" if torch.cuda.is_available() else "cpu"
print("---------------------------------")
print(f"Usando device: {device}")
print("---------------------------------")

torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32


# Absolute route for model as huggingface gives problems with dynamic paths
ROOT_DIR = Path(__file__).resolve().parent
model_path = Path(__file__).resolve().parent / "Florence2"

# Model saved locally
model = AutoModelForCausalLM.from_pretrained(
    str(model_path), torch_dtype=torch_dtype, trust_remote_code=True
).to(device)

# Getting processor from huggingface, could be saved and called locally.
processor = AutoProcessor.from_pretrained(
    "microsoft/Florence-2-base", trust_remote_code=True
)


def crops_and_ids():
    """Recovers the IDs and images crom the tempcrops folder."""
    crops = []
    ids = []

    crops_dir = ROOT_DIR / "tempcrops"

    for filename in sorted(os.listdir(crops_dir)):
        if filename.startswith("cropped") and filename.endswith(".jpeg"):
            path = os.path.join(crops_dir, filename)
            img = Image.open(path)

            crop_id = int(filename.replace("cropped", "").replace(".jpeg", ""))
            crops.append(img)
            ids.append(crop_id)

    return (crops, ids)


def caption_batch(crops, ids, model, processor, batch_size):
    """generates captions for images given

    Args:
        crops (img): list of images cropped from the original screenshot
        ids (int): id embedded to every crop
        model (): call to model for caption inferring
        processor (): model processor.
        batch_size (int): size of the amount of images going to be inferred by the model

    Returns:
        dict: returns a sorted dictionary with the id and captions for te Bboxes
    """

    captions = []
    caption_dictionary = {}

    for i in range(0, len(crops), batch_size):
        batch = crops[i : i + batch_size]
        inputs = processor(
            text=["<CAPTION>"] * len(batch),
            images=batch,
            return_tensors="pt",
            do_resize=False,
        ).to(device, torch_dtype)

        outputs = model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=50,  # Low token numbers as we just want short captions
            num_beams=1,  # Low beams for more speed
            do_sample=False,
            early_stopping=False,
        )

        decoded = processor.batch_decode(outputs, skip_special_tokens=True)

        captions.extend([caption.strip() for caption in decoded])

    count = 0
    for id in ids:
        caption_dictionary[id] = captions[count]
        count += 1

    caption_dictionary_sorted = dict(sorted(caption_dictionary.items()))

    return caption_dictionary_sorted


def caption_call():
    """Call the captioning functions to return the caption dictionary for the Bboxes
        IMPORTANT: batch size should remain lower than 20 for low end computer specs, for more speed, resolution of the cropped images should lower than the actual 320x320
                    in case of lowering from 320x320, batch size could be higher
                    [usage of images resolution of 64x64 and batches of 128 roughly takes around 4 GB of VRAM for Florence v2 model. (Information from microsoft omniparser)]
                    Resolution cannot be higher than 640x640 as it'll give errors with Florence V2

    Returns:
        caption_dict: dictionary with ids and captions of the Bboxes.
    """
    start = time.time()
    crops, ids = crops_and_ids()
    caption_dict = caption_batch(crops, ids, model, processor, batch_size=64)
    end = time.time()

    print("\n************************************************************")
    print(f"Tiempo de ejecucion de Florence: {end - start} segundos")
    print("************************************************************\n")

    return caption_dict
