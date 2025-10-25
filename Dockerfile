# Use a lightweight Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY app/requirements.txt .

RUN pip install --upgrade pip setuptools wheel
# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY app/chatbot.py .

# Command to run the Streamlit application
CMD ["streamlit", "run", "chatbot.py", "--server.port=8501", "--server.address=0.0.0.0"]