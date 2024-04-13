# Use an official Python runtime as a parent image
FROM python:3.9

# Set environment variables
ENV FLASK_ENV=production

# Set the working directory in the container
WORKDIR /opt/app

# Copy the requirements into working directory before the rest of app code so we take advantage of docker layer caching
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app code into working dir
COPY . .

# Expose the port Flask runs on
EXPOSE 8000

# Run the Flask app using python run.py
CMD ["python", "run.py"]
