from dotenv import load_dotenv
import os
import logging
from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents
import json 

load_dotenv()

api_key = os.getenv("DG_API_KEY")
is_finals = []  # Stores final transcriptions
last_final_transcript = None  # To track the latest final transcript

deepgram = DeepgramClient(api_key)
dg_connection = deepgram.listen.websocket.v("1")

def on_open(ws, *args): 
    print("Connection Open")


def on_message(ws, result):
    global is_finals, last_final_transcript
    try:
        sentence = result.channel.alternatives[0].transcript
        is_final = result.is_final

        if sentence:
            if is_final:
                is_finals.append(sentence)
                last_final_transcript = " ".join(is_finals)
                print(f"Final Transcript: {last_final_transcript}")
                is_finals = []
            else:
                print(f"Intermediate Transcript: {sentence}")
        else:
            print("No transcript available.")

    except Exception as e:
        print("Error:", e)


def on_close(ws, *args):  
    print("Connection Closed")

def on_error(ws, error):  
    print(f"Error: {error}")




def start_deepgram_stream():
    options = LiveOptions(
        model="nova-2",
        language="multi",
        smart_format=True,
        encoding="mulaw",
        channels=1,
        sample_rate=8000,
        interim_results=False,
        utterance_end_ms="1200",
        vad_events=True,
        endpointing=300,
    )
    addons = {"no_delay": "true"}

    dg_connection.on(LiveTranscriptionEvents.Open, on_open)
    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    dg_connection.on(LiveTranscriptionEvents.Close, on_close)
    dg_connection.on(LiveTranscriptionEvents.Error, on_error)

    if not dg_connection.start(options, addons=addons):
        print("Failed to connect to Deepgram")
        return None
    return dg_connection

def send_audio_to_deepgram(audio_chunk):
    dg_connection.send(audio_chunk)

def finish_deepgram_stream():
    dg_connection.finish()

def get_last_final_transcript():
    global last_final_transcript
    x = last_final_transcript
    last_final_transcript = None
    return x


####################################################################################
####################################################################################
####################################################################################
####################################################################################
####################################################################################
####################################################################################
####################################################################################


# import os
# import asyncio
# from dotenv import load_dotenv
# from signal import SIGINT, SIGTERM
# from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents

# load_dotenv()

# api_key = os.getenv("DG_API_KEY")
# is_finals = []
# last_final_transcript = None

# # Set up the Deepgram client
# deepgram = DeepgramClient("d8345751e53174c1bd25f15ea57feaa6a7678e3e")
# dg_connection = deepgram.listen.asyncwebsocket.v("1")





# # Async event handlers
# async def on_open(ws, *args): 
#     print("Connection Open")

# async def on_message(ws, result):
#     global is_finals, last_final_transcript
#     try:
#         sentence = result.channel.alternatives[0].transcript
#         is_final = result.is_final

#         if sentence:
#             if is_final:
#                 is_finals.append(sentence)
#                 last_final_transcript = " ".join(is_finals)
#                 print(f"Final Transcript: {last_final_transcript}")
#                 is_finals = []
#             else:
#                 print(f"Intermediate Transcript: {sentence}")
#         else:
#             print("No transcript available.")
#     except Exception as e:
#         print("Error:", e)

# async def on_close(ws, *args):  
#     print("Connection Closed")

# async def on_error(ws, error):  
#     print(f"Error: {error}")

# # Start the Deepgram connection asynchronously
# async def start_deepgram_stream():
#     options = LiveOptions(
#         model="nova-2",
#         language="multi",
#         smart_format=True,
#         encoding="mulaw",
#         channels=1,
#         sample_rate=8000,
#         interim_results=True,
#         utterance_end_ms="1000",
#         vad_events=True,
#         endpointing=300,
#     )
#     addons = {"no_delay": "true"}

#     dg_connection.on(LiveTranscriptionEvents.Open, on_open)
#     dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
#     dg_connection.on(LiveTranscriptionEvents.Close, on_close)
#     dg_connection.on(LiveTranscriptionEvents.Error, on_error)

#     # Start the connection and return the object if successful
#     if not await dg_connection.start(options, addons=addons):
#         print("Failed to connect to Deepgram")
#         return None
#     return dg_connection

# async def send_audio_to_deepgram(audio_chunk):
#     await dg_connection.send(audio_chunk)

# async def finish_deepgram_stream():
#     await dg_connection.finish()

# Shutdown handler for graceful exit
# async def shutdown(signal, loop, dg_connection):
#     print(f"Received exit signal {signal.name}...")
#     await finish_deepgram_stream()
#     tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
#     [task.cancel() for task in tasks]
#     print(f"Cancelling {len(tasks)} outstanding tasks")
#     await asyncio.gather(*tasks, return_exceptions=True)
#     loop.stop()
#     print("Shutdown complete.")

# Main function to start async loop and handle audio stream
# async def main():
#     try:
#         loop = asyncio.get_event_loop()

#         for sig in (SIGTERM, SIGINT):
#             loop.add_signal_handler(
#                 sig,
#                 lambda sig=sig: asyncio.create_task(shutdown(sig, loop, dg_connection))
#             )

#         # Start the WebSocket connection
#         if await start_deepgram_stream() is None:
#             print("Could not establish a connection to Deepgram")
#             return

#         print("\n\nStart talking! Press Ctrl+C to stop...\n")

#         # Wait indefinitely until shutdown
#         try:
#             while True:
#                 await asyncio.sleep(1)
#         except asyncio.CancelledError:
#             pass

#     except Exception as e:
#         print(f"Could not open socket: {e}")

# # Run the main async function
# asyncio.run(main())


