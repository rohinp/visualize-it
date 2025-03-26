import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional

from services.logging_service import LoggingService

logger = logging.getLogger("visualize-it")

router = APIRouter(prefix="/logs", tags=["logs"])



# Dependency for services
def get_logging_service():
    return LoggingService()



@router.get("/server")
async def get_server_logs(
    max_lines: Optional[int] = 1000,
    logging_service: LoggingService = Depends(get_logging_service)
):
    """
    Get server logs
    """
    logger.info(f"Retrieving server logs (max_lines={max_lines})")
    logs = logging_service.get_server_logs(max_lines)
    return {"logs": logs}



@router.post("/server/clear")
async def clear_server_logs(
    logging_service: LoggingService = Depends(get_logging_service)
):
    """
    Clear server logs
    """
    logger.info("Clearing server logs")
    success = logging_service.clear_server_logs()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to clear server logs")
    return {"status": "success"}



@router.get("/client")
async def get_client_logs(
    max_lines: Optional[int] = 1000,
    logging_service: LoggingService = Depends(get_logging_service)
):
    """
    Get client logs
    """
    logger.info(f"Retrieving client logs (max_lines={max_lines})")
    logs = logging_service.get_client_logs(max_lines)
    return {"logs": logs}



@router.post("/client/clear")
async def clear_client_logs(
    logging_service: LoggingService = Depends(get_logging_service)
):
    """
    Clear client logs
    """
    logger.info("Clearing client logs")
    success = logging_service.clear_client_logs()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to clear client logs")
    return {"status": "success"}

@router.post("/client")
async def log_client_message(
    log_data: Dict[str, Any],
    logging_service: LoggingService = Depends(get_logging_service)
):
    """
    Log a message from the client
    """
    success = logging_service.log_client_message(log_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to log client message")
    return {"status": "success"}
