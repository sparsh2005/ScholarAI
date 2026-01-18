import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ClaimsPanel } from "@/components/claims/ClaimsPanel";

const Claims = () => {
  return (
    <DashboardLayout 
      title="Claims" 
      description="Explore extracted claims organized by consensus level"
    >
      <div className="max-w-4xl">
        <ClaimsPanel />
      </div>
    </DashboardLayout>
  );
};

export default Claims;
