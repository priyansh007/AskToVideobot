FROM python:3.11.7 as app
WORKDIR /application
COPY /application/ /application/
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip 
RUN pip install -r requirement.txt
EXPOSE 8501
CMD ["streamlit","run","frontend.py","--server.port","8501","--server.address", "0.0.0.0"]