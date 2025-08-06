"use client";

import ErrorDisplay from "@/components/ErrorDisplay";
import VideoList from "@/components/VideoList";
import { useGetAndPrefetchVideos } from "@/hooks/useKubrickAPI";
import { useState } from "react";
import LoadingOverlay from "@/components/LoadingOverlay";

const PAGE_LIMIT = 12;

const Library = () => {
  const [page, setPage] = useState(1);
  // const { data, isLoading, error } = useGetAndPrefetchVideos(
  //   page - 1,
  //   PAGE_LIMIT,
  // );
  const { data, isLoading, error } = {
    data: null,
    isLoading: true,
    error: null,
  };
  const videos = data?.data ?? [];
  const total = data?.metadata?.total ?? 0;

  return (
    <div className="p-4 w-full">
      <h1 className="text-2xl font-bold mb-4">Kubrick Playground - Library</h1>

      <div>{isLoading && <LoadingOverlay isVisible={true} />}</div>
      {error && <ErrorDisplay error={error} className="mb-4 mt-4 max-w-md" />}

      {videos && videos.length > 0 ? (
        <VideoList
          videos={videos}
          page={page}
          totalVideos={total}
          perPage={PAGE_LIMIT}
          onPageChange={setPage}
        />
      ) : (
        !isLoading && <p>No videos found.</p>
      )}
    </div>
  );
};

export default Library;
