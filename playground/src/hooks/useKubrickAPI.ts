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
} from "@/types";

// TODO: Move to config?
const API_BASE = "https://xt30znkfhh.execute-api.us-east-1.amazonaws.com/dev";

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

// const createVideo = async () => {};
//
// export const useCreateVideo = () => {
//   const queryClient = useQueryClient();
//   return useMutation<string, Error, string>({
//     mutationFn: createVideo,
//     onSuccess: () => {
//       // Invalidate the 'videos' query to refetch the list of videos
//       queryClient.invalidateQueries({ queryKey: ["videos"] });
//     },
//   });
// };

interface EmbedResponse {
  id: string;
  video_url: string;
}

interface TaskStatus {
  id: string;
  status: "processing" | "ready" | "failed";
  error?: string;
}

const createEmbedTask = async (video_url: string): Promise<EmbedResponse> => {
  const formData = new FormData();
  formData.append("video_url", video_url);

  const res = await axios.post(`${API_BASE}/tasks`, formData);

  if (res.data.error) {
    throw new Error(res.data.error); // This will be caught by React Query
  }

  return res.data;
};

const getEmbedStatus = async (taskId: string): Promise<TaskStatus> => {
  const res = await axios.get(`${API_BASE}/tasks/${taskId}`);
  return res.data;
};

export const useEmbedVideo = () => {
  const [taskId, setTaskId] = useState<string | null>(null);

  const {
    mutate: submitVideo,
    isPending: isSubmitting,
    data: embedData,
    isSuccess: isSubmitSuccess,
    error: submitError,
  } = useMutation({
    mutationFn: (video_url: string) => createEmbedTask(video_url),
    onSuccess: (data) => setTaskId(data.id),
  });

  const {
    data: statusData,
    refetch,
    isFetching: isPolling,
  } = useQuery({
    enabled: !!taskId,
    queryKey: ["embedStatus", taskId],
    queryFn: () => getEmbedStatus(taskId as string),
  });

  useEffect(() => {
    if (!taskId) return;

    const interval = setInterval(() => {
      if (statusData?.status === "failed" || statusData?.status === "ready") {
        clearInterval(interval);
      } else {
        refetch();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [taskId, statusData?.status, refetch]);

  if (statusData && typeof statusData.error === "string") {
    console.log("statusData error: " + statusData.error);
  }

  return {
    submitVideo,
    isSubmitting,
    isSubmitSuccess, // Not used atm
    submitError, // Not used atm
    embedData,
    taskId, // Not used atm
    statusData,
    isPolling,
  };
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
    if (!query.data) return;

    const totalPages = Math.ceil(query.data.metadata.total / limit);

    queryClient.prefetchQuery({
      queryKey: ["data", page, limit],
      queryFn: () => fetchVideos(page, limit),
    });
    if (page + 1 < totalPages) {
      queryClient.prefetchQuery({
        queryKey: ["data", page + 1, limit],
        queryFn: () => fetchVideos(page + 1, limit),
      });
    }
  }, [query, page, limit, queryClient]);

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
    if (!isAccordionOpen || !query.data) return;

    const totalPages = Math.ceil(query.data.metadata.total / limit);

    queryClient.prefetchQuery({
      queryKey: ["data", page, limit],
      queryFn: () => fetchTasks(page, limit),
    });

    if (page + 1 < totalPages) {
      queryClient.prefetchQuery({
        queryKey: ["data", page + 1, limit],
        queryFn: () => fetchTasks(page + 1, limit),
      });
    }
  }, [query, page, limit, isAccordionOpen, queryClient]);

  return query;
};
