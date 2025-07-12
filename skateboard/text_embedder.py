import os
from dotenv import load_dotenv
from twelvelabs import TwelveLabs
from typing import List
from twelvelabs.models.embed import SegmentEmbedding

load_dotenv()
API_KEY = os.getenv('TWELVELABS_API')



def embed_text(text: str):
	client = TwelveLabs(api_key=API_KEY)

	res = client.embed.create(
		model_name="Marengo-retrieval-2.7",
		text=text,
	)
	# print(f"Created text embedding: model_name={res.model_name}")
	# def print_segments(segments: List[SegmentEmbedding], max_elements: int = 5):
	# 	for segment in segments:
	# 		print(f"  embeddings: {segment.embeddings_float[:max_elements]}")
	# if res.text_embedding is not None and res.text_embedding.segments is not None:
	# 	print_segments(res.text_embedding.segments)
	# return res.emb

	return res.text_embedding.segments[0].embeddings_float
	


