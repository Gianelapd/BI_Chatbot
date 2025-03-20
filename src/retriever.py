import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import re
import ast

def query_as_list(db, query):
    res = db.run(query)
    res = [el for sub in ast.literal_eval(res) for el in sub if el]
    res = [re.sub(r"\b\d+\b", "", string).strip() for string in res]
    return list(set(res))

class TextRetriever:
    def __init__(self, database, model_name="all-MiniLM-L6-v2"):
        """
        Initialize the retriever by fetching proper nouns from the database and encoding them.
        """
        self.database = database
        self.model = SentenceTransformer(model_name)
        self.proper_nouns, self.proper_nouns_metadata = self.fetch_proper_nouns()

        # Convert text to embeddings
        self.vectors = self.model.encode([item[0] for item in self.proper_nouns], convert_to_numpy=True).astype(np.float32)

        # Create FAISS index
        self.dimension = self.vectors.shape[1]
        self.index = faiss.IndexIDMap(faiss.IndexFlatL2(self.dimension))
        self.index.add_with_ids(self.vectors, np.array(range(len(self.proper_nouns))))

    def fetch_proper_nouns(self):
        """ Fetch venue names, venue groups, companies, and instruments from the database with column tracking. """
        data_sources = {
            "venue_name": "SELECT DISTINCT venue_name FROM dim_execution_venue",
            "venue_group": "SELECT DISTINCT venue_group FROM dim_execution_venue",
            "company": "SELECT DISTINCT company FROM dim_instrument_list",
            "instrument_name": "SELECT DISTINCT instrument_name FROM dim_instrument_list"
        }

        proper_nouns = []
        proper_nouns_metadata = {}

        for column_name, query in data_sources.items():
            values = query_as_list(self.database, query)
            for value in values:
                clean_value = str(value).strip()
                proper_nouns.append((clean_value, column_name))
                proper_nouns_metadata[clean_value] = column_name  # Map value to its column name

        return proper_nouns, proper_nouns_metadata

    def retrieve(self, query, k=3):
        """ Retrieve the closest match(es) for a given query. """
        query_vector = self.model.encode(query, convert_to_numpy=True).astype(np.float32)
        distances, indices = self.index.search(query_vector.reshape(1, -1), k)

        results = [
            {
                "value": self.proper_nouns[i][0],
                "column_name": self.proper_nouns[i][1],
                "distance": float(distances[0][j])
            }
            for j, i in enumerate(indices[0])
        ]
        return results
    
    def retrieval_tool(self, query):
        """ Wrapper for LangChain tool compatibility. """
        results = self.retrieve(query, k=3)
        return [{"value": res["value"], "column_name": res["column_name"]} for res in results]

