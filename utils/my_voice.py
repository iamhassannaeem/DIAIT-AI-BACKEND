

from elevenlabs import play
from elevenlabs.client import ElevenLabs
from elevenlabs import play, stream, save



client = ElevenLabs(
  api_key="sk_a6c595d8a81c5a4722ea1247846f54271db6687c784d428c"
)

audio = client.generate(
  text="Hello! 你好! नमस्ते! Bonjour مرحبا!",
  voice="Rachel",
  model="eleven_multilingual_v2"
)
play(audio)
save(audio, "my-file.mp3")  
