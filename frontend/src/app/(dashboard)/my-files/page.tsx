"use client";

import { useState } from "react";
import { Upload, FileSpreadsheet } from "lucide-react";
import { useDropzone } from "react-dropzone";
import { useQueryClient } from "@tanstack/react-query";
import { useFiles } from "@/hooks/useFileManager";
import { FileUploadZone } from "@/components/file/FileUploadZone";
import { MyFilesTable } from "@/components/file/MyFilesTable";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

/**
 * My Files page - standalone file management screen at /my-files.
 * Shows all uploaded files in a table with drag-and-drop upload zone at top.
 */
export default function MyFilesPage() {
  const queryClient = useQueryClient();
  const { data: files, isLoading } = useFiles();
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: () => {
      // Open the upload dialog - FileUploadZone handles the actual upload
      setUploadDialogOpen(true);
    },
    accept: {
      "text/csv": [".csv"],
      "application/vnd.ms-excel": [".xls"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
        ".xlsx",
      ],
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    multiple: false,
    noKeyboard: true,
  });

  const handleUploadComplete = () => {
    setUploadDialogOpen(false);
    queryClient.invalidateQueries({ queryKey: ["files"] });
  };

  const hasFiles = (files?.length ?? 0) > 0;

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-6xl mx-auto px-6 py-8 space-y-6">
          {/* Page header */}
          <div>
            <h1 className="text-2xl font-bold tracking-tight">My Files</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Manage your uploaded data files
            </p>
          </div>

          {/* Drag-and-drop zone */}
          <div
            {...getRootProps()}
            className={`
              border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
              transition-all duration-200 ease-in-out
              ${
                isDragActive
                  ? "border-primary bg-primary/5 scale-[1.01]"
                  : "border-border hover:border-primary/50 hover:bg-accent/50"
              }
            `}
          >
            <input {...getInputProps()} />
            <div className="flex flex-col items-center gap-2">
              <div
                className={`rounded-full p-3 ${isDragActive ? "bg-primary/10" : "bg-accent"}`}
              >
                <Upload
                  className={`h-6 w-6 ${isDragActive ? "text-primary" : "text-muted-foreground"}`}
                />
              </div>
              <p className="font-medium text-sm">
                {isDragActive
                  ? "Drop your file here"
                  : "Drag files here to upload"}
              </p>
              <p className="text-xs text-muted-foreground">
                or click to browse
              </p>
            </div>
          </div>

          {/* Upload button */}
          <div>
            <Button
              variant="outline"
              onClick={() => setUploadDialogOpen(true)}
              className="gap-2"
            >
              <Upload className="h-4 w-4" />
              Upload File
            </Button>
          </div>

          {/* Empty state or table */}
          {!isLoading && !hasFiles ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="rounded-full p-4 bg-accent mb-4">
                <FileSpreadsheet className="h-10 w-10 text-muted-foreground" />
              </div>
              <h2 className="text-lg font-semibold mb-1">No files yet</h2>
              <p className="text-sm text-muted-foreground mb-4 max-w-sm">
                Upload your first file to start analyzing data with AI-powered
                insights
              </p>
              <Button onClick={() => setUploadDialogOpen(true)} className="gap-2">
                <Upload className="h-4 w-4" />
                Upload your first file
              </Button>
            </div>
          ) : (
            <MyFilesTable files={files ?? []} isLoading={isLoading} />
          )}
        </div>
      </div>

      {/* Upload dialog */}
      <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Upload File</DialogTitle>
            <DialogDescription>
              Upload a CSV or Excel file to analyze with AI
            </DialogDescription>
          </DialogHeader>
          <FileUploadZone onUploadComplete={handleUploadComplete} />
        </DialogContent>
      </Dialog>
    </div>
  );
}
