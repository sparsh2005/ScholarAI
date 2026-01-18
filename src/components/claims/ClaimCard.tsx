import { MessageSquareQuote, ChevronRight, FileText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type ClaimType = "consensus" | "disagreement" | "uncertain";

export interface Claim {
  id: string;
  statement: string;
  type: ClaimType;
  confidence: number;
  supportingSources: number;
  contradictingSources: number;
  sourceIds: string[];
}

interface ClaimCardProps {
  claim: Claim;
}

export function ClaimCard({ claim }: ClaimCardProps) {
  const getTypeStyles = () => {
    switch (claim.type) {
      case "consensus":
        return {
          badge: "status-badge-consensus",
          border: "border-l-consensus",
          label: "Consensus",
        };
      case "disagreement":
        return {
          badge: "status-badge-disagreement",
          border: "border-l-disagreement",
          label: "Disagreement",
        };
      case "uncertain":
        return {
          badge: "status-badge-uncertain",
          border: "border-l-uncertain",
          label: "Uncertain",
        };
    }
  };

  const styles = getTypeStyles();

  return (
    <div className={cn("panel-card p-4 border-l-4", styles.border)}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className={styles.badge}>{styles.label}</span>
            <span className="text-xs text-muted-foreground">
              {claim.confidence}% confidence
            </span>
          </div>
          <p className="text-foreground leading-relaxed research-serif">
            "{claim.statement}"
          </p>
          <div className="flex items-center gap-4 mt-3 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <FileText className="h-3.5 w-3.5" />
              {claim.supportingSources} supporting
            </span>
            {claim.contradictingSources > 0 && (
              <span className="flex items-center gap-1 text-disagreement">
                {claim.contradictingSources} contradicting
              </span>
            )}
          </div>
        </div>
        <Button variant="ghost" size="icon" className="flex-shrink-0">
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
