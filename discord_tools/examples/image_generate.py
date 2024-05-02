import asyncio
from discord_tools.image_generate import GenerateImages

if __name__ == '__main__':
    generator = GenerateImages()
    images = asyncio.run(generator.generate("Tree 4K"))
    print(images)
