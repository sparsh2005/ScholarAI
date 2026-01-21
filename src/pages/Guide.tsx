import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { 
  Upload, 
  Search, 
  FileText, 
  Cpu, 
  Database, 
  Brain, 
  CheckCircle, 
  AlertTriangle, 
  HelpCircle,
  ArrowRight,
  ArrowDown,
  Layers,
  Zap,
  Globe,
  FileQuestion
} from "lucide-react";

const Guide = () => {
  const location = useLocation();

  // Scroll to section if hash is present
  useEffect(() => {
    if (location.hash) {
      const element = document.getElementById(location.hash.slice(1));
      if (element) {
        setTimeout(() => {
          element.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      }
    }
  }, [location.hash]);

  return (
    <DashboardLayout 
      title="User Guide" 
      description="Learn how to use ScholarAI and understand how it works"
    >
      <div className="max-w-4xl space-y-12">
        {/* ========================================== */}
        {/* HOW TO USE SECTION */}
        {/* ========================================== */}
        <section id="how-to-use">
          <div className="flex items-center gap-3 mb-6">
            <div className="h-10 w-10 rounded-lg bg-accent/10 flex items-center justify-center">
              <FileQuestion className="h-5 w-5 text-accent" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-foreground">How to Use ScholarAI</h2>
              <p className="text-muted-foreground">Step-by-step guide to get started</p>
            </div>
          </div>

          {/* What is ScholarAI */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-accent" />
                What is ScholarAI?
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-foreground leading-relaxed">
                ScholarAI is an <strong>Autonomous Research Engineer</strong> — an AI-powered tool that helps you 
                synthesize knowledge from multiple research documents. Unlike chatbots that give conversational 
                responses, ScholarAI produces structured research briefs that identify:
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                <div className="p-4 rounded-lg bg-consensus/10 border border-consensus/20">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle className="h-5 w-5 text-consensus" />
                    <span className="font-semibold text-consensus">Consensus</span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Points where multiple sources agree
                  </p>
                </div>
                <div className="p-4 rounded-lg bg-disagreement/10 border border-disagreement/20">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle className="h-5 w-5 text-disagreement" />
                    <span className="font-semibold text-disagreement">Disagreements</span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Conflicting findings between sources
                  </p>
                </div>
                <div className="p-4 rounded-lg bg-uncertain/10 border border-uncertain/20">
                  <div className="flex items-center gap-2 mb-2">
                    <HelpCircle className="h-5 w-5 text-uncertain" />
                    <span className="font-semibold text-uncertain">Open Questions</span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Gaps in the research that need more study
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Step by Step Guide */}
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-foreground">Step-by-Step Guide</h3>
            
            {/* Step 1 */}
            <Card>
              <CardContent className="pt-6">
                <div className="flex gap-4">
                  <div className="flex-shrink-0">
                    <div className="h-10 w-10 rounded-full bg-accent text-white flex items-center justify-center font-bold">
                      1
                    </div>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-lg text-foreground mb-2">Enter Your Research Question</h4>
                    <p className="text-muted-foreground mb-3">
                      Start by typing a specific research question in the query box. The more specific you are, 
                      the better the results.
                    </p>
                    <div className="p-3 bg-secondary/50 rounded-lg">
                      <p className="text-sm font-medium text-foreground mb-2">✅ Good examples:</p>
                      <ul className="text-sm text-muted-foreground space-y-1 ml-4">
                        <li>• "What is the scientific consensus on exercise and depression?"</li>
                        <li>• "How does sleep deprivation affect cognitive performance in adults?"</li>
                        <li>• "What are the environmental impacts of lithium-ion battery production?"</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Step 2 */}
            <Card>
              <CardContent className="pt-6">
                <div className="flex gap-4">
                  <div className="flex-shrink-0">
                    <div className="h-10 w-10 rounded-full bg-accent text-white flex items-center justify-center font-bold">
                      2
                    </div>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-lg text-foreground mb-2">Add Your Sources</h4>
                    <p className="text-muted-foreground mb-3">
                      Upload documents or add URLs to academic papers. ScholarAI supports multiple formats.
                    </p>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-3 bg-secondary/50 rounded-lg">
                        <p className="text-sm font-medium text-foreground mb-2">📄 Upload Files:</p>
                        <ul className="text-sm text-muted-foreground space-y-1">
                          <li>• PDF documents</li>
                          <li>• Word documents (.docx)</li>
                          <li>• PowerPoint (.pptx)</li>
                          <li>• Images (PNG, JPG)</li>
                        </ul>
                      </div>
                      <div className="p-3 bg-secondary/50 rounded-lg">
                        <p className="text-sm font-medium text-foreground mb-2">🔗 Add URLs:</p>
                        <ul className="text-sm text-muted-foreground space-y-1">
                          <li>• arXiv papers</li>
                          <li>• PubMed articles</li>
                          <li>• Web pages</li>
                          <li>• Online PDFs</li>
                        </ul>
                      </div>
                    </div>
                    <div className="mt-3 p-3 bg-uncertain/10 border border-uncertain/20 rounded-lg">
                      <p className="text-sm text-uncertain font-medium">💡 Tip: Upload 3-5 sources with different perspectives for the best analysis</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Step 3 */}
            <Card>
              <CardContent className="pt-6">
                <div className="flex gap-4">
                  <div className="flex-shrink-0">
                    <div className="h-10 w-10 rounded-full bg-accent text-white flex items-center justify-center font-bold">
                      3
                    </div>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-lg text-foreground mb-2">Process & Synthesize</h4>
                    <p className="text-muted-foreground mb-3">
                      Click the "Process & Synthesize" button and wait for the pipeline to complete. 
                      This involves 4 stages:
                    </p>
                    <div className="flex items-center justify-between p-4 bg-secondary/50 rounded-lg">
                      <div className="text-center">
                        <div className="h-8 w-8 rounded-full bg-primary text-white flex items-center justify-center mx-auto mb-1 text-sm">1</div>
                        <span className="text-xs text-muted-foreground">Processing</span>
                      </div>
                      <ArrowRight className="h-4 w-4 text-muted-foreground" />
                      <div className="text-center">
                        <div className="h-8 w-8 rounded-full bg-primary text-white flex items-center justify-center mx-auto mb-1 text-sm">2</div>
                        <span className="text-xs text-muted-foreground">Retrieving</span>
                      </div>
                      <ArrowRight className="h-4 w-4 text-muted-foreground" />
                      <div className="text-center">
                        <div className="h-8 w-8 rounded-full bg-primary text-white flex items-center justify-center mx-auto mb-1 text-sm">3</div>
                        <span className="text-xs text-muted-foreground">Extracting</span>
                      </div>
                      <ArrowRight className="h-4 w-4 text-muted-foreground" />
                      <div className="text-center">
                        <div className="h-8 w-8 rounded-full bg-consensus text-white flex items-center justify-center mx-auto mb-1 text-sm">✓</div>
                        <span className="text-xs text-muted-foreground">Complete</span>
                      </div>
                    </div>
                    <div className="mt-3 p-3 bg-disagreement/10 border border-disagreement/20 rounded-lg">
                      <p className="text-sm text-disagreement font-medium">
                        ⏱️ Note: First-time processing may take longer (1-3 minutes) as AI models are downloaded. 
                        Subsequent runs will be faster.
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Step 4 */}
            <Card>
              <CardContent className="pt-6">
                <div className="flex gap-4">
                  <div className="flex-shrink-0">
                    <div className="h-10 w-10 rounded-full bg-consensus text-white flex items-center justify-center font-bold">
                      4
                    </div>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-lg text-foreground mb-2">Review Your Research Brief</h4>
                    <p className="text-muted-foreground mb-3">
                      Once complete, you'll be taken to the Research Brief page. Here you can:
                    </p>
                    <ul className="space-y-2 text-muted-foreground">
                      <li className="flex items-start gap-2">
                        <CheckCircle className="h-4 w-4 text-consensus mt-1" />
                        <span>View the overall confidence score and source coverage</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="h-4 w-4 text-consensus mt-1" />
                        <span>Read consensus findings with supporting evidence</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="h-4 w-4 text-consensus mt-1" />
                        <span>Explore disagreements with side-by-side perspectives</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="h-4 w-4 text-consensus mt-1" />
                        <span>Identify open questions for further research</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="h-4 w-4 text-consensus mt-1" />
                        <span>Copy the brief to clipboard for use in your work</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        <Separator className="my-12" />

        {/* ========================================== */}
        {/* HOW IT WORKS SECTION */}
        {/* ========================================== */}
        <section id="how-it-works">
          <div className="flex items-center gap-3 mb-6">
            <div className="h-10 w-10 rounded-lg bg-accent/10 flex items-center justify-center">
              <Cpu className="h-5 w-5 text-accent" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-foreground">How It Works</h2>
              <p className="text-muted-foreground">Technical deep-dive into ScholarAI's pipeline</p>
            </div>
          </div>

          {/* Architecture Overview */}
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>System Architecture Overview</CardTitle>
              <CardDescription>
                ScholarAI uses a Retrieval-Augmented Generation (RAG) pipeline to process documents and generate insights
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Visual Pipeline Diagram */}
              <div className="p-6 bg-secondary/30 rounded-lg">
                <div className="flex flex-col items-center space-y-4">
                  {/* Row 1: Input */}
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-background rounded-lg border shadow-sm text-center min-w-[120px]">
                      <Upload className="h-6 w-6 mx-auto mb-1 text-accent" />
                      <span className="text-xs font-medium">Documents</span>
                    </div>
                    <span className="text-muted-foreground">+</span>
                    <div className="p-3 bg-background rounded-lg border shadow-sm text-center min-w-[120px]">
                      <Globe className="h-6 w-6 mx-auto mb-1 text-accent" />
                      <span className="text-xs font-medium">URLs</span>
                    </div>
                    <span className="text-muted-foreground">+</span>
                    <div className="p-3 bg-background rounded-lg border shadow-sm text-center min-w-[120px]">
                      <Search className="h-6 w-6 mx-auto mb-1 text-accent" />
                      <span className="text-xs font-medium">Query</span>
                    </div>
                  </div>

                  <ArrowDown className="h-6 w-6 text-muted-foreground" />

                  {/* Row 2: Processing */}
                  <div className="p-4 bg-primary/10 rounded-lg border border-primary/20 w-full max-w-md">
                    <div className="flex items-center gap-3 justify-center">
                      <FileText className="h-5 w-5 text-primary" />
                      <div className="text-center">
                        <span className="font-medium text-primary">1. Document Processing</span>
                        <p className="text-xs text-muted-foreground">Docling converts to structured text</p>
                      </div>
                    </div>
                  </div>

                  <ArrowDown className="h-6 w-6 text-muted-foreground" />

                  {/* Row 3: Chunking & Embedding */}
                  <div className="flex items-center gap-4">
                    <div className="p-4 bg-uncertain/10 rounded-lg border border-uncertain/20 text-center">
                      <Layers className="h-5 w-5 mx-auto mb-1 text-uncertain" />
                      <span className="text-sm font-medium text-uncertain">2. Chunking</span>
                      <p className="text-xs text-muted-foreground">Split into pieces</p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                    <div className="p-4 bg-uncertain/10 rounded-lg border border-uncertain/20 text-center">
                      <Zap className="h-5 w-5 mx-auto mb-1 text-uncertain" />
                      <span className="text-sm font-medium text-uncertain">3. Embedding</span>
                      <p className="text-xs text-muted-foreground">Convert to vectors</p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                    <div className="p-4 bg-uncertain/10 rounded-lg border border-uncertain/20 text-center">
                      <Database className="h-5 w-5 mx-auto mb-1 text-uncertain" />
                      <span className="text-sm font-medium text-uncertain">4. Vector Store</span>
                      <p className="text-xs text-muted-foreground">ChromaDB index</p>
                    </div>
                  </div>

                  <ArrowDown className="h-6 w-6 text-muted-foreground" />

                  {/* Row 4: Retrieval */}
                  <div className="p-4 bg-consensus/10 rounded-lg border border-consensus/20 w-full max-w-md">
                    <div className="flex items-center gap-3 justify-center">
                      <Search className="h-5 w-5 text-consensus" />
                      <div className="text-center">
                        <span className="font-medium text-consensus">5. Semantic Retrieval</span>
                        <p className="text-xs text-muted-foreground">Find relevant chunks using similarity search</p>
                      </div>
                    </div>
                  </div>

                  <ArrowDown className="h-6 w-6 text-muted-foreground" />

                  {/* Row 5: LLM Processing */}
                  <div className="flex items-center gap-4">
                    <div className="p-4 bg-disagreement/10 rounded-lg border border-disagreement/20 text-center">
                      <Brain className="h-5 w-5 mx-auto mb-1 text-disagreement" />
                      <span className="text-sm font-medium text-disagreement">6. Claim Extraction</span>
                      <p className="text-xs text-muted-foreground">LLM identifies claims</p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                    <div className="p-4 bg-disagreement/10 rounded-lg border border-disagreement/20 text-center">
                      <Brain className="h-5 w-5 mx-auto mb-1 text-disagreement" />
                      <span className="text-sm font-medium text-disagreement">7. Classification</span>
                      <p className="text-xs text-muted-foreground">Categorize claims</p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                    <div className="p-4 bg-disagreement/10 rounded-lg border border-disagreement/20 text-center">
                      <Brain className="h-5 w-5 mx-auto mb-1 text-disagreement" />
                      <span className="text-sm font-medium text-disagreement">8. Synthesis</span>
                      <p className="text-xs text-muted-foreground">Generate brief</p>
                    </div>
                  </div>

                  <ArrowDown className="h-6 w-6 text-muted-foreground" />

                  {/* Row 6: Output */}
                  <div className="p-4 bg-background rounded-lg border-2 border-accent shadow-sm">
                    <div className="text-center">
                      <FileText className="h-6 w-6 mx-auto mb-1 text-accent" />
                      <span className="font-semibold text-accent">Research Brief</span>
                      <p className="text-xs text-muted-foreground">Structured JSON output</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Detailed Explanations */}
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-foreground">Technical Concepts Explained</h3>

            {/* Docling */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-accent" />
                  Document Processing with Docling
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  <strong>Docling</strong> is an open-source document conversion library developed by IBM Research. 
                  It converts various document formats (PDF, DOCX, PPTX, images) into structured data.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-3 bg-secondary/50 rounded-lg">
                    <p className="text-sm font-medium mb-2">What Docling does:</p>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      <li>• Extracts text while preserving structure</li>
                      <li>• Identifies headings, paragraphs, tables</li>
                      <li>• Performs OCR on images and scanned PDFs</li>
                      <li>• Outputs clean Markdown/JSON</li>
                    </ul>
                  </div>
                  <div className="p-3 bg-secondary/50 rounded-lg">
                    <p className="text-sm font-medium mb-2">Why it matters:</p>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      <li>• Clean text = better AI understanding</li>
                      <li>• Structure helps identify sections</li>
                      <li>• Handles complex academic papers</li>
                      <li>• Works across many formats</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Chunking */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Badge variant="outline" className="mr-2">Definition</Badge>
                  Chunking
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  <strong>Chunking</strong> is the process of splitting a large document into smaller, 
                  meaningful pieces called "chunks." This is necessary because:
                </p>
                <ul className="space-y-2 text-muted-foreground mb-4">
                  <li className="flex items-start gap-2">
                    <span className="text-accent">1.</span>
                    <span>AI models have limited context windows (can only process so much text at once)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-accent">2.</span>
                    <span>Smaller chunks enable more precise retrieval</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-accent">3.</span>
                    <span>Semantic boundaries (paragraphs, sections) are preserved</span>
                  </li>
                </ul>
                <div className="p-4 bg-secondary/50 rounded-lg">
                  <p className="text-sm font-medium mb-2">ScholarAI's chunking strategy:</p>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    <li>• <strong>Chunk size:</strong> ~512 characters (configurable)</li>
                    <li>• <strong>Overlap:</strong> 50 characters between chunks</li>
                    <li>• <strong>Boundaries:</strong> Splits at sentence/paragraph breaks when possible</li>
                  </ul>
                </div>
              </CardContent>
            </Card>

            {/* Embeddings */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Badge variant="outline" className="mr-2">Definition</Badge>
                  Embeddings
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  <strong>Embeddings</strong> are numerical representations of text that capture semantic meaning. 
                  Think of them as converting words into coordinates in a high-dimensional space where 
                  similar meanings are close together.
                </p>
                <div className="p-4 bg-secondary/50 rounded-lg mb-4">
                  <p className="text-sm font-medium mb-2">Example (simplified to 3D):</p>
                  <div className="font-mono text-sm text-muted-foreground space-y-1">
                    <p>"cat" → [0.2, 0.8, 0.1]</p>
                    <p>"kitten" → [0.25, 0.75, 0.15] (very close to "cat")</p>
                    <p>"car" → [0.9, 0.1, 0.7] (far from "cat")</p>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">
                  <strong>ScholarAI uses:</strong> <code className="bg-secondary px-1 rounded">all-MiniLM-L6-v2</code> model 
                  which produces 384-dimensional vectors. This is a sentence transformer model optimized for semantic similarity.
                </p>
              </CardContent>
            </Card>

            {/* Vector Store */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5 text-accent" />
                  Vector Store (ChromaDB)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  A <strong>vector store</strong> is a specialized database designed to store and search embeddings efficiently.
                  ScholarAI uses <strong>ChromaDB</strong>, an open-source embedding database.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-3 bg-secondary/50 rounded-lg">
                    <p className="text-sm font-medium mb-2">How it works:</p>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      <li>• Stores chunk text + its embedding</li>
                      <li>• Uses approximate nearest neighbor (ANN) search</li>
                      <li>• Finds similar chunks in milliseconds</li>
                      <li>• Persists data to disk</li>
                    </ul>
                  </div>
                  <div className="p-3 bg-secondary/50 rounded-lg">
                    <p className="text-sm font-medium mb-2">In ScholarAI:</p>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      <li>• Each session has its own collection</li>
                      <li>• Chunks are tagged with source document</li>
                      <li>• Metadata stored for attribution</li>
                      <li>• Supports filtering by document</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Semantic Retrieval */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Search className="h-5 w-5 text-accent" />
                  Semantic Retrieval
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  <strong>Semantic retrieval</strong> finds relevant content based on meaning, not just keywords. 
                  When you ask a question, ScholarAI:
                </p>
                <ol className="space-y-2 text-muted-foreground mb-4">
                  <li className="flex items-start gap-2">
                    <span className="h-6 w-6 rounded-full bg-accent text-white flex items-center justify-center text-xs flex-shrink-0">1</span>
                    <span>Converts your query into an embedding (same model as documents)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="h-6 w-6 rounded-full bg-accent text-white flex items-center justify-center text-xs flex-shrink-0">2</span>
                    <span>Searches the vector store for chunks with similar embeddings</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="h-6 w-6 rounded-full bg-accent text-white flex items-center justify-center text-xs flex-shrink-0">3</span>
                    <span>Returns the top-K most relevant chunks (default: 20)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="h-6 w-6 rounded-full bg-accent text-white flex items-center justify-center text-xs flex-shrink-0">4</span>
                    <span>Uses MMR (Maximal Marginal Relevance) for diverse results</span>
                  </li>
                </ol>
                <p className="text-sm text-muted-foreground italic">
                  This is the "Retrieval" in RAG (Retrieval-Augmented Generation).
                </p>
              </CardContent>
            </Card>

            {/* Claim Extraction & LLM */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5 text-accent" />
                  Claim Extraction & Synthesis (LLM)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  The final stages use a <strong>Large Language Model (LLM)</strong> — specifically OpenAI's GPT-4o-mini — 
                  to analyze the retrieved chunks and generate structured output.
                </p>
                
                <div className="space-y-4">
                  <div className="p-4 bg-secondary/50 rounded-lg">
                    <p className="text-sm font-medium mb-2">Stage 1: Claim Extraction</p>
                    <p className="text-sm text-muted-foreground">
                      The LLM reads all retrieved chunks and identifies factual claims. Each claim is extracted with:
                    </p>
                    <ul className="text-sm text-muted-foreground mt-2 space-y-1">
                      <li>• The claim statement</li>
                      <li>• Supporting evidence quotes</li>
                      <li>• Source attribution</li>
                    </ul>
                  </div>

                  <div className="p-4 bg-secondary/50 rounded-lg">
                    <p className="text-sm font-medium mb-2">Stage 2: Classification</p>
                    <p className="text-sm text-muted-foreground">
                      Each claim is classified based on source agreement:
                    </p>
                    <ul className="text-sm text-muted-foreground mt-2 space-y-1">
                      <li>• <strong className="text-consensus">Consensus:</strong> Multiple sources support, none contradict</li>
                      <li>• <strong className="text-disagreement">Disagreement:</strong> Sources have conflicting findings</li>
                      <li>• <strong className="text-uncertain">Uncertain:</strong> Insufficient evidence or only one source</li>
                    </ul>
                  </div>

                  <div className="p-4 bg-secondary/50 rounded-lg">
                    <p className="text-sm font-medium mb-2">Stage 3: Brief Synthesis</p>
                    <p className="text-sm text-muted-foreground">
                      Finally, the LLM generates a structured research brief containing:
                    </p>
                    <ul className="text-sm text-muted-foreground mt-2 space-y-1">
                      <li>• Summary of consensus findings</li>
                      <li>• Detailed disagreements with both perspectives</li>
                      <li>• Open questions for further research</li>
                      <li>• Confidence score and limitations</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* RAG Summary */}
            <Card className="border-accent">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-accent">
                  <Zap className="h-5 w-5" />
                  What is RAG (Retrieval-Augmented Generation)?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  <strong>RAG</strong> is a technique that combines information retrieval with language model generation. 
                  Instead of relying solely on what the LLM learned during training, RAG:
                </p>
                <ol className="space-y-3 text-muted-foreground">
                  <li className="flex items-start gap-3">
                    <span className="h-6 w-6 rounded-full bg-accent text-white flex items-center justify-center text-xs flex-shrink-0">R</span>
                    <div>
                      <strong className="text-foreground">Retrieves</strong> relevant information from a knowledge base (your documents)
                    </div>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="h-6 w-6 rounded-full bg-accent text-white flex items-center justify-center text-xs flex-shrink-0">A</span>
                    <div>
                      <strong className="text-foreground">Augments</strong> the LLM's prompt with this retrieved context
                    </div>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="h-6 w-6 rounded-full bg-accent text-white flex items-center justify-center text-xs flex-shrink-0">G</span>
                    <div>
                      <strong className="text-foreground">Generates</strong> responses grounded in your actual documents
                    </div>
                  </li>
                </ol>
                <div className="mt-4 p-3 bg-accent/10 rounded-lg">
                  <p className="text-sm text-accent font-medium">
                    This means ScholarAI's output is always based on YOUR documents, not general internet knowledge!
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>
      </div>
    </DashboardLayout>
  );
};

export default Guide;
