"use client";

import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import React from "react";

const TasksTable = () => {
  return (
    <Table>
      <TableCaption>A list of your recent embedding tasks.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead >SQS Message ID</TableHead>
          <TableHead>S3 Bucket</TableHead>
          <TableHead>S3 Key</TableHead>
          <TableHead>Created At</TableHead>
          <TableHead>Updated At</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell>1dd81af9-1def-4c19-ae0d-7eed8ff0c469</TableCell>
          <TableCell>jorge-video-upload-bucket</TableCell>
          <TableCell>Explosion Sound Effects.mp4</TableCell>
          <TableCell>2025-07-24 22:30:27</TableCell>
          <TableCell>2025-07-24 22:30:47</TableCell>
          <TableCell>Completed</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  );
};

export default TasksTable;
