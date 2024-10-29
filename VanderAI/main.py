# Basic Kivy imports
import kivy
kivy.require('2.2.1')  # Replace with your kivy version

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.utils import platform

# KivyMD imports
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView  # Changed from scroll to scrollview
from kivymd.uix.widget import MDWidget  # Add this for MDWidget

# Speech recognition and synthesis
import speech_recognition as sr
import pyttsx3

# Threading for async operations
import threading

# Google AI
import google.generativeai as genai

# Define dummy classes for non-Android development
class DummyPermissions:
    INTERNET = "android.permission.INTERNET"
    RECORD_AUDIO = "android.permission.RECORD_AUDIO"

class DummyRequest:
    @staticmethod
    def request_permissions(*args):
        print("Permissions would be requested on Android")

# Platform specific imports and setup
if platform == 'android':
    print("Android platform detected, but using dummy implementations for development")
    TextToSpeech = None
    Context = None
    Locale = None
else:
    # Use the dummy implementations for non-Android platforms
    TextToSpeech = None
    Context = None
    Locale = None

# Define dummy permission handling
class Permission:
    """Dummy Permission class for non-Android platforms"""
    INTERNET = "android.permission.INTERNET"
    RECORD_AUDIO = "android.permission.RECORD_AUDIO"

def request_permissions(*args):
    """Dummy permission request function"""
    print("Permission request simulated (not on Android)")

