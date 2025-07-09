from towhee import pipe, ops, DataCollection
import torch
import torch.nn.functional as F


video_pipe = (
    pipe.input("video_path")
    .map(
        "video_path",
        "flame_gen",
        ops.video_decode.ffmpeg(
            sample_type="uniform_temporal_subsample", args={"num_samples": 12}
        ),
    )
    .map("flame_gen", "flame_list", lambda x: [y for y in x])
    .map(
        "flame_list",
        "vec",
        ops.video_text_embedding.clip4clip(
            model_name="clip_vit_b32", modality="video", device="cpu"
        ),
    )
    .output("vec")
    # .output("video_path", "flame_list", "vec")
)

video_path = "./content/exercise_ball_pushups.mp4"
# DataCollection(video_pipe(video_path)).show()
video_embedding = video_pipe(video_path).get()[0]
# print(video_embedding)


text_pipe = (
    pipe.input("text")
    .map(
        "text",
        "vec",
        ops.video_text_embedding.clip4clip(
            # make sure device is cuda if running with a gpu
            model_name="clip_vit_b32",
            modality="text",
            device="cpu",
        ),
    )
    .output("vec")
)

query = "man doing pushups on a red exercise ball"
# query = "bird flying in the mountains"
# DataCollection(text_pipe(query)).show()
text_embedding = text_pipe(query).get()[0]
# print(text_embedding)


tensor1 = torch.tensor(video_embedding)
tensor2 = torch.tensor(text_embedding)
similarity = F.cosine_similarity(tensor1, tensor2, dim=0)
print("Query:", query)
print("Cosine Similarity:", similarity)
