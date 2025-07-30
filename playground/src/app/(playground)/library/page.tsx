"use client";

import VideoList from "@/components/VideoList";
import { useGetAndPrefetchVideos } from "@/hooks/useKubrickAPI";
import { useState } from "react";

const PAGE_LIMIT = 12;

const Library = () => {
  const [page, setPage] = useState(1);
  const { data, isLoading, error } = useGetAndPrefetchVideos(page - 1, PAGE_LIMIT);
  const videos = data?.data ?? [];
  const total = data?.metadata?.total ?? 0;

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Kubrick Playground - Library</h1>

      {isLoading && <p>Loading videos...</p>}
      {error && (
        <p className="text-red-500">Error loading videos: {error.message}</p>
      )}

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
