from elevenlabs import ElevenLabs, save


def generate_audio(response,voice="Rachel", model="eleven_multilingual_v2", filename="./test_voice.wav"):

    api_key = "sk_9665807e99ed7261cd1f68145be1074ee7c80bfbaea9fa28"
    client = ElevenLabs(api_key=api_key)


    audio = client.generate(
        text=response,
        voice=voice,
        model=model
    )

    save(audio, filename)
    print(f"Audio saved as {filename}")
# response="Hello! my name is shahzaib"
# generate_audio(response)


