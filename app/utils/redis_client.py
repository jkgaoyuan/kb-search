import redis
from app.config import get_settings

_settings = get_settings()

# Shared redis client for caching/suggestions
redis_client = redis.from_url(
    _settings.redis_url,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    health_check_interval=30,
)
