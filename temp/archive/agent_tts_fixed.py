"""
Fixed TTS implementation for BusinessVoiceAgent
"""

def _create_tts(self):
    """Create TTS service with Silero as primary (reliable) and Cartesia as secondary."""
    import logging
    logger = logging.getLogger(__name__)
    
    # Start with Silero TTS as primary (free, local, no connection issues)
    try:
        logger.info("🔊 Initializing Silero TTS (primary - reliable and local)")
        # Try different Silero TTS configurations
        try:
            from livekit.plugins import silero
            return silero.TTS()
        except:
            from livekit.plugins import silero
            return silero.TTS(model="v3_en")
    except Exception as e:
        logger.warning(f"Silero TTS not available, trying Cartesia: {e}")
    
    # Try Cartesia TTS as secondary (high quality but connection issues)
    from config import config
    if hasattr(config, 'cartesia') and config.cartesia.api_key and config.cartesia.api_key.startswith("sk_car_"):
        try:
            logger.info("🔊 Initializing Cartesia TTS (secondary - high quality)")
            from livekit.plugins import cartesia
            return cartesia.TTS(
                api_key=config.cartesia.api_key,
                model="sonic-turbo",
                voice="bf0a246a-8642-498a-9950-80c35e9276b5",
                language="en",
            )
        except Exception as e:
            logger.warning(f"Cartesia TTS failed, trying ElevenLabs: {e}")
    
    # Try ElevenLabs as tertiary fallback
    if (hasattr(config, 'elevenlabs') and 
        config.elevenlabs.api_key and 
        config.elevenlabs.api_key != "ELEVENLABS_API_KEY" and
        len(config.elevenlabs.api_key) > 10):
        try:
            logger.info("🔊 Initializing ElevenLabs TTS (tertiary fallback)")
            from livekit.plugins import elevenlabs
            return elevenlabs.TTS(
                api_key=config.elevenlabs.api_key,
                voice="21m00Tcm4TlvDq8ikWAM",
                model="eleven_turbo_v2",
                stability=0.5,
                similarity_boost=0.8,
                style=0.2,
            )
        except Exception as e:
            logger.warning(f"ElevenLabs TTS failed: {e}")
    
    # Final fallback - basic Silero with different settings
    try:
        logger.info("🔊 Using basic Silero TTS (final fallback)")
        from livekit.plugins import silero
        return silero.TTS(model="v3_en")
    except Exception as e:
        logger.error(f"All TTS services failed: {e}")
        # Last resort - raise error with helpful message
        raise Exception(
            "No TTS service available. Please check your network connection and API keys."
        )