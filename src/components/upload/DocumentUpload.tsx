import { useState, useCallback, useRef } from "react";
import { Upload, FileText, Image, File, X, Plus, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useResearch } from "@/hooks/use-research";
import { useToast } from "@/hooks/use-toast";

export function DocumentUpload() {
  const { files, addFile, removeFile, error } = useResearch();
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const handleFiles = useCallback(async (fileList: FileList | null) => {
    if (!fileList) return;

    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'image/png',
      'image/jpeg',
    ];

    for (const file of Array.from(fileList)) {
      if (!allowedTypes.includes(file.type)) {
        toast({
          title: "Invalid file type",
          description: `${file.name} is not a supported file type.`,
          variant: "destructive",
        });
        continue;
      }

      if (file.size > 50 * 1024 * 1024) {
        toast({
          title: "File too large",
          description: `${file.name} exceeds 50MB limit.`,
          variant: "destructive",
        });
        continue;
      }

      setIsUploading(true);
      try {
        await addFile(file);
        toast({
          title: "File uploaded",
          description: `${file.name} ready for processing.`,
        });
      } catch (err) {
        toast({
          title: "Upload failed",
          description: err instanceof Error ? err.message : "Unknown error",
          variant: "destructive",
        });
      } finally {
        setIsUploading(false);
      }
    }
  }, [addFile, toast]);

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
    handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleFiles(e.target.files);
    // Reset input so same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [handleFiles]);

  const getFileIcon = (type: string) => {
    switch (type) {
      case "pdf":
        return <FileText className="h-4 w-4 text-red-500" />;
      case "docx":
        return <FileText className="h-4 w-4 text-blue-500" />;
      case "pptx":
        return <FileText className="h-4 w-4 text-orange-500" />;
      case "png":
      case "jpg":
      case "jpeg":
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

      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept=".pdf,.docx,.pptx,.png,.jpg,.jpeg"
        multiple
        onChange={handleFileSelect}
      />

      <div
        className={cn(
          "border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200",
          isDragging 
            ? "border-accent bg-accent/5" 
            : "border-border hover:border-muted-foreground/50",
          isUploading && "opacity-50 pointer-events-none"
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="flex flex-col items-center gap-3">
          <div className="h-12 w-12 rounded-full bg-secondary flex items-center justify-center">
            {isUploading ? (
              <Loader2 className="h-6 w-6 text-muted-foreground animate-spin" />
            ) : (
              <Upload className="h-6 w-6 text-muted-foreground" />
            )}
          </div>
          <div>
            <p className="font-medium text-foreground">
              {isUploading ? "Uploading..." : "Drop files here or click to upload"}
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              PDF, DOCX, PPTX, PNG, JPG up to 50MB each
            </p>
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            className="mt-2"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
          >
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
