import { useState, useEffect, useCallback } from "react";

const DEFAULT_PAGE_SIZE = 4;
const PAGINATION_CONTROLS_HEIGHT = 70;
const DEFAULT_GAP = 16;
const MIN_VISIBLE_ROWS = 1;

export const useViewportPagination = () => {
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [gridContainer, setGridContainer] = useState<HTMLDivElement | null>(
    null,
  );
  const [sampleThumbnail, setSampleThumbnail] = useState<HTMLDivElement | null>(
    null,
  );

  const calculatePageSize = useCallback(() => {
    try {
      if (typeof window === "undefined" || !gridContainer || !sampleThumbnail) {
        return DEFAULT_PAGE_SIZE;
      }

      const computedStyle = window.getComputedStyle(gridContainer);
      const columns = computedStyle.gridTemplateColumns.split(" ").length;

      const thumbnailHeight = sampleThumbnail.getBoundingClientRect().height;
      const gap = parseFloat(computedStyle.gap) || DEFAULT_GAP;
      const viewportHeight = window.innerHeight;
      const containerTop = gridContainer.getBoundingClientRect().top;
      const availableHeight =
        viewportHeight - containerTop - PAGINATION_CONTROLS_HEIGHT;

      const visibleRows = Math.max(
        MIN_VISIBLE_ROWS,
        Math.floor(availableHeight / (thumbnailHeight + gap)),
      );

      return Math.max(MIN_VISIBLE_ROWS, columns * visibleRows);
    } catch (error) {
      console.warn("Failed to calculate page size:", error);
      return DEFAULT_PAGE_SIZE;
    }
  }, [gridContainer, sampleThumbnail]);

  useEffect(() => {
    if (!gridContainer || !sampleThumbnail) return;

    const updatePageSize = () => {
      const newPageSize = calculatePageSize();
      setPageSize(newPageSize);
    };

    updatePageSize();

    const resizeObserver = new ResizeObserver(updatePageSize);
    resizeObserver.observe(gridContainer);
    resizeObserver.observe(sampleThumbnail);

    window.addEventListener("resize", updatePageSize);

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener("resize", updatePageSize);
    };
  }, [calculatePageSize, gridContainer, sampleThumbnail]);

  return {
    pageSize,
    gridContainerRef: setGridContainer,
    sampleThumbnailRef: setSampleThumbnail,
    calculatePageSize,
  };
};
