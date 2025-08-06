"use client";

import { useState } from "react";
import { useSearchVideos } from "@/hooks/useKubrickAPI";
import SearchResultList from "@/components/SearchResultList";
import { SearchParams } from "@/types";
import SearchForm from "@/components/SearchForm";
import ErrorDisplay from "@/components/ErrorDisplay";

const Search = () => {
  const [searchParams, setSearchParams] = useState<SearchParams>({
    query_type: "text",
  });
  const [isOptionsOpen, setIsOptionsOpen] = useState(false);
  const { data: results, isLoading, error } = useSearchVideos(searchParams);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Playground - Search</h1>
      <SearchForm
        setSearchParams={setSearchParams}
        isOptionsOpen={isOptionsOpen}
        setIsOptionsOpen={setIsOptionsOpen}
      />

      {isLoading && <p>Loading...</p>}
      {error && <ErrorDisplay error={error} className="mb-4 mt-4 max-w-md" />}

      {results && (
        <div>
          <h2 className="text-xl font-semibold mb-4 pt-5">
            Results ({results.length})
          </h2>
          <SearchResultList results={results} />
        </div>
      )}
    </div>
  );
};

export default Search;
