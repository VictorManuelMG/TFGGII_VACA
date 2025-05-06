from PIL import Image

from transformers.models.auto.processing_auto import AutoProcessor
from transformers.models.auto.modeling_auto import AutoModelForCausalLM

import torch
import os
from pathlib import Path
import time


from CUA.util.logger import logger

class florence_captioner:
    def __init__(
        self,
        model_dir: str = "Florence2",
        crop_dir: str = "tmpcrops",
        batch_size: int = 128,
    ):
        """Initialize Florence Model

        Args:
            model_dir (str, optional): Model folder direction. Defaults to "Florence2".
            crop_dir (str, optional): Img crops folder direction. Defaults to "tmpcrops" should be the same folder as the one passed to ScreenAssistant.
            batch_size (int, optional): Img batch size to do inferring by the model. Defaults to 128.
        """
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        self.root_dir = Path(__file__).resolve().parent
        self.model_path = self.root_dir / model_dir
        self.crop_dir = self.root_dir / crop_dir
        self.batch_size = batch_size



        logger.info(f"Florence inference is using: {self.device}")


        self.model = AutoModelForCausalLM.from_pretrained(
            str(self.model_path), torch_dtype=self.torch_dtype, trust_remote_code=True
        ).to(self.device)

        self.processor = AutoProcessor.from_pretrained(
            "microsoft/Florence-2-base", trust_remote_code=True
        )

    def _crops_and_ids(self):
        """Recovers Ids and Crops from the crops folder

        Returns:
            Crops,ids: returns an array of crops and ids
        """

        crops = []
        ids = []
        for filename in sorted(os.listdir(self.crop_dir)):
            if filename.startswith("cropped") and filename.endswith(".jpeg"):
                path = os.path.join(self.crop_dir, filename)
                img = Image.open(path)
                crop_id = int(filename.replace("cropped", "").replace(".jpeg", ""))
                crops.append(img)
                ids.append(crop_id)
        return crops, ids

    def _caption_batch(self, crops, ids):
        """Generate captions for each crop

        Args:
            crops (_type_): Cropped img to analyze
            ids (_type_): Id from the cropped image

        Returns:
            sorted_dict: returns a sorted dictionary of the captions of each crop sorted by id
        """
        captions = []
        caption_dictionary = {}
        for i in range(0, len(crops), self.batch_size):
            batch = crops[i : i + self.batch_size]
            inputs = self.processor(
                text=["<CAPTION>"] * len(batch),
                images=batch,
                return_tensors="pt",
                do_resize=False,
            ).to(self.device, self.torch_dtype)

            outputs = self.model.generate(
                input_ids=inputs["input_ids"],
                pixel_values=inputs["pixel_values"],
                max_new_tokens=50,
                num_beams=1,
                do_sample=False,
                early_stopping=False,
            )

            decoded = self.processor.batch_decode(outputs, skip_special_tokens=True)
            captions.extend([cap.strip() for cap in decoded])

        count = 0
        for id in ids:
            caption_dictionary[id] = captions[count]
            count += 1

        caption_dictionary_sorted = dict(sorted(caption_dictionary.items()))

        return caption_dictionary_sorted

    def generate_captions(self):
        start = time.time()
        crops, ids = self._crops_and_ids()
        caption_dict = self._caption_batch(crops, ids)
        end = time.time()

        logger.info(f"Florence execution time: {end - start} seconds")
        return caption_dict
