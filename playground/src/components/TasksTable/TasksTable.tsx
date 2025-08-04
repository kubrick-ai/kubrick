"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import {
  IconCircleCheckFilled,
  IconLoader,
  IconAlertCircleFilled,
  IconCopy,
} from "@tabler/icons-react";
import { toast } from "sonner";
import { Task } from "@/types";
import dayjs from "dayjs";
import React from "react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface TasksListProps {
  tasks: Array<Task>;
  page: number;
  totalTasks: number;
  perPage: number;
  onPageChange: (page: number) => void;
}

const TasksTable = ({
  tasks,
  page,
  totalTasks,
  perPage,
  onPageChange,
}: TasksListProps) => {
  const totalPages = Math.ceil(totalTasks / perPage);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("SQS Message ID copied!");
  };

  return (
    <>
      <div>
        <Table className="w-full table-fixed min-h-[400px]">
          <TableHeader>
            <TableRow>
              <TableHead className="w-[180px]">SQS Message ID</TableHead>
              <TableHead className="w-[200px]">S3 Bucket</TableHead>
              <TableHead className="w-[250px]">S3 Key</TableHead>
              <TableHead className="w-[180px]">Created At</TableHead>
              <TableHead className="w-[180px]">Updated At</TableHead>
              <TableHead className="w-[150px]">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TooltipProvider>
              {tasks.map((task) => (
                <TableRow key={task.id}>
                  <TableCell className="align-top">
                    <div className="flex items-center gap-2">
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <span className="truncate max-w-[200px]">
                            {task.sqs_message_id}
                          </span>
                        </TooltipTrigger>
                        <TooltipContent>{task.sqs_message_id}</TooltipContent>
                      </Tooltip>
                      {task.sqs_message_id && (
                        <button
                          onClick={() =>
                            handleCopy(
                              task.sqs_message_id ? task.sqs_message_id : "",
                            )
                          }
                          className="text-muted-foreground hover:text-foreground transition"
                          aria-label="Copy SQS Message ID"
                        >
                          <IconCopy className="size-4" />
                        </button>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="truncate max-w-[200px] align-top">
                    {task.s3_bucket}
                  </TableCell>
                  <TableCell className="truncate max-w-[200px] align-top">
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <span>{task.s3_key}</span>
                      </TooltipTrigger>
                      <TooltipContent>{task.s3_key}</TooltipContent>
                    </Tooltip>
                  </TableCell>
                  <TableCell className="truncate max-w-[200px] align-top">
                    {dayjs(task.created_at).format("YYYY:MM:DD HH:mm:ss")}
                  </TableCell>
                  <TableCell className="truncate max-w-[200px] align-top">
                    {dayjs(task.updated_at).format("YYYY:MM:DD HH:mm:ss")}
                  </TableCell>
                  <TableCell className="align-top">
                    <div className="flex items-center gap-2 truncate max-w-[200px]">
                      {task.status === "completed" ? (
                        <IconCircleCheckFilled className="size-4 fill-green-500 dark:fill-green-400" />
                      ) : task.status === "processing" ? (
                        <IconLoader className="size-4 animate-spin text-yellow-500" />
                      ) : (
                        <IconAlertCircleFilled className="size-4 text-red-400" />
                      )}
                      {task.status[0].toUpperCase() + task.status.slice(1)}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TooltipProvider>
          </TableBody>
        </Table>
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

export default TasksTable;
