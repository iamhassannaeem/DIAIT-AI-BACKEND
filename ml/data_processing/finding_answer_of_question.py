import ast
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def process_answers(questions, data, max_tries=3, attempt=1):

    output_struct = [
        {
            "id": 238,
            "question_text": "this is sample question one",
            "answer": "your provided answer should be placed here",
        },
        {
            "id": 239,
            "question_text": "this is sample question two",
            "answer": "your provided answer should be placed here",
        },
        {
            "id": 240,
            "question_text": "what is next ",
            "answer": "your process will be countinued for all input question",
        },
    ]

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"""You are a Reading Comprehension assistant:

                                This refers to the ability to read, understand, and interpret written texts. It involves not just reading the words, but understanding the meaning, context, and structure of what is being communicated.
                                Example: In school tests, students are often asked to read a passage and then answer questions based on what they've understood — this is known as a reading comprehension test.
                                In this scenario you will be provided with a conversation between 2 people, there might be some issues and error in it. As like spelling mistakes, or missing words maybe. Kepp note on it.

                            Your main task is to find the answer of those questions from the conversation.
                                Key points to remember for that:
                                - There is no way to comeup with a makeup answer, which is not present in the conversation.
                                - You are not allowed to hallusinate, or to recreate the answer from your side, as it is not allowed.
                                - Remember that this is the very crucial data and there is no way to add a single sentence from your side, which is not there in the conversation.
                                - If an answer is not provided in the conversation, you should simply reply to it as "Not answered". 

                            Your output structure should be as same as the structure provided {output_struct}.
                                The very crusial points here to keep note are following:
                                - The output structure should be same , there is no way of even to change a single symbol in it.
                                - As this structure is further going to be used in python, and if there we got some error, our system will be collapsed.
                                - So the structure should be same, as list of json.
                                - Do not bother to change the 'id' key/value or 'question_text' key/value.                                     
                                      
                                """,
            },
            {
                "role": "user",
                "content": f" Here you are provided with the {questions}. and following the next is the conversation {data}. Please follow all the instructions advised to you.",
            },
        ],
        model="gpt-4o-mini",
        temperature=0.5,
    )

    received_data = chat_completion.choices[0].message.content
    try:
        received_data = ast.literal_eval(received_data)
        # print(received_data)
        return received_data
    except:
        if attempt >= max_tries:
            for item in questions:
                item["answer"] = "can not resolve the issue"
            return questions
        return process_answers(questions, data, max_tries, attempt= attempt + 1)


####################################################################################################
####################################################################################################
####################################################################################################
####################################################################################################



# -Name: Look for common ways people introduce themselves (e.g., "My name is [name]" or "I am [name]"). It could also be inferred from context (e.g., "I'm Sarah" or "It's John").
# "fullName" : " Linda Smith",
# "fullName" : "Sarah Jones",
def extract_user_info(data, max_tries = 3 , attempt = 1):

                        
    output_struct = { "email": "example@example.com", "address": "123 Example Street", "date_of_birth": "1990-01-01", "tag": "Important"}

    

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system",
            "content" : f"""You are an AI system tasked with extracting specific details from a conversation between a user and a service representative. 
                            Given the conversation text, you need to extract the following information:

                                1. Name: Identify the name of the user (this could be mentioned in different ways, such as "My name is [name]" or "I am [name]").
                                2. Email: Extract the user's email address (this may appear as "[email@example.com]" or similar).
                                3. Address: Extract the user's address (e.g., "I live at [address]" or "My address is [street name, city, postal code]").
                                4. Date of Birth: Identify the user's date of birth (look for phrases like "I was born on [MM/DD/YYYY]" or "My birthdate is [MM/DD/YYYY]").
                                    * date of birth should be in formate of yyyy-mm-dd , there is not any other structure expected.
                                5. Lead Tag: Based on the conversation's tone and context, classify the lead as one of the following:
                                    * Positive: If the user shows clear interest, enthusiasm, or intent to proceed.
                                    * Interested: If the user expresses curiosity but has not yet made a decision.
                                    * Negative: If the user clearly expresses disinterest, dissatisfaction, or unwillingness to engage further.
                                    * Neutral: If the user is neither strongly positive nor negative, and the conversation seems neutral in tone.
                                    Please ensure the information is accurately extracted, including any contextual details that can help determine the lead's status.

                                        '''
                                        Example Input:
                                        Sales Agent: "Good morning! Thank you for reaching out to us. How can I assist you today?"
                                        Customer: "Hello, I’m Sarah. I’m interested in your service. I live at 123 Elm Street, Springfield, IL 62701. My email is sarah.jones@email.com. I was born on 04/15/1985. Can you tell me more about the features?"
                                        Sales Agent: "Hi Sarah! It’s great to hear that you're interested. I'd be happy to explain more about our features. We offer [describe service features], and we have flexible pricing plans based on your needs. Are there specific features you’re most interested in?"


                                        Example Output sould be always in the json structure:
                                         
                                        {{  "email": "sarah.jones@email.com", 
                                            "address": "123 Elm Street, Springfield, IL 62701", 
                                            "date_of_birth": "1985-04-15", 
                                            "tag": "Interested"}}

                                        '''

                                    Breakdown of How It Works:
                                        -Email: Recognize email formats (e.g., [username]@[domain].com). It’s often found in conversations when discussing contact or registration.
                                        -Address: Address information may be formal (e.g., "I live at") or informal (e.g., "My home is"). Be sure to capture street, city, state, and postal code if available.
                                        -Date of Birth: Look for clear indications of a date, particularly in formats like MM/DD/YYYY, DD/MM/YYYY, or words like "born on".
                                        -Lead Tag: Based on the user's tone and statements, categorize the lead:
                                            1.Positive: Direct statements showing interest in signing up or purchasing, excitement, or eagerness.
                                            2.Interested: Curious questions or requests for more information, but not necessarily a strong intent yet.
                                            3.Negative: Explicit disinterest, complaints, or refusal to proceed.
                                            3.Neutral: Neutral or polite conversation with no clear inclination either way.

                                    Additional Notes:
                                    If any of the required information is missing, the system should note that it could not be extracted and return None for it.
                                    If the lead tag is unclear from the conversation, label it as "Neutral" or use context to make a reasonable assumption.
                                    provided in the conversation, you should simply reply to it as None. 
                                    Always mark not provided feilds as None.

                                    

                            Your output structure should be as same as the structure provided {output_struct}.
                                The very crusial points here to keep note are following:
                                - The output structure should be same , there is no way of even to change a single symbol in it.
                                - As this structure is further going to be used in python, and if there we got some error, our system will be collapsed.
                                - So the structure should be same, as json.
                                - Do not bother to change the key/value structure.                                  
                                      
                                """,
                      
                                },

            {
                "role": "user",
                "content": f" Here you are provided with the conversation {data}. Please follow all the instructions advised to you.",
            }
        ],
        model="gpt-4o-mini",
        temperature=0.5
    )

    received_data = chat_completion.choices[0].message.content
    try:
        received_data = ast.literal_eval(received_data)
        print(received_data)
        return received_data
    except:
        if attempt >= max_tries:
            return output_struct
        return process_answers(data, max_tries, attempt= attempt + 1)


