import asyncio
import random
from discord_tools.recraft_api import ImageTypeReCraftAPI, ComplexityReCraftAPI, RecraftAPI
# from IPython.display import display, Image as Image

recraft_API = RecraftAPI(AUTH_KEY_RECRAFT, project_id)

def make_vector_grind(prompt):
    return recraft_API.generate_image(
        prompt, 
        colors=["FF0000"],
        background_color="FFFFFF",
        complexity=ComplexityReCraftAPI.high,
        image_type=ImageTypeReCraftAPI.vector_illustration,
        negative_prompt='',
        width=1024,
        height=1024,
        output_path_name=f"image_{random.randint(-999,999)}")

results = make_vector_grind(prompt)
print("results", results)

# for png_filename in results:
#     display(Image_display(filename=png_filename))
