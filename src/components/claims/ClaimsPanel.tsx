import { useState } from "react";
import { Search, CheckCircle, AlertTriangle, HelpCircle } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ClaimCard, Claim, ClaimType } from "./ClaimCard";
import { cn } from "@/lib/utils";

const mockClaims: Claim[] = [
  {
    id: "1",
    statement: "The gut microbiome communicates with the brain through neural, endocrine, and immune pathways, forming a bidirectional communication system.",
    type: "consensus",
    confidence: 95,
    supportingSources: 4,
    contradictingSources: 0,
    sourceIds: ["1", "2", "3", "4"],
  },
  {
    id: "2",
    statement: "Probiotic supplementation can significantly reduce symptoms of depression and anxiety in clinical populations.",
    type: "disagreement",
    confidence: 62,
    supportingSources: 2,
    contradictingSources: 2,
    sourceIds: ["1", "2", "3", "4"],
  },
  {
    id: "3",
    statement: "Short-chain fatty acids produced by gut bacteria can cross the blood-brain barrier and influence brain function.",
    type: "consensus",
    confidence: 88,
    supportingSources: 3,
    contradictingSources: 0,
    sourceIds: ["1", "2", "4"],
  },
  {
    id: "4",
    statement: "Specific bacterial strains (psychobiotics) have reproducible effects on mental health outcomes.",
    type: "uncertain",
    confidence: 45,
    supportingSources: 2,
    contradictingSources: 1,
    sourceIds: ["2", "3", "4"],
  },
  {
    id: "5",
    statement: "Early-life gut microbiome disruption can have lasting effects on brain development and mental health.",
    type: "consensus",
    confidence: 82,
    supportingSources: 3,
    contradictingSources: 0,
    sourceIds: ["1", "3", "4"],
  },
  {
    id: "6",
    statement: "Diet interventions targeting gut microbiome composition are effective treatments for psychiatric disorders.",
    type: "disagreement",
    confidence: 55,
    supportingSources: 1,
    contradictingSources: 2,
    sourceIds: ["2", "3", "4"],
  },
];

type FilterType = "all" | ClaimType;

interface FilterOption {
  value: FilterType;
  label: string;
  icon: React.ReactNode;
  count: number;
}

export function ClaimsPanel() {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<FilterType>("all");

  const filterOptions: FilterOption[] = [
    { value: "all", label: "All Claims", icon: null, count: mockClaims.length },
    { 
      value: "consensus", 
      label: "Consensus", 
      icon: <CheckCircle className="h-4 w-4 text-consensus" />, 
      count: mockClaims.filter(c => c.type === "consensus").length 
    },
    { 
      value: "disagreement", 
      label: "Disagreement", 
      icon: <AlertTriangle className="h-4 w-4 text-disagreement" />, 
      count: mockClaims.filter(c => c.type === "disagreement").length 
    },
    { 
      value: "uncertain", 
      label: "Uncertain", 
      icon: <HelpCircle className="h-4 w-4 text-uncertain" />, 
      count: mockClaims.filter(c => c.type === "uncertain").length 
    },
  ];

  const filteredClaims = mockClaims.filter(claim => {
    const matchesSearch = claim.statement.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = activeFilter === "all" || claim.type === activeFilter;
    return matchesSearch && matchesFilter;
  });

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
