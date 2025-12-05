# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (if any needed for sqlite)
# sqlite3 is usually included in python-slim, but we can ensure it
RUN apt-get update && apt-get install -y sqlite3 && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Initialize the database (if not already present)
# Note: In production, you might want to mount a volume for the DB
# or run the import script as part of the startup if the DB is ephemeral.
# For this container, we assume the DB is either built or mounted.
# We'll add a startup script to handle initialization if needed.

# Expose port 8000
EXPOSE 8000

# Run server.py when the container launches
CMD ["python", "server.py"]
