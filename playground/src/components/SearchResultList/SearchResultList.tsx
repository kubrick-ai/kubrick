"use client";

import { SearchResult } from "@/types";
import VideoThumbnail from "@/components/VideoThumbnail";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { useViewportPagination, DEFAULT_PAGE_SIZE } from "@/hooks/useViewportPagination";

interface SearchResultListProps {
  results: Array<SearchResult>;
}

const SearchResultList = ({ results }: SearchResultListProps) => {
  const [page, setPage] = useState(0);
  const { pageSize, gridContainerRef, sampleThumbnailRef } =
    useViewportPagination();
  const effectivePageSize = pageSize ?? DEFAULT_PAGE_SIZE;
  const maxPage = Math.ceil(results.length / effectivePageSize) - 1;

  // Calculate start/end indices for current page
  const startIdx = page * effectivePageSize;
  const endIdx = startIdx + effectivePageSize;

  // Slice videos for current page
  const currentResults = results.slice(startIdx, endIdx);

  return (
    <>
      <div
        ref={gridContainerRef}
        className="grid grid-cols-[repeat(auto-fill,minmax(250px,1fr))] gap-4"
      >
        {currentResults.map((result, index) => (
          <div
            key={result.id}
            ref={index === 0 ? sampleThumbnailRef : undefined}
            className="h-full"
          >
            <VideoThumbnail
              video={result.video}
              startTime={result.start_time ?? 0}
              enableChapters={true}
            >
              {result.modality && <p>Modality: {result.modality}</p>}
              {result.scope && <p>Scope: {result.scope}</p>}
              {result.similarity && (
                <p>Similarity: {result.similarity.toFixed(5)}</p>
              )}
            </VideoThumbnail>
          </div>
        ))}
      </div>

      {/* Pagination controls */}
      <div className="mt-6 flex justify-center items-center gap-4">
        <Button
          className="cursor-pointer"
          variant="outline"
          disabled={!page}
          onClick={() => setPage((p) => Math.max(0, p - 1))}
        >
          Previous
        </Button>

        <span>
          Page {results.length === 0 ? 0 : page + 1} of {maxPage + 1}
        </span>

        <Button
          className="cursor-pointer"
          variant="outline"
          disabled={page === maxPage || results.length === 0}
          onClick={() => setPage((p) => Math.min(maxPage, p + 1))}
        >
          Next
        </Button>
      </div>
    </>
  );
};

export default SearchResultList;
