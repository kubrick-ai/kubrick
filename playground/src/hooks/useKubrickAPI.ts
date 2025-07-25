import { useQuery, useMutation } from "@tanstack/react-query";
import axios from "axios";
import { useEffect, useState } from "react";
import {
  VideoSchema,
  Video,
  SearchParams,
  SearchResultSchema,
  SearchResult,
  VideoCollection,
  VideoCollectionSchema,
} from "@/types";

// TODO: Move to config?
const API_BASE = "https://xt30znkfhh.execute-api.us-east-1.amazonaws.com/dev";

const search = async (params: SearchParams): Promise<Array<SearchResult>> => {
  const formData = new FormData();
  if (params.query_text) {
    formData.append("query_text", params.query_text);
  }

  if (params.query_media_type) {
    formData.append("query_media_type", params.query_media_type);
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
    for (const modality of params.query_modality) {
      formData.append("query_modality", modality);
    }
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
      params.query_media_type,
      params.query_media_url,
      params.query_media_file,
      params.query_modality,
      params.page_limit,
      params.min_similarity,
      params.filter,
    ], // Unique key for this query
    queryFn: () => search(params), // Your async function to fetch data
    enabled: !!params.query_text || !!params.query_media_type, // Only run when there's something to search
  });
};

// const getVideos = async (): Promise<Array<Video>> => {
//   const response = await axios.get(`${API_BASE}/`);
//   const parsedVideos = VideoSchema.array().parse(response.data);
//   return parsedVideos;
// };
//
// export const useGetVideos = () => {
//   return useQuery<Array<Video>, Error>({
//     queryKey: ["videos"], // Unique key for this query
//     queryFn: getVideos, // Your async function to fetch data
//   });
// };
//
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
    console.log(statusData.error);
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

///

export const fetchVideos = async (
  page = 0,
  pageLimit = 12
): Promise<VideoCollection> => {
  const response = await axios.get(`${API_BASE}/videos`, {
    params: { page, limit: pageLimit },
  });


  const parsedVideos = VideoCollectionSchema.parse(response.data);
  return parsedVideos;
};

// React Query hook for videos
export const useGetVideos = (page = 0, pageLimit = 12) =>
  useQuery<VideoCollection, Error>({
    queryKey: ["data", page, pageLimit],
    queryFn: () => fetchVideos(page, pageLimit),
    placeholderData: (prev) => prev, // Keeps old data during loading
  });
