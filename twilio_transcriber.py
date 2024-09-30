import os

import assemblyai as aai
from dotenv import load_dotenv
load_dotenv()

aai.settings.api_key = os.getenv('ASSEMBLYAI_API_KEY')

TWILIO_SAMPLE_RATE = 8000 # Hz

class TwilioTranscriber(aai.RealtimeTranscriber):
    def __init__(self):
        super().__init__(
            on_data=self.on_data,
            on_error=self.on_error,
            on_open=self.on_open, # optional
            on_close=self.on_close, # optional
            sample_rate=TWILIO_SAMPLE_RATE,
            encoding=aai.AudioEncoding.pcm_mulaw
        )
        self.transcript = ""  # Variable to store the transcript

    def on_open(self, session_opened: aai.RealtimeSessionOpened):
        "Called when the connection has been established."
        # print("Session ID:", session_opened.session_id)

    def on_data(self, transcript: aai.RealtimeTranscript):
        "Called when a new transcript has been received."
        if not transcript.text:
            return

        # Store only new transcript data
        if isinstance(transcript, aai.RealtimeFinalTranscript):
            self.transcript += transcript.text + "\n"
        # else:
        #     self.transcript += transcript.text + "\r"
        
    def on_error(self, error: aai.RealtimeError):
        "Called when the connection has been closed."
        print("An error occurred in transcriber:", error)

    def on_close(self):
        "Called when the connection has been closed."
        print("Closing Session")

    def get_transcript(self):
        "Return the stored transcript"
        return self.transcript

    def reset_transcript(self):
        "Clear the stored transcript"
        self.transcript = ""
