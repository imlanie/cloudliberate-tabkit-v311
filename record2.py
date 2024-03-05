import sounddevice
from scipy.io.wavfile import write


sr = 44100
seconds = 10
print('Recording')
record_voice = sounddevice.rec(sr*seconds, samplerate=sr, channels=2)
sounddevice.wait()
write("/tmp/mynewfile.wav", sr, record_voice)
print("Finished")
