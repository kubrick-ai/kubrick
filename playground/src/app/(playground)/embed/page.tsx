"use client";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import TasksTable from "@/components/TasksTable";
import VideoUploadsForm from "@/components/VideoUploadsForm";
import { useGetAndPrefetchTasks } from "@/hooks/useKubrickAPI";
import { useState } from "react";

const PAGE_LIMIT = 10;

const Embed = () => {
  const [page, setPage] = useState(1);
  const [isAccordionOpen, setIsAccordionOpen] = useState(false);
  const { data, isLoading, error } = useGetAndPrefetchTasks(
    page - 1,
    PAGE_LIMIT,
    isAccordionOpen
  );
  const tasks = data?.data ?? [];
  const total = data?.metadata?.total ?? 0;

  const onClick = () => {
    setIsAccordionOpen(!isAccordionOpen);
  };

  return (
    <div className="px-6">
      <h1 className="text-2xl font-bold mb-6">Playground - Embed</h1>
      <div className="min-w-200">
        <VideoUploadsForm></VideoUploadsForm>
      </div>

      {/* Embedding tasks table accordion */}
      <div className="min-w-150">
        <Accordion
          type="single"
          collapsible
          className="w-full"
          defaultValue=""
          onClick={onClick}
        >
          <AccordionItem value="embedding-tasks-table" className="w-full">
            <AccordionTrigger className="w-full">
              Embedding Tasks
            </AccordionTrigger>
            <AccordionContent className="w-full flex flex-col gap-4 text-balance">
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
