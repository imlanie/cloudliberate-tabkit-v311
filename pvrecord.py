# load PvRecorder

from pvrecorder import PvRecorder
import wave
from wave import Wave_write, Wave_read
import struct
import boto3
import datetime
from datetime import timedelta, datetime
import time
from classes import S3BucketManager
import ast
import tqdm
# load all audio input devices

curr_day = datetime.now()
str_curr_day = curr_day.strftime('%y%m%d%H%M%S')
target_s3_bucket = 'imlanie'
audio_files_folder = 'recorded_messages'
path = 'c:/GitRepo/demo-flask-website/audio_recording.wav'
uri_media_file = 's3://{}/{}/audio_recording.wav'.format(
    target_s3_bucket, audio_files_folder)
#str_curr_day = str(curr_day)

for index, device in enumerate(PvRecorder.get_available_devices()):
    print(f"[{index}] {device}")

# RECORD THE VOICE ON THE MICROPHONE AND CREATE THE MEDIA FILE (.WAV) AND SAVE TO LOCAL DISK

# (32 milliseconds of 16 kHz audio)
recorder = PvRecorder(device_index=-1, frame_length=512)
audio = []

try:
    recorder.start()

    while True:
        frame = recorder.read()
        audio.extend(frame)
except KeyboardInterrupt:
    recorder.stop()

    with wave.open(path, "wb") as wavfile:

        wavfile.setparams((1, 2, 16000, 512, "NONE", "NONE"))
        wavfile.writeframes(struct.pack("h" * len(audio), *audio))
        print("Done")

finally:
    recorder.delete()

# UPLOADED THE RECORDED FILE (.WAV) TO S3 BUCKET

s3 = boto3.resource(service_name='s3')

s3.meta.client.upload_file(
    Filename=path, Bucket=target_s3_bucket, Key='recorded_messages/audio_recording.wav')

# try:
#     response = transcribe.create_vocabulary(
#         VocabularyName='us-english',
#         LanguageCode='en-US',  # | 'es-US' | 'en-AU' | 'fr-CA' | 'en-UK',
#         Phrases=[
#             'this is a test'
#         ]
#     )

# except Exception as ex:
#     print("Exception creating vocabulary: " + str(ex))


# GET THE MEDIA FILE FROM THE S3 BUCKET AND THEN TRANSCRIBE IT TO TEXT THEN SAVE THE TEXT FILE BACK TO S3 BUCKET
transcribe = boto3.client('transcribe')
translate = boto3.client(service_name='translate',
                         region_name='us-west-2', use_ssl=True)

try:
    response = transcribe.get_vocabulary(VocabularyName='us-english')
    print(response['VocabularyName'])
except Exception as ex:
    print("Exception occurred: " + str(ex))

# THE TRANSCRIBE JOB GETS THE MEDIA FILE FROM THE S3 BUCKET AND THEN PRODUCES A WRITTEN TRANSCRIPT IN JSON FORMAT AND SAVES IN S3 BUCKET

transcribe_job = "transcribe_" + str_curr_day
print("Transcribe Job Name: " + transcribe_job)

try:

    response = transcribe.start_transcription_job(
        TranscriptionJobName=transcribe_job,
        LanguageCode='en-US',  # | 'es-US' | 'en-AU' | 'fr-CA' | 'en-UK',
        MediaSampleRateHertz=16000,
        MediaFormat='wav',  # 'mp3' | 'mp4' | 'wav' | 'flac',
        Media={
            'MediaFileUri': uri_media_file
        },
        OutputBucketName=target_s3_bucket,
        Settings={
            'VocabularyName': 'us-english',
            'ShowSpeakerLabels': True,  # | False,
            'MaxSpeakerLabels': 2,
            'ChannelIdentification': True  # | False
        }
    )

    print("URI of the media file: " + str(uri_media_file))

    try:
        # While the job is running and not completed, wait
        while True:
            status = transcribe.get_transcription_job(
                TranscriptionJobName=transcribe_job)

            if status['TranscriptionJob']['TranscriptionJobStatus'] in [
                    'COMPLETED', 'FAILED']:
                break

            time.sleep(.5)

        if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
            obj = s3.Object(target_s3_bucket, transcribe_job+'.json')
            transcribed_msg = ast.literal_eval(obj.get()['Body'].read().decode(
                'UTF-8'))['results']['transcripts'][0]['transcript']
            print(transcribed_msg)

        else:
            print("Transcribe job is not completed")

        translated_msg = translate.translate_text(Text=transcribed_msg,
                                                  SourceLanguageCode="es", TargetLanguageCode="es-MX")

        print(translated_msg['TranslatedText'])

    except Exception as ex:
        print("Exception: " + str(ex))


except Exception as ex:
    print("Exception: " + str(ex))


# must complete confirmation before deleting
# finally:
#     transcribe.delete_transcription_job(
#         TranscriptionJobName=transcribe_job)
