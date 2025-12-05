import asyncio
import json
import uuid
# We need an MQTT client for testing. gmqtt is a good async client.
# But for simplicity in this test script, we can use paho-mqtt if installed, 
# or just mock the interaction if we don't want to spin up a real broker.
# However, to truly verify, we need a broker.
# Since we can't easily spin up a broker in this environment without docker, 
# we will create a mock test that imports the server handlers directly 
# to verify logic, OR we can try to use a public test broker (risky/flaky).

# Better approach: Unit test the handlers by mocking the mqtt client.

from unittest.mock import MagicMock, AsyncMock
import server

async def test_mqtt_handlers():
    print("Testing MQTT Handlers...")
    
    # Mock the MQTT client in the server module
    server.mqtt.client = MagicMock()
    server.mqtt.client.publish = MagicMock()
    
    # Test Location Request
    request_id = str(uuid.uuid4())
    payload = {
        "mcc": 310, 
        "mnc": 260, 
        "lac": 51051, 
        "cid": 44473, 
        "radio": "GSM",
        "request_id": request_id
    }
    
    print(f"Simulating Location Request: {payload}")
    await server.handle_location_request(payload, request_id)
    
    # Verify publish was called
    server.mqtt.client.publish.assert_called()
    call_args = server.mqtt.client.publish.call_args
    topic, message = call_args[0]
    
    print(f"Published to Topic: {topic}")
    print(f"Message: {message}")
    
    assert topic == f"agnss/response/location/{request_id}"
    response = json.loads(message)
    assert response['lat'] == 42.3588
    print("SUCCESS: Location Request handled correctly.")

    # Test Ephemeris Request
    request_id = str(uuid.uuid4())
    payload = {"request_id": request_id}
    
    print(f"\nSimulating Ephemeris Request: {payload}")
    await server.handle_ephemeris_request(payload, request_id)
    
    # Verify publish
    call_args = server.mqtt.client.publish.call_args
    topic, message = call_args[0]
    
    print(f"Published to Topic: {topic}")
    print(f"Message: {message}")
    
    assert topic == f"agnss/response/ephemeris/{request_id}"
    response = json.loads(message)
    assert response['status'] == 'success'
    assert 'url' in response
    print("SUCCESS: Ephemeris Request handled correctly.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_mqtt_handlers())
