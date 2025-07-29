"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormField,
  FormItem,
  FormControl,
  FormMessage,
} from "@/components/ui/form";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import TasksTable from "@/components/TasksTable";
import { useEmbedVideo, useGetTasks } from "@/hooks/useKubrickAPI";
import { useState } from "react";

const PAGE_LIMIT = 10;

const embedFormSchema = z.object({
  video_url: z.string().url("Please enter a valid URL"),
});

type EmbedForm = z.infer<typeof embedFormSchema>;

const Embed = () => {
  const form = useForm<EmbedForm>({
    resolver: zodResolver(embedFormSchema),
    defaultValues: { video_url: "" },
  });
  const [page, setPage] = useState(1);
  const { data, isLoading, error } = useGetTasks(page - 1, PAGE_LIMIT);
  const tasks = data?.data ?? [];
  const total = data?.metadata?.total ?? 0;

  const {
    submitVideo,
    isSubmitting,
    embedData,
    statusData,
    isPolling,
    submitError,
  } = useEmbedVideo();

  const onSubmit = (values: EmbedForm) => {
    submitVideo(values.video_url);
    form.reset();
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Playground - Embed</h1>

      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex w-full max-w-lg items-center gap-1"
        >
          <FormField
            control={form.control}
            name="video_url"
            render={({ field }) => (
              <FormItem>
                <FormControl>
                  <Input
                    className="min-w-90"
                    placeholder="Paste video URL (e.g. from S3)"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Submitting..." : "Embed"}
          </Button>
        </form>
      </Form>

      {/* Task Info */}
      {embedData && (
        <div className="mt-6">
          <h2 className="text-lg font-semibold">Task Created</h2>
          <p className="text-sm text-gray-600">Task ID: {embedData.id}</p>
          <p className="text-sm text-gray-600">
            Video URL: {embedData.video_url}
          </p>
        </div>
      )}

      {/* POST /tasks error */}
      {submitError && (
        <p className="text-red-500">Error: {submitError.message}</p>
      )}

      {/* Status Info */}
      {statusData && (
        <div className="mt-6">
          <h2 className="text-lg font-semibold">Task Status</h2>
          <div className="text-sm text-gray-600 space-y-1">
            <p>
              <span className="font-medium">Status:</span> {statusData.status}
              {isPolling && " (refreshing...)"}
            </p>

            {/* GET /tasks/<task_id> error */}
            {statusData.error && (
              <p className="text-red-500">
                <span className="font-medium">Error:</span> {statusData.error}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Embedding tasks table accordion */}
      <div className="pt-3">
        <Accordion type="single" collapsible className="w-full" defaultValue="">
          <AccordionItem value="embedding-tasks-table">
            <AccordionTrigger>Embedding Tasks</AccordionTrigger>
            <AccordionContent className="flex flex-col gap-4 text-balance">
              {isLoading && <p>Loading embedding tasks...</p>}
              {error && (
                <p className="text-red-500">
                  Error loading embedding tasks: {error.message}
                </p>
              )}
              {tasks && tasks.length > 0 ? (
                <TasksTable
                  tasks={tasks}
                  page={page}
                  totalTasks={total}
                  perPage={PAGE_LIMIT}
                  onPageChange={setPage}
                ></TasksTable>
              ) : (
                !isLoading && <p>No tasks found.</p>
              )}
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </div>
    </div>
  );
};

export default Embed;
