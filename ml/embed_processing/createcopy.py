import boto3
from dotenv import load_dotenv
import os
from os import environ


load_dotenv()

environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


# s3 = boto3.client(
#             "s3",
#             aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
#             aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY"),
#         )


# # List all buckets
# response = s3.list_buckets()

# # Loop through each bucket
# for bucket in response['Buckets']:
#     bucket_name = bucket['Name']
#     print(f'\nBucket: {bucket_name}')
    
#     # List all objects (files) in the current bucket
#     objects_response = s3.list_objects_v2(Bucket=bucket_name)

#     # Check if there are any objects in the bucket
#     if 'Contents' in objects_response:
#         print(f'Objects in bucket {bucket_name}:')
#         for obj in objects_response['Contents']:
#             print(f'  - {obj["Key"]}')
#     else:
#         print(f'No objects in bucket {bucket_name}.')



# import boto3
# from dotenv import load_dotenv
# import os
# from os import environ

# load_dotenv()

# environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# s3 = boto3.client(
#     "s3",
#     aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
#     aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY"),
# )

# # List all buckets
# response = s3.list_buckets()

# # Loop through each bucket
# for bucket in response['Buckets']:
#     bucket_name = bucket['Name']
#     print(f'\nBucket: {bucket_name}')
    
#     # List all objects (files) in the current bucket
#     objects_response = s3.list_objects_v2(Bucket=bucket_name)

#     # Check if there are any objects in the bucket
#     if 'Contents' in objects_response:
#         print(f'Objects in bucket {bucket_name}:')
#         for obj in objects_response['Contents']:
#             # Get the object key (file name) and size
#             file_name = obj["Key"]
#             file_size = obj["Size"]
#             print(f'  - {file_name} (Size: {file_size} bytes)')
#     else:
#         print(f'No objects in bucket {bucket_name}.')




# import boto3
# import os

# # Initialize the S3 client
# s3 = boto3.client(
#             "s3",
#             aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
#             aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY"),
#         )
# # Bucket name
# bucket_name = 'dialit-library'  # Replace with your bucket name

# # Function to delete all objects in a bucket
# def delete_all_objects(bucket_name):
#     # List all objects in the bucket
#     response = s3.list_objects_v2(Bucket=bucket_name)

#     # Check if the bucket has any objects
#     if 'Contents' in response:
#         # Prepare the list of objects to delete
#         objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
        
#         # Delete objects in batches (S3 allows up to 1000 objects per request)
#         delete_response = s3.delete_objects(
#             Bucket=bucket_name,
#             Delete={'Objects': objects_to_delete}
#         )
        
#         print(f"Deleted {len(objects_to_delete)} objects from bucket '{bucket_name}'")
        
#         # Check if there are more objects to delete (pagination)
#         if response.get('IsTruncated'):
#             continuation_token = response.get('NextContinuationToken')
#             while continuation_token:
#                 # Fetch more objects
#                 response = s3.list_objects_v2(
#                     Bucket=bucket_name,
#                     ContinuationToken=continuation_token
#                 )
                
#                 # Prepare the list of objects to delete
#                 objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
                
#                 # Delete objects in batches
#                 delete_response = s3.delete_objects(
#                     Bucket=bucket_name,
#                     Delete={'Objects': objects_to_delete}
#                 )
                
#                 print(f"Deleted {len(objects_to_delete)} objects from bucket '{bucket_name}'")
                
#                 # Get the continuation token for the next batch
#                 continuation_token = response.get('NextContinuationToken')
        
#         print(f"All objects deleted from bucket '{bucket_name}'")
#     else:
#         print(f"No objects found in bucket '{bucket_name}'.")

# # Delete all objects in the specified bucket
# delete_all_objects(bucket_name)
