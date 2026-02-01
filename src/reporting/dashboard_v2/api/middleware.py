import time
import logging
import traceback
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging request/response info and timing.
    Mirroring the logic of Flask's @log_route_call decorator.
    """
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        method = request.method
        path = request.url.path
        query_params = str(request.query_params)
        
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            
            status_code = response.status_code
            log_msg = f"{method} {path} - {status_code} ({process_time:.2f}ms)"
            if query_params:
                log_msg += f" Params: {query_params}"
            
            # Use appropriate log level
            if status_code >= 500:
                logger.error(log_msg)
            elif status_code >= 400:
                logger.warning(log_msg)
            else:
                logger.info(log_msg)
                
            # Warn on slow requests
            if process_time > 1000:
                logger.warning(f"SLOW REQUEST: {method} {path} took {process_time:.2f}ms")
                
            return response
            
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(f"EXCEPTION in {method} {path}: {str(e)} ({process_time:.2f}ms)")
            logger.error(traceback.format_exc())
            raise e
