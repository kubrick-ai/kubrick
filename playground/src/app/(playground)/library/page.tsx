"use client";

import VideoList from "@/components/VideoList";
import { useGetVideos } from "@/hooks/useKubrickAPI";
import { useState } from "react";

const PAGE_LIMIT = 12;

const Library = () => {
  const [page, setPage] = useState(1);
  const { data, isLoading, error } = useGetVideos(page - 1, PAGE_LIMIT);
  const videos = data?.videos ?? [];
  const totalVideos = data?.total ?? 0;

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
          totalVideos={totalVideos}
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
