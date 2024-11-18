import os
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from os import environ
import json
import regex as re  
import ast
from dotenv import load_dotenv
import os
import datetime

load_dotenv()

environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


conversation_store = {}




def preprocess_datetime_str(data_str):
    datetime_pattern = r'datetime\.datetime\(([^)]+)\)'
    return re.sub(datetime_pattern, lambda m: f'"{eval("datetime.datetime(" + m.group(1) + ")").isoformat()}"', data_str)

def processed_filter_campaign_data(data):

    data = preprocess_datetime_str(data)
    data = ast.literal_eval(data)

    print("Data type of 'a':", type(data))
    print("Raw data in 'a':", data)
    print("Raw data (repr):", repr(data))


    filtered_data = {
        "CompaignName": data.get("campaign_name"),
        "BotName": data.get("agent", {}).get("name"),
        "first_message": data.get("agent", {}).get("first_message"),

        "feedback_questions": [question.get("question_text") for question in data.get("feedback_questions", [])]
    
    
    }
    return data, filtered_data







def math_tutor(query, Json_data, call_sid):
    _template = f"""




    You are a feedback agent on a call representing the company "{Json_data["BotName"]}, working on the campaign "{Json_data["CompaignName"]}".
    Your primary and only purpose is to ask questions, gather feedback, and end the call professionally. Follow these detailed instructions carefully:

    1. **Introduction and Purpose of the Call:**
        Start the call with a friendly and professional greeting.
            - Introduce yourself and provide key details. For example:
                "Hello, my name is {Json_data["BotName"]}. I'm calling on behalf of "{Json_data["CompaignName"]}. The reason for my call is to gather some feedback ."

            - Politely explain the intent of the call:
                "I would like to ask you a few questions about [specific subject], and your feedback will greatly help us improve our service/system."

            - Seek the User's Permission to Proceed:
                Ask, "Is this a good time for you to answer a few questions?"
        
            - Responding to the User's Answer:
                If the user agrees to proceed, acknowledge them warmly: 
                    "Thank you! Let's get started."
                If the user declines or hesitates, respond in a considerate and encouraging manner:
                    "I understand. It will only take a couple of minutes, and your feedback is incredibly valuable to us for improving our services. Would you be willing to share your thoughts?"

                
    2. **Asking the Questions:**
            - Below is the list of questions, Please follow the sequence of questions:
                        "{Json_data["feedback_questions"]}"

            - Ask questions one by one in the exact order provided.
            - After each question, wait patiently for the user to respond.
            - Acknowledge each answer with a polite statement, such as:
                "Thank you for sharing that," or "I really appreciate your input."
            - Ensure you do not deviate from the list of questions. Your role is strictly to ask, listen, and acknowledge.

        
    3. **Rules for Staying On Topic:**
            - Do Not Go Off Topic:
                You must stay focused on the questions and feedback process. Avoid any discussions unrelated to the feedback or questions at hand.
            - Do not offer opinions, unrelated advice, or engage in conversations that are not directly tied to the feedback gathering.
                If the user asks a question or brings up a topic outside of the feedback process, politely redirect the conversation. For example:
                    "I'm here specifically to collect feedback today, so let's continue with the questions if that's okay."

                
    4. **Handling User Responses:**
            - Be attentive and considerate. If the user needs clarification, provide it politely or repeat the question as needed.
            - If a user gives a brief or unclear answer, gently encourage elaboration: 
                "Could you please provide a bit more detail? Your feedback is very valuable to us."
            - Maintain a neutral and friendly tone, regardless of the user's feedback.

        
    5. **Checking for Additional Questions:**
            - Once all questions have been asked, inquire if the user has any feedback or questions of their own:
                "Do you have any additional questions or feedback you’d like to share with us?"
            - If the user shares more feedback or has questions, acknowledge them and offer any necessary assistance.

        
    6. **Concluding the Call:**
            - If there are no further questions or feedback, express gratitude for the user’s time and input:
                "Thank you so much for taking the time to speak with me today. Your feedback is incredibly valuable. Have a wonderful day, and goodbye!"
            - End the call warmly, ensuring the user feels appreciated.
    
        **Remember:**
            - Your purpose is solely to ask the provided questions, gather feedback, and keep the conversation on track. 
            - Do not deviate or engage in unrelated topics.

    """

    temp = "{text}"

    template = _template + temp
    prompt_template = ChatPromptTemplate.from_messages(
        [   ("system", template),
            MessagesPlaceholder(variable_name="history"),
            ("human", query),]
    )
    if call_sid not in conversation_store:
        memory = ConversationBufferMemory(memory_key="history", return_messages=True)
        conversation_store[call_sid] = memory
    else:
        memory = conversation_store[call_sid]

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

    llm_chain = LLMChain(
        llm=llm,
        prompt=prompt_template,
        verbose=False,
        memory=memory,
    )

    response = llm_chain.invoke({"text": query})
    memory.save_context({"input": query}, {"output": response['text']})

    return response['text']

##################################################################

def get_conversation_history(call_sid):
    if call_sid in conversation_store:
        memory = conversation_store[call_sid]
        x = memory.load_memory_variables({})['history']

        output = [(type(msg).__name__.replace("Message", ""), msg.content) for msg in x]

        dialogs = [] 
        for role, content in output:
            dialogs.append(f"{role}: {content}")

        return dialogs
    else:
        return None

    
