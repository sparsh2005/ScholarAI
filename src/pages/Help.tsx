import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { ExternalLink, BookOpen, Github, FileQuestion } from "lucide-react";

const faqs = [
  {
    question: "What file types are supported?",
    answer: "ScholarAI supports PDF, DOCX, PPTX, PNG, and JPG files up to 50MB each. PDFs typically yield the best results for academic research."
  },
  {
    question: "How does the claim extraction work?",
    answer: "ScholarAI uses advanced language models to identify factual claims in your documents. Claims are then classified as consensus (multiple sources agree), disagreement (sources conflict), or uncertain (insufficient evidence)."
  },
  {
    question: "What makes a good research query?",
    answer: "Be specific! Include key terms, time ranges, or methodological preferences. For example: 'What is the scientific consensus on the relationship between exercise and mental health in adults over 50?' works better than 'exercise and health'."
  },
  {
    question: "How many documents should I upload?",
    answer: "We recommend 3-5 documents for comprehensive analysis. Including sources with different perspectives will yield richer insights with more identified disagreements."
  },
  {
    question: "Why is the backend unavailable?",
    answer: "Make sure the backend server is running on port 8000. Run 'uvicorn main:app --reload --port 8000' in the backend directory. Check the terminal for any error messages."
  },
  {
    question: "Can I use URLs instead of uploading files?",
    answer: "Yes! You can add URLs to academic papers, arXiv preprints, or web articles. ScholarAI will fetch and process the content automatically."
  },
];

const Help = () => {
  return (
    <DashboardLayout 
      title="Help & Support" 
      description="Get help with using ScholarAI"
    >
      <div className="max-w-3xl space-y-6">
        {/* Quick Links */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardContent className="pt-6">
              <a 
                href="http://localhost:8000/docs" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex flex-col items-center text-center gap-2"
              >
                <BookOpen className="h-8 w-8 text-accent" />
                <h3 className="font-semibold">API Documentation</h3>
                <p className="text-sm text-muted-foreground">
                  Explore the full API reference
                </p>
                <ExternalLink className="h-4 w-4 text-muted-foreground" />
              </a>
            </CardContent>
          </Card>

          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardContent className="pt-6">
              <a 
                href="https://github.com/sparsh2005/ScholarAI" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex flex-col items-center text-center gap-2"
              >
                <Github className="h-8 w-8 text-accent" />
                <h3 className="font-semibold">GitHub Repository</h3>
                <p className="text-sm text-muted-foreground">
                  View source code and contribute
                </p>
                <ExternalLink className="h-4 w-4 text-muted-foreground" />
              </a>
            </CardContent>
          </Card>
        </div>

        {/* FAQ Section */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <FileQuestion className="h-5 w-5 text-accent" />
              <CardTitle>Frequently Asked Questions</CardTitle>
            </div>
            <CardDescription>
              Find answers to common questions about ScholarAI
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Accordion type="single" collapsible className="w-full">
              {faqs.map((faq, index) => (
                <AccordionItem key={index} value={`item-${index}`}>
                  <AccordionTrigger className="text-left">
                    {faq.question}
                  </AccordionTrigger>
                  <AccordionContent className="text-muted-foreground">
                    {faq.answer}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </CardContent>
        </Card>

        {/* Getting Started */}
        <Card>
          <CardHeader>
            <CardTitle>Getting Started Guide</CardTitle>
            <CardDescription>
              Follow these steps to use ScholarAI effectively
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ol className="list-decimal list-inside space-y-3 text-sm">
              <li className="text-foreground">
                <span className="font-medium">Enter a research question</span>
                <p className="text-muted-foreground ml-5 mt-1">
                  Be specific about what you want to learn from your documents.
                </p>
              </li>
              <li className="text-foreground">
                <span className="font-medium">Upload documents or add URLs</span>
                <p className="text-muted-foreground ml-5 mt-1">
                  Add 3-5 sources for best results. Mix perspectives for richer analysis.
                </p>
              </li>
              <li className="text-foreground">
                <span className="font-medium">Click "Process & Synthesize"</span>
                <p className="text-muted-foreground ml-5 mt-1">
                  Wait for the pipeline to process your documents. This may take a few minutes.
                </p>
              </li>
              <li className="text-foreground">
                <span className="font-medium">Review your Research Brief</span>
                <p className="text-muted-foreground ml-5 mt-1">
                  Explore consensus, disagreements, and open questions identified in your sources.
                </p>
              </li>
            </ol>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default Help;
