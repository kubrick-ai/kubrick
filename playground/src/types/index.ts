import { z } from "zod";

export const MediaTypeSchema = z.enum(["image", "video", "audio", "text"]);
export type MediaType = z.infer<typeof MediaTypeSchema>;

export const CosineSimilaritySchema = z.number().min(0).max(1);
export type CosineSimilarity = z.infer<typeof CosineSimilaritySchema>;

export const EmbeddingScopeSchema = z.enum(["clip", "video"]);
export type EmbeddingScope = z.infer<typeof EmbeddingScopeSchema>;

export const EmbeddingModalitySchema = z.enum(["visual-text", "audio"]);
export type EmbeddingModality = z.infer<typeof EmbeddingModalitySchema>;

export const VideoSchema = z.object({
  id: z.number(),
  url: z.string(),
  filename: z.string(),
  duration: z.number().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
  height: z.number().nullable().optional(),
  width: z.number().nullable().optional(),
  s3_bucket: z.string().nullable().optional(),
  s3_key: z.string().nullable().optional(),
});

export type Video = z.infer<typeof VideoSchema>;

export const VideosResponseSchema = z.object({
  data: VideoSchema.array(),
  metadata: z.object({
    total: z.number().nonnegative(),
    limit: z.number().nonnegative(),
    page: z.number().nonnegative(),
  }),
});

export type VideosResponse = z.infer<typeof VideosResponseSchema>;

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

// The shape of the data collected from the SearchForm form component
export const SearchFormDataSchema = z.object({
  query_text: z
    .string()
    .max(250, "Query text is too long (max 250 chars)")
    .optional(),
  query_type: MediaTypeSchema,
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

export type SearchFormData = z.infer<typeof SearchFormDataSchema>;

// The shape of the data sent to the API as multipart/form-data
export const SearchParamsSchema = z.object({
  query_text: z.string().optional(),
  query_type: MediaTypeSchema,
  query_media_url: z.url().optional(),
  query_media_file: z.instanceof(File).optional(),
  query_modality: z.string().optional(),
  min_similarity: CosineSimilaritySchema.optional(),
  page_limit: z.int().min(0).optional(),
  filter: z.string().optional(),
});

export type SearchParams = z.infer<typeof SearchParamsSchema>;

export const TaskSchema = z.object({
  id: z.number(),
  sqs_message_id: z.string().nullable().optional(),
  s3_bucket: z.string().nullable().optional(),
  s3_key: z.string().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
  status: z.string(),
});

export type Task = z.infer<typeof TaskSchema>;

export const TasksResponseSchema = z.object({
  data: TaskSchema.array(),
  metadata: z.object({
    total: z.number().nonnegative(),
    limit: z.number().nonnegative(),
    page: z.number().nonnegative(),
  }),
});

export type TasksResponse = z.infer<typeof TasksResponseSchema>;
