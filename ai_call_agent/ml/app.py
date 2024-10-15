import base64
import json
import os
import tempfile
import wave
import audioop
import soundfile as sf
import numpy as np
from fastapi import FastAPI, Request, Response, WebSocket, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from twilio.rest import Client
from dotenv import load_dotenv
from .utils.twilio_transcriber import TwilioTranscriber
from .utils.my_bot import math_tutor
from .utils.my_voice import get_audio_from_eleven_labs
from .utils.my_bot import get_conversation_history
import ngrok
from io import BytesIO
from starlette.websockets import WebSocketDisconnect





load_dotenv()

PORT = 5000
DEBUG = False
INCOMING_CALL_ROUTE = '/'
OUTGOING_CALL_ROUTE = '/make-calls'
WEBSOCKET_ROUTE = '/realtime'

# Twilio authentication
account_sid = os.environ['TWILIO_ACCOUNT_SID']
api_key = os.environ['TWILIO_API_KEY_SID']
api_secret = os.environ['TWILIO_API_SECRET']
client = Client(api_key, api_secret, account_sid)
TWILIO_NUMBER = os.environ['TWILIO_NUMBER']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']

# ngrok authentication
ngrok.set_auth_token(os.getenv("NGROK_AUTHTOKEN"))
app = FastAPI()


host = ""



def fetch_call_details(call_sid,history=None, output_file='call_details.txt'):

    client = Client(account_sid, TWILIO_AUTH_TOKEN)

    try:
        call = client.calls(call_sid).fetch()

        # Prepare call details
        call_details = (
             # f"Call conversation: {history if history is not None else 'No history available'}\n",
            f"Call SID: {call.sid}\n"
            f"To: {call.to}\n"
            f"Status: {call.status}\n"
            f"Duration: {call.duration} seconds\n"
            f"Start Time: {call.start_time}\n"
            f"End Time: {call.end_time}\n"
            f"Date Created: {call.date_created}\n"
            f"{'-' * 40}\n"
        )

        # Check if file exists
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                lines = f.readlines()

            # Check if the call_sid already exists in the file
            existing_call_index = None
            for i, line in enumerate(lines):
                if f"Call SID: {call_sid}" in line:
                    existing_call_index = i
                    break

            # If the call_sid exists, replace the old details
            if existing_call_index is not None:
                # Find the end of the current call details (next separator line)
                end_index = existing_call_index + 1
                while end_index < len(lines) and lines[end_index].strip() != '-' * 40:
                    end_index += 1

                # Replace the old details with new details
                lines = lines[:existing_call_index] + call_details.splitlines(keepends=True) + lines[end_index + 1:]

            # If the call_sid doesn't exist, append the new details
            else:
                lines.extend(call_details.splitlines(keepends=True))

            # Write the updated details back to the file
            with open(output_file, 'w') as f:
                f.writelines(lines)

        # If the file doesn't exist, create it and write the new details
        else:
            with open(output_file, 'w') as f:
                f.write(call_details)

    except Exception as e:
        print(f"Error fetching call details: {e}")



async def send_raw_audio(ws, audio_buffer, stream_sid):
    try:
        # Read the audio buffer directly using soundfile
        audio_data = BytesIO(audio_buffer)
        data, original_samplerate = sf.read(audio_data)
        new_samplerate = 8000

        if len(data.shape) > 1:  # If stereo, take one channel
            data = data[:, 0]

        # Resample audio
        duration = data.shape[0] / original_samplerate
        new_length = int(duration * new_samplerate)
        resampled_data = np.interp(np.linspace(0, len(data), new_length), np.arange(len(data)), data)

        # Create a temporary WAV file with the resampled audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
            temp_filename = temp_wav.name
            sf.write(temp_filename, resampled_data, new_samplerate)

        # Open the temporary file and stream it via WebSocket
        with wave.open(temp_filename, 'rb') as wav_file:
            while True:
                wav_data = wav_file.readframes(320)  # Reading 320 frames for mu-law conversion
                if not wav_data:
                    print("No more data to read.")

                    await ws.send(
                        {"type": "websocket.send",

                        "text":json.dumps({
                        'streamSid': stream_sid,
                        'event': 'mark',
                        "mark": {"name": "my label"}
                    })}
                    )
                    break

                # Convert raw PCM data to mu-law
                mulaw_data = audioop.lin2ulaw(wav_data, 2)
                base64_audio = base64.b64encode(mulaw_data).decode("utf-8")
                await ws.send(
                {"type": "websocket.send",

                "text":json.dumps({
                'streamSid': stream_sid,
                'event': 'media',
                "media": {"payload": base64_audio}
                })}
                )

    finally:
        print("Finished sending audio.")


