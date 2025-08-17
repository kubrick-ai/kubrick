"use client";

import ErrorDisplay from "@/components/ErrorDisplay";
import VideoList from "@/components/VideoList";
import { useGetAndPrefetchVideos } from "@/hooks/useKubrickAPI";
import { useState } from "react";
import LoadingOverlay from "@/components/LoadingOverlay";
import {
  useViewportPagination,
  DEFAULT_PAGE_SIZE,
} from "@/hooks/useViewportPagination";

const Library = () => {
  const [page, setPage] = useState(1);
  const { pageSize, gridContainerRef, sampleThumbnailRef } =
    useViewportPagination();
  const { data, isLoading, error } = useGetAndPrefetchVideos(
    page - 1,
    pageSize ?? DEFAULT_PAGE_SIZE,
    { enabled: pageSize !== null },
  );
  const videos = data?.data ?? [];
  const total = data?.metadata?.total ?? 0;

  return (
    <div className="px-6 pb-6 pt-1 grow flex flex-col">
      <h1 className="text-2xl font-bold mb-4 grow-0">Playground - Library</h1>

      {(isLoading || pageSize === null) && <LoadingOverlay isVisible={true} />}
      {error && <ErrorDisplay error={error} className="mb-4 mt-4 max-w-md" />}

      {!isLoading && !!videos.length && !error && (
        <VideoList
          videos={videos}
          page={page}
          totalVideos={total}
          perPage={pageSize ?? DEFAULT_PAGE_SIZE}
          onPageChange={setPage}
          gridContainerRef={gridContainerRef}
          sampleThumbnailRef={sampleThumbnailRef}
        />
      )}
      {!isLoading && videos.length === 0 && !error && pageSize !== null && (
        <p>No videos found.</p>
      )}
    </div>
  );
};

export default Library;
