"""
packet_processor.py — Validates and routes incoming audio packets to session buffers.
"""
import time
from backend.app.realtime.schemas.audio_packet import AudioPacket
from backend.app.realtime.audio.chunk_buffer import buffer_registry
from backend.app.realtime.audio.audio_utils import decode_audio, is_valid_pcm16
from backend.app.realtime.monitoring.latency_tracker import latency_tracker
from backend.app.realtime.monitoring.stream_logger import stream_logger


async def process_audio_packet(packet: AudioPacket) -> bool:
    """
    Decode, validate, and buffer an incoming audio packet.
    Returns True on success, False on validation failure.
    """
    receive_time = time.time()
    transport_latency = (receive_time - packet.timestamp) * 1000  # ms

    latency_tracker.record(packet.session_id, transport_latency)
    stream_logger.log_packet_received(packet.session_id, packet.chunk_id, transport_latency)

    try:
        raw = decode_audio(packet.audio_data)
    except Exception:
        stream_logger.log_packet_dropped(packet.session_id, packet.chunk_id, "base64_decode_error")
        return False

    if not is_valid_pcm16(raw):
        stream_logger.log_packet_dropped(packet.session_id, packet.chunk_id, "invalid_pcm16")
        return False

    buf = await buffer_registry.get_or_create(packet.session_id)
    accepted = await buf.push(packet.chunk_id, raw)

    if not accepted:
        stream_logger.log_packet_dropped(packet.session_id, packet.chunk_id, "out_of_order")

    return accepted
