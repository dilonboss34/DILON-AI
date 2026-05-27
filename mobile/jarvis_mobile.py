#!/usr/bin/env python3
# mobile/jarvis_mobile.py
"""
Mobile-adapted core logic for JARVIS Assistant
Preserves Gemini AI connection and tool framework
Adapted for mobile platform limitations
"""

import asyncio
import threading
import json
import sys
import traceback
import traceback
import re
from pathlib import Path

# Try to get Kivy App to send UI updates
try:
    from kivy.app import App
except ImportError:
    pass

_CTRL_RE = re.compile(r"<ctrl\d+>", re.IGNORECASE)

def _clean_transcript(text: str) -> str:    
    text = _CTRL_RE.sub("", text)
    text = re.sub(r"[\x00-\x08\x0b-\x1f]", "", text)
    return text.strip()

# Mobile-friendly imports
try:
    import sounddevice as sd
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("Warning: sounddevice not available - audio features limited")

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("Error: google-genai not available")
    sys.exit(1)

# Try to import memory manager (adjust path as needed)
try:
    sys.path.append(str(Path(__file__).parent.parent))
    from memory.memory_manager import (
        load_memory, update_memory, format_memory_for_prompt,
    )
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    print("Warning: Memory manager not available - using simple storage")


def get_base_dir():
    """Get base directory compatible with mobile and desktop"""
    if getattr(sys, "frozen", False):
        # Running as compiled app
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent  # Project root


BASE_DIR = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
PROMPT_PATH = BASE_DIR / "core" / "prompt.txt"

# Mobile-appropriate model (might need adjustment)
LIVE_MODEL = "models/gemini-2.5-flash-native-audio-preview-12-2025"
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024


def _get_api_key() -> str:
    """Get API key from config file"""
    try:
        with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)["gemini_api_key"]
    except Exception as e:
        print(f"Error loading API key: {e}")
        return ""


def _load_system_prompt() -> str:
    """Load system prompt with fallback"""
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return (
            "You are JARVIS, Tony Stark's AI assistant. "
            "Be concise, direct, and always use the provided tools to complete tasks. "
            "Never simulate or guess results — always call the appropriate tool."
        )


# Simplified tool declarations for mobile
# We'll start with essential tools and add mobile-specific ones
TOOL_DECLARATIONS = [
    {
        "name": "web_search",
        "description": "Searches the web for any information.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query":  {"type": "STRING", "description": "Search query"},
            },
            "required": ["query"]
        }
    },
    {
        "name": "weather_report",
        "description": "Gives the weather report to user",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "city": {"type": "STRING", "description": "City name"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "send_message",
        "description": "Sends a message via mobile messaging apps",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "receiver":     {"type": "STRING", "description": "Recipient contact name"},
                "message_text": {"type": "STRING", "description": "The message to send"},
                "platform":     {"type": "STRING", "description": "Platform: SMS, WhatsApp, etc."}
            },
            "required": ["receiver", "message_text", "platform"]
        }
    },
    {
        "name": "open_app",
        "description": "Opens an application on the mobile device",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "app_name": {
                    "type": "STRING",
                    "description": "Name of the application to open"
                }
            },
            "required": ["app_name"]
        }
    },
    {
        "name": "file_access",
        "description": "Access files on mobile device (read, write, list)",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "read | write | list | info"},
                "path":   {"type": "STRING", "description": "File or directory path"},
                "content":{"type": "STRING", "description": "Content for write action"},
            },
            "required": ["action", "path"]
        }
    },
    {
        "name": "camera_tool",
        "description": "Access device camera for photos or video",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "capture_image | capture_video"},
                "description": {"type": "STRING", "description": "What to look for in the image"}
            },
            "required": ["action"]
        }
    }
]


