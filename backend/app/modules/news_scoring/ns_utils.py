from fastapi import HTTPException, status


def validate_batch_size(
    payload: list,
    min_size: int = 10,
    max_size: int = 20,
) -> bool:
    """
    Validate that a batch payload's list size is within the allowed range.
    
    Args:
        payload: List to validate.
        min_size: Minimum acceptable length (inclusive).
        max_size: Maximum acceptable length (inclusive).
        
    Returns:
        True if payload size is valid.
        
    Raises:
        HTTPException: 400 if payload size is outside the allowed range.
    """
    size = len(payload)
    if size < min_size or size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid size: received {size} items. "
                f"Expected between {min_size} and {max_size}."
            )
        )
    return True
    