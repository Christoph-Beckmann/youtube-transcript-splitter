import sys
import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound
import pyperclip

MAX_TOKENS_PER_PART = 1400

class InvalidModeError(Exception):
    pass

def get_video_ID(entry: str) -> str:
    """
    Extracts and returns the YouTube video ID from the given input string (either URL or video ID).
    Returns None if the input is invalid.
    """
    youtube_id_pattern = r'(?:v=|\/)([0-9A-Za-z_-]{10}[048AEIMQUYcgkosw])'
    match = re.search(youtube_id_pattern, entry)
    return match.group(1) if match else None

def get_transcript(video_id: str) -> str:
    """
    Fetches and returns the transcript of a YouTube video with the given video ID.
    Returns an empty string if the transcript is not found.
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry["text"] for entry in transcript])
    except NoTranscriptFound:
        return ""
    
def create_chunks(text: str, max_tokens_per_part: int, mode: str):
    """
    Splits the given text into chunks based on the specified mode and the maximum tokens per part.
    Returns a list of chunks.
    """
    
    if mode == "auto":
        token_count = len(text.split())
        if token_count <= max_tokens_per_part:
            return [text]

    words = text.split()
    chunks = []
    current_part = f"I have a text that I would like to summarize. It consists of {len(chunks)+1} and these parts are separated by '-----'. Here is the 1. part: ---- "
    current_token_count = 0
    for word in words:
        if current_token_count + 1 <= max_tokens_per_part:
            current_part += word + " "
            current_token_count += 1
        else:
            current_part += "-----\n\Please take note of this paragraph carefully and refrain from responding to it. Kindly wait for the next part. "
            chunks.append(current_part)
            current_part = f"Here is the {len(chunks)+1} part: ---- "
            current_token_count = 0
    if current_part:
        current_part += "-----\n\ntl;dr Create a very verbose summary.\n\nSummary:\n"
        chunks.append(current_part)

    return chunks

def process_args(args) -> tuple:
    """
    Processes the command-line arguments and returns a tuple containing the mode and input string.
    Raises an InvalidModeError if the specified mode is not one of 'separate', 'full', or 'auto'.
    """
    
    if len(args) != 3:
        print("Usage: python3 main.py [separate/full/auto] [Video-Link]")
        sys.exit(1)

    mode = args[1]
    input_str = args[2]

    if mode not in ['separate', 'full', 'auto']:
        raise InvalidModeError("Invalid mode. Please choose either 'separate', 'full', or 'auto'.")

    return mode, input_str

def process_transcript(mode: str, transcript: str) -> list:
    """
    Processes the transcript based on the specified mode. If the mode is 'full', the transcript is copied to the clipboard.
    If the mode is 'separate' or 'auto', the transcript is split into chunks and a list of chunks is returned.
    """
    if mode == "full":
        pyperclip.copy(transcript)
        print("Transcript successfully fetched and copied to clipboard.")
        return None
    else:
        chunks = create_chunks(transcript, MAX_TOKENS_PER_PART, mode)
        total_chunks = len(chunks)
        print(f"There are {total_chunks} chunks to be copied.\n")
        return chunks

def copy_chunks_to_clipboard(chunks: list):
    """
    Copies the chunks of text to the clipboard one at a time, prompting the user to press Enter to copy the next chunk or 'q' to quit.
    """
    
    total_chunks = len(chunks)

    for i, chunk in enumerate(chunks):
        user_input = input(f"Press Enter to copy chunk {i + 1} of {total_chunks} or type 'q' to quit: ")
        if user_input == 'q':
            break
        pyperclip.copy(chunk)
        print(f"Chunk {i + 1} of {total_chunks} copied to clipboard.")

def main():
    """
    The main function that ties all the other functions together. It processes the command-line arguments, fetches the video transcript,
    processes the transcript based on the mode, and copies the transcript or its chunks to the clipboard.
    """
    
    try:
        mode, input_str = process_args(sys.argv)
    except InvalidModeError as e:
        print(e)
        sys.exit(1)

    video_id = get_video_ID(input_str)

    if video_id is None:
        print("Invalid input. Please enter a valid YouTube-Link or YouTube-Video-ID.")
        sys.exit(1)

    transcript = get_transcript(video_id)

    if not transcript:
        print("No transcript found for the given video.")
        sys.exit(1)

    chunks = process_transcript(mode, transcript)

    if chunks:
        copy_chunks_to_clipboard(chunks)

if __name__ == "__main__":
    main()
