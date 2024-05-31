import asyncio
from discord_tools.image_generate import GenerateImages, ArtbreederImageGenerateAPI
from discord_tools.upscaler import resize_image_if_small_or_big

image_generator = GenerateImages()

async def make_inpaint_grind(image_path, prompt):
    resize_image_if_small_or_big(image_path, max_megapixels=1)
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