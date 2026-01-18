import { ReactNode } from "react";
import { ChevronDown } from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";

interface BriefSectionProps {
  title: string;
  icon: ReactNode;
  iconColor?: string;
  count?: number;
  children: ReactNode;
  defaultOpen?: boolean;
}

export function BriefSection({ 
  title, 
  icon, 
  iconColor = "text-foreground", 
  count, 
  children, 
  defaultOpen = true 
}: BriefSectionProps) {
  return (
    <Collapsible defaultOpen={defaultOpen} className="panel-card overflow-hidden">
      <CollapsibleTrigger className="flex items-center justify-between w-full p-4 hover:bg-secondary/50 transition-colors">
        <div className="flex items-center gap-3">
          <div className={cn("h-8 w-8 rounded-lg bg-secondary flex items-center justify-center", iconColor)}>
            {icon}
          </div>
          <div className="text-left">
            <h3 className="font-semibold text-foreground">{title}</h3>
            {count !== undefined && (
              <p className="text-xs text-muted-foreground">{count} items</p>
            )}
          </div>
        </div>
        <ChevronDown className="h-5 w-5 text-muted-foreground transition-transform duration-200 [[data-state=open]>svg]:rotate-180" />
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="px-4 pb-4 pt-0">
          {children}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
