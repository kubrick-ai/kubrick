from embed import extract_text_features, extract_video_features, print_segments
import vector_db

# vector_db.setup()

# video_filepaths = [
#     "./content/exercise_ball_pushups.mp4",
#     "./content/sailboat.mp4",
# ]
# for filepath in video_filepaths:
#     video_embedding = extract_video_features(filepath)
#     print_segments(video_embedding)
#
#     for segment in video_embedding:
#         vector_db.store(
#             filepath,
#             embedding_type=segment.embedding_option,
#             start_offset=segment.start_offset_sec,
#             end_offset=segment.end_offset_sec,
#             embedding=segment.embeddings_float,
#         )
#

# query = "man doing pushups in the gym on an exercise ball"
# query = "down and pushing up. Inhaling on the way down."
# query = "sailboat in the water"
query = "aerial footage of las vegas strip at night"
text_embedding = extract_text_features(query)

print(f"query: '{query}'")
results = vector_db.find_similar(text_embedding)
print("result:")

for result in results:
    source = result["source"].split("/")[-1]
    similarity = result["similarity"]
    embedding_type = result["type"]
    start_offset = result["start_offset"]
    end_offset = result["end_offset"]
    print(
        f"Source: {source.ljust(27, ' ')} | Start: {start_offset:.1} | End: {end_offset:.1} | Type: {embedding_type.ljust(11, ' ')} | Similarity: {similarity:.5}"
    )
