from .vectorstore import store_embeddings, get_embeddings

def main():
    embedding_model = get_embeddings()

    store_embeddings(embedding_model)

if __name__ == "__main__":
    main()
