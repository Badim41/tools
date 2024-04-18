import requests

url = "https://www.bing.com/images/create"

data = {
    "q": "cats HD",
    "rt": "3", "FORM": "GENCRE"}

headers = {
    "cookie": "_IDET=MIExp=0; _C_Auth=; ipv6=hit=1713440618152; MUID=3D8CD6CBA2D26BB92017C2DAA3496AC5; MUIDB=3D8CD6CBA2D26BB92017C2DAA3496AC5; _EDGE_V=1; SRCHD=AF=NOFORM; SRCHUID=V=2&GUID=61FAB222970449328B7FABABF59C9F06&dmnchg=1; ANON=A=9409242150DC63646EBD4C90FFFFFFFF&E=1da0&W=1; NAP=V=1.9&E=1d46&C=9HQg9vOFxfR2GZxYqRuq1YNXjZhGMG_Q6INyxNB6dv3Ax34KgV0bSg&W=1; PPLState=1; KievRPSSecAuth=FACCBBRaTOJILtFsMkpLVWSG6AN6C/svRwNmAAAEgAAACEvj9VbGVjTTQASt4bi/XqCj9lQrtexsGGp6tzj0QME0wYfYVrV8SrOGFSdr6cF6RnWh2LEmurQchC91jFwJaqNcrjNmJKz6HsIO+VuB0v7iNljMD6/IAhOB4Drxg6PLxHab4prAyt7FkxDCoMzO25XnLAHpXylF4TGhZH+cTTB2vcxc9GH4BM12eFmWFyDPSqEEPc/IhR5qF7JSDsBdJ0Q8i7c0t/347L0m8mEF9GC0offxTkJHniMDPb5kvtk78t40Y1B5uUokXvea5YChBpqgYrvp+YyTEru+VQJykWQvu+oGarBkIiu1BrEt7yLQjcoYjfIWKwsuk2gMY06uUczNlfDmAh0pX+CTQo83AGtQ5Uh22x9d+b/sEfU9WcfUhMp0rLS77BvwUXfqiGa+shZoV6mhulGu6Dt3e9lae3lSfEpDJL39/NQzRrMMN/2MiLXSeVZZUbEhSHz+gTIG9eDJt96pYsyvdBHnG4Fbf9uCEQn0O8hE0AMTYxafRitXUlQ7+FNF3XtBJkOA8Ugfh4ZVlimaxeTojZ5HigQtTOmMryL2z+ms5J+kxw+zUXoRMLDVrAnqdJDsb9Z/uF6ee2FGKvxxCo1kqRxEWI8J99q+mnRHcgyQnc3dvfs1ivimmojMSZFvpAgHPqoLp1zM1mJwNb76XTElo12j8AYBW/vynp+4WtaupDfQmGMSYTXaOiaRBk7r3NvqWwFICKPhCA3ZV1/2dxOfFpdPpTTHC1cKGI187ynkJcaMaF7aPL7FG5sf5/tOtKGfcbqJctrO8XUDKlIIjYG44dp34k3yKFiXarVX3ean6rUaPxNtYNOt1T3IrvfD/PTGJtyfRec3S8E4Ll/c3+dynp0fKhb74WJvp4sm89fPekx8Tk/QL2TO7f23HxWhUXhdjX2UDaOx0Q4CLYhjKUkSJtI2HF31S1J7lEWIgfdeP8FDHGZYGdjJavwG4tBXEvnR9LM1AD1NNKy93U2n9FHDuP+ngGGtXLW5eTSf/kEekm4+RAliB7MhFTeHpczhn71c65bX02Jg+kGQNE261QUXzqsTawMInYR84B7p9vtIy6L/2D8czchKpn6iGzfM9egNwRIKExdQStSjgemxxneGgDClQin/jtteX8nogKfGQNprnHNkmI4K4/w3j79zf+5XjktrHs7xMmEde6Vhz0IDVx6bJoUAg8X83M3iR5pon/N8O7ZOVzjoGr/794uVJokIyEWFUeW2At0jvdbHPiz0P6wGRSNpZtRTHmk9KANufBnW7VlH5N+2SJj/cLSDEWS1P8bSzqNHkuqAjD9NA/CBl9bQLWivXw4onjRA5Zfu9lv6KSQhmcYieb71uuGlxiju3TuOD8Gfwd+vYerV2gnu5p4bjYbFEg0MP4wCnVbBxXBNF3xuty4P/y6dyhFueRqGf2T4GS2jdKYfi4l3OL3SjJKhrBjOicFmDOqh8g0DvO7QgxQA+fkXims+ZpkOIC29buAzUuw1aGY=; _U=1yUhJ-z9CxWPu2d24C_-HzULJIXAWQaEiESf04Z0x7b9w2ZjUiSmsza6xEEV23lV8gx3rsjrs8akII8U-KnmPhY1VhiX1zpMzqrJWbLKrfFGcuekqsaaKUqPcfFp2YNDM3ik8Aex2Njh4Ch9vVIRlZWEQgfZ5LZiG0uGpvjKiwxLbOLWsoL2WIUdCUhhvC1754cqXCw1Uh0XAAdfQ_-RabJwLhxBjRhxq_IUobR3xHf8XB1dv0vC08BP8K8cAzL7Z; WLID=0CjWbjLJo9h1v7Blnq4JcX14B5oup+G1FU4HsOTsS0HOnANVFx/fRWwwGW4b7As0+sxLsHzMNCzOhaO1nfbbvNs5rWFaDgor26sWzU1bIJI=; BCP=AD=1&AL=1&SM=1; MMCASM=ID=73E3FB88C48C4A9E8611CBFB37FB9E4B; _UR=cdxcls=0&QS=0&TQS=0; _HPVN=CS=eyJQbiI6eyJDbiI6MSwiU3QiOjAsIlFzIjowLCJQcm9kIjoiUCJ9LCJTYyI6eyJDbiI6MSwiU3QiOjAsIlFzIjowLCJQcm9kIjoiSCJ9LCJReiI6eyJDbiI6MSwiU3QiOjAsIlFzIjowLCJQcm9kIjoiVCJ9LCJBcCI6dHJ1ZSwiTXV0ZSI6dHJ1ZSwiTGFkIjoiMjAyNC0wNC0xNVQwMDowMDowMFoiLCJJb3RkIjowLCJHd2IiOjAsIlRucyI6MCwiRGZ0IjpudWxsLCJNdnMiOjAsIkZsdCI6MCwiSW1wIjo4LCJUb2JuIjowfQ==; MicrosoftApplicationsTelemetryDeviceId=6183e63d-a9ce-443d-9abd-c81593e10fc5; SRCHHPGUSR=SRCHLANG=ru&PV=10.0.0&BRW=XW&BRH=M&CW=1685&CH=868&SCW=1685&SCH=868&DPR=1.0&UTC=720&DM=1&CIBV=1.1509.1&HV=1713159436&WTS=63841759147&PRVCW=1685&PRVCH=868; WLS=C=28b35adc1d1e31b8&N=%d0%92%d0%b0%d0%b4%d0%b8%d0%bc; _Rwho=u=d&ts=2024-04-18; _SS=SID=12404933E68768AA2A925D56E71A69C5&R=330&RB=330&GB=0&RG=0&RP=330; _clck=1alj3op%7C2%7Cfl1%7C0%7C1485; _clck=1alj3op%7C2%7Cfl1%7C0%7C1485; _EDGE_S=SID=12404933E68768AA2A925D56E71A69C5&mkt=fr-fr&ui=ru-ru; SRCHUSR=DOB=20240125&T=1713436715000&TPC=1713416922000&POEX=W; GI_FRE_COOKIE=gi_prompt=1; _clsk=dog84t%7C1713437026295%7C21%7C0%7Cf.clarity.ms%2Fcollect; _clsk=dog84t%7C1713437026295%7C21%7C0%7Cf.clarity.ms%2Fcollect; _RwBf=r=0&ilt=1&ihpd=0&ispd=1&rc=330&rb=330&gb=0&rg=0&pc=330&mtu=0&rbb=0&g=0&cid=&clo=0&v=20&l=2024-04-18T07:00:00.0000000Z&lft=0001-01-01T00:00:00.0000000&aof=0&ard=0001-01-01T00:00:00.0000000&rwdbt=0001-01-01T16:00:00.0000000-08:00&o=0&p=MSAAUTOENROLL&c=MR000T&t=4129&s=2024-04-05T12:38:13.9464854+00:00&ts=2024-04-18T10:50:36.3343313+00:00&rwred=0&wls=2&wlb=0&wle=1&ccp=2&lka=0&lkt=0&aad=0&TH=&mta=0&rwflt=2024-04-09T22:23:29.8621915-07:00&e=_VQg4bKB9enjjy6ESFYe-lVKWN4Sog3E2GBigovUitvkdZGo7OcWzEEM5QhM9NITqN2L7CHQAh_dxo9hZ4Tm9w&A=&cpt=0",
    "authority": "www.bing.com",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9",
    "cache-control": "max-age=0",
    "content-type": "application/x-www-form-urlencoded",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36"
}

proxy = "socks5://localhost:5051"

proxies = {
    'http': proxy,
    'https': proxy
}

response = requests.request("POST", url, data="", headers=headers, params=data, proxies=proxies)

print(response.text)
