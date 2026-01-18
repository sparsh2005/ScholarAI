import { CheckCircle, AlertTriangle, HelpCircle, AlertCircle, FileText, FileQuestion, Loader2, Download, Copy, Check } from "lucide-react";
import { BriefSection } from "./BriefSection";
import { ConfidenceIndicator } from "./ConfidenceIndicator";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useBrief, useIsProcessing, useProgress } from "@/hooks/use-research";
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { useToast } from "@/hooks/use-toast";

function BriefSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-40 rounded-lg" />
      <Skeleton className="h-64 rounded-lg" />
      <Skeleton className="h-48 rounded-lg" />
      <Skeleton className="h-48 rounded-lg" />
    </div>
  );
}

export function ResearchBriefPanel() {
  const brief = useBrief();
  const isProcessing = useIsProcessing();
  const progress = useProgress();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [copied, setCopied] = useState(false);

  // Copy brief to clipboard
  const handleCopy = async () => {
    if (!brief) return;
    
    const text = generateBriefText(brief);
    await navigator.clipboard.writeText(text);
    setCopied(true);
    toast({
      title: "Copied to clipboard",
      description: "Research brief copied as text",
    });
    setTimeout(() => setCopied(false), 2000);
  };

  // Generate text version of brief
  const generateBriefText = (b: typeof brief) => {
    if (!b) return "";
    
    let text = `# Research Brief\n\n`;
    text += `**Query:** ${b.query}\n`;
    text += `**Confidence:** ${b.confidence_level.toUpperCase()} (${b.confidence_score}%)\n`;
    text += `**Sources:** ${b.sources.length}\n\n`;
    
    if (b.consensus.length > 0) {
      text += `## Areas of Consensus\n\n`;
      b.consensus.forEach((c, i) => {
        text += `${i + 1}. ${c.statement} (${c.confidence}% confidence, ${c.sources} sources)\n`;
      });
      text += `\n`;
    }
    
    if (b.disagreements.length > 0) {
      text += `## Areas of Disagreement\n\n`;
      b.disagreements.forEach((d, i) => {
        text += `${i + 1}. ${d.claim}\n`;
        text += `   - Supporting: ${d.perspective1}\n`;
        text += `   - Opposing: ${d.perspective2}\n`;
      });
      text += `\n`;
    }
    
    if (b.open_questions.length > 0) {
      text += `## Open Questions\n\n`;
      b.open_questions.forEach((q, i) => {
        text += `${i + 1}. ${q.question}\n   ${q.context}\n`;
      });
      text += `\n`;
    }
    
    if (b.limitations.length > 0) {
      text += `## Limitations\n\n`;
      b.limitations.forEach((l) => {
        text += `- ${l}\n`;
      });
    }
    
    return text;
  };

  // Show loading state during synthesis
  if (isProcessing && progress?.stage === 'synthesizing') {
    return (
      <div className="space-y-6">
        <div className="panel-card-elevated p-8 text-center">
          <Loader2 className="h-10 w-10 animate-spin text-accent mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">
            Generating Research Brief
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
        <BriefSkeleton />
      </div>
    );
  }

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
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-lg text-foreground">Research Brief Summary</h2>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleCopy}>
              {copied ? (
                <>
                  <Check className="h-4 w-4 mr-2" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4 mr-2" />
                  Copy
                </>
              )}
            </Button>
          </div>
        </div>
        
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
            <p className="text-sm text-muted-foreground mb-2">Findings</p>
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant="outline" className="text-consensus border-consensus/30">
                {brief.consensus.length} consensus
              </Badge>
              <Badge variant="outline" className="text-disagreement border-disagreement/30">
                {brief.disagreements.length} disagreements
              </Badge>
              <Badge variant="outline" className="text-uncertain border-uncertain/30">
                {brief.open_questions.length} questions
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
                    <p className="text-sm text-muted-foreground italic">
                      {item.evidence_summary}
                    </p>
                  )}
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">
                      Supported by {item.sources} source{item.sources !== 1 ? 's' : ''}
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
                    Based on {item.sources} source{item.sources !== 1 ? 's' : ''} with conflicting findings
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

      {/* Generated timestamp */}
      <div className="text-center text-xs text-muted-foreground">
        Generated on {new Date(brief.generated_at).toLocaleString()}
      </div>
    </div>
  );
}
