# Semgrep POV Assistant

A Python application that analyzes call transcripts using Claude AI to extract key insights, action items, and sentiment analysis. The application processes transcript files and generates comprehensive analysis reports as local files.

## Features

- **Call Transcript Analysis**: Analyzes call transcripts to extract key discussion points, business context, and insights
- **Call Classification**: Automatically categorizes calls as "Discovery Call", "Demo Call", or "POV Check-in"
- **Action Item Extraction**: Identifies and categorizes action items with owners, due dates, and priorities
- **Sentiment Analysis**: Analyzes call sentiment and engagement levels
- **Local File Output**: Generates formatted text files and JSON data for easy review and sharing
- **Multi-format Support**: Supports TXT, DOCX, PDF, and MD transcript files
- **Comprehensive Logging**: Detailed logging with colored output for debugging and monitoring

## Quick Start

### 1. Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd semgrep_pov_assistant

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp env.example .env
```

### 2. Configure API Keys

Edit the `.env` file and add your Anthropic API key:

```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 3. Add Transcript Files

Place your call transcript files in the `data/transcripts/` directory. Supported formats:
- `.txt` - Plain text files
- `.docx` - Microsoft Word documents
- `.pdf` - PDF documents
- `.md` - Markdown files

### 4. Run the Application

```bash
# Process transcripts and generate local files
python main.py

# Process transcripts only (no file creation)
python main.py --no-google-docs

# Enable debug logging
python main.py --debug

# Use custom directories for engagement-specific processing
python main.py --transcripts-dir /path/to/engagement/transcripts --output-dir /path/to/engagement/results
```

## Output Files

The application generates the following files in `data/output/`:

- **Call Summary** (`call_summary_YYYYMMDD_HHMMSS.txt`): Comprehensive analysis of the call
- **Action Items** (`action_items_YYYYMMDD_HHMMSS.txt`): Extracted action items with details
- **Sentiment Analysis** (`sentiment_analysis_YYYYMMDD_HHMMSS.txt`): Sentiment and engagement analysis
- **JSON Analysis** (`call_analysis_YYYYMMDD_HHMMSS.json`): Complete structured data
- **POV Analysis** (`pov_analysis_YYYYMMDD_HHMMSS.txt`): Engagement-level POV Win/Loss analysis

### **📁 File Locations**

For engagement-specific processing, files are created in:
```
/path/to/engagement/output/analysis_YYYYMMDD_HHMMSS/
├── call_summary_YYYYMMDD_HHMMSS.txt
├── action_items_YYYYMMDD_HHMMSS.txt
├── sentiment_analysis_YYYYMMDD_HHMMSS.txt
├── call_analysis_YYYYMMDD_HHMMSS.json
└── pov_analysis_YYYYMMDD_HHMMSS.txt
```

### **📄 POV Analysis File Content**

The POV analysis file contains:
- **Win Probability Assessment** with detailed reasoning
- **Key Positive Factors** supporting the win probability
- **Risk Analysis** with severity, timeline, and mitigation strategies
- **Technical Win Strategy** including unresolved questions and recommended demos
- **Actionable Next Steps** to improve win probability
- **Key Transcript Snippets** with supporting evidence

## Call Classification

The application automatically classifies each call transcript into one of three categories:

### **📋 Call Types**

1. **Discovery Call** - Initial exploratory call to understand customer needs and pain points
2. **Demo Call** - Product demonstration showing features and capabilities  
3. **POV Check-in** - Follow-up call during or after proof of value engagement

### **🔍 Classification Methods**

The system uses two approaches to classify calls:

1. **Pattern Matching**: Analyzes the first few lines of the transcript for keywords:
   - "demo", "demonstration", "product demo" → **Demo Call**
   - "pov sync", "pov check", "proof of value" → **POV Check-in**
   - "discovery", "initial", "first call" → **Discovery Call**

2. **AI Analysis**: Uses Claude to analyze transcript content when pattern matching is inconclusive

### **📊 Classification Summary**

The application displays a classification summary showing:
- Total number of each call type
- Individual file classifications
- Processing statistics by call type

## POV Win/Loss Analysis

The application provides comprehensive Proof of Value (POV) analysis across all call transcripts in an engagement:

### **🎯 Analysis Components**

1. **Win Probability Assessment** - Percentage likelihood of winning the POV
2. **Risk Analysis** - Identified risks with severity, timeline, and mitigation strategies
3. **Technical Win Strategy** - Unresolved questions, recommended demos, and competitive advantages
4. **Actionable Next Steps** - Specific recommendations to improve win probability
5. **Key Transcript Snippets** - Relevant quotes supporting the analysis

### **📊 Analysis Output**

```
🎯 POV WIN/LOSS ANALYSIS
============================================================
📊 Win Probability: 80%
💡 Reasoning: Based on positive sentiment and high engagement

✅ Key Positive Factors:
   • Strong technical engagement
   • Positive sentiment across calls
   • Clear next steps identified

⚠️  Key Risks:
   • Privacy compliance concerns (Severity: high)
     Time Open: Since initial call
     Mitigation: Provide detailed privacy documentation

🔧 Technical Win Strategy:
   📝 Unresolved Technical Questions:
     • Integration with existing GitHub setup
     • RBAC implementation details
   🎯 Recommended Demonstrations:
     • False positive reduction capabilities
     • Dependency analysis features
   🏆 Competitive Advantages:
     • AI-powered learning vs. static rules
     • Multi-language support vs. limited options

📋 Recommended Next Steps:
   • Send pricing proposal within one week
   • Schedule follow-up call for POC planning
   • Prepare privacy documentation
```

