import { useState } from "react";
import { Search, Filter, SortAsc, FileQuestion, Loader2, RefreshCw } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { SourceCard } from "./SourceCard";
import { useResearch, useSources, useIsProcessing, useProgress } from "@/hooks/use-research";
import { useNavigate } from "react-router-dom";
import { Skeleton } from "@/components/ui/skeleton";

// Transform API Source to component Source type
function transformSource(source: import("@/lib/api").Source) {
  return {
    id: source.id,
    title: source.title,
    authors: source.authors || [],
    date: source.date || "n.d.",
    type: source.type as "pdf" | "docx" | "url" | "image",
    status: source.status as "pending" | "processing" | "processed",
    claimsExtracted: source.claims_extracted || 0,
    relevanceScore: source.relevance_score || 0,
    thumbnailColor: source.thumbnail_color || "hsl(210, 70%, 55%)",
  };
}

function SourcesSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-20 rounded-lg" />
        ))}
      </div>
      <Skeleton className="h-10 rounded-lg" />
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-28 rounded-lg" />
        ))}
      </div>
    </div>
  );
}

export function SourcesPanel() {
  const sources = useSources();
  const isProcessing = useIsProcessing();
  const progress = useProgress();
  const { brief, startResearch } = useResearch();
  const [searchQuery, setSearchQuery] = useState("");
  const navigate = useNavigate();

  // Use brief sources if available, otherwise use sources from state
  const displaySources = (brief?.sources || sources).map(transformSource);

  const filteredSources = displaySources.filter(source =>
    source.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    source.authors.some(a => a.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const processedCount = displaySources.filter(s => s.status === "processed").length;
  const totalClaims = displaySources.reduce((sum, s) => sum + s.claimsExtracted, 0);

  // Show loading state during processing
  if (isProcessing && progress?.stage === 'processing') {
    return (
      <div className="space-y-6">
        <div className="panel-card p-8 text-center">
          <Loader2 className="h-10 w-10 animate-spin text-accent mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">
            Processing Documents
          </h3>
          <p className="text-muted-foreground mb-4">
            {progress.message}
          </p>
          {progress.details && (
            <p className="text-sm text-muted-foreground">
              {progress.details}
            </p>
          )}
          <div className="w-full max-w-xs mx-auto mt-4">
            <div className="h-2 bg-secondary rounded-full overflow-hidden">
              <div 
                className="h-full bg-accent rounded-full transition-all duration-500"
                style={{ width: `${progress.progress}%` }}
              />
            </div>
          </div>
        </div>
        <SourcesSkeleton />
      </div>
    );
  }

  // Show empty state if no sources
  if (displaySources.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="h-16 w-16 rounded-full bg-secondary flex items-center justify-center mb-4">
          <FileQuestion className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold text-foreground mb-2">No sources yet</h3>
        <p className="text-muted-foreground mb-6 max-w-md">
          Upload documents and process them to see your research sources here.
        </p>
        <Button onClick={() => navigate("/")}>
          Upload Documents
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Bar */}
      <div className="grid grid-cols-3 gap-4">
        <div className="panel-card p-4 text-center">
          <p className="text-2xl font-semibold text-foreground">{displaySources.length}</p>
          <p className="text-sm text-muted-foreground">Total Sources</p>
        </div>
        <div className="panel-card p-4 text-center">
          <p className="text-2xl font-semibold text-consensus">{processedCount}</p>
          <p className="text-sm text-muted-foreground">Processed</p>
        </div>
        <div className="panel-card p-4 text-center">
          <p className="text-2xl font-semibold text-accent">{totalClaims}</p>
          <p className="text-sm text-muted-foreground">Claims Extracted</p>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search sources..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <Button variant="outline">
          <Filter className="h-4 w-4 mr-2" />
          Filter
        </Button>
        <Button variant="outline">
          <SortAsc className="h-4 w-4 mr-2" />
          Sort
        </Button>
      </div>

      {/* Sources List */}
      <div className="space-y-3">
        {filteredSources.map((source) => (
          <SourceCard key={source.id} source={source} />
        ))}
        {filteredSources.length === 0 && searchQuery && (
          <div className="text-center py-12 text-muted-foreground">
            <p>No sources match your search</p>
          </div>
        )}
      </div>
    </div>
  );
}