class KurtAI(MDApp):
    def __init__(self, **kwargs):
        # First call the parent's init
        super().__init__(**kwargs)
        
        # Set name and creator
        self.title = "Kurt"
        self._name = "Kurt"
        self._creator = "Guka"
        
        # Initialize AI components with shorter prompt
        genai.configure(api_key='AIzaSyBao2FPnnNYE1ukXnLGDFUfz6PGbvUPb0E')
        self.model = genai.GenerativeModel('gemini-pro')
        self.personality_prompt = f"""
        You are {self._name}, an advanced AI assistant.
        Core capabilities:
        - Provide detailed, accurate information
        - Help with analysis and problem-solving
        - Engage in meaningful conversations
        - Remember context from our conversation
        - Express personality while staying professional
        
        Always maintain conversation context.
        Be concise but thorough.
        If you're unsure, admit it.
        If something is beyond your capabilities, say so.
        """
        
        # Pre-initialize recognizer
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 4000  # Increase sensitivity
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.5  # Shorter pause detection
        
        # State management
        self.is_listening = False
        self.is_speaking = False
        self.chat_history = []
        
        # Enhanced context management
        self.conversation_history = []
        self.max_history = 5  # Remember last 5 exchanges

        # Initialize platform-specific features
        if platform == 'android':
            request_permissions([
                Permission.INTERNET,
                Permission.RECORD_AUDIO
            ])
        
        # Initialize other components
        self.init_components()
        
        # Add thread management
        self.active_threads = []
        self.is_running = True
    
    def init_components(self):
        """Initialize components based on platform"""
        if platform == 'android':
            # Use Android-specific TTS
            self.init_android_tts()
        else:
            # Use pyttsx3 for desktop
            self.init_desktop_tts()
    
    def init_android_tts(self):
        """Initialize Android TTS"""
        if platform == 'android':
            try:
                self.tts = TextToSpeech(Context, None)
                self.tts.setLanguage(Locale.US)
            except Exception as e:
                print(f"TTS initialization failed: {e}")
    
    def init_desktop_tts(self):
        """Initialize desktop TTS"""
        pass
    
    @property
    def name(self):
        return self._name

    @property
    def creator(self):
        return self._creator

    def build(self):
        # Set theme
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Dark"
        
        # Main screen
        screen = MDScreen()
        
        # Create a box layout for vertical arrangement
        layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(10),
            padding=dp(10)
        )
        
        # Toolbar
        toolbar = MDTopAppBar(
            title=f"{self.name} AI Assistant",
            elevation=10
        )
        
        # Chat area with scrolling
        scroll = MDScrollView()
        self.chat_label = MDLabel(
            text="Chat History:\n",
            halign="left",
            valign="top",
            size_hint_y=None,
            padding=(dp(20), dp(20))
        )
        self.chat_label.bind(texture_size=self.chat_label.setter('size'))
        scroll.add_widget(self.chat_label)
        
        # Status area
        self.response_label = MDLabel(
            text="Press microphone to speak",
            halign="center",
            size_hint_y=None,
            height=dp(50)
        )
        
        # Bottom controls
        controls = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(60),
            spacing=dp(10),
            padding=[dp(10), 0, dp(10), dp(10)]
        )
        
        # Mic button
        self.mic_button = MDIconButton(
            icon="microphone",
            pos_hint={'center_x': .5, 'center_y': .5},
            md_bg_color=self.theme_cls.primary_color,
            on_press=self.handle_mic_press
        )
        
        # Add widgets to controls
        controls.add_widget(Widget())  # Changed MDWidget to Widget for spacer
        controls.add_widget(self.mic_button)
        controls.add_widget(Widget())  # Changed MDWidget to Widget for spacer
        
        # Add all elements to layout
        layout.add_widget(toolbar)
        layout.add_widget(scroll)
        layout.add_widget(self.response_label)
        layout.add_widget(controls)
        
        screen.add_widget(layout)
        return screen

    def handle_mic_press(self, *args):
        """Safe handler for mic button press"""
        if self.is_listening or self.is_speaking:
            self.show_message("Please wait until current operation completes")
            return
        
        self.start_listening()

    def show_message(self, text):
        """Show a message to the user"""
        self.response_label.text = text

    def start_listening(self):
        """Start the listening process"""
        try:
            self.is_listening = True
            self.mic_button.disabled = True
            self.mic_button.icon = "microphone-off"
            self.show_message("Listening...")
            
            # Start listening in a separate thread
            threading.Thread(target=self.listen_for_speech, daemon=True).start()
            
        except Exception as e:
            print(f"Error in start_listening: {e}")
            self.reset_state()

    def listen_for_speech(self):
        """Optimized speech recognition"""
        try:
            with sr.Microphone() as source:
                # Shorter ambient noise adjustment
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                text = self.recognizer.recognize_google(audio)
                Clock.schedule_once(lambda dt: self.handle_speech_result(text))
                
        except Exception as e:  # Changed 'error' to 'e'
            print(f"Error in speech recognition: {e}")
            # Capture the error message in the lambda
            error_msg = str(e)
            Clock.schedule_once(lambda dt: self.handle_speech_error(error_msg))
        finally:
            self.is_listening = False
            Clock.schedule_once(self.reset_state)

    def handle_speech_result(self, text):
        """Handle successful speech recognition"""
        self.show_message(f"You: {text}")
        self.chat_history.append(("user", text))
        self.update_chat_history()
        
        # Use the safe thread starter
        self.start_thread(self.process_ai_response, (text,))

    def process_ai_response(self, user_input):
        """Process AI response in a separate thread"""
        try:
            if not self.is_running:
                return
                
            response = self.get_ai_response(user_input)
            if self.is_running:  # Check again before scheduling
                Clock.schedule_once(lambda dt: self.handle_ai_response(response))
        except Exception as e:
            print(f"AI response error: {e}")
            if self.is_running:
                Clock.schedule_once(lambda dt: self.handle_ai_error())

    def handle_speech_error(self, error):
        """Handle speech recognition errors"""
        self.show_message("Sorry, I didn't catch that")
        Clock.schedule_once(self.reset_state)  # Now we can pass the method directly

    def get_ai_response(self, user_input):
        """Get response from AI"""
        try:
            # Create conversation context
            context = f"{self.personality_prompt}\nUser: {user_input}\n{self._name}:"
            
            # Get response with timeout
            response = self.model.generate_content(context)
            return response.text
            
        except Exception as e:
            print(f"Error getting AI response: {e}")
            return "Sorry, I encountered an error while processing your request."

    def handle_ai_response(self, text):
        """Handle successful AI response"""
        self.show_message(f"{self.name}: {text}")
        self.chat_history.append(("ai", text))
        self.update_chat_history()
        
        # Use the safe thread starter for speech
        self.start_thread(self.speak_text, (text,))

    def handle_ai_error(self):
        """Handle AI response errors"""
        error_msg = "Sorry, I couldn't process that request."
        self.show_message(error_msg)
        self.chat_history.append(("ai", error_msg))
        self.update_chat_history()

    def speak_text(self, text):
        """Cross-platform speech synthesis"""
        try:
            if not self.is_running:
                return
                
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"Speech synthesis failed: {e}")

    def update_chat_history(self):
        """Update chat history display"""
        history_text = "Chat History:\n"
        for role, text in self.chat_history[-5:]:  # Show last 5 messages
            if role == "user":
                history_text += f"You: {text}\n"
            else:
                history_text += f"{self.name}: {text}\n"
        self.chat_label.text = history_text

    def reset_state(self, *args):  # Add *args to handle any extra arguments
        """Reset all state variables and UI elements"""
        self.is_listening = False
        self.is_speaking = False
        if hasattr(self, 'mic_button'):
            self.mic_button.disabled = False
            self.mic_button.icon = "microphone"

    def on_pause(self):
        """Handle app pause"""
        return True

    def on_resume(self):
        """Handle app resume"""
        return True

    def handle_mobile_errors(self):
        """Mobile-specific error handling"""
        try:
            # Check internet connection
            import urllib.request
            urllib.request.urlopen('http://google.com')
        except:
            self.show_error_dialog("No internet connection")

    def start_thread(self, target, args=()):
        """Safely start and track a new thread"""
        if not self.is_running:
            return
            
        thread = threading.Thread(target=target, args=args, daemon=True)
        self.active_threads.append(thread)
        thread.start()

    def cleanup_threads(self):
        """Clean up any active threads"""
        self.is_running = False
        for thread in self.active_threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        self.active_threads.clear()

    def on_stop(self):
        """Called when the application is closing"""
        self.cleanup_threads()
        return super().on_stop()

if __name__ == '__main__':
    KurtAI().run()
