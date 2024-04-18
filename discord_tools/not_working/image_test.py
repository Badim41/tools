import requests

url = "https://www.bing.com/images/create"

querystring = {"q":"Mesmerizing rendering of a computer-generated character named Greymon, yellow and blue digimon, fierce appearance, muscular, quadrupedal creature, large head, long tail, three horns, sharp teeth, large mouth, yellow and blue fur, large fin on back, short and powerful arms and legs, sharp claws, 3D render, high detail, Octane render, 8K, HD","rt":"4","FORM":"GENCRE"}

proxy = "socks5://localhost:5051"

proxies = {
    'http': proxy,
    'https': proxy
}

response = requests.request("POST", url, data=payload, headers=headers, params=querystring, proxies=proxies)

print(response.text)