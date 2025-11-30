import torch
from diffusers import Flux2Pipeline
from diffusers.utils import load_image
from huggingface_hub import get_token
import requests
import io
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

repo_id = "diffusers/FLUX.2-dev-bnb-4bit"
device = "cuda:0"
torch_dtype = torch.bfloat16

def remote_text_encoder(prompts):
    response = requests.post(
        "https://remote-text-encoder-flux-2.huggingface.co/predict",
        json={"prompt": prompts},
        headers={
            "Authorization": f"Bearer {get_token()}",
            "Content-Type": "application/json"
        }
    )
    response.raise_for_status()  # Raise an error for bad status codes
    
    # Check if response is valid
    if response.status_code != 200:
        raise ValueError(f"API returned status code {response.status_code}: {response.text}")
    
    # Try to load as PyTorch tensor
    try:
        prompt_embeds = torch.load(io.BytesIO(response.content), weights_only=False)
    except Exception as e:
        # If loading fails, print the response to debug
        print(f"Error loading PyTorch tensor. Response content (first 500 chars): {response.content[:500]}")
        print(f"Response headers: {response.headers}")
        raise

    return prompt_embeds.to(device)

pipe = Flux2Pipeline.from_pretrained(
    repo_id, text_encoder=None, torch_dtype=torch_dtype
).to(device)

prompt = "Realistic macro photograph of a hermit crab using a soda can as its shell, partially emerging from the can, captured with sharp detail and natural colors, on a sunlit beach with soft shadows and a shallow depth of field, with blurred ocean waves in the background. The can has the text `BFL Diffusers` on it and it has a color gradient that start with #FF5733 at the top and transitions to #33FF57 at the bottom."

image = pipe(
    prompt_embeds=remote_text_encoder(prompt),
    #image=load_image("https://huggingface.co/spaces/zerogpu-aoti/FLUX.1-Kontext-Dev-fp8-dynamic/resolve/main/cat.png") #optional image input
    generator=torch.Generator(device=device).manual_seed(42),
    num_inference_steps=50, #28 steps can be a good trade-off
    guidance_scale=4,
).images[0]

image.save("flux2_output.png")