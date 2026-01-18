import { Search, Sparkles } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { useResearch } from "@/hooks/use-research";

export function QueryInput() {
  const { query, setQuery } = useResearch();

  return (
    <div className="panel-card p-6">
      <div className="flex items-center gap-2 mb-4">
        <Search className="h-5 w-5 text-accent" />
        <h2 className="font-semibold text-foreground">Research Query</h2>
      </div>
      <div className="space-y-4">
        <Textarea
          placeholder="Enter your research question... 

Example: What is the current scientific consensus on the relationship between gut microbiome and mental health?"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="min-h-[120px] resize-none bg-background border-border focus:ring-2 focus:ring-accent/20 focus:border-accent"
        />
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            Be specific. Include key terms, time ranges, or methodological preferences.
          </p>
          <Button 
            size="sm" 
            variant="outline"
            className="text-muted-foreground hover:text-accent hover:border-accent"
          >
            <Sparkles className="h-4 w-4 mr-2" />
            Suggest refinements
          </Button>
        </div>
      </div>
    </div>
  );
}
