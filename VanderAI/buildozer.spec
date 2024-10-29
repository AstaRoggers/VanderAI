[app]
title = KurtAI
package.name = kurtai
package.domain = org.kurtai
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1

# Requirements
requirements = python3,\
    kivy==2.2.1,\
    kivymd,\
    pyttsx3,\
    SpeechRecognition,\
    google-generativeai,\
    pyaudio,\
    plyer

# Android specific
android.permissions = INTERNET,

[buildozer]
log_level = 2
warn_on_root = 1
