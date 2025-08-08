"use client";

import { Video } from "@/types";
import VideoThumbnail from "@/components/VideoThumbnail";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

interface VideoListProps {
  videos: Array<Video>;
  page: number;
  totalVideos: number;
  perPage: number;
  onPageChange: (page: number) => void;
  gridContainerRef?: (node: HTMLDivElement | null) => void;
  sampleThumbnailRef?: (node: HTMLDivElement | null) => void;
}

const VideoList = ({
  videos,
  page,
  totalVideos,
  perPage,
  onPageChange,
  gridContainerRef,
  sampleThumbnailRef,
}: VideoListProps) => {
  const totalPages = Math.ceil(totalVideos / perPage);

  return (
    <div className="w-full">
      <div
        ref={gridContainerRef}
        className="grid grid-cols-[repeat(auto-fill,minmax(250px,1fr))] gap-4 items-start"
      >
        {/* Hidden dummy element for measuring dimensions */}
        {videos.length === 0 && (
          <div
            ref={sampleThumbnailRef}
            className="h-full opacity-0 pointer-events-none"
            style={{ minHeight: "260px" }} // Approximate thumbnail height
          />
        )}
        {videos.map((video, index) => (
          <div
            key={video.id}
            ref={index === 0 ? sampleThumbnailRef : undefined}
            className="h-full"
          >
            <VideoThumbnail video={video}>
              <div className="space-y-2 text-sm">
                <div className="flex gap-2 flex-wrap">
                  <Badge variant="secondary" className="text-xs">
                    {video.duration}s
                  </Badge>
                  {video.width && video.height && (
                    <Badge variant="outline" className="text-xs">
                      {video.width}×{video.height}
                    </Badge>
                  )}
                </div>

                <Separator />

                <div className="text-xs text-muted-foreground space-y-1">
                  <div>
                    Upload date:{" "}
                    {new Date(video.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            </VideoThumbnail>
          </div>
        ))}
      </div>
      {/* Pagination controls */}
      <div className="mt-6 flex justify-center items-center gap-4">
        <Button
          className="cursor-pointer"
          variant="outline"
          disabled={page <= 1}
          onClick={() => onPageChange(Math.max(1, page - 1))}
        >
          Previous
        </Button>

        <span>
          Page {page} of {totalPages}
        </span>

        <Button
          className="cursor-pointer"
          variant="outline"
          disabled={page >= totalPages}
          onClick={() => onPageChange(Math.min(totalPages, page + 1))}
        >
          Next
        </Button>
      </div>
    </div>
  );
};

export default VideoList;
