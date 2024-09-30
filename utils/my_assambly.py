
import assemblyai as aai

# set the API key
aai.settings.api_key = "6b8f3477ebbf43e6a25b11e62aec022b"
# aai.settings.api_key = f"{ASSEMBLYAI_API_KEY}"

config = aai.TranscriptionConfig(punctuate=False, format_text=False)

transcriber = aai.Transcriber(config=config)

# # will use the same config for all `.transcribe*(...)` operations
transcript = transcriber.transcribe("./output.mp3")

print(transcript.id)
print(transcript.text)

