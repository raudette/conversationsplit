import json
from pydub import AudioSegment
from dotenv import load_dotenv
import os
import argparse
import assemblyai as aai
import requests


load_dotenv()
aai.settings.api_key= os.getenv("ASSEMBLYAI_API_KEY")

parser = argparse.ArgumentParser()
parser.add_argument("--filename", help="audio file to split into tracks per speaker", type=str)
parser.add_argument("--numspeakers", help="set number of speakers in recording", type=int, default=2)
args = parser.parse_args()

print("Number of speakers: "+str(args.numspeakers))
print("Splitting: "+args.filename)

config = aai.TranscriptionConfig(speaker_labels=True,
  speakers_expected=args.numspeakers)

transcriber = aai.Transcriber()
transcript = transcriber.transcribe(
  args.filename,
  config=config
)

#couldn't be bothered to figure out data structure of transcript returned object, so just pulling the json here
URL="https://api.assemblyai.com/v2/transcript/"+str(transcript.id)
headers = {
  "Authorization": os.getenv("ASSEMBLYAI_API_KEY"),
  }

response = requests.get(URL, headers=headers)

data = json.loads(response.text)

fullwav = AudioSegment.from_wav(args.filename)

fullwavlength=len(fullwav)

lastend = 0

speakers={}

#split the audio
for utterance in data['utterances']:
    if utterance['speaker'] not in speakers:
        speakers[utterance['speaker']] = {}
        speakers[utterance['speaker']]["audio"] = AudioSegment.silent(0)
    if "currentpos" not in speakers[utterance['speaker']]:
        speakers[utterance['speaker']]["currentpos"]=0
    if utterance['start']>speakers[utterance['speaker']]["currentpos"]:
        silence = AudioSegment.silent(utterance['start']-speakers[utterance['speaker']]["currentpos"])
        speakers[utterance['speaker']]["audio"]=speakers[utterance['speaker']]["audio"]+silence 
    soundfile=fullwav[utterance['start']:utterance['end']]
    lastend=utterance['end']
    speakers[utterance['speaker']]["audio"]=speakers[utterance['speaker']]["audio"]+soundfile 
    speakers[utterance['speaker']]["currentpos"]=utterance['end']

#add silence at end to make tracks the same length
for index, speaker in enumerate(speakers):
    silence = len(fullwav) - len(speakers[speaker]['audio'])
    if silence>0:
        speakers[speaker]['audio']=speakers[speaker]['audio']+AudioSegment.silent(silence)

for index, speaker in enumerate(speakers):
    filename = "conversationsplit "+str(index)+".wav"
    speakers[speaker]['audio'].export(filename, format="wav")

