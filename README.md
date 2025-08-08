# Semgrep POV Assistant

A comprehensive Python application that analyzes call transcripts using Claude AI to extract key insights, action items, sentiment analysis, and generate professional Word documents. The application processes transcript files and generates comprehensive analysis reports with proper formatting for sales teams and stakeholders.

## 🚀 Features

- **📊 Call Transcript Analysis**: Analyzes call transcripts to extract key discussion points, business context, and insights
- **🏷️ Call Classification**: Automatically categorizes calls as "Discovery Call", "Demo Call", or "POV Check-in"
- **📋 Action Item Extraction**: Identifies and categorizes action items with owners, due dates, and priorities
- **😊 Sentiment Analysis**: Analyzes call sentiment and engagement levels
- **📄 Professional Word Documents**: Generates beautifully formatted Word documents (.docx) with proper headings, tables, and styling
- **📊 POV Win/Loss Analysis**: Engagement-level analysis with win probability, risk assessment, and technical strategy
- **🔧 Technical Deployment Analysis**: Comprehensive technical infrastructure analysis including SCM, CI, languages, and security tools
- **👥 Customer Overview Analysis**: Detailed customer state analysis with current challenges, desired future state, and POV strategy
- **📁 Multi-format Support**: Supports TXT, DOCX, PDF, and MD transcript files
- **📝 Comprehensive Logging**: Detailed logging with colored output for debugging and monitoring
- **🎯 Engagement-Specific Processing**: Process entire engagement folders with custom input/output directories

## 🏗️ Architecture

- **ClaudeClient**: Handles communication with Anthropic's Claude API
- **TranscriptProcessor**: Orchestrates transcript analysis and processing
- **LocalFileClient**: Creates formatted output files locally (Word documents and JSON data)
- **Logger**: Comprehensive logging with colored output

## 🚀 Quick Start

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
# Process transcripts and generate Word documents
python main.py

# Enable debug logging
python main.py --debug

# Use custom directories for engagement-specific processing
python main.py --transcripts-dir /path/to/engagement/transcripts --output-dir /path/to/engagement/results
```

## 📄 Output Files

The application generates professional Word documents and JSON data files in timestamped directories:

### **📁 File Structure**
```
/path/to/engagement/output/analysis_YYYYMMDD_HHMMSS/
├── call_summary_YYYYMMDD_HHMMSS.docx          # Professional call summary
├── action_items_YYYYMMDD_HHMMSS.docx          # Formatted action items
├── sentiment_analysis_YYYYMMDD_HHMMSS.docx    # Sentiment analysis report
├── pov_analysis_YYYYMMDD_HHMMSS.docx          # POV Win/Loss analysis
├── technical_deployment_YYYYMMDD_HHMMSS.docx  # Technical infrastructure analysis
├── customer_overview_YYYYMMDD_HHMMSS.docx     # Customer overview analysis
└── call_analysis_YYYYMMDD_HHMMSS.json        # Complete structured data
```

### **📄 Word Document Features**

Each Word document includes:
- **Professional Formatting**: Proper headings, tables, bullet points, and styling
- **Executive Summary**: High-level insights and key findings
- **Detailed Analysis**: Comprehensive breakdown of all analysis components
- **Evidence-Based**: Relevant transcript snippets and supporting context
- **Actionable Insights**: Clear recommendations and next steps
- **Professional Branding**: Consistent formatting with Semgrep branding

## 🏷️ Call Classification

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

## 🎯 POV Win/Loss Analysis

The application provides comprehensive Proof of Value (POV) analysis across all call transcripts in an engagement:

### **📊 Analysis Components**

1. **Win Probability Assessment** - Percentage likelihood of winning the POV with detailed reasoning
2. **Key Positive Factors** - Supporting evidence and positive indicators
3. **Risk Analysis** - Identified risks with severity, timeline, and mitigation strategies
4. **Technical Win Strategy** - Unresolved questions, recommended demos, and competitive advantages
5. **Actionable Next Steps** - Specific recommendations to improve win probability
6. **Key Transcript Snippets** - Relevant quotes supporting the analysis

### **📄 POV Analysis Word Document Content**

The POV analysis Word document includes:
- **Win Probability Assessment** with detailed reasoning
- **Key Positive Factors** supporting the win probability
- **Risk Analysis** with severity, timeline, and mitigation strategies
- **Technical Win Strategy** including unresolved questions and recommended demos
- **Actionable Next Steps** to improve win probability
- **Key Transcript Snippets** with supporting evidence

## 🔧 Technical Deployment Analysis

The application analyzes technical infrastructure details across all call transcripts:

### **📊 Analysis Components**

1. **SCM Platform** - Source code management platform and deployment type
2. **CI Pipelines** - Continuous integration tools and workflows
3. **Programming Languages** - Primary and POC focus languages
4. **Integrations** - Current and interested integrations
5. **Supply Chain Security** - Languages tested and package managers
6. **Current Security Tools** - SAST, DAST, SCA, Secrets Detection, ASPM tools
7. **IDE Environment** - Primary IDE and additional tools
8. **Deployment Complexity** - Overall complexity assessment
9. **Migration Considerations** - Technical migration requirements
10. **Technical Risks** - Identified technical risks and challenges
11. **Recommendations** - Technical recommendations and best practices

## 👥 Customer Overview Analysis

The application provides comprehensive customer state analysis:

### **📊 Analysis Components**

1. **Current State** - Current SAST, SCA, and Secrets Detection tooling and challenges
2. **Negative Consequences** - Operational, business, and security impacts of current state
3. **Desired Future State** - Operational, security, and business goals
4. **Key Semgrep Capabilities** - Relevant capabilities for SAST, SCA, Secrets, and Integration
5. **POV Strategy** - Primary focus areas, demonstration priorities, and success metrics
6. **Key Transcript Snippets** - Supporting evidence and context

## 📁 Engagement-Specific Processing

For managing multiple engagements, you can use custom directories:

### Example Engagement Structure
```
engagements/
├── customer_engagement_2024/
│   ├── call_1_transcript.md
│   ├── call_2_transcript.txt
│   └── output/
│       └── analysis_20250806_134534/
│           ├── call_summary_20250806_134534.docx
│           ├── action_items_20250806_134534.docx
│           ├── sentiment_analysis_20250806_134534.docx
│           ├── pov_analysis_20250806_134534.docx
│           ├── technical_deployment_20250806_134534.docx
│           ├── customer_overview_20250806_134534.docx
│           └── call_analysis_20250806_134534.json
└── acme_engagement_2024/
    ├── discovery_call.md
    └── output/
