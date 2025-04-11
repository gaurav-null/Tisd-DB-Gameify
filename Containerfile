# Use an official Python runtime as the base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the entire project into the container
COPY .. .

# Copy the requirements file into the container
COPY ../requirements-linux.txt .

# Copy the container configuration ini file
COPY container.ini /app/config.ini

# Install dependencies
RUN pip install --no-cache-dir -r requirements-linux.txt

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["python", "main.py"]
