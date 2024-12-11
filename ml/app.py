import ast
import audioop
import base64
import json
import os
import sys
import tempfile
import time
import wave
from decimal import Decimal
from io import BytesIO

import django
import numpy as np
import soundfile as sf
from asgiref.sync import sync_to_async
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, WebSocket
from pyngrok import ngrok
from starlette.websockets import WebSocketDisconnect
from twilio.rest import Client

# from utils.dgtranscriber import start_deepgram_stream, send_audio_to_deepgram, finish_deepgram_stream, get_last_final_transcript
from .data_processing.data_processing import put_call_details
from .embed_processing.gather import load_send_embedding_redis, get_embedding_redis
from .utils.ai_costing import cost_in_thread
from .utils.my_bot import (
    get_chat_response,
    processed_filter_campaign_data,
    get_conversation_history,
)
from .utils.my_voice import get_audio_from_deepGram
from .utils.twilio_transcriber import TwilioTranscriber

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from ai_call_agent.tasks2 import monitor_call
from ai_call_agent.query import (
    get_provider_cost_details,
    update_call_log,
    get_user_details,
)

load_dotenv()

PORT = 5000
DEBUG = False
INCOMING_CALL_ROUTE = "/"
OUTGOING_CALL_ROUTE = "/make-calls"
WEBSOCKET_ROUTE = "/realtime"

