import os
import sys
import subprocess
import asyncio
import shutil

async def convert_wav_to_ogg(wav_path: str, ogg_path: str) -> bool:
    """
    Convert a WAV file to OGG Opus using ffmpeg.
    Telegram Requires OGG Opus for native voice notes (voice/ogg).
    """
    # Find ffmpeg in PATH; on Windows also check the WinGet install location
    ffmpeg_cmd = shutil.which("ffmpeg")
    if not ffmpeg_cmd:
        if sys.platform == "win32":
            winget_path = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe")
            ffmpeg_cmd = winget_path if os.path.exists(winget_path) else "ffmpeg.exe"
        else:
            ffmpeg_cmd = "ffmpeg"
    
    cmd = [
        ffmpeg_cmd,
        "-y",               # Overwrite output files without asking
        "-i", wav_path,     # Input file
        "-c:a", "libopus",  # Codec
        "-b:a", "32k",      # Bitrate
        "-vbr", "on",       # Variable bitrate
        "-compression_level", "10", 
        "-frame_duration", "60", 
        "-application", "voip", 
        ogg_path            # Output file
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    _, stderr = await process.communicate()
    
    if process.returncode != 0:
        print(f"FFmpeg error: {stderr.decode()}")
        return False
        
    return True