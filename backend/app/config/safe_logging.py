"""Log failure categories without serializing potentially credential-bearing payloads."""
import logging

logger = logging.getLogger(__name__)


def log_discarded_event(_event, stage: str) -> None:
    safe_stage = stage if stage in {"parse", "normalize", "readiness"} else "unknown"
    logger.warning("Pipeline event discarded (%s)", safe_stage)
