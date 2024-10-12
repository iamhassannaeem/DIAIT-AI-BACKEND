from elevenlabs import ElevenLabs, save


def generate_audio(response,voice="Rachel", model="eleven_multilingual_v2", filename="./test_voice.wav"):

    api_key = "sk_a6c595d8a81c5a4722ea1247846f54271db6687c784d428c"
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


