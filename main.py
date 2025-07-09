from embed import extract_text_features, extract_video_features
import vector_db

# vector_db.setup()

video_filepaths = [
    "./content/exercise_ball_pushups.mp4",
    "./content/sailboat.mp4",
    "./content/stock-footage-las-vegas-aerial.mp4",
]
for filepath in video_filepaths:
    video_embedding = extract_video_features(filepath)
    for segment in video_embedding:
        vector_db.store(filepath, segment)


# query = "man doing pushups in the gym on an exercise ball"
# query = "down and pushing up. Inhaling on the way down."
query = "aerial footage of las vegas strip at night"
text_embedding = extract_text_features(query)

print(f"query: '{query}'")
results = vector_db.find_similar(text_embedding)
print("result:")

for result in results:
    source = result["source"].split("/")[-1]
    similarity = result["similarity"]
    print(f"Source: {source.ljust(20, ' ')} | Similarity: {similarity}")
