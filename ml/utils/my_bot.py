from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_community.callbacks.manager import get_openai_callback

from os import environ
import json
import regex as re  
import ast
from dotenv import load_dotenv
import os
import datetime

load_dotenv()


from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage

environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


conversation_store = {}




def preprocess_datetime_str(data_str):
    datetime_pattern = r'datetime\.datetime\(([^)]+)\)'
    return re.sub(datetime_pattern, lambda m: f'"{eval("datetime.datetime(" + m.group(1) + ")").isoformat()}"', data_str)

def processed_filter_campaign_data(data):

    data = preprocess_datetime_str(str(data))
    data = ast.literal_eval(data)


    filtered_data = {
        "CompaignName": data.get("campaign_name"),
        "BotName": data.get("agent", {}).get("name"),
        "first_message": data.get("agent", {}).get("first_message"),

        "feedback_questions": [question.get("question_text") for question in data.get("feedback_questions", [])]
    
    
    }
    return data, filtered_data



def get_chat_response(query, processed_raw_data ,Json_data, call_sid , embeddings = None):
    if processed_raw_data['campaign_type'] == 'Outbound_sales':
        response, sales_price, actual_price = sales_agent(query, processed_raw_data ,Json_data, call_sid , embeddings)  
    else:
        response, sales_price, actual_price = feed_back(query, processed_raw_data ,Json_data, call_sid)
    
    return response, sales_price, actual_price
        


















def sales_agent(query, processed_raw_data ,Json_data, call_sid, embeddings):

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)
    retriever = embeddings.as_retriever(k = 3)


    contextualize_q_system_prompt = f"""
                    You are a Sales Agent at comapny named as {Json_data["CompaignName"]}.
                     Your name is {Json_data["BotName"]}, and user can refer you with it.  
                    Following are Sales Agent Call Script and Instructions:


                    Instructions for Sales Agent:
                    1. Follow the Workflow: Always adhere to the provided workflow, step by step. Do not deviate from it unless directed by the workflow.
                    2. Only Respond to Relevant Queries: Do not answer any questions that are not part of the workflow or are not addressed in the provided data source.
                    3. Be Professional and Courteous: Keep the tone friendly, confident, and professional throughout the call.
                    4. End the Call Gracefully: Ensure the call concludes with the customer feeling informed and valued.
                    5. The call should always end with a graceful closure while saying goodbye.
                    


                    Objective:
                    Make a successful sales lead call and ensure the customer is informed about the product/service, answering only specific queries as outlined in the workflow defined bellow:
                    
                    
                    Workflow for the Call:
                    {Json_data["workflow"]}.

                    1. Introduction
                    - Greet the customer warmly and introduce yourself and the company.
                    - Example: “this is {Json_data["BotName"]} from {Json_data["CompaignName"]}. How are you today?”

                    2. Purpose of the Call
                    - Explain the purpose of the call clearly and succinctly.
                    - Example: “I’m reaching out to share some exciting information about our [product/service] that might be of interest to you.”

                    3. Highlight the Benefits
                    - Present key benefits of the product or service that align with the customer's needs or interests.
                    - Example: “Our [product/service] is designed to [mention specific benefits, such as save time, increase efficiency, solve a common problem, etc.].”

                    4. Address Questions (if any)
                    - If the customer asks a question, only answer based on the information provided in the data source or as outlined in the prompt.
                    - Do not provide additional information outside of the provided details.
                    - Example: “That’s a great question! Let me explain how this works based on what we offer…”

                    5. Offer a Call to Action (CTA)
                    - Guide the customer toward the next step, whether it’s scheduling a demo, signing up, or receiving more information, according to the work flow.
                    - Example: “Would you be interested in scheduling a free demo to see how it works in action?”

                    
                    6. Final Check for Additional Questions
                    - Before closing, ask if there’s anything else the customer needs.
                    - Example: “Is there anything else I can help you with or clarify for you today?”

                    7. Graceful Closure
                    - End the call on a polite and positive note, thanking them for their time.
                    - Example: “Thank you for your time to speak. Goodbye, and thank you for connecting with us!”

                    Important Notes:
                    - If the customer asks any questions that are not in the workflow or data source, politely inform them that the information is not available.
                    - Example: “I don’t have that information at the moment, but I’d be happy to get back to you with more details if needed.”
                    - Do not attempt to answer questions outside the provided scope. Always stick to the information you have.
                    """


    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )


    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            ("human", "{context}"), 
        ]
    )

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    if call_sid not in conversation_store:
        chat_history = []
        conversation_store[call_sid] = chat_history
    else:
        chat_history = conversation_store[call_sid]

    with get_openai_callback() as tokens:
        response = rag_chain.invoke({"input": query, "chat_history": chat_history})
        chat_history.extend(
            [
                HumanMessage(content=query),
                AIMessage(content=response["answer"]),
            ]
        )

    return response['answer'] , tokens.total_cost*3 , tokens.total_cost


















def feed_back(query, processed_raw_data ,Json_data, call_sid):
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

    
    with get_openai_callback() as tokens:
        response = llm_chain.invoke({"text": query})

    memory.save_context({"input": query}, {"output": response['text']})
    return response['text'] , tokens.total_cost*3 , tokens.total_cost


































##################################################################

def get_conversation_history(call_sid , type):
    if call_sid in conversation_store:

        memory = conversation_store[call_sid]
        if type == "Outbound_sales":
            return memory
        else:
            x = memory.load_memory_variables({})['history']
            print(x)

            output = [(msg, "") for msg in x]
            print(output)

            # output = [(type(msg).__name__.replace("Message", ""), msg.content) for msg in x]

            dialogs = [] 
            for role, content in output:
                dialogs.append(f"{role}: {content}")
            print("##########33234234234@@@@@@@@@@@@@@@@@@Q",dialogs)
            return dialogs
    else:
        return None

    












# query = "hello hows u ?"
# Json_data = {"BotName" : "linda", 
#              "CompaignName" : "sample compaing",
#              "feedback_questions" : "what is your name lol"}
# call_sid =  "093403928092385069832095"


# print(math_tutor(query , Json_data, call_sid ))