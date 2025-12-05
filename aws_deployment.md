# AWS Deployment Guide (Container)

This guide details how to deploy the AGNSS service as a **Docker Container** on **AWS App Runner**. This is the recommended approach for your workload (1500 IoT devices) as it requires zero code changes and provides predictable scaling.

## 1. Build and Push Image

1.  **Create an ECR Repository**:
    ```bash
    aws ecr create-repository --repository-name agnss-service
    ```
2.  **Login to ECR**:
    ```bash
    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.us-east-1.amazonaws.com
    ```
3.  **Build & Push**:
    *   *Note: Ensure you have run `python database.py` locally first to populate `agnss.db`.*
    ```bash
    docker build -t agnss-service .
    docker tag agnss-service:latest <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/agnss-service:latest
    docker push <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/agnss-service:latest
    ```

## 2. Deploy to AWS App Runner

1.  Go to the **AWS App Runner** console.
2.  Click **Create Service**.
3.  Source: **Container Registry** -> **Amazon ECR**.
4.  Select the `agnss-service` image you just pushed.
5.  **Configuration**:
    *   **Port**: `8000`
    *   **CPU/Memory**: `1 vCPU / 2 GB` (Sufficient for ~100 concurrent requests).
    *   **Environment Variables** (Add these for MQTT):
        *   `MQTT_BROKER_HOST`: `your-broker-url.com`
        *   `MQTT_BROKER_PORT`: `1883`
        *   `MQTT_USERNAME`: `your-user`
        *   `MQTT_PASSWORD`: `your-pass`
6.  **Deploy**.

## 3. Scaling Strategy

App Runner scales automatically based on traffic.

*   **Trigger**: **Concurrency** (Active requests at the same time).
*   **Recommended Settings**:
    *   **Max Concurrency**: `100` (Spin up a new instance if >100 devices hit at once).
    *   **Max Instances**: `5` (Safety limit to prevent runaway costs).

## 4. Maintenance & Updates

### Ephemeris Data (Automated)
*   **Mechanism**: The service automatically downloads fresh data from IGS every hour.
*   **Storage**: Ephemeral (inside container). If the container restarts, it just re-downloads the file. No action needed.

### Cell Tower Data (Manual Update)
*   **Frequency**: Quarterly or when you get new data.
*   **Procedure**:
    1.  Download new CSVs locally.
    2.  Run `python database.py` to update `agnss.db`.
    3.  Re-build and push the Docker image.
    4.  App Runner will automatically deploy the update.

## 5. Cost Estimate
*   **App Runner**: ~$25.00 / month (per active instance).
*   **Data Transfer**: Minimal (mostly text/JSON).
