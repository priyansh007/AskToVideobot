import json
import boto3
import moviepy.editor as mp
from pydub import AudioSegment
import os
import shutil

def query_endpoint(endpoint_name,body, content_type):
    client = boto3.client('runtime.sagemaker')
    response = client.invoke_endpoint(EndpointName=endpoint_name, ContentType=content_type, Body=body)
    model_predictions = json.loads(response['Body'].read())
    text = model_predictions['text']
    return text

def download_from_s3(bucket, key, local_file):
    s3_client = boto3.client("s3")
    s3_client.download_file(bucket, key, local_file)

def upload_to_s3(local_file, key, bucket="speech-to-text-meetsummarizar"):
    s3_client = boto3.client("s3")
    s3_client.upload_file(local_file, bucket, key)

def convert_mp4_to_wav(input_file, output_file):
    video_clip = mp.VideoFileClip(input_file)
    audio_clip = video_clip.audio
    audio_clip.write_audiofile(output_file)
    os.remove(input_file)

def convert_audio_to_wav(input_file, output_file):
    try:
        audio = AudioSegment.from_file(input_file)
        audio.export(output_file, format="wav")
        os.remove(input_file)
        print(f"Conversion successful. WAV file saved as {output_file}")
        return True
    except Exception as e:
        print("Error occured at converting audio to wav")
        return False
    
def delete_folder(folder_path):
    try:
        shutil.rmtree(folder_path)
    except Exception as e:
        print(f"Error deleting folder '{folder_path}': {e}")

def remove_all_txt_files(name, directory_path="./"):
    try:
        for filename in os.listdir(directory_path):
            if filename.endswith(".txt") and filename != "requirement.txt" and filename not in name:
                file_path = os.path.join(directory_path, filename)
                os.remove(file_path)
                print(f"Removed: {file_path}")
    except Exception as e:
        print(f"Error: {e}")

        
def split_wav_file_and_convert_text(input_file, output_folder,endpoint_name, segment_duration=20 * 1000):
    audio = AudioSegment.from_file(input_file, format="wav")
    
    # Calculate the number of segments
    num_segments = len(audio) // segment_duration
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    path = os.path.join(output_folder,input_file)
    os.makedirs(path, exist_ok=True)
    
    final_output = []
    # Split the audio file into segments
    for i in range(num_segments):
        start_time = i * segment_duration
        end_time = (i + 1) * segment_duration
        segment = audio[start_time:end_time]
        file_name = f"segment_{i + 1}.wav"
        segment.export(os.path.join(path, file_name), format="wav")
        with open(os.path.join(path, file_name), "rb") as file:
            wav_file_read = file.read()
            temp = query_endpoint(endpoint_name, wav_file_read, "audio/wav")
            final_output.append(temp)
    delete_folder(path)
    os.remove(input_file)
    return final_output