import { useEffect, useState } from "react";
import { Zap, ArrowRight, Loader2, AlertCircle, CheckCircle, Server } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useResearch } from "@/hooks/use-research";
import { useNavigate } from "react-router-dom";
import { checkBackendHealth } from "@/lib/api";

export function ProcessButton() {
  const { 
    files, 
    urls, 
    query,
    isProcessing, 
    progress, 
    startResearch, 
    error,
    brief,
    clearError,
    backendAvailable,
    checkBackend,
  } = useResearch();
  const navigate = useNavigate();
  const [isCheckingBackend, setIsCheckingBackend] = useState(false);

  // Check backend status on mount
  useEffect(() => {
    checkBackend();
  }, [checkBackend]);

  const uploadedFiles = files.filter(f => f.status === 'uploaded');
  const totalSources = uploadedFiles.length + urls.length;
  const hasQuery = query.trim().length > 0;
  const canProcess = totalSources > 0 && hasQuery && backendAvailable;

  // Navigate to brief when complete
  useEffect(() => {
    if (brief && progress?.stage === 'complete') {
      const timer = setTimeout(() => {
        navigate('/brief');
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [brief, progress?.stage, navigate]);

  const handleRetryBackend = async () => {
    setIsCheckingBackend(true);
    await checkBackend();
    setIsCheckingBackend(false);
  };

  // Determine button state
  const getButtonState = () => {
    if (isProcessing) {
      return {
        disabled: true,
        text: progress?.message || "Processing...",
        icon: <Loader2 className="mr-2 h-4 w-4 animate-spin" />,
      };
    }
    
    if (!backendAvailable) {
      return {
        disabled: true,
        text: "Backend Unavailable",
        icon: <AlertCircle className="mr-2 h-4 w-4" />,
      };
    }
    
    if (!hasQuery) {
      return {
        disabled: true,
        text: "Enter a Research Question",
        icon: <ArrowRight className="ml-2 h-4 w-4" />,
      };
    }
    
    if (totalSources === 0) {
      return {
        disabled: true,
        text: "Add Documents or URLs",
        icon: <ArrowRight className="ml-2 h-4 w-4" />,
      };
    }
    
    return {
      disabled: false,
      text: "Process & Synthesize",
      icon: <ArrowRight className="ml-2 h-4 w-4" />,
    };
  };

  const buttonState = getButtonState();

  return (
    <div className="space-y-4">
      {/* Backend Status Warning */}
      {!backendAvailable && (
        <Alert variant="destructive">
          <Server className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>Backend server is not available. Please start the backend server.</span>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleRetryBackend}
              disabled={isCheckingBackend}
            >
              {isCheckingBackend ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Retry"
              )}
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Error Display */}
      {error && !isProcessing && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>{error}</span>
            <Button variant="ghost" size="sm" onClick={clearError}>
              Dismiss
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Main Process Button Card */}
      <div className="panel-card-elevated p-6 bg-primary text-primary-foreground">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-lg bg-white/10 flex items-center justify-center">
              {isProcessing ? (
                <Loader2 className="h-6 w-6 animate-spin" />
              ) : progress?.stage === 'complete' ? (
                <CheckCircle className="h-6 w-6" />
              ) : (
                <Zap className="h-6 w-6" />
              )}
            </div>
            <div>
              <h2 className="font-semibold text-lg">
                {isProcessing 
                  ? progress?.message || "Processing..." 
                  : progress?.stage === 'complete'
                    ? "Research Complete!"
                    : "Ready to Process"
                }
              </h2>
              <p className="text-sm text-primary-foreground/70">
                {isProcessing 
                  ? progress?.details || `Stage: ${progress?.stage || 'starting'}`
                  : progress?.stage === 'complete'
                    ? "Redirecting to research brief..."
                    : `${totalSources} source${totalSources !== 1 ? "s" : ""} ready for analysis`
                }
              </p>
            </div>
          </div>
          <Button 
            size="lg"
            className="bg-white text-primary hover:bg-white/90 font-semibold px-6"
            disabled={buttonState.disabled}
            onClick={startResearch}
          >
            {buttonState.icon}
            {buttonState.text}
            {!isProcessing && !buttonState.disabled && <ArrowRight className="ml-2 h-4 w-4" />}
          </Button>
        </div>

        {/* Progress bar */}
        {isProcessing && progress && (
          <div className="mt-4">
            <Progress 
              value={progress.progress} 
              className="h-2 bg-white/20"
            />
            <div className="flex justify-between mt-2 text-xs text-primary-foreground/60">
              <span>Stage: {progress.stage}</span>
              <span>{progress.progress}%</span>
            </div>
          </div>
        )}
      </div>

      {/* Pipeline stages indicator */}
      {isProcessing && (
        <div className="flex justify-between px-4">
          {['processing', 'retrieving', 'extracting', 'synthesizing'].map((stage, index) => {
            const isActive = progress?.stage === stage;
            const isComplete = ['processing', 'retrieving', 'extracting', 'synthesizing'].indexOf(progress?.stage || '') > index;
            
            return (
              <div key={stage} className="flex flex-col items-center gap-1">
                <div className={`
                  w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium
                  ${isComplete ? 'bg-consensus text-white' : isActive ? 'bg-primary text-white animate-pulse' : 'bg-secondary text-muted-foreground'}
                `}>
                  {isComplete ? <CheckCircle className="h-4 w-4" /> : index + 1}
                </div>
                <span className={`text-xs capitalize ${isActive ? 'text-foreground font-medium' : 'text-muted-foreground'}`}>
                  {stage}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
