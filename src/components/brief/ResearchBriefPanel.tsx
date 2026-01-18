import { CheckCircle, AlertTriangle, HelpCircle, AlertCircle, FileText } from "lucide-react";
import { BriefSection } from "./BriefSection";
import { ConfidenceIndicator } from "./ConfidenceIndicator";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

const consensusItems = [
  {
    id: "1",
    statement: "The gut-brain axis represents a bidirectional communication system linking the enteric and central nervous systems.",
    confidence: 95,
    sources: 4,
  },
  {
    id: "2",
    statement: "Gut microbiota composition influences neurotransmitter production, including serotonin and GABA.",
    confidence: 88,
    sources: 3,
  },
  {
    id: "3",
    statement: "Early-life disruption of gut microbiome development can have lasting effects on mental health outcomes.",
    confidence: 82,
    sources: 3,
  },
];

const disagreementItems = [
  {
    id: "1",
    claim: "Probiotics effectively treat depression",
    perspective1: "Meta-analyses show significant reduction in depression scores with probiotic supplementation",
    perspective2: "Effect sizes are small and clinical significance remains uncertain; many studies have methodological limitations",
    sources: 4,
  },
  {
    id: "2",
    claim: "Specific psychobiotic strains have reproducible effects",
    perspective1: "Strain-specific effects have been demonstrated in controlled trials",
    perspective2: "Results are inconsistent across studies; individual variation in gut microbiome composition affects outcomes",
    sources: 3,
  },
];

const openQuestions = [
  {
    id: "1",
    question: "What are the optimal dosing and duration protocols for psychobiotic interventions?",
    context: "Current studies vary widely in strain types, doses, and treatment duration, making it difficult to establish clinical guidelines.",
  },
  {
    id: "2",
    question: "How do individual differences in baseline microbiome composition affect treatment response?",
    context: "Personalized approaches may be necessary, but predictive biomarkers are not yet established.",
  },
  {
    id: "3",
    question: "What role do dietary factors play in mediating gut-brain axis effects independent of microbiome changes?",
    context: "Diet influences both microbiome and brain directly, making it difficult to isolate mechanisms.",
  },
];

const limitations = [
  "Limited to 5 sources; comprehensive literature review would require additional sources",
  "Publication dates range from 2015-2019; more recent studies may exist",
  "Heterogeneity in study populations and methodologies limits direct comparisons",
  "Animal model findings may not translate directly to human applications",
];

export function ResearchBriefPanel() {
  return (
    <div className="space-y-6">
      {/* Overall Confidence Summary */}
      <div className="panel-card-elevated p-6">
        <h2 className="font-semibold text-lg text-foreground mb-4">Research Brief Summary</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p className="text-sm text-muted-foreground mb-2">Overall Confidence</p>
            <ConfidenceIndicator 
              level="medium" 
              score={72} 
              label="Based on source quality and agreement levels" 
            />
          </div>
          <div>
            <p className="text-sm text-muted-foreground mb-2">Source Coverage</p>
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-accent" />
              <span className="font-medium">5 sources analyzed</span>
            </div>
          </div>
          <div>
            <p className="text-sm text-muted-foreground mb-2">Claims Extracted</p>
            <div className="flex items-center gap-2">
              <span className="font-medium">26 claims</span>
              <Badge variant="outline" className="text-xs">6 key findings</Badge>
            </div>
          </div>
        </div>
      </div>

      {/* Consensus Section */}
      <BriefSection
        title="Areas of Consensus"
        icon={<CheckCircle className="h-4 w-4" />}
        iconColor="text-consensus"
        count={consensusItems.length}
      >
        <div className="space-y-4">
          {consensusItems.map((item, index) => (
            <div key={item.id}>
              {index > 0 && <Separator className="my-4" />}
              <div className="space-y-2">
                <p className="text-foreground research-serif leading-relaxed">
                  "{item.statement}"
                </p>
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

      {/* Disagreements Section */}
      <BriefSection
        title="Areas of Disagreement"
        icon={<AlertTriangle className="h-4 w-4" />}
        iconColor="text-disagreement"
        count={disagreementItems.length}
      >
        <div className="space-y-6">
          {disagreementItems.map((item, index) => (
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

      {/* Open Questions Section */}
      <BriefSection
        title="Open Questions"
        icon={<HelpCircle className="h-4 w-4" />}
        iconColor="text-uncertain"
        count={openQuestions.length}
      >
        <div className="space-y-4">
          {openQuestions.map((item, index) => (
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

      {/* Limitations Section */}
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
            {limitations.map((limitation, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-foreground">
                <span className="text-muted-foreground mt-1">•</span>
                {limitation}
              </li>
            ))}
          </ul>
        </div>
      </BriefSection>
    </div>
  );
}
