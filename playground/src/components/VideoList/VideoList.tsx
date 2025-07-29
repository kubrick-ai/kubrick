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
}

const VideoList = ({
  videos,
  page,
  totalVideos,
  perPage,
  onPageChange,
}: VideoListProps) => {
  const totalPages = Math.ceil(totalVideos / perPage);

  return (
    <>
      <div className="flex flex-wrap gap-4 justify-start">
        {videos.map((video) => (
          <VideoThumbnail key={video.id} video={video}>
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
                <div>Upload date: {video.created_at.split("T")[0]}</div>
              </div>
            </div>
          </VideoThumbnail>
        ))}
      </div>

      {/* Pagination controls */}
      <div className="mt-6 flex justify-center items-center gap-4">
        <Button
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
          variant="outline"
          disabled={page >= totalPages}
          onClick={() => onPageChange(Math.min(totalPages, page + 1))}
        >
          Next
        </Button>
      </div>
    </>
  );
};

export default VideoList;
