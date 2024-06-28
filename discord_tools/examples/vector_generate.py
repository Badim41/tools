import asyncio
import random
from discord_tools.recraft_api import ImageTypeReCraftAPI, ComplexityReCraftAPI, RecraftAPI
# from IPython.display import display, Image as Image

import random

project_id = '742eb1fd-dd8e-4129-90e6-96f133a9b36c'
AUTH_KEY_RECRAFT = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJ5ei1YaE9TSnZ2T3FLWVFFS0xONks0M3JFWDlOelNNd1Fnd1F1VEtIbG1VIn0.eyJleHAiOjE3MTg3NjEwNDEsImlhdCI6MTcxODE1NjI0MSwiYXV0aF90aW1lIjoxNzE4MTU2MjQwLCJqdGkiOiI2ZmJjNGY5OS02NDhmLTQ3OWQtYjc2OC0wNzViZDRjNzg1ZTAiLCJpc3MiOiJodHRwczovL2lkLnJlY3JhZnQuYWkvcmVhbG1zL3JlY3JhZnQiLCJhdWQiOiJhY2NvdW50Iiwic3ViIjoiYmE2YjY0YzItYjJlZC00YzhjLWJkNzktN2VmZTFiYjUxNTkwIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiZnJvbnRlbmQtY2xpZW50Iiwic2Vzc2lvbl9zdGF0ZSI6ImQ2ZjkzZDE0LWM5ZGUtNDIzNC1hMTI1LTE4MzU3NzVjZWIwYSIsInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJkZWZhdWx0LXJvbGVzLXJlY3JhZnQiLCJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJvcGVuaWQgZW1haWwgcHJvZmlsZSIsInNpZCI6ImQ2ZjkzZDE0LWM5ZGUtNDIzNC1hMTI1LTE4MzU3NzVjZWIwYSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJyYW1kb21ha2tAZ21haWwuY29tIiwiZW1haWwiOiJyYW1kb21ha2tAZ21haWwuY29tIn0.EY-_uAFMliGwvUij6DchuKuL82nWhmS6ZNE2WHrE6Z29b57IyM9W9gIPA-dxu-2qkgTCpVeeFNWGuCqNkelU9UaIoEbCRT3uOU2PTW7cT3JjkAomUxZMFM53m21F49lpSguriWW_OzRn_gyil3GWXXe3Byr0MG2K-ZS4-8wCz3WOwMYIh0Ox5BlPUlZQ4G3Aa2K9zyFkV0GUYwND5pNOyshlZtqrAhFohfIHs52GWKLQxTQJKpT485KsaB0EcPtUKP2ucxk157I91FIbNaS7YYBB8XiCi87PcLA6p1VIlFFneD0g0Zp2YWf6HJ7uLG09asSBw9mdrNRWrXuxIuEGZQ"
prompt = 'logo, люди, simple style'
complexity = 1
colors = ['2E112D', '820333']
width = 1024
height = 1024
seed = random.randint(11111,99999)

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
