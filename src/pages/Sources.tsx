import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { SourcesPanel } from "@/components/sources/SourcesPanel";

const Sources = () => {
  return (
    <DashboardLayout 
      title="Sources" 
      description="View and manage your processed research documents"
    >
      <div className="max-w-4xl">
        <SourcesPanel />
      </div>
    </DashboardLayout>
  );
};

export default Sources;
