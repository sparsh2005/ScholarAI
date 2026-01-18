import { useState } from "react";
import { Link, Plus, X, Globe, ExternalLink } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useResearch } from "@/hooks/use-research";
import { useToast } from "@/hooks/use-toast";

export function UrlInput() {
  const { urls, addUrl, removeUrl } = useResearch();
  const [inputUrl, setInputUrl] = useState("");
  const { toast } = useToast();

  const handleAddUrl = () => {
    if (!inputUrl.trim()) return;

    // Validate URL
    try {
      const url = new URL(inputUrl);
      // Only allow http/https
      if (!['http:', 'https:'].includes(url.protocol)) {
        throw new Error('Invalid protocol');
      }
    } catch {
      toast({
        title: "Invalid URL",
        description: "Please enter a valid HTTP or HTTPS URL",
        variant: "destructive",
      });
      return;
    }

    addUrl(inputUrl);
    setInputUrl("");
    toast({
      title: "URL added",
      description: "URL ready for processing.",
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddUrl();
    }
  };

  return (
    <div className="panel-card p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Link className="h-5 w-5 text-accent" />
          <h2 className="font-semibold text-foreground">Add URLs</h2>
        </div>
        {urls.length > 0 && (
          <Badge variant="secondary">{urls.length} URL{urls.length !== 1 ? 's' : ''}</Badge>
        )}
      </div>

      <div className="flex gap-2">
        <Input
          placeholder="Paste a URL to a paper, article, or webpage..."
          value={inputUrl}
          onChange={(e) => setInputUrl(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-1"
        />
        <Button onClick={handleAddUrl} variant="outline" disabled={!inputUrl.trim()}>
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      <p className="text-xs text-muted-foreground mt-2">
        Supports PDFs, web pages, and academic paper URLs (arXiv, PubMed, etc.)
      </p>

      {urls.length > 0 && (
        <div className="mt-4 space-y-2">
          {urls.map((urlItem) => (
            <div 
              key={urlItem.id}
              className="flex items-center justify-between p-3 bg-secondary/50 rounded-lg group"
            >
              <div className="flex items-center gap-3 overflow-hidden flex-1">
                <Globe className="h-4 w-4 text-accent flex-shrink-0" />
                <div className="overflow-hidden flex-1">
                  <p className="text-sm font-medium text-foreground truncate">{urlItem.title}</p>
                  <p className="text-xs text-muted-foreground truncate">{urlItem.url}</p>
                </div>
              </div>
              <div className="flex items-center gap-1 flex-shrink-0">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={() => window.open(urlItem.url, '_blank')}
                >
                  <ExternalLink className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={() => removeUrl(urlItem.id)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
