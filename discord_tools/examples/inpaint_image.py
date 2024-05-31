import asyncio
from discord_tools.image_generate import GenerateImages, ArtbreederImageGenerateAPI

image_generator = GenerateImages()

async def make_inpaint_grind(image_path, prompt):
    return await image_generator.generate_image_grid(model_class=ArtbreederImageGenerateAPI,
                                                       image_name="1",
                                                       prompt=prompt,
                                                       row_prompt=prompt,
                                                       delete_temp=False,
                                                       input_image_path=image_path)


prompt = "make image in anime style"
image_path = input("File:")
result = asyncio.run(make_inpaint_grind(image_path, prompt))
print("result", result)