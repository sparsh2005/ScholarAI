import { Info } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface ConfidenceIndicatorProps {
  level: "high" | "medium" | "low";
  score: number;
  label?: string;
}

export function ConfidenceIndicator({ level, score, label }: ConfidenceIndicatorProps) {
  const getStyles = () => {
    switch (level) {
      case "high":
        return {
          bg: "bg-consensus/20",
          fill: "bg-consensus",
          text: "text-consensus",
        };
      case "medium":
        return {
          bg: "bg-uncertain/20",
          fill: "bg-uncertain",
          text: "text-uncertain",
        };
      case "low":
        return {
          bg: "bg-disagreement/20",
          fill: "bg-disagreement",
          text: "text-disagreement",
        };
    }
  };

  const styles = getStyles();

  return (
    <div className="flex items-center gap-2">
      <div className={cn("w-24 h-2 rounded-full overflow-hidden", styles.bg)}>
        <div 
          className={cn("h-full rounded-full transition-all", styles.fill)}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className={cn("text-sm font-medium", styles.text)}>
        {score}%
      </span>
      {label && (
        <Tooltip>
          <TooltipTrigger>
            <Info className="h-4 w-4 text-muted-foreground" />
          </TooltipTrigger>
          <TooltipContent>
            <p className="text-sm">{label}</p>
          </TooltipContent>
        </Tooltip>
      )}
    </div>
  );
}
