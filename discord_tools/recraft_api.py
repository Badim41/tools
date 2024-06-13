import svgwrite
import cairosvg
import requests
import re
import random
import io
from PIL import Image


class ComplexityReCraftAPI:
    primitive = 0
    log = 1
    medium = 2
    high = 3
    extreme = 4

class ImageTypeReCraftAPI:
    icon = "icon"
    icon_outline = "icon_outline"
    icon_broken_line = "icon_broken_line"
    icon_colored_shapes = "icon_colored_shapes"
    icon_colored_outline = "icon_colored_outline"
    icon_uneven_fill = "icon_uneven_fill"
    icon_doodle_fill = "icon_doodle_fill"
    icon_offset_fill = "icon_offset_fill"
    icon_doodle_offset_fill = "icon_doodle_offset_fill"
    icon_outline_gradient = "icon_outline_gradient"
    icon_colored_shapes_gradient = "icon_colored_shapes_gradient"
    pictogram = "pictogram"
    digital_illustration_pixel_art = "digital_illustration_pixel_art"
    digital_illustration = "digital_illustration"
    digital_illustration_seamless = "digital_illustration_seamless"
    digital_illustration_3d = "digital_illustration_3d"
    digital_illustration_2d_art_poster_2 = "digital_illustration_2d_art_poster_2"
    digital_illustration_engraving_color = "digital_illustration_engraving_color"
    digital_illustration_hand_drawn_outline = "digital_illustration_hand_drawn_outline"
    digital_illustration_handmade_3d = "digital_illustration_handmade_3d"
    digital_illustration_psychedelic = "digital_illustration_psychedelic"
    digital_illustration_hand_drawn = "digital_illustration_hand_drawn"
    digital_illustration_grain = "digital_illustration_grain"
    digital_illustration_glow = "digital_illustration_glow"
    digital_illustration_80s = "digital_illustration_80s"
    digital_illustration_watercolor = "digital_illustration_watercolor"
    digital_illustration_voxel = "digital_illustration_voxel"
    digital_illustration_infantile_sketch = "digital_illustration_infantile_sketch"
    digital_illustration_2d_art_poster = "digital_illustration_2d_art_poster"
    digital_illustration_kawaii = "digital_illustration_kawaii"
    illustration_3d = "illustration_3d"
    realistic_image = "realistic_image"
    realistic_image_mockup = "realistic_image_mockup"
    realistic_image_b_and_w = "realistic_image_b_and_w"
    realistic_image_hard_flash = "realistic_image_hard_flash"
    realistic_image_hdr = "realistic_image_hdr"
    realistic_image_natural_light = "realistic_image_natural_light"
    realistic_image_studio_portrait = "realistic_image_studio_portrait"
    realistic_image_enterprise = "realistic_image_enterprise"
    variate = "variate"
    vector_illustration_line_art = "vector_illustration_line_art"
    vector_illustration_doodle_line_art = "vector_illustration_doodle_line_art"
    vector_illustration_linocut = "vector_illustration_linocut"
    vector_illustration_engraving = "vector_illustration_engraving"
    vector_illustration = "vector_illustration"
    vector_illustration_seamless = "vector_illustration_seamless"
    vector_illustration_flat_2 = "vector_illustration_flat_2"
    vector_illustration_cartoon = "vector_illustration_cartoon"
    vector_illustration_kawaii = "vector_illustration_kawaii"
    vector_illustration_line_circuit = "vector_illustration_line_circuit"
    logo = "logo"

