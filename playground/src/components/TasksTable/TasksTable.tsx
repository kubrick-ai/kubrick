"use client";

import {
  Table,
  TableBody,
  // TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Task } from "@/types";

import React from "react";

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

  function formatDateTime(isoString: string) {
    const date = new Date(isoString);
    const pad = (n: number) => String(n).padStart(2, "0");

    const year = date.getFullYear();
    const month = pad(date.getMonth() + 1);
    const day = pad(date.getDate());
    const hours = pad(date.getHours());
    const minutes = pad(date.getMinutes());
    const seconds = pad(date.getSeconds());

    return `${year}:${month}:${day} ${hours}:${minutes}:${seconds}`;
  }

  return (
    <>
      <Table>
        {/* <TableCaption>A list of your recent embedding tasks.</TableCaption> */}
        <TableHeader>
          <TableRow>
            <TableHead>SQS Message ID</TableHead>
            <TableHead>S3 Bucket</TableHead>
            <TableHead>S3 Key</TableHead>
            <TableHead>Created At</TableHead>
            <TableHead>Updated At</TableHead>
            <TableHead>Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {tasks.map((task) => (
            <TableRow key={task.id}>
              <TableCell>
                {task.sqs_message_id ? task.sqs_message_id : ""}
              </TableCell>
              <TableCell>{task.s3_bucket}</TableCell>
              <TableCell>{task.s3_key}</TableCell>
              <TableCell>{formatDateTime(task.created_at)}</TableCell>
              <TableCell>{formatDateTime(task.updated_at)}</TableCell>
              <TableCell>{task.status}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
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
