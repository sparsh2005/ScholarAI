import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ResearchBriefPanel } from "@/components/brief/ResearchBriefPanel";

const Brief = () => {
  return (
    <DashboardLayout 
      title="Research Brief" 
      description="Synthesized findings from your research sources"
    >
      <div className="max-w-4xl">
        <ResearchBriefPanel />
      </div>
    </DashboardLayout>
  );
};

export default Brief;