```

### Processing an Engagement
```bash
# Process all transcripts in an engagement folder
python main.py --transcripts-dir engagements/customer_engagement_2024 --output-dir engagements/customer_engagement_2024/output

# Process with debug logging
python main.py --transcripts-dir /path/to/engagement --output-dir /path/to/results --debug
```

## ⚙️ Configuration

Edit `config/config.yaml` to customize:

- **Claude Models**: Primary and fallback models
- **Token Limits**: Maximum tokens per request
- **Temperature**: Response creativity (0.0-1.0)
- **Output Settings**: File paths and formatting options
- **Logging**: Log levels and output options

## 📊 Example Output

### Call Summary Word Document
```
Call Summary - Semgrep POV Assistant

Call Details
- Date: 2024-01-15
- Participants: John Smith, Sarah Johnson, Mike Davis
- Duration: 90 minutes
- Call Type: Discovery call

Executive Summary
Comprehensive analysis of security pipeline integration discussion...

Key Discussion Points
• Security pipeline integration
• Technical capabilities discussion
• POC planning
• Training and support requirements

Action Items
• Send POC proposal and timeline (John Smith, End of day, High)
• Schedule technical deep-dive session (John Smith, TBD, High)
• Coordinate POC setup (Sarah Johnson, TBD, High)
```

### POV Analysis Word Document
```
POV Win/Loss Analysis - Semgrep POV Assistant

Win Probability Assessment
Win Probability: 80%
Reasoning: Based on positive sentiment and high engagement

Key Positive Factors
✅ Strong technical engagement
✅ Positive sentiment across calls
✅ Clear next steps identified

Key Risks
⚠️ Privacy compliance concerns (Severity: high)
   Time Open: Since initial call
   Mitigation: Provide detailed privacy documentation

Technical Win Strategy
📝 Unresolved Technical Questions:
   • Integration with existing GitHub setup
   • RBAC implementation details

🎯 Recommended Demonstrations:
   • False positive reduction capabilities
   • Dependency analysis features

🏆 Competitive Advantages:
   • AI-powered learning vs. static rules
   • Multi-language support vs. limited options
```

## 🔧 Requirements

- Python 3.8+
- Anthropic API key
- Required packages (see `requirements.txt`):
  - `anthropic>=0.18.0` - Claude API client
  - `python-docx>=0.8.11` - Word document creation
  - `python-dotenv>=1.0.0` - Environment variable management
  - `pyyaml>=6.0` - Configuration file parsing
  - Additional dependencies for text processing and utilities

## 🛠️ Troubleshooting

### Common Issues

1. **Missing API Key**: Ensure `ANTHROPIC_API_KEY` is set in `.env`
2. **No Transcript Files**: Add transcript files to `data/transcripts/`
3. **Permission Errors**: Check file permissions for output directory
4. **API Rate Limits**: The application includes retry logic with exponential backoff
5. **Word Document Creation**: Ensure `python-docx` is installed for Word document generation

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
DEBUG -   📁 Directory: output
DEBUG - Total items in directory: 3
DEBUG - Found 1 md files:
DEBUG -   - call_1_transcript.md
DEBUG - Found 1 txt files:
DEBUG -   - call_2_transcript.txt
```

## 🧪 Testing Setup

Run the test setup script to verify your environment:

```bash
python test_setup.py
```

This will check:
- ✅ Python version compatibility
- ✅ All required dependencies
- ✅ Environment variables
- ✅ Configuration files
- ✅ Directory structure
- ✅ Anthropic API connection

## 📈 Business Value

- **Professional Deliverables**: Sales teams can share professionally formatted analysis documents
- **Comprehensive Analysis**: Multi-level analysis from individual calls to engagement-level insights
- **Evidence-Based**: Clear citations and context from actual call transcripts
- **Actionable Insights**: Structured recommendations and next steps
- **Scalable Solution**: Easy to extend for additional document types or formatting needs
- **Engagement Management**: Process entire customer engagements with custom directories

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

[Add your license information here] 