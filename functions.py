from pymongo import MongoClient
from bcrypt import hashpw, gensalt, checkpw
from pymongo.server_api import ServerApi
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import CSVLoader
from langchain_community.document_loaders import TextLoader
import csv
import os
import json
from bson import ObjectId
import datetime
# from config import Config
from langchain.chains import VectorDBQA
import pandas as pd

with open('config.json', 'r') as f:
    config = json.load(f)

mongo_uri = config['app']['MONGO_URI']

client = MongoClient(mongo_uri)




def submit_data(question, answer, user_id, AdminID, department):
    client = MongoClient(mongo_uri, server_api=ServerApi('1'))
    db = client[AdminID]
    collection_problems = db['Problems']
    collection_users = db['Users']
    collection_documents = db['Documents']
    # Insert data into MongoDB collections
    problem_data = {
        'Question': question,
        'Answer': answer,
        'rating': 0,
        'user_id': user_id,  # Associate problem with the logged-in user
        'department': department
    }
    problem_id = collection_problems.insert_one(problem_data).inserted_id
    print("##########Data Added to MongoDB")
    # Add data to CSV file
    csv_path = 'csv/documents.csv'
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["ID", "Problem", "Solution", "Text"])  # Write headers
        writer.writerow([str(problem_id), question, answer, 'Text'])
    print("##########Data Added to CSV")
    Loader = CSVLoader(file_path= csv_path) 
    pages = Loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=250)
    docs = text_splitter.split_documents(pages)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

    db_directory = f'./{department}+{AdminID}'

    if not os.path.exists(db_directory):
        os.makedirs(db_directory)
        print(f"Folder '{db_directory}' created successfully.")
        extension = FAISS.from_documents(docs, embeddings)
        extension.save_local(db_directory)
        print("Folder is Created and Embeddings Stored In new Folder")

    else:
        print(f"Folder '{db_directory}' already exists.")
        store = FAISS.load_local(
        db_directory, embeddings, allow_dangerous_deserialization=True
        )
        extension = FAISS.from_documents(docs, embeddings)
        store.merge_from(extension)
        store.save_local(db_directory)
        print("Folder Exist and Embeddings Merged In new Folder And Saved Locally")

    return {'message': 'Data submitted successfully', 'id': str(problem_id)}


def sub_document(file, session, AdminID, department):
    client = MongoClient(mongo_uri, server_api=ServerApi('1'))
    db = client[AdminID]
    collection_problems = db['Problems']
    collection_users = db['Users']
    collection_documents = db['Documents']
    print("#####111")
    file_path = f'uploads/{file.filename}'  # Choose an appropriate directory
    file.save(file_path)

    loader = PyPDFLoader(file_path)
    pages = loader.load_and_split()
    #Initializing Empty String to store content of PDF Document
    string = ""
    for page in pages:
         string += page.page_content
    problem_data = {
        'Text': string,
        'FileName': file.filename,
        'user_id': session,  # Associate problem with the logged-in user
        'department': department
    }
    problem_id = collection_documents.insert_one(problem_data).inserted_id
    print("##########Data Added to MongoDB")

    text_file_path = 'csv/data.txt'
    with open(text_file_path, 'w', encoding='utf-8') as textfile:  # Use 'w' to write data
        textfile.write(f"user_id: {problem_id}\n")  # Write user_id
        textfile.write(f"FileName: {file.filename}\n") 
        textfile.write(f"Text: {string}\n")    # Write textData
        textfile.write("\n")  # Add a newline to separate entries
    print("##########Data Added to Text File")
    loader = TextLoader(file_path= text_file_path)
    pages = loader.load_and_split()
    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=250)
    docs = text_splitter.split_documents(pages)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

    db_directory = f'./{department}+{AdminID}'
    if not os.path.exists(db_directory):
        os.makedirs(db_directory)
        print(f"Folder '{db_directory}' created successfully.")
        extension = FAISS.from_documents(docs, embeddings)
        extension.save_local(db_directory)
        print("Folder is Created and Embeddings Stored In new Folder")
    else:
        print(f"Folder '{db_directory}' already exists.")
        # Open the folder
        # os.chdir(db_directory)
        store = FAISS.load_local(
        db_directory, embeddings, allow_dangerous_deserialization=True
        )
        extension = FAISS.from_documents(docs, embeddings)
        store.merge_from(extension)
        store.save_local(db_directory)
        print("Folder Exist and Embeddings Merged In Folder And Saved Locally")
    return {'message': 'Data submitted successfully', 'id': str(problem_id)}






