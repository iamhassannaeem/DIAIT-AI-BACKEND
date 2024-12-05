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
        return process_answers(questions, data, max_tries, attempt=attempt + 1)
