import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { QueryInput } from "@/components/upload/QueryInput";
import { DocumentUpload } from "@/components/upload/DocumentUpload";
import { UrlInput } from "@/components/upload/UrlInput";
import { ProcessButton } from "@/components/upload/ProcessButton";

const Index = () => {
  return (
    <DashboardLayout 
      title="Upload & Query" 
      description="Add your research sources and define your research question"
    >
      <div className="max-w-4xl space-y-6">
        <QueryInput />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <DocumentUpload />
          <UrlInput />
        </div>
        <ProcessButton />
      </div>
    </DashboardLayout>
  );
};

export default Index;
