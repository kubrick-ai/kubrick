"use client";

import { useState } from "react";
import { useSearchVideos } from "@/hooks/useKubrickAPI";
import SearchResultList from "@/components/SearchResultList";
import { SearchParams } from "@/types";
import SearchForm from "@/components/SearchForm";
import ErrorDisplay from "@/components/ErrorDisplay";
import LoadingOverlay from "@/components/LoadingOverlay";

const Search = () => {
  const [searchParams, setSearchParams] = useState<SearchParams>({
    query_type: "text",
  });
  const [isOptionsOpen, setIsOptionsOpen] = useState(false);
  const { data: results, isLoading, error } = useSearchVideos(searchParams);

  return (
    <div className="px-6 py-1 flex flex-col grow">
      <h1 className="grow-0 text-2xl font-bold mb-6">Playground - Search</h1>
      <SearchForm
        setSearchParams={setSearchParams}
        isOptionsOpen={isOptionsOpen}
        setIsOptionsOpen={setIsOptionsOpen}
      />

      {isLoading && <LoadingOverlay isVisible={true} />}
      {error && <ErrorDisplay error={error} className="mb-4 mt-4 max-w-md" />}

      {results && (
        <div className="h-full">
          <h2 className="text-xl font-semibold mb-4">
            Results ({results.length})
          </h2>
          <SearchResultList results={results} />
        </div>
      )}
    </div>
  );
};

export default Search;
