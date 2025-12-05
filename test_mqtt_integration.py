import asyncio
import json
import uuid
import os
from gmqtt import Client as MQTTClient

# Configuration
BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", 1883))

async def test_mqtt_integration():
    client = MQTTClient("test-client")
    
    await client.connect(BROKER_HOST, BROKER_PORT)
    print("Connected to broker.")
    
    # Subscribe to responses
    client.subscribe("agnss/response/#")
    
    # Future to store response
    response_future = asyncio.get_event_loop().create_future()
    
    def on_message(client, topic, payload, qos, properties):
        print(f"Received: {topic} -> {payload.decode()}")
        if not response_future.done():
            response_future.set_result(json.loads(payload.decode()))

    client.on_message = on_message
    
    # --- Test 1: Location Request ---
    request_id = str(uuid.uuid4())
    payload = {
        "mcc": 310, "mnc": 260, "lac": 51051, "cid": 44473, 
        "radio": "GSM", "request_id": request_id
    }
    print(f"Sending Location Request: {payload}")
    client.publish("agnss/request/location", json.dumps(payload))
    
    try:
        resp = await asyncio.wait_for(response_future, timeout=5.0)
        print("Location Response:", resp)
        assert resp['lat'] == 42.3588
        print("SUCCESS: Location Verified")
    except asyncio.TimeoutError:
        print("FAILURE: Location Request Timed Out")
        
    # Reset future for next test
    response_future = asyncio.get_event_loop().create_future()
    
    # --- Test 2: Nordic Ephemeris Request ---
    request_id = str(uuid.uuid4())
    payload = {"request_id": request_id}
    print(f"Sending Nordic Ephemeris Request: {payload}")
    client.publish("agnss/request/ephemeris/nordic", json.dumps(payload))
    
    try:
        resp = await asyncio.wait_for(response_future, timeout=10.0)
        print(f"Nordic Response Status: {resp.get('status')}")
        if 'data' in resp:
            print(f"Received {len(resp['data'])} satellite records.")
        assert resp['status'] == 'success'
        print("SUCCESS: Nordic Ephemeris Verified")
    except asyncio.TimeoutError:
        print("FAILURE: Nordic Ephemeris Request Timed Out")

    await client.disconnect()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_mqtt_integration())
