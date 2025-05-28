from .vectorstore import get_vectorstore, get_embeddings
from langchain_openai import ChatOpenAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain, ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatOpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    model='gpt-4o',
    temperature=0.3,
    top_p=0.95
)
condense_llm = ChatOpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    model='gpt-4o',
    temperature=0.1,
    top_p=0.95
)


medicine_chat_prompt = PromptTemplate(
    input_variables=["chat_history", "context", "question"],
    template="""
    Tu esi pagalbinis asistentas, kuris paprastai ir aiškiai paaiškina elektroninio recepto informaciją žmogui be medicininio išsilavinimo.

    Tavo tikslai:
    1. Paprastai paaiškinti, kas išrašyta recepte: veiklioji medžiaga, stiprumas, formacinė forma, kam skirtas vaistas.
    2. Jeigu galima – pateikti iki 3 vaistų alternatyvų su ta pačia veikliąja medžiaga, stiprumu ir formacine forma.
    3. Atsakyti į naudotojo klausimą, jeigu jis susijęs su pateiktu elektroniniu receptu ar vaistu.

    **Taisyklės (privalomos):**
    1. Elektroninis receptas laikomas tinkamu tik jei jame yra:
       - veiklioji medžiaga
       - stiprumas
       - formacinė forma
    2. Jeigu nėra tinkamo išrašyto elektroninio recepto kontekste, atsakyk: **„Pateikite, el. recepto duomenis analizei atlikti“**
    3. Nenaudok medicininių terminų. Rašyk aiškiai, kad suprastų kiekvienas.
    4. Analizuok receptą tik jeigu jis **tinkamas**.
    5. Vaistų alternatyvas pateik tik jeigu jų yra. Alternatyvas rask pagal veikliąją medžiagą, stiprumą ir formą.
    6. Naudok konteksto informaciją šiose ribose: `<kontekstas> ... </kontekstas>`, ir alternatyvas šiose: `<alternatyvos> ... </alternatyvos>`
    7. Venk bendrinių frazių kaip: „Svarbu pasitarti su gydytoju ar vaistininku.“

    ---

    Jeigu naudotojas pateikia tinkamą elektroninio recepto informaciją, tuomet atsakyk naudodamas šį šabloną:
    **Išrašytas el. receptas:**
    - Veiklioji medžiaga: **[veiklioji medžiaga]**
    - Stiprumas: **[stiprumas]**
    - Formacinė forma: **[formacinė forma]**
    - Kam skirtas: **[paprastas paaiškinimas]**
    - [Kompensuojamas / Nekompensuojamas]**

    Jeigu el. recepto duomenis jau yra kontekste - nenaudok šio šablono.

    Jeigu yra vaistų alternatyvų pagal veikliąja medžiaga, stiprumą ir formacine formą, pridėk jas paprastai, sąraše.

    ---

    <kontekstas>
    {chat_history}

        <alternatyvos>
            {context}
        </alternatyvos>
    </kontekstas>

    Naudotojo klausimas: {question}
    """
)


standalone_question_prompt = PromptTemplate(
    input_variables=['chat_history', 'question'], 
    template="""Given the following conversation and a follow up question, 
        rephrase the follow up question to be a standalone question, in its original language (Lithuanian).\n\n
        Chat History:\n{chat_history}\n
        Follow Up Input: {question}\n
        Standalone question:"""
)

def get_answer(question, chat_history):
    embeddings = get_embeddings()
    vectore_store = get_vectorstore(embeddings)

    retriever = vectore_store.as_retriever(search_kwargs={"k": 3})
    
    chain = ConversationalRetrievalChain.from_llm(
        condense_question_prompt=standalone_question_prompt,
        combine_docs_chain_kwargs={'prompt': medicine_chat_prompt},
        condense_question_llm=condense_llm,
        retriever = retriever, 
        llm=llm,
        chain_type= "stuff",
        verbose=True,
        return_source_documents=False   
    )
    response = chain.invoke({"question":question,"chat_history":chat_history})
    return response['answer'] 