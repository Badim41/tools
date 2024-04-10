import asyncio

from discord_tools.image_generate import GenerateImages
generator = GenerateImages(secret_keys_kandinsky="DAD032D2C756C534CA938269620777EF",
                                     apis_kandinsky="C1B19528244C431627CC718B8E3792B0")
images = asyncio.run(generator.generate("Tree 4K"))
print(images)