@app.post(INCOMING_CALL_ROUTE)
async def receive_call(request: Request):
    host = request.url.hostname  # Getting the hostname from the request URL
    form_data = await request.form()  # Parse form data in FastAPI
    call_sid = form_data.get('CallSid')  # Get 'CallSid' from form data
    fetch_call_details(call_sid)  

        # Log or process the call SID as needed
    print(f"Received call with Call SID: {call_sid}")
    xml = f"""
<Response>
    <Say>
        Speak to see your speech transcribed in the console
    </Say>
    <Connect>
        <Stream url='wss://{host}{WEBSOCKET_ROUTE}' />
    </Connect>
</Response>
""".strip()

    return Response(content=xml, media_type='text/xml')



async def stop_stream(ws, stream_sid):
    await ws.send({
        "type": "websocket.send",
        "text": json.dumps({"event": "clear", "streamSid": stream_sid})
    })



@app.websocket(WEBSOCKET_ROUTE)
async def transcription_websocket(websocket: WebSocket):
    await websocket.accept()
    print("starting while loop")
    transcriber = None
    stream_sid = None

    try:
        while True:
            data = await websocket.receive_text()
            data = json.loads(data)

            match data['event']:
                case "connected":
                    print("connected")
                    transcriber = TwilioTranscriber()
                    transcriber.connect()
                case "start":
                    call_sid = data['start']['callSid']

                case "media":
                    payload_b64 = data['media']['payload']
                    payload_mulaw = base64.b64decode(payload_b64)
                    transcriber.stream(payload_mulaw)

                    transcript_segment = transcriber.get_transcript()
                    if transcript_segment:
                        await stop_stream(websocket, stream_sid)
                        print("from Twilio:", transcript_segment)
                        response = math_tutor(transcript_segment, call_sid)
                        print(response)

                        audio = get_audio_from_eleven_labs(response)
                        transcriber.reset_transcript()
                        stream_sid = data['streamSid']
                        await send_raw_audio(websocket, audio, stream_sid)

                case "stop":
                    print("case stop")
                    fetch_call_details(call_sid)

                    if transcriber:
                        transcriber.close()
                    break  # Exit the loop once the "stop" event is received

    except WebSocketDisconnect as e:
        print(f"WebSocket disconnected: {e}")
    except Exception as e:
        print(f"Error in WebSocket handling: {e}")
    finally:
        await websocket.close()






def make_call(host, phone_numbers):
    for to_number in phone_numbers:
        try:
            # Create a call with TwiML that initiates the websocket stream
            print("###########################################################",host)
            call = client.calls.create(
                twiml=f"""
                        <Response>
                            <Say>Speak to see your speech transcribed in the console</Say>
                            <Connect>
                                <Stream url='wss://{host}{WEBSOCKET_ROUTE}' />
                            </Connect>
                        </Response> 
                        """,
                to=to_number,
                from_=TWILIO_NUMBER,
            )

            # Store the call SID in a variable
            call_sid = call.sid
            fetch_call_details(call_sid)

            print(f"Call initiated to {to_number} with Call SID: {call_sid}")  # Optional: print the SID

        except Exception as e:
            print(f"Failed to initiate call to {to_number}: {e}")





@app.post(OUTGOING_CALL_ROUTE)
async def call_multiple_numbers(request: Request):
    try:
        # Get the JSON data from the request
        host = request.url.hostname  
        data = await request.json()
        phone_numbers = data.get('phone_numbers')

        # Check if phone_numbers are provided
        if not phone_numbers:
            raise HTTPException(status_code=400, detail="Missing phone_numbers")

        # Initiate the call (assuming make_call is defined)
        make_call(host, phone_numbers=phone_numbers)

        # Return success response
        return {"status": "success", "message": "Calls initiated."}

    except Exception as e:
        # Return an error response
        return JSONResponse(status_code=500, content={"error": str(e)})