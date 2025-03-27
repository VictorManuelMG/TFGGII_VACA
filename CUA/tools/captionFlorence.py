#This module is still not implemented on the main program.

from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM 
import torch

device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

#Model saved locally
model = AutoModelForCausalLM.from_pretrained("./Florence2",torch_dtype=torch_dtype,trust_remote_code=True).to(device)
#Getting processor from huggingface, could be saved and called locally.
processor = AutoProcessor.from_pretrained("microsoft/Florence-2-base", trust_remote_code=True)


prompt = "<CAPTION>"


#Change cropped image to get caption from (This is just for trying out the model)
image = Image.open("./tempcrops/cropped54.jpeg")

inputs = processor(text=prompt, images=image, return_tensors="pt",do_resize=False).to(device, torch_dtype)

generated_ids = model.generate(
    input_ids=inputs["input_ids"],
    pixel_values=inputs["pixel_values"],
    max_new_tokens=200,
    num_beams=3,
    do_sample=False,
)

generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
response = processor.batch_decode(generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)


image.thumbnail((1920,1080))

print(response)
image.show()