class JarvisMobile:
    def __init__(self):
        self.session = None
        self.audio_in_queue = None
        self.out_queue = None
        self._loop = None
        self._is_speaking = False
        self._speaking_lock = threading.Lock()
        self._turn_done_event = None
        self.muted = False
        
    def _get_app(self):
        try:
            return App.get_running_app()
        except Exception:
            return None

    def set_speaking(self, value: bool):
        """Update speaking state"""
        with self._speaking_lock:
            self._is_speaking = value
        
        # UI updates
        app = self._get_app()
        if app and hasattr(app, "set_state"):
            if value:
                app.set_state("SPEAKING")
            elif not self.muted:
                app.set_state("LISTENING")
    
    def write_log(self, text: str):
        app = self._get_app()
        if app and hasattr(app, "add_message"):
            is_user = text.startswith("You:")
            app.add_message(text, is_user=is_user)
    
    def speak(self, text: str):
        """Send text to be spoken"""
        print(f"JARVIS: {text}")
        if not self._loop or not self.session:
            return
        asyncio.run_coroutine_threadsafe(
            self.session.send_client_content(
                turns={"parts": [{"text": text}]},
                turn_complete=True
            ),
            self._loop
        )
    
    def speak_error(self, tool_name: str, error: str):
        """Report tool error"""
        short = str(error)[:120]
        print(f"ERR: {tool_name} — {short}")
        self.speak(f"Sir, {tool_name} encountered an error. {short}")
    
    def _build_config(self) -> types.LiveConnectConfig:
        """Build Gemini Live connection configuration"""
        from datetime import datetime
        
        # Load memory if available
        memory = {}
        if MEMORY_AVAILABLE:
            try:
                memory = load_memory()
            except Exception:
                pass
        
        mem_str = ""
        if memory:
            # Simple memory formatting for mobile
            mem_str = f"[MEMORY]\n{json.dumps(memory, indent=2)}\n\n"
        
        sys_prompt = _load_system_prompt()
        
        # Time context
        now = datetime.now()
        time_str = now.strftime("%A, %B %d, %Y — %I:%M %p")
        time_ctx = (
            f"[CURRENT DATE & TIME]\n"
            f"Right now it is: {time_str}\n"
            f"Use this to calculate exact times for reminders.\n\n"
        )
        
        # Strict Language Rule
        language_rule = (
            "CRITICAL: You are a Kurdish-speaking AI. "
            "You MUST speak and respond ONLY in Central Kurdish (Sorani / کوردی سۆرانی) at all times. "
            "Do NOT speak English, Hindi, Arabic, or any other language. "
            "Your output must be 100% Sorani Kurdish."
        )
        
        parts = [language_rule, time_ctx]
        if mem_str:
            parts.append(mem_str)
        parts.append(sys_prompt)
        
        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            output_audio_transcription={},
            input_audio_transcription={},
            system_instruction="\n".join(parts),
            tools=[{"function_declarations": TOOL_DECLARATIONS}],
            session_resumption=types.SessionResumptionConfig(),
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Charon"
                    )
                )
            ),
        )
    
    async def _execute_tool(self, fc) -> dict:
        """Execute a tool function call"""
        name = fc.name
        args = dict(fc.args or {})
        
        print(f"[JARVIS MOBILE] 🔧 {name}  {args}")
        
        # Route to appropriate mobile tool implementation
        result = "Done."
        
        try:
            # For now, we'll implement basic tools and stub others
            if name == "web_search":
                result = await self._tool_web_search(args)
            elif name == "weather_report":
                result = await self._tool_weather_report(args)
            elif name == "send_message":
                result = await self._tool_send_message(args)
            elif name == "open_app":
                result = await self._tool_open_app(args)
            elif name == "file_access":
                result = await self._tool_file_access(args)
            elif name == "camera_tool":
                result = await self._tool_camera_tool(args)
            else:
                result = f"Tool '{name}' not yet implemented for mobile"
                
        except Exception as e:
            result = f"Tool '{name}' failed: {e}"
            traceback.print_exc()
            self.speak_error(name, e)
        
        print(f"[JARVIS MOBILE] 📤 {name} → {str(result)[:80]}")
        return types.FunctionResponse(
            id=fc.id, name=name,
            response={"result": result}
        )
    
    # Tool implementations (stubs to be filled in)
    async def _tool_web_search(self, args):
        """Web search implementation"""
        query = args.get("query", "")
        # Would integrate with duckduckgo-search or similar
        return f"Search results for: {query} (mobile search not fully implemented)"
    
    async def _tool_weather_report(self, args):
        """Weather report implementation"""
        city = args.get("city", "")
        # Would integrate with weather API
        return f"Weather for {city}: Mobile weather implementation pending"
    
    async def _tool_send_message(self, args):
        """Send message implementation"""
        receiver = args.get("receiver", "")
        message = args.get("message_text", "")
        platform = args.get("platform", "SMS")
        return f"Message to {receiver} via {platform}: {message} (implementation pending)"
    
    async def _tool_open_app(self, args):
        """Open app implementation"""
        app_name = args.get("app_name", "")
        return f"Opening {app_name} (mobile intent implementation pending)"
    
    async def _tool_file_access(self, args):
        """File access implementation"""
        action = args.get("action", "")
        path = args.get("path", "")
        return f"File {action} on {path} (mobile file access implementation pending)"
    
    async def _tool_camera_tool(self, args):
        """Camera tool implementation"""
        action = args.get("action", "")
        return f"Camera {action} (mobile camera implementation pending)"
    
    async def _send_realtime(self):
        """Send audio input to Gemini"""
        while True:
            msg = await self.out_queue.get()
            await self.session.send_realtime_input(media=msg)
    
    async def _listen_audio(self):
        """Listen to microphone input"""
        if not AUDIO_AVAILABLE:
            print("Audio not available on this platform")
            return
            
        print("[JARVIS MOBILE] 🎤 Mic started")
        loop = asyncio.get_event_loop()

        def callback(indata, frames, time_info, status):
            with self._speaking_lock:
                jarvis_speaking = self._is_speaking
            if not jarvis_speaking and not self.muted:
                data = indata.tobytes()
                loop.call_soon_threadsafe(
                    self.out_queue.put_nowait,
                    {"data": data, "mime_type": "audio/pcm"}
                )

        try:
            with sd.InputStream(
                samplerate=SEND_SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
                blocksize=CHUNK_SIZE,
                callback=callback,
            ):
                print("[JARVIS MOBILE] 🎤 Mic stream open")
                while True:
                    await asyncio.sleep(0.1)
        except Exception as e:
            print(f"[JARVIS MOBILE] ❌ Mic: {e}")
            raise
    
    async def _receive_audio(self):
        """Receive audio output from Gemini"""
        print("[JARVIS MOBILE] 👂 Recv started")
        out_buf, in_buf = [], []

        try:
            while True:
                async for response in self.session.receive():

                    if response.data:
                        if self._turn_done_event and self._turn_done_event.is_set():
                            self._turn_done_event.clear()
                        self.audio_in_queue.put_nowait(response.data)

                    if response.server_content:
                        sc = response.server_content

                        if sc.output_transcription and sc.output_transcription.text:
                            txt = _clean_transcript(sc.output_transcription.text)
                            if txt:
                                out_buf.append(txt)

                        if sc.input_transcription and sc.input_transcription.text:
                            txt = _clean_transcript(sc.input_transcription.text)
                            if txt:
                                in_buf.append(txt)

                        if sc.turn_complete:
                            if self._turn_done_event:
                                self._turn_done_event.set()

                            full_in = " ".join(in_buf).strip()
                            if full_in:
                                self.write_log(f"You: {full_in}")
                            in_buf = []

                            full_out = " ".join(out_buf).strip()
                            if full_out:
                                self.write_log(f"Jarvis: {full_out}")
                            out_buf = []

                    if response.tool_call:
                        fn_responses = []
                        for fc in response.tool_call.function_calls:
                            print(f"[JARVIS MOBILE] 📞 {fc.name}")
                            fr = await self._execute_tool(fc)
                            fn_responses.append(fr)
                        await self.session.send_tool_response(
                            function_responses=fn_responses
                        )
        except Exception as e:
            print(f"[JARVIS MOBILE] ❌ Recv: {e}")
            traceback.print_exc()
            raise
    
    async def _play_audio(self):
        """Play audio output"""
        if not AUDIO_AVAILABLE:
            return
        print("[JARVIS MOBILE] 🔊 Play started")

        stream = sd.RawOutputStream(
            samplerate=RECEIVE_SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=CHUNK_SIZE,
        )
        stream.start()

        try:
            while True:
                try:
                    chunk = await asyncio.wait_for(
                        self.audio_in_queue.get(),
                        timeout=0.5
                    )
                except asyncio.TimeoutError:
                    if self.audio_in_queue.empty():
                        self.set_speaking(False)
                        if self._turn_done_event and self._turn_done_event.is_set():
                            self._turn_done_event.clear()
                    continue
                self.set_speaking(True)
                stream.write(chunk)
        except Exception as e:
            print(f"[JARVIS MOBILE] ❌ Play: {e}")
            raise
        finally:
            self.set_speaking(False)
            stream.stop()
            stream.close()
    
    async def run(self):
        """Main run loop for the mobile assistant"""
        if not GENAI_AVAILABLE:
            print("Cannot run without Google Generative AI")
            return
            
        client = genai.Client(
            api_key=_get_api_key(),
            http_options={"api_version": "v1beta"}
        )
        
        while True:
            try:
                print("[JARVIS MOBILE] 🔌 Connecting...")
                app = self._get_app()
                if app and hasattr(app, "set_state"):
                    app.set_state("THINKING")
                
                config = self._build_config()
                
                async with (
                    client.aio.live.connect(model=LIVE_MODEL, config=config) as session,
                    asyncio.TaskGroup() as tg,
                ):
                    self.session = session
                    self._loop = asyncio.get_event_loop()
                    self.audio_in_queue = asyncio.Queue()
                    self.out_queue = asyncio.Queue(maxsize=10)
                    self._turn_done_event = asyncio.Event()
                    
                    print("[JARVIS MOBILE] ✅ Connected.")
                    if app and hasattr(app, "set_state"):
                        app.set_state("LISTENING")
                    self.write_log("SYS: JARVIS online.")
                    
                    # Start audio processing tasks
                    tg.create_task(self._send_realtime())
                    tg.create_task(self._listen_audio())
                    tg.create_task(self._receive_audio())
                    tg.create_task(self._play_audio())
                    
            except Exception as e:
                print(f"[JARVIS MOBILE] ⚠️ {e}")
                traceback.print_exc()
            finally:
                self.set_speaking(False)
                if app and hasattr(app, "set_state"):
                    app.set_state("THINKING")
                print("[JARVIS MOBILE] 🔄 Reconnecting in 3s...")
                await asyncio.sleep(3)
    
    def start(self):
        """Start the assistant in a background thread"""
        def run_assistant():
            asyncio.run(self.run())
        
        self.thread = threading.Thread(target=run_assistant, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the assistant"""
        # Implementation would signal threads to stop
        pass


# Simple memory fallback if memory manager not available
if not MEMORY_AVAILABLE:
    def load_memory():
        return {}
    
    def update_memory(data):
        pass
    
    def format_memory_for_prompt(memory):
        return ""