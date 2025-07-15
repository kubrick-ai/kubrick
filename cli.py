import os
from dotenv import load_dotenv
from enum import Enum

from app.services.embed_service import EmbedService
from app.services.vector_db_service import VectorDBService
from app.config import Config
from app.utils import downloader

from prompt_toolkit import PromptSession, print_formatted_text, HTML
from prompt_toolkit.completion import FuzzyWordCompleter
from prompt_toolkit.shortcuts import clear


def print_hint():
    print_formatted_text(
        HTML(
            "Type <b><orange>/exit</orange></b> to exit or <b><orange>/help</orange></b> for help."
        )
    )


def print_help():
    help_doc = HTML(
        """
Commands:
<b><orange>/help</orange></b>           : Display this document
<b><orange>/exit</orange></b>           : Exit the session
<b><orange>/clear</orange></b>          : Clear the screen
<b><orange>/db_setup</orange></b>       : Setup database table with pgvector
<b><orange>/add_file</orange></b>       : Add a video file by filepath
<b><orange>/add_youtube</orange></b>    : Add a video file by youtube link
<b><orange>/search_text</orange></b>    : Search with a text query
"""
    )
    print_formatted_text(help_doc)


class CommandType(Enum):
    EXIT = "exit"
    HELP = "help"
    CLEAR = "clear"
    DB_SETUP = "db_setup"
    ADD_FILE = "add_file"
    ADD_YOUTUBE = "add_youtube"
    SEARCH_TEXT = "search_text"
    UNKNOWN = "unknown"


def parse_command(user_input: str) -> CommandType | None:
    if not user_input.startswith("/"):
        return None

    cmd = user_input.split()[0].lower()[1:]
    command_map = {
        "help": CommandType.HELP,
        "exit": CommandType.EXIT,
        "clear": CommandType.CLEAR,
        "db_setup": CommandType.DB_SETUP,
        "add_file": CommandType.ADD_FILE,
        "add_youtube": CommandType.ADD_YOUTUBE,
        "search_text": CommandType.SEARCH_TEXT,
        "unknown": CommandType.UNKNOWN,
    }

    return command_map.get(cmd, None)


def handle_command(
    result: CommandType,
    session: PromptSession,
    embed_service: EmbedService,
    vector_db_service: VectorDBService,
) -> None:
    match result:
        case CommandType.HELP:
            print_help()
        case CommandType.EXIT:
            print("Exiting...")
        case CommandType.CLEAR:
            clear()
            print_hint()
        case CommandType.DB_SETUP:
            vector_db_service.setup()
        case CommandType.ADD_FILE:
            user_input = session.prompt("Enter filepath: ")
            # TODO: Add validation
            add_file(user_input, embed_service, vector_db_service)
            print(f"{user_input} has been added to database")
        case CommandType.ADD_YOUTUBE:
            user_input = session.prompt("Enter youtube link: ")
            # TODO: Add validation
            path = downloader.download_video(user_input)
            add_file(path, embed_service, vector_db_service)
            print(f"{path} has been added to database")
        case CommandType.SEARCH_TEXT:
            user_input = session.prompt("Search for: ")
            results = search_text(user_input, embed_service, vector_db_service)
            print_results(results)
        case _:
            print_hint()


def should_exit(result: CommandType) -> bool:
    return result == CommandType.EXIT


def run(DEBUG=False):
    # Initialize services
    config = Config()
    embed_service = EmbedService(config)
    vector_db_service = VectorDBService(config)

    completer = FuzzyWordCompleter(
        [f"/{cmd.value}" for cmd in CommandType if cmd != CommandType.UNKNOWN]
    )
    session = PromptSession(
        completer=completer, vi_mode=True, enable_open_in_editor=True
    )

    clear()
    print("welcome to kubrick!")
    print("-" * 50)
    print_hint()

    while True:
        user_input = session.prompt("> ")
        command = parse_command(user_input)
        if command:
            handle_command(command, session, embed_service, vector_db_service)
            if command == CommandType.EXIT:
                break
            continue


def add_file(
    filepath,
    embed_service: EmbedService,
    vector_db_service: VectorDBService,
    DEBUG=False,
):
    video_embedding = embed_service.extract_video_features(filepath)
    if DEBUG:
        embed_service.print_segments(video_embedding)

    for segment in video_embedding:
        vector_db_service.store(
            filepath,
            embedding_type=segment.embedding_option,
            start_offset=segment.start_offset_sec,
            end_offset=segment.end_offset_sec,
            embedding=segment.embeddings_float,
        )


def search_text(
    query, embed_service: EmbedService, vector_db_service: VectorDBService, DEBUG=False
):
    text_embedding = embed_service.extract_text_embedding(query)
    if DEBUG and text_embedding is not None:
        print("text_embedding:", text_embedding)

    results = vector_db_service.find_similar(text_embedding)

    return results


def print_results(results):
    print("results:")

    for result in results:
        source = result["source"].split("/")[-1]
        similarity = result["similarity"]
        embedding_type = result["type"]
        start_offset = result["start_offset"]
        end_offset = result["end_offset"]
        print(
            f"Source: {source.ljust(27, ' ')} | Start: {start_offset}s | End: {end_offset}s | Type: {embedding_type.ljust(11, ' ')} | Similarity: {similarity:.5}"
        )


if __name__ == "__main__":
    load_dotenv()

    DEBUG = os.getenv("DEBUG", "").lower() == "true"

    run(DEBUG)
