import sys
from pynput import keyboard
import time
import pyaudio
import wave
from playsound import playsound
from pydub import AudioSegment

state = "wait"

# FUNCTION_KEY = keyboard.Key.space
FUNCTION_KEY = keyboard.Key.page_down

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
    global g_stream, g_frames, g_record_idx, g_audio
    if g_stream is None:
        # record() was never called.
        return False

    g_stream.stop_stream()
    g_stream.close()
    # g_audio.terminate()
    fn = "{}_{}.wav".format(WAVE_OUTPUT_PREFIX, g_record_idx)
    fn_mp3 = "{}_{}.mp3".format(WAVE_OUTPUT_PREFIX, g_record_idx)
    wf = wave.open(fn, "wb")
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(g_audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b"".join(g_frames))
    wf.close()
    print("saved to {}".format(fn))

    AudioSegment.from_wav(fn).export(fn_mp3, format="mp3")
    playsound(fn_mp3)

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


def process():
    # TODO: implement webrtc based voice chat
    print("process")


if __name__ == "__main__":

    FUNCTION_KEY = keyboard.Key.space

    listener = keyboard.Listener(
        on_press=on_press, on_release=on_release, suppress=True
    )
    listener.start()
    print("ready")
    while not is_state("quit"):
        if is_state("record"):
            record(1)
        elif is_state("process"):
            if stop_record():
                process()
                set_state("wait")
            else:
                set_state("wait")
        else:
            time.sleep(0.01)