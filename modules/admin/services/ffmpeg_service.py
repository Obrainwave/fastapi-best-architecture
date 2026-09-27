# app/services/ffmpeg_service.py
import json
import os
import subprocess
from dataclasses import dataclass


@dataclass
class ProbeResult:
    duration_seconds: float
    width: int
    height: int


@dataclass
class LadderEntry:
    label: str
    height: int
    bitrate_kbps: int


@dataclass
class RenditionResult:
    bandwidth: int
    width: int
    height: int


RENDITION_LADDER = [
    LadderEntry(label="1080p", height=1080, bitrate_kbps=5000),
    LadderEntry(label="720p", height=720, bitrate_kbps=2800),
    LadderEntry(label="480p", height=480, bitrate_kbps=1400),
    LadderEntry(label="240p", height=240, bitrate_kbps=600),
]


def probe_video(path: str) -> ProbeResult:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-show_entries", "format=duration",
         "-of", "json", path],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout)
    stream = data["streams"][0]
    return ProbeResult(
        duration_seconds=float(data["format"]["duration"]),
        width=int(stream["width"]), height=int(stream["height"]),
    )


def generate_encrypted_hls_rendition(
    source_path: str, output_dir: str, ladder_entry: LadderEntry, encryption_key: bytes,
) -> RenditionResult:
    key_path = os.path.join(output_dir, "key.bin")
    with open(key_path, "wb") as f:
        f.write(encryption_key)

    key_info_path = os.path.join(output_dir, "key_info.txt")
    with open(key_info_path, "w") as f:
        # Line 1 is written verbatim into the manifest's EXT-X-KEY URI. It's a
        # placeholder, rewritten to a real token-bearing URL at request time in
        # the streaming API, so the raw key path never leaves this worker.
        f.write("KEY_PLACEHOLDER\n")
        f.write(f"{key_path}\n")

    playlist_path = os.path.join(output_dir, "playlist.m3u8")
    segment_pattern = os.path.join(output_dir, "segment_%04d.ts")

    # subprocess.run with a list, never shell=True, filenames coming from user
    # uploads should never be interpolated into a shell string.
    subprocess.run(
        ["ffmpeg", "-y", "-i", source_path,
         "-vf", f"scale=-2:{ladder_entry.height}",
         "-c:v", "libx264", "-preset", "veryfast", "-b:v", f"{ladder_entry.bitrate_kbps}k",
         "-c:a", "aac", "-b:a", "128k",
         "-hls_time", "6", "-hls_playlist_type", "vod",
         "-hls_key_info_file", key_info_path,
         "-hls_segment_filename", segment_pattern,
         playlist_path],
        check=True, capture_output=True,
    )

    os.remove(key_path)
    os.remove(key_info_path)

    return RenditionResult(
        bandwidth=ladder_entry.bitrate_kbps * 1000,
        width=int(ladder_entry.height * 16 / 9), height=ladder_entry.height,
    )


def generate_thumbnail(source_path: str, output_dir: str, at_seconds: float) -> str:
    thumb_path = os.path.join(output_dir, "thumbnail.jpg")
    subprocess.run(
        ["ffmpeg", "-y", "-ss", str(at_seconds), "-i", source_path,
         "-frames:v", "1", "-q:v", "2", thumb_path],
        check=True, capture_output=True,
    )
    return thumb_path