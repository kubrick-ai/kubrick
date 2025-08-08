import { useState, useEffect, useRef, useCallback } from "react";

const DEFAULT_PAGE_SIZE = 10;
const PAGINATION_CONTROLS_HEIGHT = 100;
const DEFAULT_GAP = 16;
const MIN_VISIBLE_ROWS = 1;

export const useViewportPagination = () => {
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const gridContainerRef = useRef<HTMLDivElement>(null);
  const sampleThumbnailRef = useRef<HTMLDivElement>(null);

  const calculatePageSize = useCallback(() => {
    try {
      if (typeof window === "undefined" || !gridContainerRef.current) {
        return DEFAULT_PAGE_SIZE;
      }

      const gridContainer = gridContainerRef.current;
      const computedStyle = window.getComputedStyle(gridContainer);

      const gridTemplateColumns = computedStyle.gridTemplateColumns;
      const columns = gridTemplateColumns.split(" ").length;

      let visibleRows = MIN_VISIBLE_ROWS;

      if (sampleThumbnailRef.current) {
        const thumbnailHeight =
          sampleThumbnailRef.current.getBoundingClientRect().height;
        const gap = parseFloat(computedStyle.gap) || DEFAULT_GAP;
        const viewportHeight = window.innerHeight;
        const containerTop = gridContainer.getBoundingClientRect().top;
        const availableHeight =
          viewportHeight - containerTop - PAGINATION_CONTROLS_HEIGHT;

        visibleRows = Math.max(
          MIN_VISIBLE_ROWS,
          Math.floor(availableHeight / (thumbnailHeight + gap)),
        );
      }

      return Math.max(MIN_VISIBLE_ROWS, columns * visibleRows);
    } catch (error) {
      console.warn("Failed to calculate page size:", error);
      return DEFAULT_PAGE_SIZE;
    }
  }, []);

  useEffect(() => {
    const updatePageSize = () => {
      const newPageSize = calculatePageSize();
      setPageSize(newPageSize);
    };

    if (document.readyState === "complete") {
      updatePageSize();
    } else {
      window.addEventListener("load", updatePageSize);
    }

    window.addEventListener("resize", updatePageSize);

    return () => {
      window.removeEventListener("load", updatePageSize);
      window.removeEventListener("resize", updatePageSize);
    };
  }, [calculatePageSize]);

  return {
    pageSize,
    gridContainerRef,
    sampleThumbnailRef,
    calculatePageSize,
  };
};
