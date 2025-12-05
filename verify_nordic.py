import asyncio
import json
import uuid
from unittest.mock import MagicMock
import server
import rinex_parser
import os

async def test_nordic_handlers():
    print("Testing Nordic Compatibility Handlers...")
    
    # Mock the MQTT client in the server module
    server.mqtt.client = MagicMock()
    server.mqtt.client.publish = MagicMock()
    
    # Ensure we have a dummy file to parse if download fails
    # (The fetcher creates one, but the parser needs valid RINEX structure)
    # We'll create a minimal valid RINEX file for testing
    os.makedirs("ephemeris_data", exist_ok=True)
    dummy_rinex = "ephemeris_data/test_rinex.n"
    with open(dummy_rinex, "w") as f:
        f.write("""     2.10           N: GPS NAV DATA                         RINEX VERSION / TYPE
                                                            END OF HEADER
 1 25 12 04 12 00 00.0-4.600000000000E-04-1.000000000000E-11 0.000000000000E+00
    1.000000000000E+02 2.000000000000E+02 4.000000000000E-09 1.500000000000E+00
    3.000000000000E-06 5.000000000000E-03 6.000000000000E-06 5.153700000000E+03
    4.320000000000E+05 8.000000000000E-08-2.000000000000E+00 9.000000000000E-08
    9.500000000000E-01 2.500000000000E+02 1.500000000000E+00-7.000000000000E-09
    5.000000000000E-10 0.000000000000E+00 2.395000000000E+03 0.000000000000E+00
    2.000000000000E+00 0.000000000000E+00-5.000000000000E-09 1.000000000000E+02
    0.000000000000E+00 0.000000000000E+00 0.000000000000E+00 0.000000000000E+00
""")
    
    # Mock the fetcher to return our dummy file
    server.ephemeris_fetcher.fetch_daily_gps_ephemeris = MagicMock(return_value=dummy_rinex)

    # Test Nordic Ephemeris Request via MQTT
    request_id = str(uuid.uuid4())
    payload = {"request_id": request_id}
    
    print(f"Simulating Nordic Ephemeris Request: {payload}")
    await server.handle_nordic_ephemeris_request(payload, request_id)
    
    # Verify publish
    server.mqtt.client.publish.assert_called()
    call_args = server.mqtt.client.publish.call_args
    topic, message = call_args[0]
    
    print(f"Published to Topic: {topic}")
    # print(f"Message: {message}") # Too large to print
    
    assert topic == f"agnss/response/ephemeris/nordic/{request_id}"
    response = json.loads(message)
    assert response['status'] == 'success'
    assert 'data' in response
    assert len(response['data']) > 0
    
    # Check parsed fields
    sat1 = response['data'][0]
    print(f"Parsed Satellite Data: {sat1}")
    assert sat1['sv_id'] == 1
    assert sat1['iode'] == 100
    assert sat1['sqrt_a'] == 5153.7
    
    print("SUCCESS: Nordic Ephemeris Request handled correctly.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_nordic_handlers())
