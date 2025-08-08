import { useState, useEffect, useRef, useCallback } from "react";

const DEFAULT_PAGE_SIZE = 4;
const PAGINATION_CONTROLS_HEIGHT = 70;
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

  const gridContainerCallbackRef = useCallback(
    (node: HTMLDivElement | null) => {
      if (node) {
        gridContainerRef.current = node;
        // Trigger calculation when grid container is mounted
        setTimeout(() => {
          const newPageSize = calculatePageSize();
          setPageSize(newPageSize);
        }, 0);
      }
    },
    [calculatePageSize],
  );

  const sampleThumbnailCallbackRef = useCallback(
    (node: HTMLDivElement | null) => {
      if (node) {
        sampleThumbnailRef.current = node;
        // Trigger calculation when thumbnail is mounted and has dimensions
        setTimeout(() => {
          if (gridContainerRef.current) {
            const newPageSize = calculatePageSize();
            setPageSize(newPageSize);
          }
        }, 0);
      }
    },
    [calculatePageSize],
  );

  useEffect(() => {
    const updatePageSize = () => {
      const newPageSize = calculatePageSize();
      setPageSize(newPageSize);
    };

    const resizeObserver = new ResizeObserver(() => {
      updatePageSize();
    });

    if (gridContainerRef.current) {
      resizeObserver.observe(gridContainerRef.current);
      updatePageSize();
    }

    if (sampleThumbnailRef.current) {
      resizeObserver.observe(sampleThumbnailRef.current);
      if (gridContainerRef.current) {
        updatePageSize();
      }
    }

    window.addEventListener("resize", updatePageSize);

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener("resize", updatePageSize);
    };
  }, [calculatePageSize]);

  useEffect(() => {
    if (gridContainerRef.current && sampleThumbnailRef.current) {
      const newPageSize = calculatePageSize();
      setPageSize(newPageSize);
    }
  }, [calculatePageSize]);

  return {
    pageSize,
    gridContainerRef: gridContainerCallbackRef,
    sampleThumbnailRef: sampleThumbnailCallbackRef,
    calculatePageSize,
  };
};
