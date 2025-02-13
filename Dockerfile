# Use an official Python runtime as a parent image (Linux)
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install required packages
RUN pip install --no-cache-dir -r requirements.txt

# Install Airflow & Supervisor
RUN pip install apache-airflow apache-airflow-providers-mysql supervisor

# Initialize Airflow DB
RUN airflow db init

# Expose required ports
EXPOSE 5000 8080

# Copy Supervisor configuration file
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Start Supervisor
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]