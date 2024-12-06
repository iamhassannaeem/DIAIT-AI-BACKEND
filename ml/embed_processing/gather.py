
import os
import boto3
# import redis
import shutil
import pickle
import asyncio
from io import BytesIO
from zipfile import ZipFile
from ..utils.our_redis import pool , StrictRedis
from langchain.vectorstores import FAISS
from concurrent.futures import ThreadPoolExecutor
from langchain.embeddings import HuggingFaceEmbeddings
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv
load_dotenv()




def download_and_unzip_files_from_json(outbound_sales_data, bucket_name='dialit-library'):
    download_folder = f"{outbound_sales_data['agent']['user_id']}_{outbound_sales_data['agent']['id']}_{outbound_sales_data['campaign_id']}"
    os.makedirs(download_folder, exist_ok=True)
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.environ['S3_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['S3_SECRET_ACCESS_KEY'],
    )
    
    def process_zip_file(zip_file, download_folder, s3_client):
        try:
            zip_subfolder = os.path.join(download_folder, os.path.basename(zip_file).replace('.zip', ''))
            os.makedirs(zip_subfolder, exist_ok=True)

            response = s3_client.get_object(Bucket=bucket_name, Key=zip_file)
            zip_content = response['Body'].read()

            with ZipFile(BytesIO(zip_content), 'r') as zip_ref:
                zip_ref.extractall(zip_subfolder)
            print(f"Successfully extracted {zip_file} to {zip_subfolder}.")

        except Exception as e:
            print(f"Error processing {zip_file}: {e}")

    futures = []


    agent_files = outbound_sales_data.get('agent_files', [])
    
    for file_info in agent_files:
        file_id = file_info['file__id']
        user_id = outbound_sales_data['agent']['user_id']
        
        s3_prefix = f"{user_id}/{file_id}/"
        print(f"Looking for .zip files in: {s3_prefix}")

        try:
            response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=s3_prefix)
            zip_files = []

            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['Key'].endswith('.zip'):
                        zip_files.append(obj['Key'])

                if zip_files:
                    with ThreadPoolExecutor() as executor:
                        for zip_file in zip_files:
                            futures.append(executor.submit(process_zip_file, zip_file, download_folder, s3_client))
                    for future in futures:
                        future.result()

                else:
                    print(f"No .zip files found in {s3_prefix}")
            else:
                print(f"No objects found for {s3_prefix}")
        
        except NoCredentialsError:
            print("Credentials not available.")
        except ClientError as e:
            print(f"Failed to list or download files. Error: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
    return download_folder




# #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# Asynchronous function to handle merging embeddings from subfolders
async def process_subfolder(subfolder, main_folder, model_name, db_path_pattern, loop, executor):
    subfolder_path = os.path.join(main_folder, subfolder)
    if os.path.isdir(subfolder_path):
        faiss_index_path = os.path.join(subfolder_path, db_path_pattern)
        print(f"Checking for FAISS index in: {faiss_index_path}")
        result = await loop.run_in_executor(executor, load_and_merge_faiss, subfolder_path, model_name, main_folder)
        return result, subfolder_path
    return None, None

def load_and_merge_faiss(faiss_index_path, model_name, main_folder):
    x = HuggingFaceEmbeddings(model_name=model_name, model_kwargs={'device': 'cpu'})
    try:
        vector_db = FAISS.load_local(faiss_index_path, x, allow_dangerous_deserialization=True)
        print(f"Successfully loaded FAISS index from {faiss_index_path}")
        return vector_db
    except Exception as e:
        print(f"Error loading FAISS index from {faiss_index_path}: {e}")
        return None


async def combine_embeddings_from_subfolders(main_folder, db_path_pattern='faiss_index', model_name='sentence-transformers/all-MiniLM-L6-v2'):
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=10) 
    x = HuggingFaceEmbeddings(model_name=model_name, model_kwargs={'device': 'cpu'})
    merged_vector_db = None  
    
    # List all subfolders inside the main folder
    subfolders = [f for f in os.listdir(main_folder) if os.path.isdir(os.path.join(main_folder, f))]
    
    tasks = []
    for subfolder in subfolders:
        task = process_subfolder(subfolder, main_folder, model_name, db_path_pattern, loop, executor)
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    for vector_db, subfolder_path in results:
        if vector_db is not None:
            if merged_vector_db is None:
                merged_vector_db = vector_db
            else:
                merged_vector_db.merge_from(vector_db)

            shutil.rmtree(subfolder_path)

    shutil.rmtree(main_folder)
    if merged_vector_db:
        return merged_vector_db
    else:
        print("No embeddings found to merge.")
        return None









# Run the async function
async def load_embeddings(outbound_sales):

    
    embed_folder = download_and_unzip_files_from_json(outbound_sales)
    print(embed_folder)
    if embed_folder:
        merged_db = await combine_embeddings_from_subfolders(embed_folder)
        if merged_db:
            print("Final merged embeddings stored.")
            # retriever = merged_db.as_retriever()
            return merged_db
        else:
            print("No embeddings were merged.")
            return None
    else:
        return None
    



def load_send_embedding_redis(outbound_sales_data):
    r = StrictRedis(connection_pool=pool)


    my_data = asyncio.run(load_embeddings(outbound_sales_data))
    unique_id = f"{outbound_sales_data['agent']['user_id']}_{outbound_sales_data['agent']['id']}_{outbound_sales_data['campaign_id']}"
    serialized_data = pickle.dumps(my_data)
    r.set(unique_id, serialized_data)


def get_embedding_redis(outbound_sales_data):
    r = StrictRedis(connection_pool=pool)
    unique_id = f"{outbound_sales_data['agent']['user_id']}_{outbound_sales_data['agent']['id']}_{outbound_sales_data['campaign_id']}"


    fetched_data = pickle.loads(r.get(unique_id))
    return fetched_data



# outbound_sales = [{
#             'campaign_id': 42, 
#             'campaign_name': 'Test', 
#             'campaign_type': 'Outbound_sales', 
#             'campaign_status': 'Started', 
#             'agent': {'user_id': 2, 'id': 28, 'name': 'John', 'active': True, 
#                     'first_message': 'Hello, this is Domify. How may I assist you today?', 
#                     'gender': 'female', 
#                     'twillio_number': {'id': 2, 'phone_number': '+19528003480', 'status': 'active'}}, 
#             'feedback_questions': [], 
#             'call_details': [{'call_id': 45, 'phone_number': '+923487823836', 'call_start_time': None, 'call_end_time': None, 'conversation': None, 'status': None, 'call_cost': None}],
#             'agent_files': [
#                 {'file__id': 76, 'file__file_name': 'sample.pdf', 'file__file_type': '.pdf', 'file__file_size': 129390, 'file__content_type': 'application/pdf', 'file_type': 'product_pricing'}, 
#                 {'file__id': 77, 'file__file_name': 'sample.pdf', 'file__file_type': '.pdf', 'file__file_size': 129390, 'file__content_type': 'application/pdf', 'file_type': 'product_pricing'}, 
#                 {'file__id': 78, 'file__file_name': 'sample.pdf', 'file__file_type': '.pdf', 'file__file_size': 129390, 'file__content_type': 'application/pdf', 'file_type': 'product_pricing'}, 
            
#             ]
#         }]
    

# load_send_embedding_redis(outbound_sales)
# get_embedding_redis(outbound_sales)