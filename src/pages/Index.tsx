import { useEffect } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { QueryInput } from "@/components/upload/QueryInput";
import { DocumentUpload } from "@/components/upload/DocumentUpload";
import { UrlInput } from "@/components/upload/UrlInput";
import { ProcessButton } from "@/components/upload/ProcessButton";
import { Button } from "@/components/ui/button";
import { RotateCcw, CheckCircle } from "lucide-react";
import { useResearch } from "@/hooks/use-research";
import { useNavigate } from "react-router-dom";

const Index = () => {
  const { reset, brief, progress, checkBackend } = useResearch();
  const navigate = useNavigate();

  // Check backend on mount
  useEffect(() => {
    checkBackend();
  }, [checkBackend]);

  const hasResults = brief !== null;

  return (
    <DashboardLayout 
      title="Upload & Query" 
      description="Add your research sources and define your research question"
    >
      <div className="max-w-4xl space-y-6">
        {/* Show success banner if we have results */}
        {hasResults && progress?.stage === 'complete' && (
          <div className="panel-card p-4 bg-consensus/10 border-consensus/20 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-5 w-5 text-consensus" />
              <div>
                <p className="font-medium text-foreground">Research Complete!</p>
                <p className="text-sm text-muted-foreground">
                  Your research brief is ready. View it or start a new research session.
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={reset}>
                <RotateCcw className="h-4 w-4 mr-2" />
                New Research
              </Button>
              <Button size="sm" onClick={() => navigate('/brief')}>
                View Brief
              </Button>
            </div>
          </div>
        )}

        <QueryInput />
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <DocumentUpload />
          <UrlInput />
        </div>
        
        <ProcessButton />

        {/* Quick tips */}
        <div className="panel-card p-4 bg-secondary/30">
          <h3 className="text-sm font-medium text-foreground mb-2">💡 Tips for better results</h3>
          <ul className="text-sm text-muted-foreground space-y-1">
            <li>• Upload 3-5 sources for comprehensive analysis</li>
            <li>• Include sources with different perspectives for richer insights</li>
            <li>• Be specific in your research question for more relevant claims</li>
            <li>• Academic papers (PDF) typically yield the best results</li>
          </ul>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Index;
