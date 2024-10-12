from ai_call_agent.ml.app import *




if __name__ == "__main__":

    import uvicorn
    try:
        # Open Ngrok tunnel
        listener = ngrok.forward(f"http://localhost:{PORT}")
        print(f"Ngrok tunnel opened at {listener.url()} for port {PORT}")
        NGROK_URL = listener.url()

        # Set ngrok URL to be the webhook for the appropriate Twilio number
        twilio_numbers = client.incoming_phone_numbers.list()
        twilio_number_sid = [num.sid for num in twilio_numbers if num.phone_number == TWILIO_NUMBER][0]
        client.incoming_phone_numbers(twilio_number_sid).update(account_sid, voice_url=f"{NGROK_URL}{INCOMING_CALL_ROUTE}")

        
        uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
    finally:
        ngrok.disconnect()
