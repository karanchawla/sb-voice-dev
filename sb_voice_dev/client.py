import asyncio
import queue
from concurrent.futures import thread
from io import BytesIO
from random import setstate

import pyaudio
from playsound import playsound
from pydub import AudioSegment
from pydub.playback import play
from pynput import keyboard

from sb_voice_dev.web_socket_handler import WebSocketHandler

state = "wait"

FUNCTION_KEY = keyboard.Key.space

# audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
WAVE_OUTPUT_PREFIX = "voice"

g_audio = pyaudio.PyAudio()
g_stream = None
g_frames = []
g_record_idx = 0

session_id = "123"
user_id = "456"
current_audio_file_path = ""


def set_state(s):
    global state
    state = s
    print(f"state: {state}")


def is_state(s):
    global state
    return state == s


def start_record():
    global g_audio, g_stream, g_frames, g_record_idx
    assert g_stream is None
    g_stream = g_audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )


def stop_record():
    global g_stream, g_frames, g_record_idx, g_audio, current_audio_file_path
    if g_stream is None:
        # record() was never called.
        return False

    g_stream.stop_stream()
    g_stream.close()
    # g_audio.terminate()
    print(f"Lenght of gframes: {len(g_frames)}")

    audio_segment = AudioSegment(
        data=b"".join(g_frames),
        sample_width=g_audio.get_sample_size(FORMAT),
        frame_rate=RATE,
        channels=CHANNELS,
    )
    fn_mp3 = "{}_{}.mp3".format(WAVE_OUTPUT_PREFIX, g_record_idx)
    audio_segment.export(fn_mp3, format="mp3")
    current_audio_file_path = fn_mp3
    # playsound(fn_mp3)

    g_record_idx += 1
    g_frames = []
    g_stream = None
    return True


def on_press(key):
    global FUNCTION_KEY

    try:
        if key == FUNCTION_KEY:
            if is_state("wait"):
                set_state("record")
        elif key.char == "q":
            set_state("quit")
            return False
    except AttributeError:
        pass
    return True


def on_release(key):
    global FUNCTION_KEY, state

    if key == keyboard.Key.esc:
        # Stop listener
        return False
    elif key == FUNCTION_KEY:
        if is_state("record"):
            set_state("process")
    return True


def record(seconds):
    global g_stream, g_frames
    if g_stream is None:
        start_record()

    for i in range(0, int(RATE / CHUNK * seconds)):
        data = g_stream.read(CHUNK)
        g_frames.append(data)


websocket_url = (
    f"wss://karanchawla-dev--fastapi-websocket-websocket-handler-dev.modal.run/ws?session_id={session_id}&user_id={user_id}"
)

# Object for creating a persistent websocket connection
audio_queue = queue.Queue()


async def handle_incoming_message(message):
    if isinstance(message, str) and message == "END_OF_AUDIO":
        print("Received end of audio signal")
        audio_queue.put(None)  # Signal the end of audio
    elif isinstance(message, bytes):
        audio_queue.put(message)


def audio_player(stop_event):
    # This is not the best implementation, rethink this if I have time
    while not stop_event.is_set():
        audio_stream = BytesIO()
        while not stop_event.is_set():
            chunk = audio_queue.get()
            if chunk is None:
                break
            elif isinstance(chunk, bytes):
                audio_stream.write(chunk)

        audio_stream.seek(0)
        audio_stream.seek(0)
        if audio_stream.getbuffer().nbytes > 0:  # Check if there's anything to play
            audio_segment = AudioSegment.from_file(audio_stream, format="mp3")
            play(audio_segment)
        audio_stream.close()


async def send_audio(file_path):
    if websocket_handler.is_active:
        with open(file_path, "rb") as audio_file:
            data = audio_file.read()
            await websocket_handler.send_audio(data)


# Websocket handling
websocket_handler = WebSocketHandler(websocket_uri=websocket_url, message_handler=handle_incoming_message)


async def process(file_path: str):
    if file_path:
        await send_audio(file_path)


async def main():
    listener = keyboard.Listener(on_press=on_press, on_release=on_release, suppress=True)
    listener.start()
    print("ready")
    # Establish connection when we first launch the client
    await websocket_handler.connect()

    import threading

    stop_event = threading.Event()
    player_thread = threading.Thread(target=audio_player, args=(stop_event,))
    player_thread.start()
    try:
        while not is_state("quit"):
            if is_state("record"):
                record(1)
            elif is_state("process"):
                if stop_record():
                    await process(file_path=current_audio_file_path)
                    set_state("wait")
                else:
                    set_state("wait")
            else:
                await asyncio.sleep(0.1)
    finally:
        await websocket_handler.close()
        listener.stop()
        stop_event.set()
        # Unblock the queue if waiting
        audio_queue.put(None)
        player_thread.join()


if __name__ == "__main__":
    asyncio.run(main())
