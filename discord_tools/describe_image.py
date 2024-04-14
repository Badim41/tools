from discord_tools.logs import Logs
from discord_tools.astica_API import Astica_Describe_Params, Astica_API

logger = Logs(warnings=True)


def detect_bad_image(image_path, isAdultContent=True, isRacyContent=True, isGoryContent=True, proxies=None):
    try:
        astica_api = Astica_API(proxies=proxies)
        result = astica_api.get_image_description(
            image_path,
            vision_params=Astica_Describe_Params.moderate)

        return (result['moderate']['isAdultContent'] and isAdultContent) or \
            (result['moderate']['isRacyContent'] and isRacyContent) or \
            (result['moderate']['isGoryContent'] and isGoryContent)
    except:
        return None


def describe_image(image_path, prompt="", isAdultContent=True, isRacyContent=True, isGoryContent=True, proxies=None):
    try:
        def get_object_info(data, result="", indent=0):
            for item in data:
                object_name = item['object']
                result += '  ' * indent + f'Object: {object_name}'
                if 'parent' in item:
                    get_object_info([item['parent']], result=result, indent=indent + 1)
                return result

        astica_api = Astica_API(proxies=proxies)
        result = astica_api.get_image_description(
            image_path,
            prompt=prompt,
            vision_params=Astica_Describe_Params.gpt_detailed)

        if result.get('caption_GPTS'):
            caption = result['caption_GPTS']
        else:
            caption = result['caption']['text'] + "\n\n" + get_object_info(data=result['objects'])

        return (result['moderate']['isAdultContent'] and isAdultContent) or \
               (result['moderate']['isRacyContent'] and isRacyContent) or \
               (result['moderate']['isGoryContent'] and isGoryContent), caption
    except Exception as e:
        logger.logging(e)
        return None, "-"
