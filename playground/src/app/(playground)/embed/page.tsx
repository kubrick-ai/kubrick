"use client";

import VideoUploadsForm from "@/components/VideoUploadsForm";

const Embed = () => {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Playground - Embed</h1>
      <div className="min-w-200">
        <VideoUploadsForm />
      </div>
    </div>
  );
};

export default Embed;
