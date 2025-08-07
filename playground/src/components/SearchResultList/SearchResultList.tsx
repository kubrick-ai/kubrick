"use client";

import { SearchResult } from "@/types";
import VideoThumbnail from "@/components/VideoThumbnail";
import { Button } from "@/components/ui/button";
import { useState } from "react";

interface SearchResultListProps {
  results: Array<SearchResult>;
}

const THUMBNAILS_PER_PAGE = 8;

const SearchResultList = ({ results }: SearchResultListProps) => {
  const [page, setPage] = useState(0);
  const maxPage = Math.ceil(results.length / THUMBNAILS_PER_PAGE) - 1;

  // Calculate start/end indices for current page
  const startIdx = page * THUMBNAILS_PER_PAGE;
  const endIdx = startIdx + THUMBNAILS_PER_PAGE;

  // Slice videos for current page
  const currentResults = results.slice(startIdx, endIdx);

  return (
    <>
      <div className="grid grid-cols-[repeat(auto-fill,minmax(250px,1fr))] gap-4 ">
        {currentResults.map((result) => (
          <VideoThumbnail
            key={result.id}
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
