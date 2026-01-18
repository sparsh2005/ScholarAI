import { Zap, ArrowRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useResearch } from "@/hooks/use-research";
import { useNavigate } from "react-router-dom";
import { useEffect } from "react";

export function ProcessButton() {
  const { 
    files, 
    urls, 
    isProcessing, 
    progress, 
    startResearch, 
    error,
    brief,
  } = useResearch();
  const navigate = useNavigate();

  const totalSources = files.length + urls.length;

  // Navigate to brief when complete
  useEffect(() => {
    if (brief && progress?.stage === 'complete') {
      // Small delay so user sees "complete" message
      const timer = setTimeout(() => {
        navigate('/brief');
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [brief, progress?.stage, navigate]);

  return (
    <div className="panel-card-elevated p-6 bg-primary text-primary-foreground">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 rounded-lg bg-white/10 flex items-center justify-center">
            {isProcessing ? (
              <Loader2 className="h-6 w-6 animate-spin" />
            ) : (
              <Zap className="h-6 w-6" />
            )}
          </div>
          <div>
            <h2 className="font-semibold text-lg">
              {isProcessing ? progress?.message || "Processing..." : "Ready to Process"}
            </h2>
            <p className="text-sm text-primary-foreground/70">
              {isProcessing 
                ? `Stage: ${progress?.stage || 'starting'}`
                : `${totalSources} source${totalSources !== 1 ? "s" : ""} ready for analysis`
              }
            </p>
          </div>
        </div>
        <Button 
          size="lg"
          className="bg-white text-primary hover:bg-white/90 font-semibold px-6"
          disabled={isProcessing || totalSources === 0}
          onClick={startResearch}
        >
          {isProcessing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              Process & Synthesize
              <ArrowRight className="ml-2 h-4 w-4" />
            </>
          )}
        </Button>
      </div>

      {/* Progress bar */}
      {isProcessing && progress && (
        <div className="mt-4">
          <Progress 
            value={progress.progress} 
            className="h-2 bg-white/20"
          />
        </div>
      )}

      {/* Error display */}
      {error && !isProcessing && (
        <div className="mt-4 p-3 bg-destructive/20 rounded-lg">
          <p className="text-sm text-destructive-foreground">{error}</p>
        </div>
      )}
    </div>
  );
}
