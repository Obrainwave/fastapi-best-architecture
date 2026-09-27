import time

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.core.config import settings

_serializer = URLSafeTimedSerializer(settings.STREAM_TOKEN_SECRET)


def issue_stream_token(user_id: str, video_id: str) -> str:
    return _serializer.dumps({"uid": user_id, "vid": video_id, "iat": int(time.time())})


def verify_stream_token(token: str, video_id: str) -> str:
    try:
        payload = _serializer.loads(token, max_age=settings.STREAM_TOKEN_TTL_SECONDS)
    except SignatureExpired:
        raise ValueError("Stream session expired, request a new one")
    except BadSignature:
        raise ValueError("Invalid stream token")

    if payload["vid"] != video_id:
        raise ValueError("Token is not valid for this video")

    return payload["uid"]