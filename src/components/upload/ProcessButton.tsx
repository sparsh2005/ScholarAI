import { Zap, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ProcessButtonProps {
  isProcessing?: boolean;
  documentCount?: number;
  urlCount?: number;
}

export function ProcessButton({ isProcessing = false, documentCount = 2, urlCount = 1 }: ProcessButtonProps) {
  const totalSources = documentCount + urlCount;

  return (
    <div className="panel-card-elevated p-6 bg-primary text-primary-foreground">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 rounded-lg bg-white/10 flex items-center justify-center">
            <Zap className="h-6 w-6" />
          </div>
          <div>
            <h2 className="font-semibold text-lg">Ready to Process</h2>
            <p className="text-sm text-primary-foreground/70">
              {totalSources} source{totalSources !== 1 ? "s" : ""} ready for analysis
            </p>
          </div>
        </div>
        <Button 
          size="lg"
          className="bg-white text-primary hover:bg-white/90 font-semibold px-6"
          disabled={isProcessing}
        >
          {isProcessing ? (
            <>
              <span className="animate-pulse-subtle">Processing...</span>
            </>
          ) : (
            <>
              Process & Synthesize
              <ArrowRight className="ml-2 h-4 w-4" />
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
