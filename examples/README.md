# ScholarAI Example Documents

This directory contains example documents and sample outputs for testing ScholarAI.

## Example Documents

### `sample_research_paper.md`
A sample research paper in Markdown format about exercise and mental health. Use this to test document processing without needing a real PDF.

### `sample_meta_analysis.md`
A sample meta-analysis paper covering multiple studies. Tests ScholarAI's ability to extract claims from comprehensive reviews.

## Sample Outputs

### `sample_process_response.json`
Example response from the `/api/process-docs` endpoint.

### `sample_claims_response.json`
Example response from the `/api/extract-claims` endpoint showing consensus, disagreement, and uncertain claims.

### `sample_brief_response.json`
Example response from the `/api/synthesize-report` endpoint with a complete research brief.

## Testing Workflow

1. Upload `sample_research_paper.md` (or copy its content)
2. Set query: "What are the effects of exercise on mental health?"
3. Process and review the generated brief
4. Compare with sample outputs

## Typical Research Queries

- "What is the scientific consensus on exercise and depression?"
- "How does physical activity affect anxiety levels?"
- "What are the mechanisms linking exercise to mental health?"
- "What dosage of exercise is most effective for mental health benefits?"
