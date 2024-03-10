import yt_dlp
from contextlib import suppress
from urllib.parse import urlparse, parse_qs
from discord_tools.logs import Logs

logger = Logs(warnings=True)


class VideoDurationError(Exception):
    pass


def yt_download(link, max_duration=1800):
    ydl_opts = {
        'format': 'bestaudio',
        'outtmpl': '%(title)s',
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'no_warnings': True,
        'quiet': True,
        'extractaudio': True,
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            video_info = ydl.extract_info(link, download=False)

            if 'duration' in video_info:
                duration_seconds = int(video_info['duration'])
                if duration_seconds > max_duration:
                    raise VideoDurationError("Превышено максимальное время видео")
            else:
                logger.logging("ERROR: Длительность видео не найдена.")

            result = ydl.extract_info(link, download=True)
            download_path = ydl.prepare_filename(result, outtmpl='%(title)s.mp3')

        except Exception as e:
            logger.logging("ERROR IN DOWNLOAD VIDEO:", e)
            raise e

        logger.logging("Downloaded", download_path)
    return download_path


def get_youtube_video_id(url, ignore_playlist=True):
    """
    Examples:
    http://youtu.be/SA2iWivDJiE
    http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
    http://www.youtube.com/embed/SA2iWivDJiE
    http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
    """

    if 'youtu.be' in url:
        video_id = url.split("/")[-1].split("?")[0]
        url = f"https://www.youtube.com/watch?v={video_id}"

    query = urlparse(url)

    if query.hostname in {'www.youtube.com', 'youtube.com', 'music.youtube.com'}:
        if not ignore_playlist:
            # use case: get playlist id not current video in playlist
            with suppress(KeyError):
                return parse_qs(query.query)['list'][0]
        if query.path == '/watch':
            return parse_qs(query.query)['v'][0]
        if query.path[:7] == '/watch/':
            return query.path.split('/')[1]
        if query.path[:7] == '/embed/':
            return query.path.split('/')[2]
        if query.path[:3] == '/v/':
            return query.path.split('/')[2]

    # returns None for invalid YouTube url
    return None
