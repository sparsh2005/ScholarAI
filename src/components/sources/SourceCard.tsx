import { FileText, Calendar, User, ExternalLink, MoreVertical } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export interface Source {
  id: string;
  title: string;
  authors: string[];
  date: string;
  type: "pdf" | "docx" | "url" | "image";
  status: "processed" | "processing" | "pending";
  claimsExtracted: number;
  relevanceScore: number;
  thumbnailColor: string;
}

interface SourceCardProps {
  source: Source;
}

export function SourceCard({ source }: SourceCardProps) {
  const getStatusBadge = () => {
    switch (source.status) {
      case "processed":
        return <Badge variant="outline" className="text-consensus border-consensus/30 bg-consensus-muted">Processed</Badge>;
      case "processing":
        return <Badge variant="outline" className="text-uncertain border-uncertain/30 bg-uncertain-muted animate-pulse-subtle">Processing</Badge>;
      case "pending":
        return <Badge variant="outline" className="text-muted-foreground">Pending</Badge>;
    }
  };

  return (
    <div className="panel-card p-4 hover:shadow-md transition-shadow group">
      <div className="flex gap-4">
        {/* Thumbnail */}
        <div 
          className="w-16 h-20 rounded-md flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: source.thumbnailColor }}
        >
          <FileText className="h-8 w-8 text-white/80" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-medium text-foreground leading-snug line-clamp-2">
              {source.title}
            </h3>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem>View original</DropdownMenuItem>
                <DropdownMenuItem>View extracted claims</DropdownMenuItem>
                <DropdownMenuItem>Re-process</DropdownMenuItem>
                <DropdownMenuItem className="text-destructive">Remove</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <User className="h-3.5 w-3.5" />
              {source.authors.slice(0, 2).join(", ")}
              {source.authors.length > 2 && ` +${source.authors.length - 2}`}
            </span>
            <span className="flex items-center gap-1">
              <Calendar className="h-3.5 w-3.5" />
              {source.date}
            </span>
          </div>

          <div className="flex items-center justify-between mt-3">
            <div className="flex items-center gap-2">
              {getStatusBadge()}
              {source.status === "processed" && (
                <span className="text-xs text-muted-foreground">
                  {source.claimsExtracted} claims extracted
                </span>
              )}
            </div>
            {source.status === "processed" && (
              <div className="flex items-center gap-1">
                <div className="w-16 h-1.5 bg-secondary rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-accent rounded-full"
                    style={{ width: `${source.relevanceScore}%` }}
                  />
                </div>
                <span className="text-xs text-muted-foreground">{source.relevanceScore}%</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
