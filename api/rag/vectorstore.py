import os
import psycopg2
from pgvector.psycopg2 import register_vector
from langchain_postgres.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from langchain.schema import Document
import getpass
import json
from decimal import Decimal

load_dotenv()

DB_URL = os.getenv("DB_URL")

if not DB_URL:
    raise ValueError("DB_URL environment variable missing")

if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter your OpenAI API key: ")

def convert_decimals(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [convert_decimals(x) for x in obj]
    return obj

def get_embeddings():
    return OpenAIEmbeddings(
        model="text-embedding-3-large",
        openai_api_key=os.environ["OPENAI_API_KEY"]
    )

def store_embeddings(embedding_model):
    print("Connecting to database to store embeddings...")
    connection = psycopg2.connect(DB_URL)
    cursor = connection.cursor()
    register_vector(cursor)
    print("Vector registered successfully.")

    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='medicine' AND column_name='embedding'
    """)
    if cursor.fetchone() is None:
        print("Column 'embedding' not found in 'medicine'. Creating it...")
        cursor.execute("ALTER TABLE medicine ADD COLUMN embedding vector(3072);")
        connection.commit()
        print("Column 'embedding' created successfully.")
    else:
        print("Column 'embedding' already exists.")

    cursor.execute("""

    SELECT medicine_id, name, active_substance, strength, formative_form, use_method, drug_type, atc_code, atc_name, drug_subgroup, quantity, base_price
    -- SELECT medicine_id, name, active_substance, strength, formative_form, use_method, drug_type, atc_code, atc_name, drug_subgroup, quantity, box_paper, base_price
    FROM medicine
    """)
    medicines = cursor.fetchall()
    print(f"Fetched {len(medicines)} medicine from the database.")

    vector_store = get_vectorstore(embedding_model)

    documents = []
    ids = []
    texts = []
    medicine_ids = []

    for medicine in medicines:
        # medicine_id, name, active_substance, strength, formative_form, use_method, drug_type, atc_code, atc_name, drug_subgroup, quantity, box_paper, base_price = medicine
        medicine_id, name, active_substance, strength, formative_form, use_method, drug_type, atc_code, atc_name, drug_subgroup, quantity, base_price = medicine

        payload = convert_decimals({
            "vaisto_id": medicine_id,
            "pavadinimas": name,
            "veiklioji_medz": active_substance,
            "stiprumas": strength,
            "formacine_forma": formative_form,
            "vartojimo_budas": use_method,
            "vaisto_tipas": drug_type,
            "atc_kodas": atc_code,
            "atc_pavadinimas": atc_name,
            "subgrupe": drug_subgroup,
            "kiekis": quantity,
            # "box_paper": box_paper,
            "bazine_kaina": base_price
        })

        payload_json = json.dumps(payload)
        texts.append(payload_json)
        medicine_ids.append(medicine_id)

        doc = Document(
            page_content=payload_json, 
            metadata=convert_decimals({
                "vaisto_id": medicine_id,
                "pavadinimas": name,
                "veiklioji_medz": active_substance,
                "stiprumas": strength,
                "formacine_forma": formative_form,
                "vartojimo_budas": use_method,
                "vaisto_tipas": drug_type,
                "atc_kodas": atc_code,
                "atc_pavadinimas": atc_name,
                "subgrupe": drug_subgroup,
                "kiekis": quantity,
                # "box_paper": box_paper,
                "bazine_kaina": base_price
            }),
        )
        documents.append(doc)
        ids.append(medicine_id)

    print(f"Generating embeddings for {len(texts)} medicines...")

    embeddings = [embedding_model.embed_query(text) for text in texts]
    column_name = "embedding"

    print(f"Embeddings generated. Example: {embeddings[0][:5]}...")

    for medicine_id, embedding in zip(medicine_ids, embeddings):
        cursor.execute(
            f"""
            UPDATE medicine
            SET {column_name} = %s
            WHERE medicine_id = %s
            """,
            (embedding, medicine_id),
        )

    connection.commit()
    print(f"Embeddings stored for {len(medicines)} medicine in {column_name}.")
    cursor.close()
    connection.close()

    print("Adding documents to vector store...")
    vector_store.add_documents(documents, ids=ids)
    print("Documents added to vector store.")

def get_vectorstore(embedding_model):
    print("Initializing PGVector vector store...")
    connection = DB_URL
    vector_store = PGVector(
        embeddings=embedding_model,
        collection_name="medicine",
        connection=connection,
        use_jsonb=True,
    )
    return vector_store
