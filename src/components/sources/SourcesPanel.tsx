import { useState } from "react";
import { Search, Filter, SortAsc } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { SourceCard, Source } from "./SourceCard";

const mockSources: Source[] = [
  {
    id: "1",
    title: "The Gut-Brain Axis: Interactions Between Enteric Microbiota, Central and Enteric Nervous Systems",
    authors: ["Carabotti M", "Scirocco A", "Maselli MA", "Severi C"],
    date: "2015",
    type: "pdf",
    status: "processed",
    claimsExtracted: 12,
    relevanceScore: 94,
    thumbnailColor: "hsl(0, 70%, 60%)",
  },
  {
    id: "2",
    title: "Psychobiotics and the Manipulation of Bacteria–Gut–Brain Signals",
    authors: ["Sarkar A", "Lehto SM", "Harty S", "Dinan TG", "Cryan JF"],
    date: "2016",
    type: "pdf",
    status: "processed",
    claimsExtracted: 8,
    relevanceScore: 87,
    thumbnailColor: "hsl(210, 70%, 55%)",
  },
  {
    id: "3",
    title: "The Microbiome-Gut-Brain Axis in Health and Disease",
    authors: ["Cryan JF", "O'Riordan KJ", "Cowan CSM"],
    date: "2019",
    type: "pdf",
    status: "processing",
    claimsExtracted: 0,
    relevanceScore: 0,
    thumbnailColor: "hsl(160, 60%, 45%)",
  },
  {
    id: "4",
    title: "Gut Microbiota's Effect on Mental Health: The Gut-Brain Axis",
    authors: ["Clapp M", "Aurora N", "Herrera L", "Bhatia M"],
    date: "2017",
    type: "url",
    status: "processed",
    claimsExtracted: 6,
    relevanceScore: 78,
    thumbnailColor: "hsl(280, 60%, 55%)",
  },
  {
    id: "5",
    title: "Role of the Gut Microbiota in Nutrition and Health",
    authors: ["Valdes AM", "Walter J", "Segal E", "Spector TD"],
    date: "2018",
    type: "pdf",
    status: "pending",
    claimsExtracted: 0,
    relevanceScore: 0,
    thumbnailColor: "hsl(35, 70%, 50%)",
  },
];

export function SourcesPanel() {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredSources = mockSources.filter(source =>
    source.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    source.authors.some(a => a.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const processedCount = mockSources.filter(s => s.status === "processed").length;
  const totalClaims = mockSources.reduce((sum, s) => sum + s.claimsExtracted, 0);

  return (
    <div className="space-y-6">
      {/* Stats Bar */}
      <div className="grid grid-cols-3 gap-4">
        <div className="panel-card p-4 text-center">
          <p className="text-2xl font-semibold text-foreground">{mockSources.length}</p>
          <p className="text-sm text-muted-foreground">Total Sources</p>
        </div>
        <div className="panel-card p-4 text-center">
          <p className="text-2xl font-semibold text-consensus">{processedCount}</p>
          <p className="text-sm text-muted-foreground">Processed</p>
        </div>
        <div className="panel-card p-4 text-center">
          <p className="text-2xl font-semibold text-accent">{totalClaims}</p>
          <p className="text-sm text-muted-foreground">Claims Extracted</p>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search sources..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <Button variant="outline">
          <Filter className="h-4 w-4 mr-2" />
          Filter
        </Button>
        <Button variant="outline">
          <SortAsc className="h-4 w-4 mr-2" />
          Sort
        </Button>
      </div>

      {/* Sources List */}
      <div className="space-y-3">
        {filteredSources.map((source) => (
          <SourceCard key={source.id} source={source} />
        ))}
      </div>
    </div>
  );
}