class RecraftAPI:
    def __init__(self, auth_key_craft, project_id, proxies=None):
        self.auth_key_craft = auth_key_craft
        self.project_id = project_id
        self.proxies = proxies

    def generate_image(self, prompt, colors:list, background_color="FFFFFF", complexity=ComplexityReCraftAPI.high, image_type=ImageTypeReCraftAPI.vector_illustration, negative_prompt='', width=1024, height=1024, seed=None, number=2, output_path_name="image"):
        rgb_colors = [{'rgb': [int(x, 16) for x in re.findall(r'.{2}', color.upper().replace("#",""))]} for color in colors]
        background_color = {'rgb': [int(x, 16) for x in re.findall(r'.{2}', background_color.upper().replace("#",""))]}

        if not seed:
            seed= random.randint(111111, 999999)

        operation_id = self.get_operation_id(
                image_type=image_type,
                negative_prompt=negative_prompt,
                complexity=complexity,
                rgb_colors=rgb_colors,
                height=height,
                width=width,
                seed=seed,
                background_color=background_color,
                prompt=prompt  # Используйте значение переменной prompt здесь
            )
        print("operation_id",operation_id)

        return self.get_result(operationId, output_path_name)
        
    def get_operation_id(self, prompt, image_type, negative_prompt, complexity, rgb_colors, height, width, seed, background_color):
        headers = {
                'accept': '*/*',
                'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'authorization': f'Bearer {self.auth_key_craft}',
                'content-type': 'application/json',
                'origin': 'https://app.recraft.ai',
                'priority': 'u=1, i',
                'referer': 'https://app.recraft.ai/',
                'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                'x-client-type': 'web-app.recraft.ai',
            }
            
        params = {
                'project_id': self.project_id,
            }
            
        json_data = {
                'prompt': prompt,
                'image_type': image_type,
                'negative_prompt': negative_prompt,
                'user_controls': {
                    'complexity': complexity,
                    'colors': rgb_colors,
                },
                'background_color': background_color,
                'layer_size': {
                    'height': height,
                    'width': width,
                },
                'random_seed': seed,
                'developer_params': {},
            }
            
        response = requests.post('https://api.recraft.ai/queue_recraft/prompt_to_image', params=params, headers=headers, json=json_data)
            
        return response.json()['operationId']
    
    def get_result(self, operationId, output_path_name):
        headers = {
            'accept': '*/*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'authorization': f'Bearer {AUTH_KEY_RECRAFT}',
            'origin': 'https://app.recraft.ai',
            'priority': 'u=1, i',
            'referer': 'https://app.recraft.ai/',
            'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'x-client-type': 'web-app.recraft.ai',
        }
    
        params = {
          'operation_id': operationId,
      } 
        
        response = requests.get('https://api.recraft.ai/poll_recraft', params=params, headers=headers)

        output_paths = []

        for i, data in enumerate(response.json()['images']):
            if "rector" in data:
                # Создаем новый SVG файл
                svg_filename = f'{output_path_name}{i}.svg'
                dwg = svgwrite.Drawing(svg_filename, profile='tiny', size=(data["rector"]["height"], data["rector"]["height"]))
        
                # Добавляем фигуры в SVG
                for shape in data["rector"]["shapes"]:
                    style = data["rector"]["styles"][shape["style_index"]]
                    fill_color = style["fill"]["solid_color"]["rgba_hex"][:7] if style["fill"]["style_type"] == "solid" else "none"
                    stroke_color = "none" if style["stroke"]["style_type"] == "none" else style["stroke"]["solid_color"]["rgba_hex"][:7]
                    stroke_width = style["stroke_width"]
        
                    dwg.add(dwg.path(d=shape["svg_path"], fill=fill_color, stroke=stroke_color, stroke_width=stroke_width))
        
                # Сохраняем SVG файл
                dwg.save()
        
                png_filename = svg_filename.replace('.svg', '.png')
                cairosvg.svg2png(url=svg_filename, write_to=png_filename, output_width=256, output_height=256)
        
                output_paths.append(png_filename)
                # display(Image_display(filename=png_filename))
            else:
                image_id = data['image_id']
                print("image_id", image_id)
                png_filename = f'{output_path_name}{i}.png'
                headers = {'authorization': f'Bearer {AUTH_KEY_RECRAFT}'}
                response_2 = requests.get(f"https://api.recraft.ai/image/{image_id}", headers=headers)
                if response_2.status_code == 200:
                    image = Image.open(io.BytesIO(response_2.content))
                    image.save(png_filename, "PNG")
                    output_paths.append(png_filename)
                else:
                    print("NOT SUCCESS")
        return output_paths[:2]
