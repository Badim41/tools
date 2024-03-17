from discord_tools.yt_downloader import get_youtube_video_id, yt_download

url = "https://youtube.com/..."
song_id = get_youtube_video_id(url)

if song_id is None:
    raise Exception("Нет song id")

song_link = song_id.split('&')[0]
audio_path = yt_download(song_link, max_duration=3600) # время в секундах
