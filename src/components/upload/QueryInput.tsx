import { Search, Sparkles, AlertCircle } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { useResearch } from "@/hooks/use-research";
import { cn } from "@/lib/utils";

const EXAMPLE_QUERIES = [
  "What is the current scientific consensus on the relationship between gut microbiome and mental health?",
  "How do transformer architectures compare to RNNs for natural language processing tasks?",
  "What are the environmental impacts of lithium-ion battery production?",
  "What evidence exists for the effectiveness of mindfulness meditation on anxiety?",
];

export function QueryInput() {
  const { query, setQuery, error, clearError } = useResearch();

  const handleExampleClick = () => {
    const randomExample = EXAMPLE_QUERIES[Math.floor(Math.random() * EXAMPLE_QUERIES.length)];
    setQuery(randomExample);
  };

  const isValid = query.trim().length >= 10;
  const charCount = query.length;

  return (
    <div className="panel-card p-6">
      <div className="flex items-center gap-2 mb-4">
        <Search className="h-5 w-5 text-accent" />
        <h2 className="font-semibold text-foreground">Research Query</h2>
      </div>
      <div className="space-y-4">
        <div className="relative">
          <Textarea
            placeholder="Enter your research question... 

Example: What is the current scientific consensus on the relationship between gut microbiome and mental health?"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              if (error) clearError();
            }}
            className={cn(
              "min-h-[120px] resize-none bg-background border-border focus:ring-2 focus:ring-accent/20 focus:border-accent",
              !isValid && query.length > 0 && "border-uncertain focus:border-uncertain"
            )}
          />
          {!isValid && query.length > 0 && (
            <div className="absolute bottom-3 left-3 flex items-center gap-1 text-xs text-uncertain">
              <AlertCircle className="h-3 w-3" />
              Query should be at least 10 characters
            </div>
          )}
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <p className="text-xs text-muted-foreground">
              Be specific. Include key terms, time ranges, or methodological preferences.
            </p>
            <span className={cn(
              "text-xs",
              charCount > 0 ? (isValid ? "text-consensus" : "text-uncertain") : "text-muted-foreground"
            )}>
              {charCount} characters
            </span>
          </div>
          <Button 
            size="sm" 
            variant="outline"
            className="text-muted-foreground hover:text-accent hover:border-accent"
            onClick={handleExampleClick}
          >
            <Sparkles className="h-4 w-4 mr-2" />
            Try an example
          </Button>
        </div>
      </div>
    </div>
  );
}
