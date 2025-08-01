import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { useEffect, useState } from "react";
import {
  SearchParams,
  SearchResultSchema,
  SearchResult,
  VideosResponse,
  VideosResponseSchema,
  TasksResponse,
  TasksResponseSchema,
  VideoUploadResponse,
  VideoUploadResponseSchema,
} from "@/types";

// TODO: Move to config?
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:5000";

const search = async (params: SearchParams): Promise<Array<SearchResult>> => {
  const formData = new FormData();
  if (params.query_text) {
    formData.append("query_text", params.query_text);
  }

  formData.append("query_type", params.query_type);

  if (params.query_type !== "text") {
    if (params.query_media_url) {
      formData.append("query_media_url", params.query_media_url);
    } else if (params.query_media_file) {
      formData.append("query_media_file", params.query_media_file);
    }
  }

  if (params.page_limit) {
    formData.append("page_limit", params.page_limit.toString());
  }
  if (params.min_similarity) {
    formData.append("min_similarity", params.min_similarity.toString());
  }
  if (params.filter) {
    formData.append("filter", params.filter);
  }
  if (params.query_modality) {
    formData.append("query_modality", params.query_modality);
  }

  const response = await axios.post(`${API_BASE}/search`, formData);
  const parsedVideos = SearchResultSchema.array().parse(response.data.data);
  return parsedVideos;
};

export const useSearchVideos = (params: SearchParams) => {
  return useQuery<Array<SearchResult>, Error>({
    queryKey: [
      "searchVideos",
      params.query_text,
      params.query_type,
      params.query_media_url,
      params.query_media_file,
      params.query_modality,
      params.page_limit,
      params.min_similarity,
      params.filter,
    ], // Unique key for this query
    queryFn: () => search(params), // Your async function to fetch data
    enabled:
      !!(params.query_type === "text" && params.query_text) ||
      !!(
        params.query_type !== "text" &&
        (params.query_media_file || params.query_media_url)
      ), // Only run when there's something to search
  });
};

export const uploadVideo = async (file: File, filename: string) => {
  const videoLinkResponse = await generateVideoUploadLink(filename);
  const presignedUrl = videoLinkResponse.data.presigned_url;
  const contentType = videoLinkResponse.data.content_type;
  const response = await axios.put(presignedUrl, file, {
    headers: {
      "Content-Type": contentType,
    },
  });

  if (response.status !== 200 && response.status !== 204) {
    throw new Error("Upload failed");
  }

  return {
    url: presignedUrl.split("?")[0],
  };
};

export const generateVideoUploadLink = async (
  filename: string
): Promise<VideoUploadResponse> => {
  const response = await axios.get(`${API_BASE}/generate-upload-link`, {
    params: { filename },
  });

  const parsedVideoUploadLink = VideoUploadResponseSchema.parse(response.data);

  return parsedVideoUploadLink;
};

export const fetchVideos = async (
  page = 0,
  limit: number
): Promise<VideosResponse> => {
  const response = await axios.get(`${API_BASE}/videos`, {
    params: { page, limit },
  });

  const parsedVideos = VideosResponseSchema.parse(response.data);
  return parsedVideos;
};

// React Query hook for videos
export const useGetAndPrefetchVideos = (page: number, limit: number) => {
  const queryClient = useQueryClient();

  const query = useQuery<VideosResponse, Error>({
    queryKey: ["data", page, limit],
    queryFn: () => fetchVideos(page, limit),
    placeholderData: (prev) => prev,
  });

  useEffect(() => {
    if (!query.data?.metadata.total) return;

    const totalPages = Math.ceil(query.data.metadata.total / limit);

    if (page + 1 < totalPages) {
      queryClient.prefetchQuery({
        queryKey: ["data", page + 1, limit],
        queryFn: () => fetchVideos(page + 1, limit),
      });
    }
  }, [query.data?.metadata.total, page, limit, queryClient]);

  return query;
};

export const fetchTasks = async (
  page = 0,
  limit: number
): Promise<TasksResponse> => {
  const response = await axios.get(`${API_BASE}/tasks`, {
    params: { page, limit },
  });

  const parsedTasks = TasksResponseSchema.parse(response.data);
  return parsedTasks;
};

// React Query hook for tasks
export const useGetAndPrefetchTasks = (
  page: number,
  limit: number,
  isAccordionOpen: boolean
) => {
  const queryClient = useQueryClient();

  const query = useQuery<TasksResponse, Error>({
    queryKey: ["data", page, limit],
    queryFn: () => fetchTasks(page, limit),
    placeholderData: (prev) => prev,
    refetchInterval: 5000,
    enabled: isAccordionOpen,
  });

  useEffect(() => {
    if (!isAccordionOpen || !query.data?.metadata.total) return;

    const totalPages = Math.ceil(query.data.metadata.total / limit);

    if (page + 1 < totalPages) {
      queryClient.prefetchQuery({
        queryKey: ["data", page + 1, limit],
        queryFn: () => fetchTasks(page + 1, limit),
      });
    }
  }, [query.data?.metadata.total, page, limit, isAccordionOpen, queryClient]);

  return query;
};
