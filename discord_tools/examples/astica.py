from discord_tools.astica_API import Astica_API, Astica_Describe_Params

image_path = "cookie.png"
astica_api = Astica_API()
result = astica_api.get_image_description(image_path,
                                          prompt="Что это за картинка?",
                                          vision_params=Astica_Describe_Params.gpt_detailed)

print(result['caption_GPTS'])

