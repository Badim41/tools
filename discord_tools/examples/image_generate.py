import asyncio
from discord_tools.image_generate import GenerateImages

if __name__ == '__main__':
    generator = GenerateImages()
    images = asyncio.run(generator.generate("аватарка, тележка с покупками, простой стиль", polinations=False, hugging_face=False))
    print(images)
