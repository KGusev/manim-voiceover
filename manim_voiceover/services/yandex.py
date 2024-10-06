from dotenv import find_dotenv, load_dotenv
from pathlib import Path
from manim import logger
from manim_voiceover.helper import prompt_ask_missing_extras, remove_bookmarks
from manim_voiceover.services.base import SpeechService

try:
    from speechkit import model_repository, configure_credentials, creds
except ImportError:
    logger.error(
        'Missing packages. Run `pip install "manim-voiceover[yandex-speechkit]"` to use YandexSpeechKitService.'
    )


load_dotenv(find_dotenv(usecwd=True))


def create_dotenv_yandex_speechkit():
    logger.info(
        "Check out https://yandex.cloud/en/docs/speechkit/sdk/python/auth to learn how to create an account and get your api key."
    )
    if not create_dotenv_file(["YANDEX_SPEECHKIT_API_KEY"]):
        raise Exception(
            "The environment variable YANDEX_SPEECHKIT_API_KEY is not set. Please set them or create a .env file with the variables."
        )
    logger.info("The .env file has been created. Please run Manim again.")
    sys.exit()


def init_yandex_speechkit():
    try:
        api_key = os.environ["YANDEX_SPEECHKIT_API_KEY"]
    except KeyError:
        logger.error(
            "Could not find the environment variable YANDEX_SPEECHKIT_API_KEY. Yandex SpeechKit API needs account credentials to connect."
        )
        create_dotenv_yandex_speechkit()

    configure_credentials(yandex_credentials=creds.YandexCredentials(api_key=api_key))


class YandexSpeechKitService(SpeechService):
    """SpeechService class for Yandex SpeechKit API.
    This is a wrapper for the yandex-speechkit library.
    See the `Yandex SpeechKit documentation <https://yandex.cloud/en/docs/speechkit>`__
    for more information."""

    def __init__(self, lang="en-US", voice="john", **kwargs):
        """
        Args:
            lang (str, optional): Language to use for the speech.
                See `Yandex SpeechKit docs <https://yandex.cloud/en/docs/speechkit/tts/voices>`__
                for all the available languages. Defaults to "en-US".
            voice (str, optional): .
                See `Yandex SpeechKit docs <https://yandex.cloud/en/docs/speechkit/tts/voices>`__
                for all the available voices. Default to "john".
        """
        prompt_ask_missing_extras("yandex-speechkit", "yandex-speechkit", "YandexSpeechKitService")
        SpeechService.__init__(self, **kwargs)

        init_yandex_speechkit()
        self.model = model_repository.synthesis_model()
        self.model.lang = lang
        self.model.voice = voice

    def generate_from_text(
        self, text: str, cache_dir: str = None, path: str = None, **kwargs
    ) -> dict:
        """"""
        if cache_dir is None:
            cache_dir = self.cache_dir

        input_text = remove_bookmarks(text)
        input_data = {
            "input_text": input_text,
            "service": "yandex-speechkit",
            "language": self.model.lang,
            "voice": self.model.voice,
        }

        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".mp3"
        else:
            audio_path = path

        try:
            result = self.model.synthesize(text, raw_format=False)
        except Exception as e:
            logger.error(e)
            raise Exception(
                "Failed to  synthesize. "
                "See the documentation for more information."
            )

        try:
            result.export(str(Path(cache_dir) / audio_path), 'mp3')
        except Exception as e:
            logger.error(e)
            raise Exception(
                "Yandex SpeechKit gave an error. You are either not connected to the internet, or there is a problem with the Yandex SpeechKit."
            )

        json_dict = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }

        return json_dict
