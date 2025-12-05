# AGNSS Service

A lightweight, containerized service providing Assisted GNSS (A-GNSS) data for IoT devices. It acts as a bridge between your devices and public GNSS data sources, offering cell tower location lookup and parsed ephemeris data compatible with Nordic nRF9160 modems.

## Features

*   **Cell Tower Location**: Resolves Cell IDs (MCC, MNC, LAC, CID) to approximate Latitude/Longitude using OpenCellID data.
*   **Ephemeris Data**: Automatically fetches and caches the latest GPS broadcast ephemeris (RINEX) from IGS.
*   **Nordic Compatibility**: Parses raw RINEX data into the specific JSON format required by Nordic nRF9160 modems (`nrf_modem_gnss_agnss_write`).
*   **Dual Interface**: Supports both **HTTP** (REST) and **MQTT** protocols.
*   **Dockerized**: Ready for deployment on AWS App Runner, ECS, or any Docker-compatible environment.

## Getting Started

### Prerequisites

*   **Docker** (for running the service)
*   **Python 3.9+** (for local development/testing)

### Installation & Running (Docker)

1.  **Build the Image**
    ```bash
    docker build -t agnss-service .
    ```

2.  **Run (HTTP Only)**
    ```bash
    docker run -d -p 8000:8000 --name agnss-service agnss-service
    ```

3.  **Run (HTTP + MQTT)**
    *Requires an MQTT broker (e.g., Mosquitto, AWS IoT Core).*
    ```bash
    docker run -d -p 8000:8000 \
      -e ENABLE_MQTT=true \
      -e MQTT_BROKER_HOST=host.docker.internal \
      -e MQTT_BROKER_PORT=1883 \
      agnss-service
    ```

## Configuration

The service is configured via environment variables:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `ENABLE_MQTT` | `false` | Set to `true` to enable MQTT client. |
| `MQTT_BROKER_HOST` | `localhost` | Hostname/IP of the MQTT broker. |
| `MQTT_BROKER_PORT` | `1883` | Port of the MQTT broker. |
| `MQTT_USERNAME` | `None` | MQTT username (optional). |
| `MQTT_PASSWORD` | `None` | MQTT password (optional). |
| `HOST_IP` | `localhost` | Public IP/Hostname used in download URLs. |

## Usage

### HTTP API

*   **Get Location**
    *   `POST /location`
    *   Body: `{"mcc": 310, "mnc": 410, "lac": 12345, "cid": 67890, "radio": "GSM"}`
*   **Get Raw Ephemeris**
    *   `GET /ephemeris/current`
    *   Returns: Gzipped RINEX file.
*   **Get Nordic Ephemeris**
    *   `GET /ephemeris/nordic`
    *   Returns: JSON list of satellite records for nRF9160.

### MQTT Interface

The service subscribes to `agnss/request/#` and publishes to `agnss/response/#`.

*   **Location Request**
    *   Topic: `agnss/request/location`
    *   Payload: `{"request_id": "uuid", "mcc": 310, ...}`
    *   Response: `agnss/response/location/{request_id}`
*   **Nordic Ephemeris Request**
    *   Topic: `agnss/request/ephemeris/nordic`
    *   Payload: `{"request_id": "uuid"}`
    *   Response: `agnss/response/ephemeris/nordic/{request_id}`

## Deployment

This service is designed to be stateless and scalable.

*   **Recommended**: AWS App Runner (Auto-scaling container service).
*   **Guide**: See [aws_deployment.md](aws_deployment.md) for detailed deployment instructions.

## Development

To run locally without Docker:

1.  Create a virtual environment: `python -m venv venv`
2.  Install dependencies: `pip install -r requirements.txt`
3.  Initialize DB (if needed): `python database.py`
4.  Run server: `python server.py`
