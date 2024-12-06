import os
import zipfile
import shutil
import tempfile
from langchain_community.document_loaders import PDFPlumberLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
import boto3
from botocore.exceptions import ClientError
import pdfplumber
from langchain.schema import Document


def create_vector_db(file_obj,bucket_name,location, s3):

    faiss_path = tempfile.mkdtemp()

    with pdfplumber.open(file_obj) as pdf:
        documents = []
        for page in pdf.pages:
            page_text = page.extract_text()
            document = Document(page_content=page_text)
            documents.append(document)


    text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20,length_function=len, is_separator_regex=False,)
    texts = text_splitter.split_documents(documents)
    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2', model_kwargs={'device': 'cpu'})
    db = FAISS.from_documents(texts, embeddings)
    db.save_local(faiss_path)

    zip_filename = f"{faiss_path}.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(faiss_path):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), faiss_path))

    s3_key = os.path.join(location, os.path.basename(zip_filename)) 

    with open(zip_filename, 'rb') as zip_file:
        response = s3.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=zip_file, 
            ContentType="zip",
        )

    shutil.rmtree(faiss_path)  
    os.remove(f"{faiss_path}.zip")  

    
    return zip_filename


def delete_zip_files_in_directory(s3_client, bucket_name, directory_path):
    try:
        print(directory_path)
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=directory_path)
        if 'Contents' in response:
            for obj in response['Contents']:
                file_key = obj['Key']
                
                if file_key.endswith('.zip'):
                    s3_client.delete_object(Bucket=bucket_name, Key=file_key)
                    print(f"Deleted file: {file_key}")
        else:
            print("No files found in the directory.")
    
    except ClientError as e:
        print(f"Error listing or deleting files: {e}")

