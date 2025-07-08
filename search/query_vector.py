from redisvl.query import VectorQuery
from vector_helper import hf
from index_helper import main as index_helper_main
import pandas as pd

user_query = input("Enter your query: ")

embedded_user_query = hf.embed(user_query)

vec_query = VectorQuery(
    vector=embedded_user_query,
    vector_field_name="vector",
    num_results=3,
    return_fields=["description", "source"],
    return_score=True
)

index = index_helper_main("symptoms")
result = index.query(vec_query)
print(pd.DataFrame(result))