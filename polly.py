import boto3
import os
from classes import S3BucketManager

translate = boto3.client(service_name='translate',
                         region_name='us-west-2', use_ssl=True)
# polly = boto3.client('polly', region_name='us-west-2')

polly_client = boto3.Session(
    region_name='us-west-2').client('polly')


s3_client = boto3.client('s3')

S3_BUCKET = "imlanie"
OUTPUT_DIR = "/tmp/"
AUDIO_FILE = "speech.mp3"

bucket_manager = S3BucketManager(S3_BUCKET)

# Original Message in text format


def run_voice_new(orig_message):

    try:

        translated_msg = translate.translate_text(Text=orig_message,
                                                  SourceLanguageCode="es", TargetLanguageCode="es-MX")

        spoken_text = polly_client.synthesize_speech(VoiceId='Lucia',
                                                     OutputFormat='mp3',
                                                     Text=translated_msg.get(
                                                         'TranslatedText'),
                                                     Engine='neural')

        file = open(OUTPUT_DIR + AUDIO_FILE, 'wb')
        file.write(spoken_text['AudioStream'].read())
        print("MP3 file created")

        bucket_manager.upload_file(OUTPUT_DIR + AUDIO_FILE, AUDIO_FILE)
        print("MP3 file uploaded")
        file.close()

    except Exception as ex:
        print("Exception occurred: " + str(ex))


# def run_voice(in_lang, in_voice_name, in_message):

#     #in_message = "Hello, I am Elaine.  Today is Monday, the third.  Here's the task list for today."

#     result = translate.translate_text(Text=in_message,
#                                       SourceLanguageCode="es", TargetLanguageCode=in_lang)

#     spoken_text = polly.synthesize_speech(Text=result.get('TranslatedText'),
#                                           LanguageCode='es-MX',
#                                           OutputFormat='mp3',
#                                           VoiceId=in_voice_name)

#     with open('output.mp3', 'wb') as f:
#         f.write(spoken_text['AudioStream'].read())
#         f.close()

#     mixer.init()
#     mixer.music.load('output.mp3')
#     mixer.music.play()

#     while mixer.music.get_busy() == True:
#         pass

#     mixer.quit()
#     os.remove('output.mp3')


# run_voice("es-MX", "Mia",
#           "Hello, I am Elaine.  Today is Monday, the third.  Here's the task list for today.")
