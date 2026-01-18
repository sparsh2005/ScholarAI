import { useState, useCallback } from "react";
import { Upload, FileText, Image, File, X, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface UploadedFile {
  id: string;
  name: string;
  type: string;
  size: string;
}

const mockFiles: UploadedFile[] = [
  { id: "1", name: "gut_microbiome_review_2024.pdf", type: "pdf", size: "2.4 MB" },
  { id: "2", name: "mental_health_study.docx", type: "docx", size: "892 KB" },
];

export function DocumentUpload() {
  const [files, setFiles] = useState<UploadedFile[]>(mockFiles);
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    // Handle file drop
  }, []);

  const removeFile = (id: string) => {
    setFiles(files.filter(f => f.id !== id));
  };

  const getFileIcon = (type: string) => {
    switch (type) {
      case "pdf":
        return <FileText className="h-4 w-4 text-red-500" />;
      case "docx":
        return <FileText className="h-4 w-4 text-blue-500" />;
      case "pptx":
        return <FileText className="h-4 w-4 text-orange-500" />;
      case "image":
        return <Image className="h-4 w-4 text-green-500" />;
      default:
        return <File className="h-4 w-4 text-muted-foreground" />;
    }
  };

  return (
    <div className="panel-card p-6">
      <div className="flex items-center gap-2 mb-4">
        <Upload className="h-5 w-5 text-accent" />
        <h2 className="font-semibold text-foreground">Upload Documents</h2>
      </div>

      <div
        className={cn(
          "border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200",
          isDragging 
            ? "border-accent bg-accent/5" 
            : "border-border hover:border-muted-foreground/50"
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="flex flex-col items-center gap-3">
          <div className="h-12 w-12 rounded-full bg-secondary flex items-center justify-center">
            <Upload className="h-6 w-6 text-muted-foreground" />
          </div>
          <div>
            <p className="font-medium text-foreground">Drop files here or click to upload</p>
            <p className="text-sm text-muted-foreground mt-1">
              PDF, DOCX, PPTX, PNG, JPG up to 50MB each
            </p>
          </div>
          <Button variant="outline" size="sm" className="mt-2">
            <Plus className="h-4 w-4 mr-2" />
            Browse files
          </Button>
        </div>
      </div>

      {files.length > 0 && (
        <div className="mt-4 space-y-2">
          <p className="text-sm font-medium text-muted-foreground">Uploaded files</p>
          {files.map((file) => (
            <div 
              key={file.id}
              className="flex items-center justify-between p-3 bg-secondary/50 rounded-lg group"
            >
              <div className="flex items-center gap-3">
                {getFileIcon(file.type)}
                <div>
                  <p className="text-sm font-medium text-foreground">{file.name}</p>
                  <p className="text-xs text-muted-foreground">{file.size}</p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={() => removeFile(file.id)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