####################################################################################
####################################################################################
####################################################################################
############################     Reference Code            #########################
####################################################################################
####################################################################################
####################################################################################
####################################################################################



# from signal import SIGINT, SIGTERM
# import asyncio
# from dotenv import load_dotenv
# import logging
# from deepgram.utils import verboselogs
# from time import sleep

# from deepgram import (
#     DeepgramClient,
#     DeepgramClientOptions,
#     LiveTranscriptionEvents,
#     LiveOptions,
#     Microphone,
# )

# load_dotenv()

# # We will collect the is_final=true messages here so we can use them when the person finishes speaking
# is_finals = []


# async def main():
#     try:
#         loop = asyncio.get_event_loop()

#         for signal in (SIGTERM, SIGINT):
#             loop.add_signal_handler(
#                 signal,
#                 lambda: asyncio.create_task(
#                     shutdown(signal, loop, dg_connection, microphone)
#                 ),
#             )

#         # example of setting up a client config. logging values: WARNING, VERBOSE, DEBUG, SPAM
#         # api_key = os.getenv("DG_API_KEY")
#         # is_finals = []  # Stores final transcriptions
#         # last_final_transcript = None  # To track the latest final transcript

#         # deepgram = DeepgramClient("d8345751e53174c1bd25f15ea57feaa6a7678e3e")
#         # # dg_connection = deepgram.listen.websocket.v("1")
#         # config: DeepgramClientOptions = DeepgramClientOptions(
#         #     options={"keepalive": "true"}
#         # )
#         # deepgram: DeepgramClient = DeepgramClient("", config)
#         # otherwise, use default config
#         deepgram: DeepgramClient = DeepgramClient("d8345751e53174c1bd25f15ea57feaa6a7678e3e")

#         dg_connection = deepgram.listen.asyncwebsocket.v("1")

#         async def on_open(self, open, **kwargs):
#             print("Connection Open")

#         async def on_message(self, result, **kwargs):
#             global is_finals
#             sentence = result.channel.alternatives[0].transcript
#             if len(sentence) == 0:
#                 return
#             if result.is_final:
#                 # We need to collect these and concatenate them together when we get a speech_final=true
#                 # See docs: https://developers.deepgram.com/docs/understand-endpointing-interim-results
#                 is_finals.append(sentence)

#                 # Speech Final means we have detected sufficent silence to consider this end of speech
#                 # Speech final is the lowest latency result as it triggers as soon an the endpointing value has triggered
#                 if result.speech_final:
#                     utterance = " ".join(is_finals)
#                     print(f"Speech Final: {utterance}")
#                     is_finals = []
#                 else:
#                     # These are useful if you need real time captioning and update what the Interim Results produced
#                     print(f"Is Final: {sentence}")
#             else:
#                 # These are useful if you need real time captioning of what is being spoken
#                 print(f"Interim Results: {sentence}")

#         async def on_metadata(self, metadata, **kwargs):
#             print(f"Metadata: {metadata}")

#         async def on_speech_started(self, speech_started, **kwargs):
#             print("Speech Started")

#         async def on_utterance_end(self, utterance_end, **kwargs):
#             print("Utterance End")
#             global is_finals
#             if len(is_finals) > 0:
#                 utterance = " ".join(is_finals)
#                 print(f"Utterance End: {utterance}")
#                 is_finals = []

#         async def on_close(self, close, **kwargs):
#             print("Connection Closed")

#         async def on_error(self, error, **kwargs):
#             print(f"Handled Error: {error}")

#         async def on_unhandled(self, unhandled, **kwargs):
#             print(f"Unhandled Websocket Message: {unhandled}")

#         dg_connection.on(LiveTranscriptionEvents.Open, on_open)
#         dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
#         dg_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
#         dg_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
#         dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
#         dg_connection.on(LiveTranscriptionEvents.Close, on_close)
#         dg_connection.on(LiveTranscriptionEvents.Error, on_error)
#         dg_connection.on(LiveTranscriptionEvents.Unhandled, on_unhandled)

#         # connect to websocket
#         options: LiveOptions = LiveOptions(
#             model="nova-2",
#             language="en-US",
#             # Apply smart formatting to the output
#             smart_format=True,
#             # Raw audio format deatils
#             encoding="linear16",
#             channels=1,
#             sample_rate=16000,
#             # To get UtteranceEnd, the following must be set:
#             interim_results=True,
#             utterance_end_ms="1000",
#             vad_events=True,
#             # Time in milliseconds of silence to wait for before finalizing speech
#             endpointing=300,
#         )

#         addons = {
#             # Prevent waiting for additional numbers
#             "no_delay": "true"
#         }

#         print("\n\nStart talking! Press Ctrl+C to stop...\n")
#         if await dg_connection.start(options, addons=addons) is False:
#             print("Failed to connect to Deepgram")
#             return

#         # Open a microphone stream on the default input device
#         microphone = Microphone(dg_connection.send)

#         # start microphone
#         microphone.start()

#         # wait until cancelled
#         try:
#             while True:
#                 await asyncio.sleep(1)
#         except asyncio.CancelledError:
#             # This block will be executed when the shutdown coroutine cancels all tasks
#             pass
#         finally:
#             microphone.finish()
#             await dg_connection.finish()

#         print("Finished")

#     except Exception as e:
#         print(f"Could not open socket: {e}")
#         return


# async def shutdown(signal, loop, dg_connection, microphone):
#     print(f"Received exit signal {signal.name}...")
#     microphone.finish()
#     await dg_connection.finish()
#     tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
#     [task.cancel() for task in tasks]
#     print(f"Cancelling {len(tasks)} outstanding tasks")
#     await asyncio.gather(*tasks, return_exceptions=True)
#     loop.stop()
#     print("Shutdown complete.")


# asyncio.run(main())