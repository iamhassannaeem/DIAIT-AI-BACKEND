import base64
import json
import os
import tempfile
import wave
import audioop
import soundfile as sf
import numpy as np
from flask import Flask, request, Response, jsonify
from flask_sock import Sock
import ngrok
from twilio.rest import Client
from dotenv import load_dotenv
from utils.twilio_transcriber import TwilioTranscriber
from utils.my_bot import math_tutor
from utils.my_voice import generate_audio
from utils.my_bot import get_conversation_history


load_dotenv()

# Flask settings
PORT = 5000
DEBUG = False
INCOMING_CALL_ROUTE = '/'
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
app = Flask(__name__)
sock = Sock(app)

# Global variable to store NGROK URL
NGROK_URL = ""


import os

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




def send_raw_audio(ws, file_path, stream_sid):
    try:
        # print("Stream SID:", stream_sid)
        data, original_samplerate = sf.read(file_path)
        new_samplerate = 8000
        if len(data.shape) > 1:  # If stereo, take one channel
            data = data[:, 0]

        # Resample audio
        duration = data.shape[0] / original_samplerate
        new_length = int(duration * new_samplerate)
        resampled_data = np.interp(np.linspace(0, len(data), new_length), np.arange(len(data)), data)

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
            temp_filename = temp_wav.name
            sf.write(temp_filename, resampled_data, new_samplerate)

        # print("Temporary file created:", temp_filename)

        with wave.open(temp_filename, 'rb') as wav_file:
            while True:
                wav_data = wav_file.readframes(320)
                if not wav_data:
                    print("No more data to read.")
                    ws.send(json.dumps({"event": "mark", "streamSid": stream_sid, "mark": {"name": "my label"}}))
                    break

                mulaw_data = audioop.lin2ulaw(wav_data, 2)
                base64_audio = base64.b64encode(mulaw_data).decode("utf-8")
                ws.send(json.dumps({"event": "media", "streamSid": stream_sid, "media": {"payload": base64_audio}}))
    finally:
        print("Finished sending audio.")


@app.route(INCOMING_CALL_ROUTE, methods=['GET', 'POST'])
def receive_call():
    if request.method == 'POST':
        call_sid = request.form.get('CallSid')
        fetch_call_details(call_sid)

        # Log or process the call SID as needed
        print(f"Received call with Call SID: {call_sid}")
        xml = f"""
<Response>
    <Say>
        Speak to see your speech transcribed in the console
    </Say>
    <Connect>
        <Stream url='wss://{NGROK_URL}{WEBSOCKET_ROUTE}' />
    </Connect>
</Response>
""".strip()

        return Response(xml, mimetype='text/xml')
    else:
        return "Real-time phone call transcription app"


def stop_stream(ws, stream_sid):
    ws.send(json.dumps({"event": "clear", "streamSid": stream_sid}))


@sock.route(WEBSOCKET_ROUTE)
def transcription_websocket(ws):
    print("transcription_websocket")
    transcriber = None
    stream_sid = None

    while True:
        data = json.loads(ws.receive())

        match data['event']:
            case "connected":
                print("connected")
                transcriber = TwilioTranscriber()
                transcriber.connect()
            case "start":
                # print('Twilio started')
                call_sid = data['start']['callSid']

            case "media":

                payload_b64 = data['media']['payload']
                payload_mulaw = base64.b64decode(payload_b64)
                transcriber.stream(payload_mulaw)

                transcript_segment = transcriber.get_transcript()
                if transcript_segment:
                    stop_stream(ws, stream_sid)
                    # print("from Twilio:", transcript_segment)
                    print("all_sid all_sid",call_sid)
                    response = math_tutor(transcript_segment,call_sid)
                    generate_audio(response)

                    transcriber.reset_transcript()
                    stream_sid = data['streamSid']
                    file_path = "test_voice.wav"
                    send_raw_audio(ws, file_path, stream_sid)

            case "stop":
                print("case stop")
                # history = get_conversation_history(call_sid)
                # if history:
                #     for message in history:
                #         print("at lastttt ",message)
                # else:
                #     print("No history found for this call_sid.")
                fetch_call_details(call_sid)


                # print('Twilio stopped')
                transcriber.close()
                # print('Transcriber closed')


def make_call(phone_numbers):
    for to_number in phone_numbers:
        try:
            # Create a call with TwiML that initiates the websocket stream
            call = client.calls.create(
                twiml=f"""
<Response>
    <Say>Speak to see your speech transcribed in the console</Say>
    <Connect>
        <Stream url='wss://{NGROK_URL}{WEBSOCKET_ROUTE}' />
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




@app.route('/make-calls', methods=['POST'])
def call_multiple_numbers():
    try:
        data = request.get_json()
        phone_numbers = data.get('phone_numbers')

        if not phone_numbers:
            return jsonify({"error": "Missing phone_numbers"}), 400


        make_call(phone_numbers=phone_numbers)
        return jsonify({"status": "success", "message": "Calls initiated."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    try:
        listener = ngrok.forward(f"http://localhost:{PORT}")



        NGROK_URL = listener.url().replace("http://", "").replace("https://", "")



        twilio_numbers = client.incoming_phone_numbers.list()
        twilio_number_sid = [num.sid for num in twilio_numbers if num.phone_number == TWILIO_NUMBER][0]
        print(twilio_number_sid)
        client.incoming_phone_numbers(twilio_number_sid).update(account_sid, voice_url=f"{listener.url()}{INCOMING_CALL_ROUTE}")


        app.run(port=PORT, debug=DEBUG)

    finally:
        ngrok.disconnect()
