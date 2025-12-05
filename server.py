from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import database
import ephemeris_fetcher
import os
from fastapi.responses import FileResponse
from fastapi_mqtt import FastMQTT, MQTTConfig
import json
import rinex_parser

# MQTT Configuration
# In a real deployment, these would come from environment variables
mqtt_config = MQTTConfig(
    host=os.getenv("MQTT_BROKER_HOST", "localhost"),
    port=int(os.getenv("MQTT_BROKER_PORT", 1883)),
    keepalive=60,
    username=os.getenv("MQTT_USERNAME"),
    password=os.getenv("MQTT_PASSWORD"),
)

mqtt = FastMQTT(config=mqtt_config)

class CellQuery(BaseModel):
    mcc: int
    mnc: int
    lac: int
    cid: int
    radio: Optional[str] = "GSM"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    database.init_db()
    if os.getenv("ENABLE_MQTT", "false").lower() == "true":
        # Hack: Re-create asyncio Event on the current loop to avoid mismatch
        import asyncio
        mqtt.client._connected = asyncio.Event()
        await mqtt.mqtt_startup()
    yield
    # Shutdown
    if os.getenv("ENABLE_MQTT", "false").lower() == "true":
        await mqtt.mqtt_shutdown()

app = FastAPI(title="Local AGNSS Service", lifespan=lifespan)

# Remove the old init_app call and startup event
# if os.getenv("ENABLE_MQTT", "false").lower() == "true":
#     mqtt.init_app(app) 
# @app.on_event("startup") ...

@mqtt.on_connect()
def connect(client, flags, rc, properties):
    print(f"Connected to MQTT Broker: {client} flags={flags} rc={rc} properties={properties}")
    # Subscribe to topics
    mqtt.client.subscribe("agnss/request/location")
    mqtt.client.subscribe("agnss/request/ephemeris")
    mqtt.client.subscribe("agnss/request/ephemeris/nordic")
    print("Subscribed to agnss/request/#")

@mqtt.on_message()
async def message(client, topic, payload, qos, properties):
    print(f"Received message: {topic}, payload: {payload.decode()}")
    
    try:
        data = json.loads(payload.decode())
        request_id = data.get("request_id")
        
        if not request_id:
            print("Error: No request_id in payload")
            return

        if topic == "agnss/request/location":
            await handle_location_request(data, request_id)
        elif topic == "agnss/request/ephemeris":
            await handle_ephemeris_request(data, request_id)
        elif topic == "agnss/request/ephemeris/nordic":
            await handle_nordic_ephemeris_request(data, request_id)
            
    except Exception as e:
        print(f"Error processing MQTT message: {e}")

async def handle_location_request(data, request_id):
    try:
        mcc = data.get("mcc")
        mnc = data.get("mnc")
        lac = data.get("lac")
        cid = data.get("cid")
        radio = data.get("radio", "GSM")
        
        result = database.get_cell_location(mcc, mnc, lac, cid, radio)
        if not result:
             # Try without radio type
            result = database.get_cell_location(mcc, mnc, lac, cid)
            
        response_topic = f"agnss/response/location/{request_id}"
        
        if result:
            mqtt.client.publish(response_topic, json.dumps(result))
            print(f"Published location to {response_topic}")
        else:
            mqtt.client.publish(response_topic, json.dumps({"error": "Not found"}))
            print(f"Published error to {response_topic}")
            
    except Exception as e:
        print(f"Error handling location request: {e}")

async def handle_ephemeris_request(data, request_id):
    try:
        # Check freshness logic is handled inside fetcher now
        file_path = ephemeris_fetcher.fetch_daily_gps_ephemeris()
        response_topic = f"agnss/response/ephemeris/{request_id}"
        
        if file_path and os.path.exists(file_path):
            # Construct a download URL
            # In production, this should be the public DNS/IP
            # For local/container, we assume standard port 8000
            host_ip = os.getenv("HOST_IP", "localhost") 
            download_url = f"http://{host_ip}:8000/ephemeris/current"
            
            response_payload = {
                "status": "success",
                "url": download_url,
                "filename": os.path.basename(file_path),
                "size": os.path.getsize(file_path)
            }
            mqtt.client.publish(response_topic, json.dumps(response_payload))
            print(f"Published ephemeris URL to {response_topic}")
        else:
            mqtt.client.publish(response_topic, json.dumps({"status": "error", "message": "Unavailable"}))
            
    except Exception as e:
        print(f"Error handling ephemeris request: {e}")

async def handle_nordic_ephemeris_request(data, request_id):
    try:
        file_path = ephemeris_fetcher.fetch_daily_gps_ephemeris()
        response_topic = f"agnss/response/ephemeris/nordic/{request_id}"
        
        if file_path and os.path.exists(file_path):
            # Parse the RINEX file
            ephemeris_list = rinex_parser.parse_rinex_nav(file_path)
            
            # Send the parsed data
            mqtt.client.publish(response_topic, json.dumps({"status": "success", "data": ephemeris_list}))
            print(f"Published Nordic ephemeris data to {response_topic}")
        else:
            mqtt.client.publish(response_topic, json.dumps({"status": "error", "message": "Unavailable"}))
            
    except Exception as e:
        print(f"Error handling Nordic ephemeris request: {e}")

@app.post("/location")
async def get_location(query: CellQuery):
    """
    Get approximate location (lat, lon) for a given Cell ID.
    """
    result = database.get_cell_location(query.mcc, query.mnc, query.lac, query.cid, query.radio)
    if result:
        return result
    
    # Try without radio type if specific one fails
    result = database.get_cell_location(query.mcc, query.mnc, query.lac, query.cid)
    if result:
        return result
        
    raise HTTPException(status_code=404, detail="Cell tower not found")

@app.get("/ephemeris/current")
async def get_current_ephemeris():
    """
    Get the latest GPS broadcast ephemeris file.
    Triggers a fetch if not already cached.
    """
    file_path = ephemeris_fetcher.fetch_daily_gps_ephemeris()
    if file_path and os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/gzip", filename=os.path.basename(file_path))
    
    raise HTTPException(status_code=503, detail="Ephemeris data unavailable")

@app.get("/ephemeris/nordic")
async def get_nordic_ephemeris():
    """
    Get parsed ephemeris data in JSON format suitable for Nordic nRF9160.
    """
    file_path = ephemeris_fetcher.fetch_daily_gps_ephemeris()
    if file_path and os.path.exists(file_path):
        data = rinex_parser.parse_rinex_nav(file_path)
        return {"status": "success", "data": data}
    
    raise HTTPException(status_code=503, detail="Ephemeris data unavailable")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
