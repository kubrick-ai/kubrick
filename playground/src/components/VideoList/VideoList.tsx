"use client";

import { Video } from "@/types";
import VideoThumbnail from "@/components/VideoThumbnail";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useState } from "react";

interface VideoListProps {
  videos: Array<Video>;
}

const THUMBNAILS_PER_PAGE = 12;

const VideoList = ({ videos }: VideoListProps) => {
  const [page, setPage] = useState(1);

  const totalPages = Math.ceil(videos.length / THUMBNAILS_PER_PAGE);

  // Calculate start/end indices for current page
  const startIdx = (page - 1) * THUMBNAILS_PER_PAGE;
  const endIdx = startIdx + THUMBNAILS_PER_PAGE;

  // Slice videos for current page
  const currentVideos = videos.slice(startIdx, endIdx);

  return (
    <>
      <div className="flex flex-wrap gap-4 justify-start">
        {currentVideos.map((video) => (
          <VideoThumbnail key={video.id} video={video}>
            <div className="space-y-2 text-sm">
              <div className="font-medium truncate">{video.filename}</div>

              <div className="flex gap-2 flex-wrap">
                <Badge variant="secondary" className="text-xs">
                  {video.duration}s
                </Badge>
                <Badge variant="outline" className="text-xs">
                  {video.width}×{video.height}
                </Badge>
              </div>

              <Separator />

              <div className="text-xs text-muted-foreground space-y-1">
                <div>{video.created_at}</div>
                <a
                  href={video.url}
                  className="text-blue-600 hover:text-blue-800 underline inline-block max-w-full overflow-hidden whitespace-nowrap text-ellipsis"
                  target="_blank"
                  rel="noopener noreferrer"
                  title={video.url}
                >
                  source
                </a>
              </div>
            </div>
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

export default VideoList;
