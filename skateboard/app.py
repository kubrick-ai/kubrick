import text_embedder
import vector_db


query_embedding = text_embedder.embed_text("3-pointer")
similarities = vector_db.find_similar(query_embedding)

for line in similarities:
    print(f"source:{line['source']} minutes: {int(line['start_time']/60)} seconds: {int(line['start_time']%60)}")