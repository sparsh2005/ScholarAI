import { useState } from "react";
import { Link, Plus, X, Globe } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface AddedUrl {
  id: string;
  url: string;
  title?: string;
}

const mockUrls: AddedUrl[] = [
  { id: "1", url: "https://pubmed.ncbi.nlm.nih.gov/12345678/", title: "PubMed Article" },
];

export function UrlInput() {
  const [urls, setUrls] = useState<AddedUrl[]>(mockUrls);
  const [inputUrl, setInputUrl] = useState("");

  const addUrl = () => {
    if (inputUrl.trim()) {
      setUrls([...urls, { id: Date.now().toString(), url: inputUrl, title: "Webpage" }]);
      setInputUrl("");
    }
  };

  const removeUrl = (id: string) => {
    setUrls(urls.filter(u => u.id !== id));
  };

  return (
    <div className="panel-card p-6">
      <div className="flex items-center gap-2 mb-4">
        <Link className="h-5 w-5 text-accent" />
        <h2 className="font-semibold text-foreground">Add URLs</h2>
      </div>

      <div className="flex gap-2">
        <Input
          placeholder="Paste a URL to a paper, article, or webpage..."
          value={inputUrl}
          onChange={(e) => setInputUrl(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addUrl()}
          className="flex-1"
        />
        <Button onClick={addUrl} variant="outline">
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      {urls.length > 0 && (
        <div className="mt-4 space-y-2">
          {urls.map((urlItem) => (
            <div 
              key={urlItem.id}
              className="flex items-center justify-between p-3 bg-secondary/50 rounded-lg group"
            >
              <div className="flex items-center gap-3 overflow-hidden">
                <Globe className="h-4 w-4 text-accent flex-shrink-0" />
                <div className="overflow-hidden">
                  <p className="text-sm font-medium text-foreground truncate">{urlItem.title}</p>
                  <p className="text-xs text-muted-foreground truncate">{urlItem.url}</p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
                onClick={() => removeUrl(urlItem.id)}
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
