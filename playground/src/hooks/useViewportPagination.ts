import { useState, useEffect, useRef } from "react";

export const useViewportPagination = () => {
  const [pageSize, setPageSize] = useState(10);
  const gridContainerRef = useRef<HTMLDivElement>(null);
  const sampleThumbnailRef = useRef<HTMLDivElement>(null);

  const calculatePageSize = () => {
    if (typeof window === "undefined" || !gridContainerRef.current) return 10;

    const gridContainer = gridContainerRef.current;
    const computedStyle = window.getComputedStyle(gridContainer);

    const gridTemplateColumns = computedStyle.gridTemplateColumns;
    const columns = gridTemplateColumns.split(" ").length;

    let visibleRows = 1;

    if (sampleThumbnailRef.current) {
      const thumbnailHeight =
        sampleThumbnailRef.current.getBoundingClientRect().height;
      const gap = parseFloat(computedStyle.gap) || 16;
      const viewportHeight = window.innerHeight;
      const containerTop = gridContainer.getBoundingClientRect().top;
      const paginationControlsHeight = 100; // More conservative buffer
      const availableHeight =
        viewportHeight - containerTop - paginationControlsHeight;

      visibleRows = Math.max(
        1,
        Math.floor(availableHeight / (thumbnailHeight + gap)),
      );
    }

    const rows = visibleRows;

    return Math.max(1, columns * rows);
  };

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

    // Cleanup
    return () => {
      window.removeEventListener("load", updatePageSize);
    };
  }, []);

  return {
    pageSize,
    gridContainerRef,
    sampleThumbnailRef,
    calculatePageSize,
  };
};