# Function to get data from the "Problems" and "Users" collections
def get_data(source_ids,user_ids, AdminID):
    client = MongoClient(mongo_uri, server_api=ServerApi('1'))
    db = client[AdminID]
    collection_problems = db['Problems']
    collection_users = db['Users']
    collection_documents = db['Documents']
    combined_data = []

    
    for user_id in user_ids:
        print(user_ids)

        # Convert user_id to ObjectId before querying
        docs_data = collection_documents.find_one({'_id': ObjectId(user_id)})
        if docs_data:
            # Extract relevant data from the "Documents" document
            FileName = docs_data.get("FileName")
            department = docs_data.get("department")
            user_id = docs_data.get("user_id")

            # Query the "Users" collection for the user with the matching user_id
            user_doc = collection_users.find_one({"_id": ObjectId(user_id)})

            if user_doc:
                # Extract relevant data from the "Users" document
                name = user_doc.get("username")
                email = user_doc.get("email")

                # Combine the data into a single dictionary
                data_entry = {
                    "FileName": FileName,
                    'department': department
                }
                combined_data.append(data_entry)

    for source_id in source_ids:
        # Convert source_id to ObjectId
        object_id = ObjectId(source_id)

        # Query the "Problems" collection for the document with the given source_id
        problem_doc = collection_problems.find_one({"_id": object_id})
        

        if problem_doc:
            # Extract relevant data from the "Problems" document
            question = problem_doc.get("Question")
            answer = problem_doc.get("Answer")
            user_id = problem_doc.get("user_id")

            # Query the "Users" collection for the user with the matching user_id
            user_doc = collection_users.find_one({"_id": ObjectId(user_id)})

            if user_doc:
                # Extract relevant data from the "Users" document
                name = user_doc.get("name")
                email = user_doc.get("email")
                job_title = user_doc.get("job_title")
                department = user_doc.get("department")

                # Combine the data into a single dictionary
                data_entry = {
                    "name": name,
                    "email": email,
                    "job_title": job_title,
                    "Question": question,
                    "Answer": answer,
                    'department': department
                }

                # Append the combined data to the result list
                combined_data.append(data_entry)


    return combined_data




def update_document(file, session, document_id, AdminID, department):
    client = MongoClient(mongo_uri, server_api=ServerApi('1'))
    db = client[AdminID]
    collection_documents = db['Documents']
    

    file_path = f'uploads/{file.filename}'  # Choose an appropriate directory
    file.save(file_path)

    loader = PyPDFLoader(file_path)
    pages = loader.load_and_split()
    
    # Initializing Empty String to store content of PDF Document
    string = ""
    for page in pages:
         string += page.page_content

    # Update existing document with new content
    collection_documents.update_one(
        {"_id": ObjectId(document_id)},
        {"$set": {
            'Text': string,
            'FileName': file.filename,
            'user_id': session,  # Associate problem with the logged-in user
            'department': department
        }}
    )
    print(department)

    print("Document Updated in MongoDB")

    # Update text file
    text_file_path = 'csv/data.txt'
    with open(text_file_path, 'w', encoding='utf-8') as textfile:  # Use 'w' to write data
        textfile.write(f"user_id: {document_id}\n")  # Write user_id
        textfile.write(f"FileName: {file.filename}\n") 
        textfile.write(f"Text: {string}\n")    # Write textData
        textfile.write("\n")  # Add a newline to separate entries
    print("Data Updated in Text File")

    # Update embeddings
    db_directory = f'./{department}+{AdminID}'
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    local_data_base = FAISS.load_local(
        db_directory, embeddings, allow_dangerous_deserialization=True
    )
    delete_document(local_data_base, document_id, db_directory)

    loader = TextLoader(file_path=text_file_path, encoding='utf-8')
    pages = loader.load_and_split()
    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=250)
    docs = text_splitter.split_documents(pages)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    store = FAISS.load_local(
        db_directory, embeddings, allow_dangerous_deserialization=True
    )
    extension = FAISS.from_documents(docs, embeddings)
    store.merge_from(extension)
    
    store.save_local(db_directory)
    print("Embeddings Updated")

    return {'message': 'Document updated successfully', 'id': document_id}




def vdb_to_df(db_local):
    v_dict = db_local.docstore._dict
    data_rows = []
    for k, doc in v_dict.items():
        content_lines = doc.page_content.split('\n')
        doc_id = problem = solution = text = None
        try:
            if len(content_lines) >= 1:
                doc_id = content_lines[0].split(': ')[1]
            if len(content_lines) >= 2:
                problem = content_lines[1].split(': ')[1]
            if len(content_lines) >= 3:
                solution = content_lines[2].split(': ')[1]
            if len(content_lines) >= 4:
                text = content_lines[3].split(': ')[1] if len(content_lines[3].split(': ')) > 1 else None
        except IndexError:
            pass  # Ignore this document if it doesn't follow the expected format
        data_rows.append(
            {
                "chunk_id": k,
                "document": doc_id,
                "problem": problem if problem else None,
                "solution": solution if solution else None,
                "text": text,
            }
        )
    vector_df = pd.DataFrame(data_rows)
    return vector_df




def delete_document(db_local, doc_id, db_directory):
    vector_df = vdb_to_df(db_local)
    chunks_list = vector_df.loc[vector_df["document"] == doc_id]["chunk_id"].tolist()
    if chunks_list:
        db_local.delete(chunks_list)
        # Save updates using the correct path
        print("############# 3 ##############")
        db_local.save_local(db_directory)  
        print(f"Document with doc_id '{doc_id}' deleted successfully.")
    else:
        print("Document does not exist.")




def delete_document_from_mongodb(AdminID, doc_id, department):
    client = MongoClient(mongo_uri, server_api=ServerApi('1'))
    db = client[AdminID]
    collection_documents = db['Documents']
    db_directory = f'./{department}+{AdminID}'
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    local_data_base = FAISS.load_local(
        db_directory, embeddings, allow_dangerous_deserialization=True
    )

    # Find document before deletion to retrieve user ID
    document = collection_documents.find_one({'_id': ObjectId(doc_id)})
    if document:
        user_id = document.get('user_id')
        print(user_id)
        delete_document(local_data_base, doc_id, db_directory)  # Pass db_directory here

    # Delete document
    result = collection_documents.delete_one({'_id': ObjectId(doc_id)})
    if result.deleted_count > 0:
        print(f"Document with doc_id '{doc_id}' deleted successfully from MongoDB.")
        if document:
            return {'user_id': document.get('user_id'), 'doc_id': doc_id}
    else:
        print("Document does not exist in MongoDB.")
        return None
