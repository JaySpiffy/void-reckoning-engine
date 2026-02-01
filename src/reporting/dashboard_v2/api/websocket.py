import asyncio
import json
import logging
import time
from typing import List, Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from src.reporting.dashboard_v2.api.models import (
    WSMessage, WSStatusUpdate, WSMetricsUpdate, WSEventStream, 
    WSErrorNotification, WSPingPong, WSResponse, WSAlertTriggered
)
from src.reporting.dashboard_v2.api.config import settings

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Manages active WebSocket connections and handles broadcasting.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients."""
        async with self._lock:
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send message to client: {e}")
                    disconnected.append(connection)
            
            # Cleanup failed connections
            for conn in disconnected:
                if conn in self.active_connections:
                    self.active_connections.remove(conn)

    async def send_personal(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")

manager = ConnectionManager()

async def broadcast_metrics_loop(service):
    """Background task to periodically broadcast live metrics."""
    logger.info("Starting background metrics broadcast loop")
    while True:
        try:
            if manager.active_connections:
                metrics = service.get_live_metrics()
                if metrics:
                    msg = WSMetricsUpdate(data=metrics).dict()
                    await manager.broadcast(msg)
            await asyncio.sleep(settings.METRICS_UPDATE_INTERVAL)
        except asyncio.CancelledError:
            logger.info("Metrics broadcast loop cancelled")
            break
        except Exception as e:
            logger.error(f"Error in metrics broadcast loop: {e}")
            await asyncio.sleep(5)

async def ping_loop(websocket: WebSocket):
    """Health check loop for a specific WebSocket connection."""
    try:
        while True:
            await asyncio.sleep(settings.WEBSOCKET_PING_INTERVAL)
            ping_msg = WSPingPong(type="ping").dict()
            await websocket.send_json(ping_msg)
            # Logic for timeout/pong verification could be added here
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.debug(f"Ping loop terminated for client: {e}")

async def websocket_endpoint(websocket: WebSocket, service):
    """
    Main WebSocket handler for /ws.
    """
    await manager.connect(websocket)
    
    # 1. Enable Telemetry Streaming for this connection
    if service.telemetry:
        service.telemetry.enable_streaming()
        logger.info("Enabled telemetry streaming for new WebSocket connection")
    
    # 2. Send Initial Snapshot
    # 2. Send Initial Snapshot
    try:
        status = service.get_status()
        status["streaming"] = service.telemetry is not None
        initial_msg = WSStatusUpdate(data=status).dict()
        await websocket.send_json(initial_msg)
        
        # FIX: Send initial Metrics immediately so UI doesn't wait for broadcast loop
        metrics = service.get_live_metrics()
        if metrics:
            metrics_msg = WSMetricsUpdate(data=metrics).dict()
            await websocket.send_json(metrics_msg)
            
    except Exception as e:
        logger.error(f"Failed to send initial snapshot: {e}")

    # 3. Capture running loop for thread-safe callback dispatch
    loop = asyncio.get_running_loop()

    # 4. Subscribe to Telemetry Stream
    def telemetry_callback(event: Dict[str, Any]):
        """Callback for real-time telemetry events."""
        # Map categories to specific event types for contract parity
        category = event.get("category")
        event_type = "event_stream"
        
        if category == "combat":
            event_type = "battle_event"
        elif category == "economy":
            event_type = "resource_event"
        elif category == "technology":
            event_type = "tech_event"
        elif category == "construction":
            event_type = "construction_event"
        elif category == "system":
            event_type = "system_event"
        
        # Convert to WS format with mapped type
        ws_event = {
            "type": event_type,
            "timestamp": time.time(),
            "data": event
        }
        
        # Dispatch to the event loop thread from whichever thread the telemetry collector is on
        try:
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(manager.broadcast(ws_event), loop)
        except Exception as e:
             logger.error(f"Failed to dispatch telemetry event to WebSocket: {e}")

    if service.telemetry:
        service.telemetry.subscribe(telemetry_callback)
        logger.info("Subscribed WebSocket to telemetry stream")

    # 4.5. Subscribe to Alerts
    def alert_callback(alert):
        """Callback for real-time alerts."""
        ws_alert = {
            "type": "alert_triggered",
            "timestamp": time.time(),
            "data": alert.to_dict()
        }
        try:
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(manager.broadcast(ws_alert), loop)
        except Exception as e:
            logger.error(f"Failed to dispatch alert to WebSocket: {e}")

    try:
        from src.reporting.alert_manager import AlertManager
        alert_manager = AlertManager()
        if alert_manager.notification_manager:
            # We use a custom attribute to track if the singleton already has a broadcast hook
            # but for FastAPI, we want to broadcast to the modern ConnectionManager.
            # Multiple connections will share this singleton-level callback, which is fine
            # as manager.broadcast() handles the collection of active websockets.
            alert_manager.notification_manager.set_external_callback(alert_callback)
            logger.info("Subscribed WebSocket to alert stream")
    except Exception as e:
        logger.error(f"Failed to subscribe to alert manager: {e}")

    # 5. Start Connection-Specific Tasks
    ping_task = asyncio.create_task(ping_loop(websocket))

    try:
        while True:
            # Handle incoming messages
            data = await websocket.receive_text()
            try:
                msg_json = json.loads(data)
                msg_type = msg_json.get("type")
                
                if msg_type == "pong":
                    # logger.debug("Received pong from client")
                    pass
                elif msg_type == "request_snapshot":
                    metrics = service.get_live_metrics()
                    response = WSResponse(type="snapshot", data=metrics).dict()
                    await websocket.send_json(response)
                elif msg_type == "ping_check":
                    await websocket.send_json({"type": "pong", "timestamp": time.time()})
                
            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON from client: {data}")
            except Exception as e:
                logger.error(f"Error processing client message: {e}")

    except WebSocketDisconnect:
        logger.info("WebSocket disconnect signal received")
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        # Cleanup
        ping_task.cancel()
        if service.telemetry:
            service.telemetry.unsubscribe(telemetry_callback)
            logger.info("Unsubscribed WebSocket from telemetry stream")
            
            # Disable streaming if no more connections
            if not manager.active_connections:
                service.telemetry.disable_streaming()
                logger.info("Disabled telemetry streaming (no active WebSocket connections)")
                
                # Cleanup global alert hook if no more connections
                try:
                    from src.reporting.alert_manager import AlertManager
                    am = AlertManager()
                    if am.notification_manager and am.notification_manager.external_callback == alert_callback:
                        am.notification_manager.set_external_callback(None)
                        logger.info("Cleaned up global alert broadcast hook")
                except:
                    pass
                
        await manager.disconnect(websocket)
