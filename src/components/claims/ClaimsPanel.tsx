import { useState } from "react";
import { Search, CheckCircle, AlertTriangle, HelpCircle, FileQuestion } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ClaimCard, type ClaimType } from "./ClaimCard";
import { cn } from "@/lib/utils";
import { useResearch } from "@/hooks/use-research";
import { useNavigate } from "react-router-dom";

// Transform API Claim to component Claim type
function transformClaim(claim: import("@/lib/api").Claim) {
  return {
    id: claim.id,
    statement: claim.statement,
    type: claim.type as ClaimType,
    confidence: claim.confidence,
    supportingSources: claim.supporting_sources,
    contradictingSources: claim.contradicting_sources,
    sourceIds: claim.source_ids,
  };
}

type FilterType = "all" | ClaimType;

interface FilterOption {
  value: FilterType;
  label: string;
  icon: React.ReactNode;
  count: number;
}

export function ClaimsPanel() {
  const { claims, brief } = useResearch();
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<FilterType>("all");
  const navigate = useNavigate();

  // Extract claims from brief consensus/disagreements or use claims from state
  const displayClaims = claims.map(transformClaim);
  
  // If we have a brief, construct claims from it
  const briefClaims = brief ? [
    ...brief.consensus.map((c, i) => ({
      id: c.id,
      statement: c.statement,
      type: "consensus" as ClaimType,
      confidence: c.confidence,
      supportingSources: c.sources,
      contradictingSources: 0,
      sourceIds: c.source_ids || [],
    })),
    ...brief.disagreements.map((d, i) => ({
      id: d.id,
      statement: d.claim,
      type: "disagreement" as ClaimType,
      confidence: 50,
      supportingSources: Math.ceil(d.sources / 2),
      contradictingSources: Math.floor(d.sources / 2),
      sourceIds: d.source_ids || [],
    })),
    ...brief.open_questions.map((q, i) => ({
      id: q.id,
      statement: q.question,
      type: "uncertain" as ClaimType,
      confidence: 30,
      supportingSources: 0,
      contradictingSources: 0,
      sourceIds: q.related_claim_ids || [],
    })),
  ] : displayClaims;

  const allClaims = briefClaims.length > 0 ? briefClaims : displayClaims;

  const filterOptions: FilterOption[] = [
    { value: "all", label: "All Claims", icon: null, count: allClaims.length },
    { 
      value: "consensus", 
      label: "Consensus", 
      icon: <CheckCircle className="h-4 w-4 text-consensus" />, 
      count: allClaims.filter(c => c.type === "consensus").length 
    },
    { 
      value: "disagreement", 
      label: "Disagreement", 
      icon: <AlertTriangle className="h-4 w-4 text-disagreement" />, 
      count: allClaims.filter(c => c.type === "disagreement").length 
    },
    { 
      value: "uncertain", 
      label: "Uncertain", 
      icon: <HelpCircle className="h-4 w-4 text-uncertain" />, 
      count: allClaims.filter(c => c.type === "uncertain").length 
    },
  ];

  const filteredClaims = allClaims.filter(claim => {
    const matchesSearch = claim.statement.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = activeFilter === "all" || claim.type === activeFilter;
    return matchesSearch && matchesFilter;
  });

  // Show empty state if no claims
  if (allClaims.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="h-16 w-16 rounded-full bg-secondary flex items-center justify-center mb-4">
          <FileQuestion className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold text-foreground mb-2">No claims extracted yet</h3>
        <p className="text-muted-foreground mb-6 max-w-md">
          Process your documents to extract and analyze claims from your research sources.
        </p>
        <Button onClick={() => navigate("/")}>
          Start Research
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Filter Chips */}
      <div className="flex flex-wrap gap-2">
        {filterOptions.map((option) => (
          <Button
            key={option.value}
            variant={activeFilter === option.value ? "default" : "outline"}
            size="sm"
            onClick={() => setActiveFilter(option.value)}
            className={cn(
              "transition-all",
              activeFilter === option.value && "shadow-sm"
            )}
          >
            {option.icon}
            <span className="ml-1">{option.label}</span>
            <span className={cn(
              "ml-2 px-1.5 py-0.5 rounded-full text-xs",
              activeFilter === option.value 
                ? "bg-primary-foreground/20 text-primary-foreground" 
                : "bg-secondary text-muted-foreground"
            )}>
              {option.count}
            </span>
          </Button>
        ))}
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search claims..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Claims List */}
      <div className="space-y-3">
        {filteredClaims.map((claim) => (
          <ClaimCard key={claim.id} claim={claim} />
        ))}
        {filteredClaims.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            <p>No claims match your filters</p>
          </div>
        )}
      </div>
    </div>
  );
}
