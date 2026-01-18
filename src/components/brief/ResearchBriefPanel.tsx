import { CheckCircle, AlertTriangle, HelpCircle, AlertCircle, FileText, FileQuestion } from "lucide-react";
import { BriefSection } from "./BriefSection";
import { ConfidenceIndicator } from "./ConfidenceIndicator";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { useResearch } from "@/hooks/use-research";
import { useNavigate } from "react-router-dom";

export function ResearchBriefPanel() {
  const { brief } = useResearch();
  const navigate = useNavigate();

  // Show empty state if no brief
  if (!brief) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="h-16 w-16 rounded-full bg-secondary flex items-center justify-center mb-4">
          <FileQuestion className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold text-foreground mb-2">No research brief yet</h3>
        <p className="text-muted-foreground mb-6 max-w-md">
          Upload documents and run the research pipeline to generate a comprehensive research brief.
        </p>
        <Button onClick={() => navigate("/")}>
          Start Research
        </Button>
      </div>
    );
  }

  const totalClaims = brief.consensus.length + brief.disagreements.length + brief.open_questions.length;

  return (
    <div className="space-y-6">
      {/* Overall Confidence Summary */}
      <div className="panel-card-elevated p-6">
        <h2 className="font-semibold text-lg text-foreground mb-4">Research Brief Summary</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p className="text-sm text-muted-foreground mb-2">Overall Confidence</p>
            <ConfidenceIndicator 
              level={brief.confidence_level} 
              score={brief.confidence_score} 
              label="Based on source quality and agreement levels" 
            />
          </div>
          <div>
            <p className="text-sm text-muted-foreground mb-2">Source Coverage</p>
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-accent" />
              <span className="font-medium">{brief.sources.length} sources analyzed</span>
            </div>
          </div>
          <div>
            <p className="text-sm text-muted-foreground mb-2">Claims Extracted</p>
            <div className="flex items-center gap-2">
              <span className="font-medium">{totalClaims} claims</span>
              <Badge variant="outline" className="text-xs">
                {brief.consensus.length} consensus
              </Badge>
            </div>
          </div>
        </div>
        
        {/* Query */}
        <div className="mt-4 pt-4 border-t">
          <p className="text-sm text-muted-foreground mb-1">Research Query</p>
          <p className="text-foreground font-medium">{brief.query}</p>
        </div>
      </div>

      {/* Consensus Section */}
      {brief.consensus.length > 0 && (
        <BriefSection
          title="Areas of Consensus"
          icon={<CheckCircle className="h-4 w-4" />}
          iconColor="text-consensus"
          count={brief.consensus.length}
        >
          <div className="space-y-4">
            {brief.consensus.map((item, index) => (
              <div key={item.id}>
                {index > 0 && <Separator className="my-4" />}
                <div className="space-y-2">
                  <p className="text-foreground research-serif leading-relaxed">
                    "{item.statement}"
                  </p>
                  {item.evidence_summary && (
                    <p className="text-sm text-muted-foreground">
                      {item.evidence_summary}
                    </p>
                  )}
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">
                      Supported by {item.sources} sources
                    </span>
                    <ConfidenceIndicator level="high" score={item.confidence} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </BriefSection>
      )}

      {/* Disagreements Section */}
      {brief.disagreements.length > 0 && (
        <BriefSection
          title="Areas of Disagreement"
          icon={<AlertTriangle className="h-4 w-4" />}
          iconColor="text-disagreement"
          count={brief.disagreements.length}
        >
          <div className="space-y-6">
            {brief.disagreements.map((item, index) => (
              <div key={item.id}>
                {index > 0 && <Separator className="my-4" />}
                <div className="space-y-3">
                  <h4 className="font-medium text-foreground">{item.claim}</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-3 rounded-lg bg-consensus-muted/50 border border-consensus/20">
                      <p className="text-xs font-medium text-consensus mb-1">Supporting View</p>
                      <p className="text-sm text-foreground">{item.perspective1}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-disagreement-muted/50 border border-disagreement/20">
                      <p className="text-xs font-medium text-disagreement mb-1">Opposing View</p>
                      <p className="text-sm text-foreground">{item.perspective2}</p>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Based on {item.sources} sources with conflicting findings
                  </p>
                </div>
              </div>
            ))}
          </div>
        </BriefSection>
      )}

      {/* Open Questions Section */}
      {brief.open_questions.length > 0 && (
        <BriefSection
          title="Open Questions"
          icon={<HelpCircle className="h-4 w-4" />}
          iconColor="text-uncertain"
          count={brief.open_questions.length}
        >
          <div className="space-y-4">
            {brief.open_questions.map((item, index) => (
              <div key={item.id}>
                {index > 0 && <Separator className="my-4" />}
                <div className="space-y-2">
                  <h4 className="font-medium text-foreground">{item.question}</h4>
                  <p className="text-sm text-muted-foreground">{item.context}</p>
                </div>
              </div>
            ))}
          </div>
        </BriefSection>
      )}

      {/* Limitations Section */}
      {brief.limitations.length > 0 && (
        <BriefSection
          title="Confidence & Limitations"
          icon={<AlertCircle className="h-4 w-4" />}
          iconColor="text-muted-foreground"
          defaultOpen={false}
        >
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              This research brief should be interpreted with the following limitations in mind:
            </p>
            <ul className="space-y-2">
              {brief.limitations.map((limitation, index) => (
                <li key={index} className="flex items-start gap-2 text-sm text-foreground">
                  <span className="text-muted-foreground mt-1">•</span>
                  {limitation}
                </li>
              ))}
            </ul>
          </div>
        </BriefSection>
      )}
    </div>
  );
}
