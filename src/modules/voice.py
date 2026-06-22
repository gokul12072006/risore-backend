import subprocess
import os

def speak(text: str):
    """
    Voice Assistant module.
    Primary: ElevenLabs (Requires API key to be set in environment variables).
    Fallback: System native TTS.
    """
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    if elevenlabs_api_key:
        try:
            from elevenlabs import generate, play, set_api_key
            set_api_key(elevenlabs_api_key)
            audio = generate(
                text=text,
                voice="Rachel",
                model="eleven_monolingual_v1"
            )
            play(audio)
            return
        except ImportError:
            pass
        except Exception as e:
            print(f"Voice generation failed: {e}")
            
    # Fallback to local Windows TTS
    try:
        clean_text = text.replace('"', '').replace('\n', ' ')
        script = f'Add-Type -AssemblyName System.speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{clean_text[:200]}")'
        subprocess.run(["powershell", "-Command", script], capture_output=True, text=True)
    except Exception:
        pass
