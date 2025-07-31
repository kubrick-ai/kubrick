"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { CloudUpload, X } from "lucide-react";
import { useCallback, useState } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  FileUpload,
  FileUploadDropzone,
  FileUploadItem,
  FileUploadItemDelete,
  FileUploadItemMetadata,
  FileUploadItemPreview,
  FileUploadList,
  FileUploadTrigger,
} from "@/components/ui/file-upload";
import { toast } from "sonner";
import { UploadVideosFormData, UploadVideosFormDataSchema } from "@/types";
import { uploadVideo } from "@/hooks/useKubrickAPI";

const MAX_FILES = 5;
const MAX_SIZE = 2 * 1024 * 1024 * 1024;

const VideoUploadsForm = () => {
  const form = useForm<UploadVideosFormData>({
    resolver: zodResolver(UploadVideosFormDataSchema),
    defaultValues: {
      files: [],
    },
  });
  const [isSending, setIsSending] = useState(false);

  const onSubmit = useCallback(
    async (data: UploadVideosFormData) => {
      setIsSending(true);

      try {
        await Promise.all(
          data.files.map((file) => uploadVideo(file, file.name))
        );
        form.reset({ files: [] });
      } catch (error) {
        toast.error("An error occurred while uploading the videos.");
        console.error(error);
      } finally {
        setIsSending(false); // always stop sending, even if there was an error
      }
    },
    [form]
  );

  return (
    <>
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="w-full max-w-md"
        >
          <FormField
            control={form.control}
            name="files"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Attachments</FormLabel>
                <FormControl>
                  <FileUpload
                    value={field.value}
                    onValueChange={field.onChange}
                    accept="video/*"
                    maxFiles={MAX_FILES}
                    maxSize={MAX_SIZE}
                    onFileReject={(_, message) => {
                      form.setError("files", {
                        message,
                      });
                    }}
                    multiple
                  >
                    <FileUploadDropzone className="flex-row flex-wrap border-dotted text-center">
                      <CloudUpload className="size-4" />
                      Drag and drop or
                      <FileUploadTrigger asChild>
                        <Button variant="link" size="sm" className="p-0">
                          choose files
                        </Button>
                      </FileUploadTrigger>
                      to upload
                    </FileUploadDropzone>
                    <FileUploadList>
                      {field.value.map((file, index) => (
                        <FileUploadItem key={index} value={file}>
                          <FileUploadItemPreview />
                          <FileUploadItemMetadata />
                          <FileUploadItemDelete asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="size-7"
                            >
                              <X />
                              <span className="sr-only">Delete</span>
                            </Button>
                          </FileUploadItemDelete>
                        </FileUploadItem>
                      ))}
                    </FileUploadList>
                  </FileUpload>
                </FormControl>
                <FormDescription>
                  Upload up to {MAX_FILES} videos up to {MAX_SIZE / 1024 ** 3}GB each.
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
          <Button
            type="submit"
            className="mt-4"
            disabled={!form.formState.isValid || isSending}
          >
            Submit
          </Button>
        </form>
      </Form>
      {isSending && (
        <div className="pt-2">
          <p>Hang on! Uploading your video(s)...</p>
        </div>
      )}
    </>
  );
};

export default VideoUploadsForm;