### **🔍 Analysis Methodology**

The system aggregates insights across all call transcripts to provide engagement-level analysis:

1. **Individual Call Analysis** - Extracts key insights from each transcript
2. **Engagement Aggregation** - Combines insights across all calls
3. **POV Probability Assessment** - Generates comprehensive win/loss analysis
4. **Risk & Mitigation Planning** - Identifies and addresses blockers

### **📈 Benefits**

- **Engagement-Level Insights** - Analysis across multiple calls, not just individual transcripts
- **Risk Identification** - Proactive identification of deal blockers
- **Actionable Guidance** - Specific steps to improve win probability
- **Evidence-Based Analysis** - Uses actual transcript content and sentiment data

## Engagement-Specific Processing

For managing multiple engagements, you can use custom directories:

### Example Engagement Structure
```
engagements/
├── customer_engagement_2024/
│   ├── call_1_transcript.md
│   ├── call_2_transcript.txt
│   └── results/
│       └── analysis_20250806_134534/
│           ├── call_summary_20250806_134534.txt
│           ├── action_items_20250806_134534.txt
│           ├── sentiment_analysis_20250806_134534.txt
│           └── call_analysis_20250806_134534.json
└── acme_engagement_2024/
    ├── discovery_call.md
    └── results/
```

### Processing an Engagement
```bash
# Process all transcripts in an engagement folder
python main.py --transcripts-dir engagements/customer_engagement_2024 --output-dir engagements/customer_engagement_2024/results

# Process with debug logging
python main.py --transcripts-dir /path/to/engagement --output-dir /path/to/results --debug
```

## Configuration

Edit `config/config.yaml` to customize:

- **Claude Models**: Primary and fallback models
- **Token Limits**: Maximum tokens per request
- **Temperature**: Response creativity (0.0-1.0)
- **Output Settings**: File paths and formatting options
- **Logging**: Log levels and output options

## Example Output

### Call Summary
```
# Call Summary - Semgrep POV Assistant

## Call Details
- Date: 2024-01-15
- Participants: John Smith, Sarah Johnson, Mike Davis
- Duration: 90 minutes
- Call Type: Discovery call

## Executive Summary
Comprehensive analysis of security pipeline integration discussion...

## Key Discussion Points
- Security pipeline integration
- Technical capabilities discussion
- POC planning
- Training and support requirements

## Action Items
- Send POC proposal and timeline (John Smith, End of day, High)
- Schedule technical deep-dive session (John Smith, TBD, High)
- Coordinate POC setup (Sarah Johnson, TBD, High)
```

### Action Items
```
# Action Items - Semgrep POV Assistant

## Summary
Total Action Items: 5

## Action Items List

### Action Item 1
- **Action**: Send POC proposal and timeline
- **Owner**: John Smith
- **Due Date**: by end of day
- **Priority**: High
```

## Architecture

- **ClaudeClient**: Handles communication with Anthropic's Claude API
- **TranscriptProcessor**: Orchestrates transcript analysis and processing
- **LocalFileClient**: Creates formatted output files locally
- **Logger**: Comprehensive logging with colored output

## Requirements

- Python 3.8+
- Anthropic API key
- Required packages (see `requirements.txt`)

## Troubleshooting

### Common Issues

1. **Missing API Key**: Ensure `ANTHROPIC_API_KEY` is set in `.env`
2. **No Transcript Files**: Add transcript files to `data/transcripts/`
3. **Permission Errors**: Check file permissions for output directory
4. **API Rate Limits**: The application includes retry logic with exponential backoff

### Debug Mode

Enable debug logging to see detailed processing information:

```bash
python main.py --debug
```

Debug mode provides detailed information including:
- **Directory Paths**: Full absolute paths for transcript and output directories
- **Directory Contents**: Complete listing of all files and subdirectories in the transcripts folder
- **File Discovery**: Which supported file formats were found and their names
- **Processing Details**: Token usage, API calls, and intermediate results
- **Error Diagnostics**: Detailed error information for troubleshooting

#### Example Debug Output
```
DEBUG - Transcripts directory (absolute path): /Users/user/semgrep_pov_assistant/engagements/customer_engagement_2024
DEBUG - Directory contents of /Users/user/semgrep_pov_assistant/engagements/customer_engagement_2024:
DEBUG -   📄 File: call_1_transcript.md (64836 bytes)
DEBUG -   📄 File: call_2_transcript.txt (12345 bytes)
DEBUG -   📁 Directory: results
DEBUG - Total items in directory: 3
DEBUG - Found 1 md files:
DEBUG -   - call_1_transcript.md
DEBUG - Found 1 txt files:
DEBUG -   - call_2_transcript.txt
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here] 