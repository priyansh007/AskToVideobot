from langchain.chains import LLMChain
from langchain.llms.bedrock import Bedrock
from langchain.prompts import PromptTemplate
import boto3
import os
import sourcecode

class ScrumBot():
    def __init__(self, 
                 s3bucket, 
                 input_video_file_name,
                 text_file_name,
                 summary_file_name, 
                 endpoint_name,
                 file_extension):
        self.s3bucket = s3bucket
        self.input_video_file_name = input_video_file_name
        self.endpoint_name = endpoint_name
        self.text_file_name = text_file_name
        self.summary_file_name = summary_file_name
        self.file_extension = file_extension


    def uploadTextFile(self,
                       ans, 
                       s3_key):
            with open(s3_key, 'w') as file:
                file.write(ans)
            sourcecode.upload_to_s3(s3_key, s3_key, self.s3bucket)
            print(f"Text file uploaded to S3://{self.s3bucket}/{s3_key}")

    def videoToScript(self):
            sourcecode.upload_to_s3(self.input_video_file_name, self.input_video_file_name, self.s3bucket)
            output_wav_file_name = self.input_video_file_name.replace(self.file_extension, "wav")
            if self.file_extension not in ["mp3"]:
                 sourcecode.convert_mp4_to_wav(self.input_video_file_name, output_wav_file_name)
            else:
                 sourcecode.convert_audio_to_wav(self.input_video_file_name, output_wav_file_name)
            print(f"Conversion and upload successful. WAV file saved as {output_wav_file_name}")
            output_folder = "SpeechToText"
            ans = sourcecode.split_wav_file_and_convert_text(output_wav_file_name, output_folder, self.endpoint_name)
            ans = ' '.join(item[0] for item in ans)
            self.uploadTextFile(ans,self.text_file_name)
            return(ans)
    
    def llm_bot(self,
                isChatBot=False,
                query=""):
        if not os.path.exists(self.text_file_name):
            sourcecode.download_from_s3(self.s3bucket, self.text_file_name, self.text_file_name)
        with open(self.text_file_name,'r') as file:
            content = file.read()
        bedrock_client = boto3.client(
            service_name = "bedrock-runtime",
            region_name="us-east-1"
        )

        modelId = "anthropic.claude-v2"

        llm = Bedrock(model_id=modelId,
                    client=bedrock_client,
                    model_kwargs={"temperature":0.9}
                    )
        if isChatBot:
            template = "You are a Scrum master/Project Manager bot who has knowledge of all scrum ceremonies and best practices. Using this meeting transcribe context: {transcribe}, answer this question: {query}"
        else:
            template="You are a scrum master bot who has knowledge of all scrum ceremonies and best practices. Your job is to find To-Do task, Roadblockers and Action Item from the transcribe of a meeting. If Assignee is mentioned in transcribe please incluse name as well. At the end of your answer please include the summary of meeting. Transcribe is {transcribe}"
        

        prompt = PromptTemplate(
            input_variables=["transcribe","query"],
            template=template
            )
        bedrock_chain = LLMChain(llm=llm, prompt=prompt)

        response=bedrock_chain({'transcribe':content, 'query': query})

        if not isChatBot:
             self.uploadTextFile(response['text'],self.summary_file_name)
        return response['text']
