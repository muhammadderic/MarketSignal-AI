from enum import Enum


class LinkResolutionStatus(str, Enum):
    PENDING = "pending"
    RESOLVED = "resolved"
    FAILED = "failed"