# Twilio authentication
account_sid = os.environ["TWILIO_ACCOUNT_SID"]
api_key = os.environ["TWILIO_API_KEY_SID"]
api_secret = os.environ["TWILIO_API_SECRET"]
client = Client(api_key, api_secret, account_sid)
TWILIO_NUMBER = os.environ["TWILIO_NUMBER"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
# ngrok authentication
ngrok.set_auth_token(os.getenv("NGROK_AUTHTOKEN"))
app = FastAPI()


async def send_raw_audio(ws, audio_buffer, stream_sid):
    try:
        audio_data = BytesIO(audio_buffer)
        data, original_samplerate = sf.read(audio_data)
        new_samplerate = 8000

        if len(data.shape) > 1:  # If stereo, take one channel
            data = data[:, 0]

        duration = data.shape[0] / original_samplerate
        new_length = int(duration * new_samplerate)
        resampled_data = np.interp(
            np.linspace(0, len(data), new_length), np.arange(len(data)), data
        )

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            temp_filename = temp_wav.name
            sf.write(temp_filename, resampled_data, new_samplerate)

        with wave.open(temp_filename, "rb") as wav_file:
            while True:
                wav_data = wav_file.readframes(320)
                if not wav_data:
                    # print("No more data to read.")

                    await ws.send(
                        {
                            "type": "websocket.send",
                            "text": json.dumps(
                                {
                                    "streamSid": stream_sid,
                                    "event": "mark",
                                    "mark": {"name": "my label"},
                                }
                            ),
                        }
                    )
                    break

                mulaw_data = audioop.lin2ulaw(wav_data, 2)
                base64_audio = base64.b64encode(mulaw_data).decode("utf-8")
                await ws.send(
                    {
                        "type": "websocket.send",
                        "text": json.dumps(
                            {
                                "streamSid": stream_sid,
                                "event": "media",
                                "media": {"payload": base64_audio},
                            }
                        ),
                    }
                )
    except Exception as e:
        print(f"Error in send_raw_audio: {e}")

    finally:
        print("Finished sending audio.")


@app.get(INCOMING_CALL_ROUTE)
async def receive_call(request: Request):
    host = request.url.hostname
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    parameter = request.query_params.get("a")

    if parameter:
        put_call_details(call_sid, history=None)
        xml = f"""
                <Response>
                    <Connect>
                        <Stream url='wss://{host}{WEBSOCKET_ROUTE}' >
                            <Parameter name="a" value="{parameter}" />
                        </Stream>
                    </Connect>
                </Response>
                """.strip()

        return Response(content=xml, media_type="text/xml")
    else:
        return Response(
            content="<Response><Say>Call SID not provided.</Say></Response>",
            media_type="text/xml",
        )


async def stop_stream(ws, stream_sid):
    await ws.send(
        {
            "type": "websocket.send",
            "text": json.dumps({"event": "clear", "streamSid": stream_sid}),
        }
    )


def stop_call_for_low_balance(call_sid):
    client = Client(account_sid, TWILIO_AUTH_TOKEN)
    call = client.calls(call_sid).update(status="completed")


async def end_call(call_sid, b, raw):
    client = Client(account_sid, TWILIO_AUTH_TOKEN)
    try:
        client.calls(call_sid).update(status="completed")
        await sync_to_async(put_call_details)(
            call_sid,
            history=get_conversation_history(call_sid, raw["campaign_type"]),
            uid=b,
            raw_data=raw,
        )

    except Exception as e:
        print(f"Failed to end call: {e}")


@app.websocket(WEBSOCKET_ROUTE)
async def transcription_websocket(websocket: WebSocket):
    await websocket.accept()
    transcriber = None
    stream_sid = None
    fetched_data = None
    call_sid = None
    embd = None

    try:
        while True:
            data = await websocket.receive_text()
            data = json.loads(data)

            match data["event"]:
                case "connected":
                    print("connected")
                    transcriber = TwilioTranscriber()
                    transcriber.connect()
                    # dg_connection = start_deepgram_stream()

                case "start":
                    raw_data_json = data["start"]["customParameters"]["a"]
                    filter_data_json = data["start"]["customParameters"]["aa"]
                    b = data["start"]["customParameters"]["b"]

                    if isinstance(raw_data_json, str):
                        raw_data_json = ast.literal_eval(raw_data_json)
                    if isinstance(filter_data_json, str):
                        filter_data_json = ast.literal_eval(filter_data_json)

                    if raw_data_json["agent"]["first_message"]:
                        audio = get_audio_from_deepGram(
                            raw_data_json["agent"]["first_message"]
                        )
                        await send_raw_audio(websocket, audio, data["streamSid"])

                    if raw_data_json["campaign_type"] == "Outbound_sales":
                        embd = get_embedding_redis(raw_data_json)
                    else:
                        print("no embeddings")
                    call_sid = data["start"]["callSid"]

                case "media":
                    payload_b64 = data["media"]["payload"]
                    payload_mulaw = base64.b64decode(payload_b64)
                    transcriber.stream(payload_mulaw)
                    transcript_segment = transcriber.get_transcript()
                    # send_audio_to_deepgram(payload_mulaw)
                    # transcript_segment =  get_last_final_transcript()

                    if transcript_segment:
                        await stop_stream(websocket, stream_sid)

                        response, sell_price, cost_price = get_chat_response(
                            transcript_segment,
                            raw_data_json,
                            filter_data_json,
                            call_sid,
                            embeddings=embd,
                        )
                        cost_in_thread(
                            call_sid,
                            raw_data_json["agent"]["user_id"],
                            sell_price,
                            cost_price,
                        )

                        # print(response)
                        audio = get_audio_from_deepGram(response)
                        transcriber.reset_transcript()
                        # transcript_segment = None
                        stream_sid = data["streamSid"]
                        await send_raw_audio(websocket, audio, stream_sid)

                        if "goodbye" in response.lower():
                            time.sleep(10)
                            ###end cal##
                            await end_call(call_sid, b, raw_data_json)

                case "stop":
                    ###end cal##
                    print("case stop")
                    await sync_to_async(put_call_details)(
                        call_sid,
                        history=get_conversation_history(
                            call_sid, raw_data_json["campaign_type"]
                        ),
                        uid=b,
                        raw_data=raw_data_json,
                    )

                    if transcriber:
                        transcriber.close()
                    break

    except WebSocketDisconnect as e:
        print(f"WebSocket disconnected: {e}")
    except Exception as e:
        print(f"Error in WebSocket handling: {e}")
    finally:
        await websocket.close()


def has_phone_numbers(data):
    phone_numbers = []
    if (
        "call_details" in data
        and isinstance(data["call_details"], list)
        and data["call_details"]
    ):
        for call in data["call_details"]:

            if "phone_number" in call:
                phone_numbers.append(
                    {
                        "call_id": call["call_id"],
                        "phone_number": call["phone_number"],
                    }
                )
        return phone_numbers if phone_numbers else False
    else:
        return False


def make_call(parameter):

    processed_raw_data, parameter = processed_filter_campaign_data(parameter)
    phone_numbers = has_phone_numbers(processed_raw_data)
    if phone_numbers:
        pass
    else:
        print("No phone numbers found")

    user = get_user_details(user_id=processed_raw_data["agent"]["user_id"])

    provider_costs = get_provider_cost_details()
    total_sell_cost_per_5_seconds = sum(
        Decimal(details["sell_price"] / 60 * 5) for details in provider_costs.values()
    )
    if processed_raw_data["campaign_type"] == "Outbound_sales":
        load_send_embedding_redis(processed_raw_data)

    for to_number in phone_numbers:
        print(to_number)
        try:
            if user["UserBalance"] < total_sell_cost_per_5_seconds:
                print(f"Insufficient balance for call {call_sid}. Ending call.")
                break

            call = client.calls.create(
                twiml=f"""
                        <Response>
                            <Connect>
                                <Stream url='wss://{os.environ['HOST']}{WEBSOCKET_ROUTE}' >
                                    <Parameter name="a" value="{processed_raw_data}" />
                                    <Parameter name="aa" value="{parameter}" />
                                    <Parameter name="b" value="{to_number['call_id']}" />

                                    </Stream>
                            </Connect>
                        </Response> 
                        """,
                to=to_number["phone_number"],
                from_=TWILIO_NUMBER,
            )

            call_sid = call.sid
            call_log_id = to_number["call_id"]

            task_result = monitor_call.apply_async(
                args=[user["id"], call.sid, call_log_id]
            )
            task_id = task_result.id

            update_call_log(
                call_log_id=call_log_id, call_task_id=task_id, call_sid=call_sid
            )

            put_call_details(
                call_sid,
                history=None,
                uid=to_number["call_id"],
                raw_data=processed_raw_data,
            )
            print(
                f"Call initiated to {to_number['phone_number']} with Call SID: {call_sid}"
            )

        except Exception as e:
            print(f"Failed to initiate call to {to_number['phone_number']}: {e}")
