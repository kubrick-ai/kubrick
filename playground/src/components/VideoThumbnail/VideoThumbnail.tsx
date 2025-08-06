"use client";

import * as MediaPlayer from "@/components/ui/media-player";
import { useEffect, useRef } from "react";
import {
  Card,
  CardContent,
  CardTitle,
  CardDescription,
  CardFooter,
} from "@/components/ui/card";
import { Video } from "@/types";

interface VideoThumbnailProps {
  video: Video;
  startTime?: number;
  endTime?: number;
  width?: number;
  height?: number;
  children?: React.ReactNode;
  enableChapters?: boolean;
}

const VideoThumbnail = ({
  video,
  startTime = 0,
  width = 300,
  height = 300,
  children,
  enableChapters = false,
}: VideoThumbnailProps) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const clipLength = 6;

  useEffect(() => {
    const mediaElement = videoRef.current;
    if (!mediaElement || !enableChapters) return;

    const handleLoadedMetadata = () => {
      // Remove any existing chapter tracks
      const existingTracks = Array.from(mediaElement.textTracks).filter(
        (track) => track.kind === "chapters"
      );
      existingTracks.forEach((track) => {
        // Clear existing cues
        while (track.cues && track.cues.length > 0) {
          track.removeCue(track.cues[0]);
        }
      });

      const chapterTrack = mediaElement.addTextTrack(
        "chapters",
        "Chapters",
        "en"
      );
      chapterTrack.mode = "hidden";

      const duration = mediaElement.duration;
      const clipEndTime = startTime + clipLength;

      if (startTime > 0) {
        const preclipCue = new VTTCue(0, startTime, "");
        chapterTrack.addCue(preclipCue);
      }

      const clipCue = new VTTCue(
        startTime,
        Math.min(clipEndTime, duration),
        "Result"
      );
      chapterTrack.addCue(clipCue);

      if (clipEndTime < duration) {
        const postclipCue = new VTTCue(clipEndTime, duration, "");
        chapterTrack.addCue(postclipCue);
      }
    };

    if (mediaElement.readyState >= 1) {
      handleLoadedMetadata();
    } else {
      mediaElement.addEventListener("loadedmetadata", handleLoadedMetadata);
    }

    return () => {
      mediaElement.removeEventListener("loadedmetadata", handleLoadedMetadata);
    };
  }, [startTime, enableChapters]);

  useEffect(() => {
    const curVideo = videoRef.current;
    if (!curVideo) return;

    const setInitialTime = () => {
      curVideo.currentTime = startTime;
    };

    if (curVideo.readyState >= 1) {
      setInitialTime();
    } else {
      curVideo.addEventListener("loadedmetadata", setInitialTime);
    }

    return () => {
      curVideo.removeEventListener("loadedmetadata", setInitialTime);
    };
  }, [startTime]);

  return (
    <Card className="w-full relative overflow-hidden rounded-xl shadow-sm pt-0">
      <CardContent className="p-0">
        <div className="relative w-full aspect-video">
          <MediaPlayer.Root
            autoHide={false}
            className="absolute inset-0 w-full h-full"
          >
            <MediaPlayer.Video
              ref={videoRef}
              className="w-full h-full object-cover rounded-md"
            >
              <source src={video.url} type="video/mp4" />
            </MediaPlayer.Video>

            <MediaPlayer.Loading />
            <MediaPlayer.Error />
            <MediaPlayer.VolumeIndicator />

            <MediaPlayer.Controls className="absolute bottom-0 left-0 w-full p-2 bg-gradient-to-t from-black/60 to-transparent flex flex-col gap-1">
              <MediaPlayer.ControlsOverlay />

              <div className="flex items-center gap-2 justify-between">
                <div className="flex items-center gap-2">
                  <MediaPlayer.Play className="text-white w-6 h-6 cursor-pointer" />
                  <MediaPlayer.Time />
                </div>
                <div className="flex items-center gap-2">
                  <MediaPlayer.Volume className="cursor-pointer" />
                  <MediaPlayer.Fullscreen className="cursor-pointer" />
                </div>
              </div>

              <MediaPlayer.Seek withoutChapter={!enableChapters} />
            </MediaPlayer.Controls>
          </MediaPlayer.Root>
        </div>
      </CardContent>

      <CardFooter className="flex-col items-start gap-2 px-4">
        <a href={video.url} target="_blank" rel="noopener">
          <CardTitle className="hover:underline cursor-pointer">
            {video.filename}
          </CardTitle>
        </a>
        <CardDescription>{children}</CardDescription>
      </CardFooter>
    </Card>
  );
};

export default VideoThumbnail;
