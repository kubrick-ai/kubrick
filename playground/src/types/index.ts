import { z } from "zod";

export const MediaTypeSchema = z.enum(["image", "video", "audio"]);
export type MediaType = z.infer<typeof MediaTypeSchema>;

export const CosineSimilaritySchema = z.number().min(0).max(1);
export type CosineSimilarity = z.infer<typeof CosineSimilaritySchema>;

export const EmbeddingScopeSchema = z.enum(["clip", "video"]);
export type EmbeddingScope = z.infer<typeof EmbeddingScopeSchema>;

export const EmbeddingModalitySchema = z.enum(["visual-text", "audio"]);
export type EmbeddingModality = z.infer<typeof EmbeddingModalitySchema>;

export const VideoSchema = z.object({
  id: z.number(),
  title: z.string().nullable().optional().default(undefined),
  url: z.string(),
  filename: z.string().nullable().optional(),
  duration: z.number().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
  height: z.number().nullable().optional(),
  width: z.number().nullable().optional(),
  s3_bucket: z.string().nullable().optional(),
  s3_key: z.string().nullable().optional(),
});

export type Video = z.infer<typeof VideoSchema>;

export const SearchResultSchema = z.object({
  id: z.number(),
  modality: EmbeddingModalitySchema.optional(),
  scope: EmbeddingScopeSchema.optional(),
  start_time: z.number().optional(),
  end_time: z.number().optional(),
  similarity: z.number(),
  video: VideoSchema,
});

export type SearchResult = z.infer<typeof SearchResultSchema>;

export const SearchFormSchema = z.object({
  query_text: z.string().optional(),
  query_media_type: MediaTypeSchema.optional(),
  query_media_url: z.url().optional(),
  query_media_file: z.instanceof(File).optional(),
  query_modality: EmbeddingModalitySchema.array().optional(),
  search_scope: z.union([EmbeddingScopeSchema, z.literal("all")]).optional(),
  search_modality: z
    .union([EmbeddingModalitySchema, z.literal("all")])
    .optional(),
  min_similarity: z.number().min(0).max(1).optional(),
  page_limit: z.int().min(0),
  filter: z.string().optional(),
});

export const SearchParamsSchema = z.object({
  query_text: z.string().optional(),
  query_media_type: MediaTypeSchema.optional(),
  query_media_url: z.url().optional(),
  query_media_file: z.instanceof(File).optional(),
  query_modality: EmbeddingModalitySchema.array().optional(),
  min_similarity: CosineSimilaritySchema.optional(),
  page_limit: z.int().min(0).optional(),
  filter: z.string().optional(),
});

export type SearchParams = z.infer<typeof SearchParamsSchema>;
