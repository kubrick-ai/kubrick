"use client";

import { SearchResult } from "@/types";
import VideoThumbnail from "@/components/VideoThumbnail";
import { Button } from "@/components/ui/button";
import { useState } from "react";

interface SearchResultListProps {
  results: Array<SearchResult>;
}

const THUMBNAILS_PER_PAGE = 12;

const SearchResultList = ({ results }: SearchResultListProps) => {
  const [page, setPage] = useState(1);

  const totalPages = Math.ceil(results.length / THUMBNAILS_PER_PAGE);

  // Calculate start/end indices for current page
  const startIdx = (page - 1) * THUMBNAILS_PER_PAGE;
  const endIdx = startIdx + THUMBNAILS_PER_PAGE;

  // Slice videos for current page
  const currentResults = results.slice(startIdx, endIdx);

  return (
    <>
      <div className="flex flex-wrap gap-4 justify-start">
        {currentResults.map((result) => (
          <VideoThumbnail
            key={result.id}
            video={result.video}
            startTime={result.start_time ?? 0}
          >
            {result.modality && <p>Modality: {result.modality}</p>}
            {result.scope && <p>Scope: {result.scope}</p>}
            {result.similarity && (
              <p>Similarity: {result.similarity.toFixed(5)}</p>
            )}
          </VideoThumbnail>
        ))}
      </div>

      {/* Pagination controls */}
      <div className="mt-6 flex justify-center items-center gap-4">
        <Button
          variant="outline"
          disabled={page === 1}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
        >
          Previous
        </Button>

        <span>
          Page {page} of {totalPages}
        </span>

        <Button
          variant="outline"
          disabled={page === totalPages}
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
        >
          Next
        </Button>
      </div>
    </>
  );
};

export default SearchResultList;
