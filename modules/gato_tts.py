from elevenlabs import play, stream, Voice, VoiceSettings
from elevenlabs.client import ElevenLabs
import asyncio
import maricon

#maps user to voice
voicemap = {
    #'breezyexcursion':'Y3UmCxq1IvIqL9cqp8T6',
    'breezyexcursion' : 'ScLiWidzk03OmbHyb05K',
    'pwnlamesa' : 'kdVjFjOXaqExaDvXZECX',
    'hiten' : 'oVaceCee8Km6PpC6zacp',
    'hq4': 'Lhkfd0eq2F87bgx4Aozc',
    'shinnokz' : '6xPz2opT0y5qtoRh1U1Y',
    }

#for local test
def speakertest(text):
    client = ElevenLabs(
      api_key=maricon.elevenlabs_key
    )

    audio = client.generate(
      text=text,
      voice="QUh09v7ceTINrO6VcjXq",
      model="eleven_multilingual_v2"
      
    )
    play(audio)
    return

#for discord bot usage
async def speaker(user, text):
    client = ElevenLabs(
      api_key=maricon.elevenlabs_key
    )

    user = str(user)

    #select voice based on user
    if user in voicemap:
        voice = voicemap[user]
    else:
        voice = "QUh09v7ceTINrO6VcjXq"

    # still testing dont wanna waste api calls on very long messages. return if longer than 200 characters
    if len(text) > 200:
        return
    # if emoji is detected, return
    if text[0] == '<':
        return
    #if link is detected, return
    if 'http' in text:
        return
    #skip single word messages
    if len(text.split()) < 2:
        return
    else:
        print(f'gato_tts engaging for [{user}] {text}')

    audio = client.generate(
      text=text,
      voice=Voice(
          voice_id=voice,
          settings=VoiceSettings(stability=0.50, similarity_boost=0.75, style=0.8, user_speaker_boost=True),
      ),
      model="eleven_multilingual_v2"
    )
    play(audio)
    return


#speakertest('dudes will scoff at a $36 bottle of lotion and then drop $1200 on a gun')