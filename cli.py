import os
from dotenv import load_dotenv
from enum import Enum

from embed import extract_text_features, extract_video_features, print_segments
import downloader
import pg_db
from mongo import MongoVectorStore
from vector_db_pinecone import PineconeVectorStore

from prompt_toolkit import PromptSession, print_formatted_text, HTML
from prompt_toolkit.completion import FuzzyWordCompleter
from prompt_toolkit.shortcuts import clear

import certifi
os.environ["SSL_CERT_FILE"] = certifi.where()

mongo_db = MongoVectorStore()
pinecone = PineconeVectorStore()

def print_hint():
    print_formatted_text(
        HTML(
            "Type <b><orange>/exit</orange></b> to exit or <b><orange>/help</orange></b> for help."
        )
    )


def print_help():
    help_doc = HTML("""
Commands:
<b><orange>/help</orange></b>           : Display this document
<b><orange>/exit</orange></b>           : Exit the session
<b><orange>/clear</orange></b>          : Clear the screen
<b><orange>/db_setup</orange></b>       : Setup database table with pgvector
<b><orange>/add_file</orange></b>       : Add a video file by filepath
<b><orange>/add_youtube</orange></b>    : Add a video file by youtube link
<b><orange>/search_text</orange></b>    : Search with a text query
""")
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


def handle_command(result: CommandType, session: PromptSession) -> None:
    match result:
        case CommandType.HELP:
            print_help()
        case CommandType.EXIT:
            print("Exiting...")
        case CommandType.CLEAR:
            clear()
            print_hint()
        case CommandType.DB_SETUP:
            pg_db.setup()
        case CommandType.ADD_FILE:
            user_input = session.prompt("Enter filepath: ")
            # TODO: Add validation
            add_file(user_input)
            print(f"{user_input} has been added to database")
        case CommandType.ADD_YOUTUBE:
            user_input = session.prompt("Enter youtube link: ")
            # TODO: Add validation
            path = downloader.download_video(user_input)
            add_file(path)
            print(f"{path} has been added to database")
        case CommandType.SEARCH_TEXT:
            user_input = session.prompt("Search for: ")
            results = search_text(user_input)
            print_results(results)
        case _:
            print_hint()


def should_exit(result: CommandType) -> bool:
    return result == CommandType.EXIT


def run(DEBUG=False):
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
            handle_command(command, session)
            if command == CommandType.EXIT:
                break
            continue


def add_file(filepath, DEBUG=False):

    video_embedding = extract_video_features(filepath, DEBUG)
    if DEBUG:
        print_segments(video_embedding)

    # Store embeddings in mongo atlas and pinecone
    mongo_db.store(filepath, video_embedding)
    pinecone.store(filepath, video_embedding)

    for segment in video_embedding:
        pg_db.store(
            filepath,
            embedding_type=segment.embedding_option,
            start_offset=segment.start_offset_sec,
            end_offset=segment.end_offset_sec,
            embedding=segment.embeddings_float,
        )


def search_text(query, DEBUG=False):
    text_embedding = extract_text_features(query)
    if DEBUG and text_embedding is not None:
        print("text_embedding:", text_embedding)

    pg_results = pg_db.find_similar(text_embedding)
    mongo_results = mongo_db.search(text_embedding)
    pinecone_results = pinecone.search(text_embedding)
    return [pg_results, mongo_results, pinecone_results]


def print_results(results):
    pg_results, mongo_results, pinecone_results = results

    def print_formatted(title, results, source_key="source", similarity_key="similarity"):
        print(f"\n{title}")
        print("-" * 115)
        print(f"{'Source':<80} | {'Start':<7} | {'End':<7} | {'Type':<11} | {'Similarity':<10}")
        print("-" * 115)

        for result in results:
            source = result.get(source_key, "unknown")
            if isinstance(source, str):
                source = source.split("/")[-1].replace("./downloads/", "")

            start = result.get("start_offset", "?")
            end = result.get("end_offset", "?")
            embedding_type = result.get("type", "unknown")
            similarity = result.get(similarity_key, 0)

            print(f"{source:<80} | {str(start):<7} | {str(end):<7} | {embedding_type:<11} | {similarity:<10.5f}")
        print()

    print_formatted("Postgres Results:", pg_results, source_key="source", similarity_key="similarity")
    print_formatted("MongoDB Results:", mongo_results, source_key="filepath", similarity_key="score")
    print_formatted("Pinecone Results:", pinecone_results, source_key="filepath", similarity_key="score")


if __name__ == "__main__":
    load_dotenv()

    DEBUG = os.getenv("DEBUG", "").lower() == "true"

    run(DEBUG)
