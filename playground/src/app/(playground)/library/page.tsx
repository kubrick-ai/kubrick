"use client";

import VideoList from "@/components/VideoList";
import { useGetVideos } from "@/hooks/useKubrickAPI";

const Library = () => {
  // Currently the backend API endpoint only returns 10 by default;
  // FE needs to be fixed to work with backend and utilize this service
  // I also think the OFFSET in the backend needs a fix to make it work properly
  const { data: videos, isLoading, error } = useGetVideos(0, 50);

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Kubrick Playground - Library</h1>

      {isLoading && <p>Loading videos...</p>}
      {error && (
        <p className="text-red-500">Error loading videos: {error.message}</p>
      )}

      {videos && videos.length > 0 ? (
        <VideoList videos={videos} />
      ) : (
        !isLoading && <p>No videos found.</p>
      )}
    </div>
  );
};

export default Library;
