#!/usr/bin/env python3
"""
Semgrep POV Assistant - Main Application

This is the main entry point for the Semgrep POV Assistant application.
It processes call transcripts and generates analysis reports.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.claude_client import ClaudeClient
from src.transcript_processor import TranscriptProcessor
from src.local_file_client import LocalFileClient
from src.utils.logger import setup_logger, log_startup_info, log_shutdown_info, log_info, log_debug, log_warning, log_error
from src.utils.file_utils import FileUtils

def load_config() -> Dict[str, Any]:
    """Load configuration from config file."""
    try:
        import yaml
        config_file = Path('config/config.yaml')
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            log_debug("Configuration loaded successfully")
            return config
        else:
            log_warning("Config file not found, using default configuration")
            return {}
            
    except Exception as e:
        log_error(f"Failed to load configuration: {e}")
        return {}

def check_environment() -> bool:
    """Check if required environment variables are set."""
    required_vars = ['ANTHROPIC_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        log_error(f"Missing required environment variables: {', '.join(missing_vars)}")
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file or environment.")
        return False
    
    return True

def setup_directories(config: Dict[str, Any]) -> None:
    """Create necessary directories if they don't exist."""
    paths = config.get('paths', {})
    
    directories = [
        paths.get('transcripts_dir', 'data/transcripts'),
        paths.get('output_dir', 'data/output'),
        paths.get('logs_dir', 'logs')
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        log_debug(f"Created directory: {directory}")

def find_transcript_files(config: Dict[str, Any]) -> List[Path]:
    """Find all supported transcript files."""
    transcripts_dir = Path(config.get('paths', {}).get('transcripts_dir', 'data/transcripts'))
    
    # Handle tilde expansion for home directory
    if str(transcripts_dir).startswith('~'):
        transcripts_dir = transcripts_dir.expanduser()
        log_debug(f"Expanded tilde path: {transcripts_dir}")
    
    # Get absolute path and log it
    try:
        absolute_transcripts_dir = transcripts_dir.resolve()
        log_debug(f"Transcripts directory (absolute path): {absolute_transcripts_dir}")
    except Exception as e:
        log_debug(f"Could not resolve absolute path for {transcripts_dir}: {e}")
        absolute_transcripts_dir = transcripts_dir
    
    if not transcripts_dir.exists():
        log_warning(f"Transcripts directory not found: {transcripts_dir}")
        log_debug(f"Directory does not exist: {absolute_transcripts_dir}")
        return []
    
    # Log directory contents
    try:
        all_files = list(transcripts_dir.iterdir())
        log_debug(f"Directory contents of {absolute_transcripts_dir}:")
        for item in all_files:
            if item.is_file():
                log_debug(f"  📄 File: {item.name} ({item.stat().st_size} bytes)")
            elif item.is_dir():
                log_debug(f"  📁 Directory: {item.name}")
        log_debug(f"Total items in directory: {len(all_files)}")
    except Exception as e:
        log_debug(f"Could not read directory contents: {e}")
    
    supported_formats = config.get('text_processing', {}).get('supported_formats', ['txt', 'docx', 'pdf', 'md'])
    transcript_files = []
    
    for format in supported_formats:
        found_files = list(transcripts_dir.glob(f"*.{format}"))
        if found_files:
            log_debug(f"Found {len(found_files)} {format} files:")
            for file in found_files:
                log_debug(f"  - {file.name}")
        transcript_files.extend(found_files)
    
    log_info(f"Found {len(transcript_files)} supported transcript files in {transcripts_dir}")
    return transcript_files

def process_transcripts(transcript_files: List[Path], config: Dict[str, Any], use_google_docs: bool = True) -> Dict[str, Any]:
    """Process all transcript files."""
    if not transcript_files:
        log_warning("No transcript files found to process")
        return {
            'total_files': 0,
            'successful_files': 0,
            'failed_files': 0,
            'transcripts': [],
            'summary': {},
            'call_classifications': {}
        }
    
    log_info(f"Found {len(transcript_files)} transcript files")
    log_info("Starting transcript processing")
    
    # Initialize Claude client
    claude_client = ClaudeClient(config=config)
    log_info("Claude client initialized successfully")
    
    # Initialize transcript processor
    transcript_processor = TranscriptProcessor(claude_client, config=config)
    log_info("Transcript processor initialized successfully")
    
    # Initialize file output client
    if use_google_docs:
        try:
            file_client = LocalFileClient(config=config)
            log_info("Local file client initialized successfully")
        except Exception as e:
            log_error(f"Failed to initialize local file client: {e}")
            return {
                'error': f"Failed to initialize file client: {e}",
                'total_files': len(transcript_files),
                'successful_files': 0,
                'failed_files': len(transcript_files)
            }
    else:
        file_client = None
        log_info("Skipping file creation (--no-google-docs flag)")
    
    # Step 1: Classify all calls
    log_info("Step 1: Classifying call types...")
    call_classifications = {}
    for transcript_file in transcript_files:
        try:
            # Read transcript content for classification
            file_utils = FileUtils()
            transcript_content = file_utils.read_text_file(transcript_file)
            
            if transcript_content:
                call_type = classify_call_type(transcript_content, claude_client)
                call_classifications[transcript_file.name] = call_type
                log_info(f"📋 {transcript_file.name}: {call_type}")
            else:
                call_classifications[transcript_file.name] = "Unknown"
                log_warning(f"Could not read transcript for classification: {transcript_file.name}")
        except Exception as e:
            call_classifications[transcript_file.name] = "Error"
            log_error(f"Error classifying {transcript_file.name}: {e}")
    
    # Display classification summary
    print("\n" + "=" * 60)
    print("📋 CALL CLASSIFICATION SUMMARY")
    print("=" * 60)
    for filename, call_type in call_classifications.items():
        print(f"   • {filename}: {call_type}")
    
    # Step 2: Process transcripts
    log_info("Step 2: Processing transcripts...")
    results = transcript_processor.process_multiple_transcripts(transcript_files)
    
    # Add classifications to results
    results['call_classifications'] = call_classifications
    
    # Step 3: POV Win/Loss Analysis
    if results.get('transcripts') and len(results['transcripts']) > 0:
        log_info("Step 3: Analyzing POV Win/Loss Probability...")
        pov_analysis = analyze_pov_win_probability(results['transcripts'], call_classifications, claude_client)
        results['pov_analysis'] = pov_analysis
        
        # Display POV analysis summary
        print("\n" + "=" * 60)
        print("🎯 POV WIN/LOSS ANALYSIS")
        print("=" * 60)
        
        if pov_analysis and 'error' not in pov_analysis:
            print(f"📊 Win Probability: {pov_analysis.get('win_probability', 0)}%")
            print(f"💡 Reasoning: {pov_analysis.get('probability_reasoning', 'No reasoning provided')}")
            
            # Key positive factors
            positive_factors = pov_analysis.get('key_positive_factors', [])
            if positive_factors:
                print(f"\n✅ Key Positive Factors:")
                for factor in positive_factors:
                    print(f"   • {factor}")
            
            # Key risks
            risks = pov_analysis.get('key_risks', [])
            if risks:
                print(f"\n⚠️  Key Risks:")
                for risk in risks:
                    print(f"   • {risk.get('risk', 'Unknown risk')} (Severity: {risk.get('severity', 'Unknown')})")
                    print(f"     Time Open: {risk.get('time_open', 'Unknown')}")
                    print(f"     Mitigation: {risk.get('mitigation', 'No mitigation provided')}")
            
            # Technical win strategy
            tech_strategy = pov_analysis.get('technical_win_strategy', {})
            if tech_strategy:
                print(f"\n🔧 Technical Win Strategy:")
                
                unresolved_questions = tech_strategy.get('unresolved_technical_questions', [])
                if unresolved_questions:
                    print(f"   📝 Unresolved Technical Questions:")
                    for question in unresolved_questions:
                        print(f"     • {question}")
                
                recommended_demos = tech_strategy.get('recommended_demonstrations', [])
                if recommended_demos:
                    print(f"   🎯 Recommended Demonstrations:")
                    for demo in recommended_demos:
                        print(f"     • {demo}")
                
                competitive_advantages = tech_strategy.get('competitive_advantages', [])
                if competitive_advantages:
                    print(f"   🏆 Competitive Advantages:")
                    for advantage in competitive_advantages:
                        print(f"     • {advantage}")
            
            # Next steps
            next_steps = pov_analysis.get('next_steps', [])
            if next_steps:
                print(f"\n📋 Recommended Next Steps:")
                for step in next_steps:
                    print(f"   • {step}")
            
            # Key transcript snippets
            snippets = pov_analysis.get('key_transcript_snippets', [])
            if snippets:
                print(f"\n💬 Key Transcript Snippets:")
                for snippet in snippets:
                    print(f"   📄 {snippet.get('call', 'Unknown call')}")
                    print(f"     Context: {snippet.get('context', 'No context')}")
                    print(f"     Quote: \"{snippet.get('quote', 'No quote')}\"")
                    print(f"     Significance: {snippet.get('significance', 'No significance provided')}")
        else:
            print(f"❌ POV Analysis Error: {pov_analysis.get('error', 'Unknown error')}")
            print("📝 A fallback POV analysis file will be created with basic information.")
    else:
        log_warning("No transcript results available for POV analysis")
    
    # Step 4: Technical Deployment Details Analysis
    if results.get('transcripts') and len(results['transcripts']) > 0:
        log_info("Step 4: Analyzing Technical Deployment Details...")
        deployment_analysis = analyze_technical_deployment_details(results['transcripts'], call_classifications, claude_client)
        results['deployment_analysis'] = deployment_analysis
        
        # Display technical deployment analysis summary
        print("\n" + "=" * 60)
        print("🔧 TECHNICAL DEPLOYMENT ANALYSIS")
        print("=" * 60)
        
        if deployment_analysis and 'error' not in deployment_analysis:
            # SCM Platform
            scm = deployment_analysis.get('scm_platform', {})
            if scm:
                print(f"📁 SCM Platform: {scm.get('platform', 'Unknown')}")
                print(f"   Deployment Type: {scm.get('deployment_type', 'Unknown')}")
                print(f"   Details: {scm.get('details', 'No details provided')}")
            
            # CI Pipelines
            ci = deployment_analysis.get('ci_pipelines', {})
            if ci:
                print(f"\n🔄 CI Pipelines:")
                print(f"   Primary CI: {ci.get('primary_ci', 'Unknown')}")
                additional_ci = ci.get('additional_ci', [])
                if additional_ci:
                    print(f"   Additional CI: {', '.join(additional_ci)}")
                print(f"   Details: {ci.get('details', 'No details provided')}")
            
            # Programming Languages
            languages = deployment_analysis.get('programming_languages', {})
            if languages:
                print(f"\n💻 Programming Languages:")
                primary_langs = languages.get('primary_languages', [])
                if primary_langs:
                    print(f"   Primary Languages: {', '.join(primary_langs)}")
                poc_langs = languages.get('poc_focus_languages', [])
                if poc_langs:
                    print(f"   POC Focus Languages: {', '.join(poc_langs)}")
                print(f"   Details: {languages.get('details', 'No details provided')}")
            
            # Integrations
            integrations = deployment_analysis.get('integrations', {})
            if integrations:
                print(f"\n🔗 Integrations:")
                interested = integrations.get('interested_integrations', [])
                if interested:
                    print(f"   Interested In: {', '.join(interested)}")
                current = integrations.get('current_integrations', [])
                if current:
                    print(f"   Current: {', '.join(current)}")
                print(f"   Details: {integrations.get('details', 'No details provided')}")
            
            # Supply Chain Security
            sca = deployment_analysis.get('supply_chain_security', {})
            if sca:
                print(f"\n📦 Supply Chain Security:")
                sca_langs = sca.get('languages_tested', [])
                if sca_langs:
                    print(f"   Languages Tested: {', '.join(sca_langs)}")
                package_mgrs = sca.get('package_managers', [])
                if package_mgrs:
                    print(f"   Package Managers: {', '.join(package_mgrs)}")
                print(f"   Details: {sca.get('details', 'No details provided')}")
            
            # Current Security Tools
            security_tools = deployment_analysis.get('current_security_tools', {})
            if security_tools:
                print(f"\n🛡️  Current Security Tools:")
                print(f"   SAST: {security_tools.get('sast', 'Unknown')}")
                print(f"   DAST: {security_tools.get('dast', 'Unknown')}")
                print(f"   SCA: {security_tools.get('sca', 'Unknown')}")
                print(f"   Secrets Detection: {security_tools.get('secrets_detection', 'Unknown')}")
                print(f"   ASPM: {security_tools.get('aspm', 'Unknown')}")
                print(f"   Details: {security_tools.get('details', 'No details provided')}")
            
            # IDE Environment
            ide = deployment_analysis.get('ide_environment', {})
            if ide:
                print(f"\n💻 IDE Environment:")
                print(f"   Primary IDE: {ide.get('primary_ide', 'Unknown')}")
                additional_tools = ide.get('additional_tools', [])
                if additional_tools:
                    print(f"   Additional Tools: {', '.join(additional_tools)}")
                print(f"   Details: {ide.get('details', 'No details provided')}")
            
            # Additional Technical Details
            additional_details = deployment_analysis.get('additional_technical_details', [])
            if additional_details:
                print(f"\n📋 Additional Technical Details:")
                for detail in additional_details:
                    print(f"   • {detail}")
            
            # Deployment Complexity
            complexity = deployment_analysis.get('deployment_complexity', 'Unknown')
            print(f"\n📊 Deployment Complexity: {complexity}")
            
            # Migration Considerations
            migration = deployment_analysis.get('migration_considerations', [])
            if migration:
                print(f"\n🔄 Migration Considerations:")
                for consideration in migration:
                    print(f"   • {consideration}")
            
            # Technical Risks
            risks = deployment_analysis.get('technical_risks', [])
            if risks:
                print(f"\n⚠️  Technical Risks:")
                for risk in risks:
                    print(f"   • {risk}")
            
            # Recommendations
            recommendations = deployment_analysis.get('recommendations', [])
            if recommendations:
                print(f"\n💡 Technical Recommendations:")
                for rec in recommendations:
                    print(f"   • {rec}")
        else:
            print(f"❌ Technical Deployment Analysis Error: {deployment_analysis.get('error', 'Unknown error')}")
            print("📝 A fallback technical deployment analysis file will be created with basic information.")
    else:
        log_warning("No transcript results available for technical deployment analysis")
    
    # Create output files if requested
    if use_google_docs and file_client and results.get('transcripts'):
        log_info("Starting local file creation")
        
        created_files = []
        for transcript_result in results['transcripts']:
            if 'error' not in transcript_result:
                try:
                    # Create call summary file
                    summary_file = file_client.create_call_summary_file(transcript_result)
                    created_files.append(summary_file)
                    
                    # Create JSON analysis file
                    json_file = file_client.create_json_analysis_file(transcript_result)
                    created_files.append(json_file)
                    
                    # Create action items file
                    action_items = transcript_result.get('action_items', [])
                    if action_items:
                        action_file = file_client.create_action_items_file(action_items)
                        created_files.append(action_file)
                    
                    # Create sentiment analysis file
                    sentiment_data = transcript_result.get('sentiment_analysis', {})
                    if sentiment_data:
                        sentiment_file = file_client.create_sentiment_analysis_file(sentiment_data)
                        created_files.append(sentiment_file)
                    
                except Exception as e:
                    log_error(f"Failed to create files for transcript: {e}")
        
        # Create POV analysis file if available
        pov_analysis = results.get('pov_analysis', {})
        if pov_analysis:
            try:
                pov_file = file_client.create_pov_analysis_file(pov_analysis)
                created_files.append(pov_file)
                log_info(f"Created POV analysis file: {pov_file}")
            except Exception as e:
                log_error(f"Failed to create POV analysis file: {e}")
        else:
            # Create a fallback POV analysis file if no analysis was generated
            try:
                fallback_pov_data = {
                    'win_probability': 50,
                    'probability_reasoning': 'POV analysis was not generated due to processing issues',
                    'key_positive_factors': ['Analysis data available'],
                    'key_risks': [{'risk': 'POV analysis failed', 'severity': 'medium', 'time_open': 'Unknown', 'mitigation': 'Review transcript processing'}],
                    'technical_win_strategy': {
                        'unresolved_technical_questions': ['Need to review transcript processing'],
                        'recommended_demonstrations': ['Standard product capabilities'],
                        'competitive_advantages': ['Need more analysis data']
                    },
                    'next_steps': ['Review transcript processing and re-run analysis'],
                    'key_transcript_snippets': [],
                    'fallback_analysis': True
                }
                pov_file = file_client.create_pov_analysis_file(fallback_pov_data)
                created_files.append(pov_file)
                log_info(f"Created fallback POV analysis file: {pov_file}")
            except Exception as e:
                log_error(f"Failed to create fallback POV analysis file: {e}")
        
        # Create technical deployment analysis file if available
        deployment_analysis = results.get('deployment_analysis', {})
        if deployment_analysis:
            try:
                deployment_file = file_client.create_technical_deployment_analysis_file(deployment_analysis)
                created_files.append(deployment_file)
                log_info(f"Created technical deployment analysis file: {deployment_file}")
            except Exception as e:
                log_error(f"Failed to create technical deployment analysis file: {e}")
        else:
            # Create a fallback technical deployment analysis file if no analysis was generated
            try:
                fallback_deployment_data = {
                    'scm_platform': {
                        'platform': 'Unknown',
                        'deployment_type': 'Unknown',
                        'details': 'Technical deployment analysis was not generated due to processing issues',
                        'evidence': 'Fallback analysis based on processing issues'
                    },
                    'ci_pipelines': {
                        'primary_ci': 'Unknown',
                        'additional_ci': [],
                        'details': 'Technical deployment analysis was not generated due to processing issues',
                        'evidence': 'Fallback analysis based on processing issues'
                    },
                    'programming_languages': {
                        'primary_languages': [],
                        'poc_focus_languages': [],
                        'details': 'Technical deployment analysis was not generated due to processing issues',
                        'evidence': 'Fallback analysis based on processing issues'
                    },
                    'integrations': {
                        'interested_integrations': [],
                        'current_integrations': [],
                        'details': 'Technical deployment analysis was not generated due to processing issues',
                        'evidence': 'Fallback analysis based on processing issues'
                    },
                    'supply_chain_security': {
                        'languages_tested': [],
                        'package_managers': [],
                        'details': 'Technical deployment analysis was not generated due to processing issues',
                        'evidence': 'Fallback analysis based on processing issues'
                    },
                    'current_security_tools': {
                        'sast': 'Unknown',
                        'dast': 'Unknown',
                        'sca': 'Unknown',
                        'secrets_detection': 'Unknown',
                        'aspm': 'Unknown',
                        'details': 'Technical deployment analysis was not generated due to processing issues',
                        'evidence': 'Fallback analysis based on processing issues'
                    },
                    'ide_environment': {
                        'primary_ide': 'Unknown',
                        'additional_tools': [],
                        'details': 'Technical deployment analysis was not generated due to processing issues',
                        'evidence': 'Fallback analysis based on processing issues'
                    },
                    'additional_technical_details': [],
                    'deployment_complexity': 'Unknown',
                    'migration_considerations': [],
                    'technical_risks': [],
                    'recommendations': [],
                    'fallback_analysis': True,
                    'analysis_method': 'fallback'
                }
                deployment_file = file_client.create_technical_deployment_analysis_file(fallback_deployment_data)
                created_files.append(deployment_file)
                log_info(f"Created fallback technical deployment analysis file: {deployment_file}")
            except Exception as e:
                log_error(f"Failed to create fallback technical deployment analysis file: {e}")
        
        results['created_files'] = created_files
        log_info(f"Created {len(created_files)} local files")
    
    return results

def print_summary(results: Dict[str, Any], use_google_docs: bool = True) -> None:
    """Print processing summary."""
    print("\n" + "=" * 60)
    print("SEMGREP POV ASSISTANT - PROCESSING SUMMARY")
    print("=" * 60)
    
    # Call classification summary
    call_classifications = results.get('call_classifications', {})
    if call_classifications:
        print(f"\n📋 CALL CLASSIFICATIONS:")
        discovery_count = sum(1 for call_type in call_classifications.values() if call_type == "Discovery Call")
        demo_count = sum(1 for call_type in call_classifications.values() if call_type == "Demo Call")
        pov_count = sum(1 for call_type in call_classifications.values() if call_type == "POV Check-in")
        other_count = len(call_classifications) - discovery_count - demo_count - pov_count
        
        print(f"   • Discovery Calls: {discovery_count}")
        print(f"   • Demo Calls: {demo_count}")
        print(f"   • POV Check-ins: {pov_count}")
        if other_count > 0:
            print(f"   • Other/Unknown: {other_count}")
    
    # Transcript processing summary
    total_files = results.get('total_files', 0)
    successful_files = results.get('successful_files', 0)
    failed_files = results.get('failed_files', 0)
    
    print(f"\n📊 TRANSCRIPT PROCESSING:")
    print(f"   • Total files processed: {total_files}")
    print(f"   • Successful: {successful_files}")
    print(f"   • Failed: {failed_files}")
    
    # Action items summary
    if results.get('transcripts'):
        total_action_items = 0
        high_priority = 0
        medium_priority = 0
        low_priority = 0
        
        for transcript in results['transcripts']:
            if 'error' not in transcript:
                action_items = transcript.get('action_items', [])
                total_action_items += len(action_items)
                
                for item in action_items:
                    priority = item.get('priority', 'Medium').lower()
                    if priority == 'high':
                        high_priority += 1
                    elif priority == 'medium':
                        medium_priority += 1
                    elif priority == 'low':
                        low_priority += 1
        
        print(f"   • Total action items extracted: {total_action_items}")
        print(f"   • High priority items: {high_priority}")
        print(f"   • Medium priority items: {medium_priority}")
        print(f"   • Low priority items: {low_priority}")
    
    # File creation summary
    if use_google_docs:
        created_files = results.get('created_files', [])
        print(f"\n📄 LOCAL FILE CREATION:")
        print(f"   • Files created: {len(created_files)}")
        if created_files:
            print(f"   • Output directory: data/output")
            for file_path in created_files:
                print(f"     - {file_path}")
    else:
        print(f"\n📄 LOCAL FILE CREATION:")
        print(f"   • Files created: 0 (disabled)")
    
    # Technical deployment analysis summary
    deployment_analysis = results.get('deployment_analysis', {})
    if deployment_analysis and 'error' not in deployment_analysis:
        print(f"\n🔧 TECHNICAL DEPLOYMENT SUMMARY:")
        scm = deployment_analysis.get('scm_platform', {})
        if scm:
            print(f"   • SCM Platform: {scm.get('platform', 'Unknown')}")
        ci = deployment_analysis.get('ci_pipelines', {})
        if ci:
            print(f"   • Primary CI: {ci.get('primary_ci', 'Unknown')}")
        languages = deployment_analysis.get('programming_languages', {})
        if languages:
            primary_langs = languages.get('primary_languages', [])
            if primary_langs:
                print(f"   • Primary Languages: {', '.join(primary_langs)}")
        complexity = deployment_analysis.get('deployment_complexity', 'Unknown')
        print(f"   • Deployment Complexity: {complexity}")
    else:
        print(f"\n🔧 TECHNICAL DEPLOYMENT SUMMARY:")
        print(f"   • Analysis: Not available")
    
    print("\n" + "=" * 60)

def classify_call_type(transcript_content: str, claude_client) -> str:
    """Classify the call type based on transcript content."""
    try:
        # First, try pattern matching on the first few lines
        first_lines = transcript_content[:500].lower()
        
        # Pattern matching for quick classification
        if any(keyword in first_lines for keyword in ['demo', 'demonstration', 'product demo', 'semgrep demo']):
            log_debug("Pattern match: Classified as Demo Call")
            return "Demo Call"
        elif any(keyword in first_lines for keyword in ['pov sync', 'pov check', 'pov meeting', 'proof of value']):
            log_debug("Pattern match: Classified as POV Check-in")
            return "POV Check-in"
        elif any(keyword in first_lines for keyword in ['discovery', 'initial', 'first call', 'introductory']):
            log_debug("Pattern match: Classified as Discovery Call")
            return "Discovery Call"
        
        # If pattern matching doesn't work, use Claude to classify
        log_debug("Pattern matching inconclusive, using Claude for classification")
        
        classification_prompt = f"""You are an expert at classifying sales calls. Based on the following call transcript, classify this call into one of these three categories:

1. "Discovery Call" - Initial exploratory call to understand customer needs and pain points
2. "Demo Call" - Product demonstration showing features and capabilities
3. "POV Check-in" - Follow-up call during or after proof of value engagement

Call transcript (first 1000 characters):
{transcript_content[:1000]}

Please respond with ONLY the classification: "Discovery Call", "Demo Call", or "POV Check-in"."""

        response = claude_client.analyze_call_transcript(transcript_content[:1000], classification_prompt)
        
        if response.get('success'):
            classification = response.get('analysis', '').strip()
            # Clean up the response to get just the classification
            if 'discovery call' in classification.lower():
                return "Discovery Call"
            elif 'demo call' in classification.lower():
                return "Demo Call"
            elif 'pov check-in' in classification.lower() or 'pov check' in classification.lower():
                return "POV Check-in"
            else:
                # Default classification based on content analysis
                if any(word in transcript_content.lower() for word in ['demo', 'demonstration', 'show', 'feature']):
                    return "Demo Call"
                elif any(word in transcript_content.lower() for word in ['pov', 'proof of value', 'check-in', 'sync']):
                    return "POV Check-in"
                else:
                    return "Discovery Call"
        else:
            log_warning("Failed to classify call with Claude, using default")
            return "Discovery Call"
            
    except Exception as e:
        log_error(f"Error classifying call type: {e}")
        return "Discovery Call"

def analyze_pov_win_probability(transcript_results: List[Dict], call_classifications: Dict[str, str], claude_client) -> Dict[str, Any]:
    """Analyze POV win probability across all call transcripts in an engagement."""
    
    log_info("Starting POV Win/Loss Probability Analysis...")
    
    # Step 1: Extract key insights from each transcript
    engagement_insights = []
    for result in transcript_results:
        if 'error' not in result:
            insights = {
                'filename': result.get('filename', 'Unknown'),
                'call_type': call_classifications.get(result.get('filename', ''), 'Unknown'),
                'sentiment': result.get('sentiment_analysis', {}).get('overall_sentiment', 'Neutral'),
                'engagement_level': result.get('sentiment_analysis', {}).get('engagement_level', 'Medium'),
                'action_items': result.get('action_items', []),
                'key_discussion_points': result.get('analysis', {}).get('key_discussion_points', []),
                'business_context': result.get('analysis', {}).get('business_context', {}),
                'next_steps': result.get('analysis', {}).get('next_steps', []),
                'raw_analysis': result.get('analysis', {}).get('raw_analysis', '')
            }
            engagement_insights.append(insights)
    
    if not engagement_insights:
        log_warning("No valid transcript insights found for POV analysis")
        return {
            'error': 'No valid transcript data available for POV analysis',
            'win_probability': 0,
            'reasoning': 'Insufficient data for analysis'
        }
    
    # Step 2: Create comprehensive engagement summary for Claude analysis
    engagement_summary = _create_engagement_summary(engagement_insights)
    
    # Step 3: Generate POV analysis using Claude
    pov_analysis = _generate_pov_analysis(engagement_summary, claude_client)
    
    return pov_analysis

def _create_engagement_summary(engagement_insights: List[Dict]) -> str:
    """Create a comprehensive summary of all engagement insights."""
    
    summary_parts = []
    
    # Call Overview
    call_types = [insight['call_type'] for insight in engagement_insights]
    call_type_counts = {call_type: call_types.count(call_type) for call_type in set(call_types)}
    
    summary_parts.append("## ENGAGEMENT OVERVIEW")
    summary_parts.append(f"Total Calls: {len(engagement_insights)}")
    summary_parts.append("Call Types:")
    for call_type, count in call_type_counts.items():
        summary_parts.append(f"  - {call_type}: {count}")
    
    # Sentiment Analysis
    sentiments = [insight['sentiment'] for insight in engagement_insights]
    sentiment_counts = {sentiment: sentiments.count(sentiment) for sentiment in set(sentiments)}
    
    summary_parts.append("\n## SENTIMENT ANALYSIS")
    for sentiment, count in sentiment_counts.items():
        summary_parts.append(f"  - {sentiment}: {count} calls")
    
    # Engagement Levels
    engagement_levels = [insight['engagement_level'] for insight in engagement_insights]
    engagement_counts = {level: engagement_levels.count(level) for level in set(engagement_levels)}
    
    summary_parts.append("\n## ENGAGEMENT LEVELS")
    for level, count in engagement_counts.items():
        summary_parts.append(f"  - {level}: {count} calls")
    
    # Key Insights from Each Call
    summary_parts.append("\n## DETAILED CALL INSIGHTS")
    for i, insight in enumerate(engagement_insights, 1):
        summary_parts.append(f"\n### Call {i}: {insight['filename']}")
        summary_parts.append(f"Type: {insight['call_type']}")
        summary_parts.append(f"Sentiment: {insight['sentiment']}")
        summary_parts.append(f"Engagement: {insight['engagement_level']}")
        
        # Key discussion points
        if insight['key_discussion_points']:
            summary_parts.append("Key Discussion Points:")
            for point in insight['key_discussion_points'][:5]:  # Top 5 points
                summary_parts.append(f"  - {point}")
        
        # Action items
        if insight['action_items']:
            summary_parts.append("Action Items:")
            for item in insight['action_items'][:5]:  # Top 5 items
                summary_parts.append(f"  - {item.get('action', 'N/A')} (Owner: {item.get('owner', 'N/A')}, Priority: {item.get('priority', 'N/A')})")
        
        # Business context
        if insight['business_context']:
            summary_parts.append("Business Context:")
            for key, value in insight['business_context'].items():
                if isinstance(value, list):
                    summary_parts.append(f"  - {key}: {', '.join(value[:5])}")  # Top 5 items
                else:
                    summary_parts.append(f"  - {key}: {value}")
        
        # Raw analysis (first 500 characters)
        if insight['raw_analysis']:
            summary_parts.append("Key Insights:")
            raw_text = insight['raw_analysis'][:500] + "..." if len(insight['raw_analysis']) > 500 else insight['raw_analysis']
            summary_parts.append(f"  {raw_text}")
    
    # Overall engagement patterns
    summary_parts.append("\n## ENGAGEMENT PATTERNS")
    
    # Most common action items
    all_action_items = []
    for insight in engagement_insights:
        all_action_items.extend(insight['action_items'])
    
    if all_action_items:
        summary_parts.append("Most Common Action Items:")
        action_counts = {}
        for item in all_action_items:
            action = item.get('action', 'Unknown')
            action_counts[action] = action_counts.get(action, 0) + 1
        
        for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            summary_parts.append(f"  - {action} (mentioned {count} times)")
    
    # Overall sentiment trend
    positive_calls = sum(1 for insight in engagement_insights if insight['sentiment'].lower() == 'positive')
    total_calls = len(engagement_insights)
    sentiment_percentage = (positive_calls / total_calls * 100) if total_calls > 0 else 0
    
    summary_parts.append(f"\nOverall Sentiment Trend: {positive_calls}/{total_calls} calls positive ({sentiment_percentage:.1f}%)")
    
    return "\n".join(summary_parts)

def _generate_pov_analysis(engagement_summary: str, claude_client) -> Dict[str, Any]:
    """Generate comprehensive POV analysis using Claude."""
    
    # Ensure we have enough content for analysis
    if len(engagement_summary) < 100:
        log_warning("Engagement summary too short for meaningful POV analysis")
        return {
            'win_probability': 50,
            'probability_reasoning': 'Insufficient data for detailed analysis',
            'key_positive_factors': ['Limited data available'],
            'key_risks': [{'risk': 'Insufficient data', 'severity': 'medium', 'time_open': 'Unknown', 'mitigation': 'Gather more call data'}],
            'technical_win_strategy': {
                'unresolved_technical_questions': ['Need more call data'],
                'recommended_demonstrations': ['Standard product demo'],
                'competitive_advantages': ['Need more data for analysis']
            },
            'next_steps': ['Gather more call transcripts for analysis'],
            'key_transcript_snippets': []
        }
    
    pov_analysis_prompt = f"""You are an expert sales strategist analyzing a Proof of Value (POV) engagement. Based on the following engagement data, provide a comprehensive POV Win/Loss analysis.

ENGAGEMENT DATA:
{engagement_summary}

Please provide a detailed analysis in the following JSON format. IMPORTANT: Respond with ONLY the JSON object, no additional text, explanations, or markdown formatting:

{{
    "win_probability": <percentage 0-100>,
    "probability_reasoning": "<detailed explanation of the probability score>",
    "key_positive_factors": [
        "<factor 1>",
        "<factor 2>",
        "<factor 3>"
    ],
    "key_risks": [
        {{
            "risk": "<risk description>",
            "severity": "<high/medium/low>",
            "time_open": "<how long has this been an issue>",
            "mitigation": "<recommended mitigation steps>"
        }}
    ],
    "technical_win_strategy": {{
        "unresolved_technical_questions": [
            "<question 1>",
            "<question 2>"
        ],
        "recommended_demonstrations": [
            "<use case 1>",
            "<use case 2>"
        ],
        "competitive_advantages": [
            "<advantage 1>",
            "<advantage 2>"
        ]
    }},
    "next_steps": [
        "<action 1>",
        "<action 2>",
        "<action 3>"
    ],
    "key_transcript_snippets": [
        {{
            "call": "<call filename>",
            "context": "<what was happening>",
            "quote": "<relevant quote from transcript>",
            "significance": "<why this quote is important>"
        }}
    ]
}}

Focus on:
1. Concrete evidence from the transcripts
2. Specific risks with clear timelines
3. Actionable next steps
4. Relevant quotes that support your analysis

CRITICAL: Respond with ONLY the JSON object above, no markdown formatting, no code blocks, no additional text."""

    try:
        response = claude_client.analyze_pov_win_probability(engagement_summary, pov_analysis_prompt)
        
        if response.get('success'):
            analysis_text = response.get('analysis', '')
            log_debug(f"Raw Claude response for POV analysis: {analysis_text[:500]}...")
            
            # Try to extract JSON from the response
            try:
                # First, try to find JSON wrapped in markdown code blocks
                import re
                
                # Look for JSON in markdown code blocks
                json_code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', analysis_text, re.DOTALL)
                if json_code_block_match:
                    json_str = json_code_block_match.group(1)
                    log_debug("Found JSON in markdown code block")
                else:
                    # Look for JSON without markdown wrapping - improved pattern
                    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', analysis_text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        log_debug("Found JSON without markdown wrapping")
                    else:
                        # Try to find the largest JSON-like structure with better pattern
                        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', analysis_text, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(0)
                            log_debug("Found JSON using improved pattern")
                        else:
                            # Last resort: find any JSON-like structure
                            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
                            if json_match:
                                json_str = json_match.group(0)
                                log_debug("Found JSON using fallback pattern")
                            else:
                                raise ValueError("No JSON structure found in response")
                
                # Clean up the JSON string
                json_str = json_str.strip()
                
                # Remove any leading/trailing text that might be before/after the JSON
                if json_str.startswith('```'):
                    json_str = json_str[3:]
                if json_str.endswith('```'):
                    json_str = json_str[:-3]
                
                # Additional cleanup for common issues
                json_str = json_str.replace('\n    ', '\n')  # Fix indentation issues
                json_str = json_str.replace('\n  ', '\n')    # Fix double spaces
                json_str = json_str.replace('\n    "', '\n"')  # Fix specific indentation issue
                json_str = json_str.replace('\n  "', '\n"')    # Fix double space before quotes
                
                log_debug(f"Cleaned JSON string (first 200 chars): {json_str[:200]}...")
                log_debug(f"JSON string length: {len(json_str)}")
                
                # Parse the JSON
                import json
                pov_analysis = json.loads(json_str)
                
                # Validate the structure
                required_keys = ['win_probability', 'probability_reasoning', 'key_positive_factors', 'key_risks', 'technical_win_strategy', 'next_steps']
                missing_keys = [key for key in required_keys if key not in pov_analysis]
                
                if missing_keys:
                    log_warning(f"Missing required keys in POV analysis: {missing_keys}")
                    # Fill in missing keys with defaults
                    if 'win_probability' not in pov_analysis:
                        pov_analysis['win_probability'] = 50
                    if 'probability_reasoning' not in pov_analysis:
                        pov_analysis['probability_reasoning'] = 'Analysis incomplete'
                    if 'key_positive_factors' not in pov_analysis:
                        pov_analysis['key_positive_factors'] = []
                    if 'key_risks' not in pov_analysis:
                        pov_analysis['key_risks'] = []
                    if 'technical_win_strategy' not in pov_analysis:
                        pov_analysis['technical_win_strategy'] = {
                            'unresolved_technical_questions': [],
                            'recommended_demonstrations': [],
                            'competitive_advantages': []
                        }
                    if 'next_steps' not in pov_analysis:
                        pov_analysis['next_steps'] = []
                    if 'key_transcript_snippets' not in pov_analysis:
                        pov_analysis['key_transcript_snippets'] = []
                
                log_info("Successfully generated POV analysis")
                return pov_analysis
                
            except json.JSONDecodeError as e:
                log_warning(f"Failed to parse JSON from Claude response: {e}")
                log_debug(f"JSON parsing error details: {e}")
                log_debug(f"Attempted to parse: {json_str[:200]}...")
                log_debug(f"Full JSON string: {json_str}")
                return _parse_pov_analysis_text(analysis_text)
            except Exception as e:
                log_warning(f"Error extracting JSON from Claude response: {e}")
                log_debug(f"Full analysis text: {analysis_text}")
                return _parse_pov_analysis_text(analysis_text)
        else:
            log_error("Failed to generate POV analysis with Claude")
            return _create_fallback_pov_analysis(engagement_summary)
            
    except Exception as e:
        log_error(f"Error generating POV analysis: {e}")
        return _create_fallback_pov_analysis(engagement_summary)

def _create_fallback_pov_analysis(engagement_summary: str) -> Dict[str, Any]:
    """Create a fallback POV analysis when Claude analysis fails."""
    
    log_debug("Creating intelligent fallback POV analysis")
    
    # Analyze the engagement summary to provide better insights
    summary_lower = engagement_summary.lower()
    
    # Calculate win probability based on engagement indicators
    win_probability = 50  # Default neutral probability
    
    # Positive indicators
    positive_indicators = {
        'positive': 15,
        'high': 10,
        'demo': 5,
        'excellent': 20,
        'strong': 15,
        'good': 10,
        'favorable': 15,
        'promising': 10,
        'interested': 10,
        'engaged': 10,
        'love': 20,
        'fantastic': 20,
        'win': 15
    }
    
    # Negative indicators
    negative_indicators = {
        'negative': -15,
        'low': -10,
        'concern': -10,
        'issue': -10,
        'problem': -15,
        'risk': -10,
        'challenge': -5,
        'weak': -10,
        'poor': -15,
        'bad': -15
    }
    
    # Calculate score based on indicators
    for indicator, score in positive_indicators.items():
        if indicator in summary_lower:
            win_probability += score
            log_debug(f"Found positive indicator '{indicator}': +{score}")
    
    for indicator, score in negative_indicators.items():
        if indicator in summary_lower:
            win_probability -= score
            log_debug(f"Found negative indicator '{indicator}': {score}")
    
    # Clamp to 0-100 range
    win_probability = max(0, min(100, win_probability))
    
    # Generate reasoning based on engagement data
    reasoning_parts = []
    
    # Analyze call types
    if 'demo call' in summary_lower:
        reasoning_parts.append("Demo calls indicate active product evaluation")
    if 'discovery call' in summary_lower:
        reasoning_parts.append("Discovery calls show initial interest and exploration")
    if 'pov check-in' in summary_lower:
        reasoning_parts.append("POV check-ins suggest ongoing engagement")
    
    # Analyze sentiment
    positive_calls = summary_lower.count('positive')
    negative_calls = summary_lower.count('negative')
    if positive_calls > negative_calls:
        reasoning_parts.append(f"Overall positive sentiment ({positive_calls} positive indicators)")
    elif negative_calls > positive_calls:
        reasoning_parts.append(f"Some concerns identified ({negative_calls} negative indicators)")
    else:
        reasoning_parts.append("Mixed sentiment across calls")
    
    # Analyze engagement level
    if 'high' in summary_lower and 'engagement' in summary_lower:
        reasoning_parts.append("High engagement levels observed")
    elif 'low' in summary_lower and 'engagement' in summary_lower:
        reasoning_parts.append("Lower engagement levels noted")
    
    # Generate positive factors
    positive_factors = []
    if 'positive' in summary_lower:
        positive_factors.append("Positive sentiment across calls")
    if 'high' in summary_lower and 'engagement' in summary_lower:
        positive_factors.append("High customer engagement")
    if 'demo' in summary_lower:
        positive_factors.append("Product demonstrations conducted")
    if 'action' in summary_lower and 'item' in summary_lower:
        positive_factors.append("Clear action items identified")
    
    # Generate risks
    risks = []
    if 'negative' in summary_lower:
        risks.append({
            'risk': 'Negative sentiment in some calls',
            'severity': 'medium',
            'time_open': 'Recent',
            'mitigation': 'Address concerns in follow-up calls'
        })
    if 'low' in summary_lower and 'engagement' in summary_lower:
        risks.append({
            'risk': 'Low engagement levels',
            'severity': 'high',
            'time_open': 'Ongoing',
            'mitigation': 'Increase engagement through targeted outreach'
        })
    if 'concern' in summary_lower or 'issue' in summary_lower:
        risks.append({
            'risk': 'Customer concerns identified',
            'severity': 'medium',
            'time_open': 'Unknown',
            'mitigation': 'Address concerns proactively'
        })
    
    # Generate next steps
    next_steps = []
    if 'follow up' in summary_lower:
        next_steps.append("Schedule follow-up calls")
    if 'demo' in summary_lower:
        next_steps.append("Prepare additional product demonstrations")
    if 'action' in summary_lower and 'item' in summary_lower:
        next_steps.append("Track and complete action items")
    if 'pov' in summary_lower:
        next_steps.append("Continue POV engagement")
    
    # Ensure we have basic content
    if not positive_factors:
        positive_factors = ['Engagement data available for analysis']
    if not risks:
        risks = [{'risk': 'Limited detailed analysis data', 'severity': 'medium', 'time_open': 'Unknown', 'mitigation': 'Improve data collection and analysis'}]
    if not next_steps:
        next_steps = ['Continue engagement and gather more data']
    
    reasoning = f"Fallback analysis based on engagement patterns. {'. '.join(reasoning_parts)}. Probability: {win_probability}%"
    
    return {
        'win_probability': win_probability,
        'probability_reasoning': reasoning,
        'key_positive_factors': positive_factors,
        'key_risks': risks,
        'technical_win_strategy': {
            'unresolved_technical_questions': ['Need more detailed call data for technical analysis'],
            'recommended_demonstrations': ['Standard product capabilities based on engagement'],
            'competitive_advantages': ['Need more competitive analysis data']
        },
        'next_steps': next_steps,
        'key_transcript_snippets': [],
        'fallback_analysis': True,
        'analysis_method': 'intelligent_fallback'
    }

def _parse_pov_analysis_text(analysis_text: str) -> Dict[str, Any]:
    """Parse POV analysis from text response when JSON parsing fails."""
    
    log_debug("Attempting to parse POV analysis from text response")
    
    # Extract win probability
    import re
    
    # Look for win probability in various formats
    prob_patterns = [
        r'win_probability["\s]*:["\s]*(\d+)',
        r'probability["\s]*:["\s]*(\d+)',
        r'win["\s]*probability["\s]*:["\s]*(\d+)',
        r'(\d+)%["\s]*win',
        r'win["\s]*rate["\s]*:["\s]*(\d+)'
    ]
    
    win_probability = 50  # Default
    for pattern in prob_patterns:
        prob_match = re.search(pattern, analysis_text, re.IGNORECASE)
        if prob_match:
            win_probability = int(prob_match.group(1))
            log_debug(f"Extracted win probability: {win_probability}%")
            break
    
    # Extract reasoning
    reasoning_patterns = [
        r'probability_reasoning["\s]*:["\s]*"([^"]+)"',
        r'reasoning["\s]*:["\s]*"([^"]+)"',
        r'reason["\s]*:["\s]*"([^"]+)"',
        r'because["\s]*([^"]+)',
        r'due["\s]*to["\s]*([^"]+)'
    ]
    
    reasoning = "Analysis parsing failed"
    for pattern in reasoning_patterns:
        reasoning_match = re.search(pattern, analysis_text, re.IGNORECASE)
        if reasoning_match:
            reasoning = reasoning_match.group(1)
            log_debug(f"Extracted reasoning: {reasoning[:100]}...")
            break
    
    # Extract positive factors
    positive_factors = []
    positive_patterns = [
        r'positive_factors["\s]*:["\s]*\[([^\]]+)\]',
        r'positive["\s]*factors["\s]*:["\s]*\[([^\]]+)\]',
        r'strengths["\s]*:["\s]*\[([^\]]+)\]',
        r'advantages["\s]*:["\s]*\[([^\]]+)\]'
    ]
    
    for pattern in positive_patterns:
        factors_match = re.search(pattern, analysis_text, re.IGNORECASE)
        if factors_match:
            factors_str = factors_match.group(1)
            # Split by commas and clean up
            factors = [f.strip().strip('"') for f in factors_str.split(',')]
            positive_factors = [f for f in factors if f and len(f) > 3]
            log_debug(f"Extracted {len(positive_factors)} positive factors")
            break
    
    # Extract risks
    risks = []
    risk_patterns = [
        r'risks["\s]*:["\s]*\[([^\]]+)\]',
        r'key_risks["\s]*:["\s]*\[([^\]]+)\]',
        r'concerns["\s]*:["\s]*\[([^\]]+)\]',
        r'challenges["\s]*:["\s]*\[([^\]]+)\]'
    ]
    
    for pattern in risk_patterns:
        risks_match = re.search(pattern, analysis_text, re.IGNORECASE)
        if risks_match:
            risks_str = risks_match.group(1)
            # Split by commas and clean up
            risk_items = [r.strip().strip('"') for r in risks_str.split(',')]
            risks = [{'risk': r, 'severity': 'medium', 'time_open': 'Unknown', 'mitigation': 'Review and address'} 
                    for r in risk_items if r and len(r) > 3]
            log_debug(f"Extracted {len(risks)} risks")
            break
    
    # Extract next steps
    next_steps = []
    steps_patterns = [
        r'next_steps["\s]*:["\s]*\[([^\]]+)\]',
        r'next["\s]*steps["\s]*:["\s]*\[([^\]]+)\]',
        r'actions["\s]*:["\s]*\[([^\]]+)\]',
        r'recommendations["\s]*:["\s]*\[([^\]]+)\]'
    ]
    
    for pattern in steps_patterns:
        steps_match = re.search(pattern, analysis_text, re.IGNORECASE)
        if steps_match:
            steps_str = steps_match.group(1)
            # Split by commas and clean up
            steps = [s.strip().strip('"') for s in steps_str.split(',')]
            next_steps = [s for s in steps if s and len(s) > 3]
            log_debug(f"Extracted {len(next_steps)} next steps")
            break
    
    # If we couldn't extract structured data, try to find key phrases
    if not positive_factors and not risks and not next_steps:
        log_debug("No structured data found, extracting key phrases")
        
        # Look for positive indicators
        positive_indicators = ['positive', 'good', 'strong', 'high', 'excellent', 'favorable', 'promising']
        for indicator in positive_indicators:
            if indicator in analysis_text.lower():
                positive_factors.append(f"Engagement shows {indicator} indicators")
        
        # Look for risk indicators
        risk_indicators = ['risk', 'concern', 'challenge', 'issue', 'problem', 'weakness']
        for indicator in risk_indicators:
            if indicator in analysis_text.lower():
                risks.append({'risk': f"Potential {indicator} identified", 'severity': 'medium', 'time_open': 'Unknown', 'mitigation': 'Address proactively'})
        
        # Look for action indicators
        action_indicators = ['follow up', 'schedule', 'prepare', 'provide', 'send', 'meet']
        for indicator in action_indicators:
            if indicator in analysis_text.lower():
                next_steps.append(f"Need to {indicator}")
    
    # Ensure we have at least some basic content
    if not positive_factors:
        positive_factors = ['Engagement data available for analysis']
    if not risks:
        risks = [{'risk': 'Limited structured analysis data', 'severity': 'medium', 'time_open': 'Unknown', 'mitigation': 'Improve data extraction'}]
    if not next_steps:
        next_steps = ['Review and improve analysis process']
    
    return {
        'win_probability': win_probability,
        'probability_reasoning': reasoning,
        'key_positive_factors': positive_factors,
        'key_risks': risks,
        'technical_win_strategy': {
            'unresolved_technical_questions': ['Need more detailed call data'],
            'recommended_demonstrations': ['Standard product capabilities'],
            'competitive_advantages': ['Need more competitive analysis data']
        },
        'next_steps': next_steps,
        'key_transcript_snippets': [],
        'raw_analysis': analysis_text[:1000] + "..." if len(analysis_text) > 1000 else analysis_text,
        'parsing_method': 'text_fallback'
    }

def analyze_technical_deployment_details(transcript_results: List[Dict], call_classifications: Dict[str, str], claude_client) -> Dict[str, Any]:
    """Analyze technical deployment details across all call transcripts in an engagement."""
    
    log_info("Starting Technical Deployment Details Analysis...")
    
    # Step 1: Extract technical insights from each transcript
    technical_insights = []
    for result in transcript_results:
        if 'error' not in result:
            insights = {
                'filename': result.get('filename', 'Unknown'),
                'call_type': call_classifications.get(result.get('filename', ''), 'Unknown'),
                'raw_analysis': result.get('analysis', {}).get('raw_analysis', ''),
                'key_discussion_points': result.get('analysis', {}).get('key_discussion_points', []),
                'business_context': result.get('analysis', {}).get('business_context', {}),
                'action_items': result.get('action_items', []),
                'sentiment_analysis': result.get('sentiment_analysis', {})
            }
            technical_insights.append(insights)
    
    if not technical_insights:
        log_warning("No valid transcript insights found for technical deployment analysis")
        return {
            'error': 'No valid transcript data available for technical deployment analysis',
            'deployment_summary': {},
            'reasoning': 'Insufficient data for analysis'
        }
    
    # Step 2: Create comprehensive technical summary for Claude analysis
    technical_summary = _create_technical_deployment_summary(technical_insights)
    
    # Step 3: Generate technical deployment analysis using Claude
    deployment_analysis = _generate_technical_deployment_analysis(technical_summary, claude_client)
    
    return deployment_analysis

def _create_technical_deployment_summary(technical_insights: List[Dict]) -> str:
    """Create a comprehensive summary of all technical deployment insights."""
    
    summary_parts = []
    
    # Call Overview
    call_types = [insight['call_type'] for insight in technical_insights]
    call_type_counts = {call_type: call_types.count(call_type) for call_type in set(call_types)}
    
    summary_parts.append("## TECHNICAL DEPLOYMENT OVERVIEW")
    summary_parts.append(f"Total Calls: {len(technical_insights)}")
    summary_parts.append("Call Types:")
    for call_type, count in call_type_counts.items():
        summary_parts.append(f"  - {call_type}: {count}")
    
    # Technical Insights from Each Call
    summary_parts.append("\n## DETAILED TECHNICAL INSIGHTS")
    for i, insight in enumerate(technical_insights, 1):
        summary_parts.append(f"\n### Call {i}: {insight['filename']}")
        summary_parts.append(f"Type: {insight['call_type']}")
        
        # Key discussion points
        if insight['key_discussion_points']:
            summary_parts.append("Key Technical Discussion Points:")
            for point in insight['key_discussion_points'][:10]:  # Top 10 points
                summary_parts.append(f"  - {point}")
        
        # Business context
        if insight['business_context']:
            summary_parts.append("Business Context:")
            for key, value in insight['business_context'].items():
                if isinstance(value, list):
                    summary_parts.append(f"  - {key}: {', '.join(value[:5])}")  # Top 5 items
                else:
                    summary_parts.append(f"  - {key}: {value}")
        
        # Action items related to technical deployment
        if insight['action_items']:
            summary_parts.append("Technical Action Items:")
            for item in insight['action_items'][:5]:  # Top 5 items
                action = item.get('action', 'N/A')
                if any(tech_keyword in action.lower() for tech_keyword in ['integration', 'api', 'deployment', 'setup', 'configuration', 'language', 'platform', 'tool', 'system']):
                    summary_parts.append(f"  - {action} (Owner: {item.get('owner', 'N/A')}, Priority: {item.get('priority', 'N/A')})")
        
        # Raw analysis (first 1000 characters for technical details)
        if insight['raw_analysis']:
            summary_parts.append("Technical Details:")
            raw_text = insight['raw_analysis'][:1000] + "..." if len(insight['raw_analysis']) > 1000 else insight['raw_analysis']
            summary_parts.append(f"  {raw_text}")
    
    # Overall technical patterns
    summary_parts.append("\n## TECHNICAL PATTERNS")
    
    # Most common technical terms
    all_text = " ".join([insight.get('raw_analysis', '') for insight in technical_insights])
    technical_terms = ['github', 'gitlab', 'azure', 'aws', 'jenkins', 'gitlab ci', 'github actions', 'java', 'python', 'javascript', 'typescript', 'node', 'maven', 'npm', 'docker', 'kubernetes', 'jira', 'slack', 'microsoft', 'visual studio', 'intellij', 'eclipse', 'vscode', 'monorepo', 'microservices', 'api', 'rest', 'graphql', 'database', 'sql', 'nosql', 'redis', 'postgresql', 'mysql', 'mongodb']
    
    found_terms = []
    for term in technical_terms:
        if term.lower() in all_text.lower():
            found_terms.append(term)
    
    if found_terms:
        summary_parts.append("Technical Terms Mentioned:")
        for term in found_terms:
            summary_parts.append(f"  - {term}")
    
    return "\n".join(summary_parts)

def _generate_technical_deployment_analysis(technical_summary: str, claude_client) -> Dict[str, Any]:
    """Generate comprehensive technical deployment analysis using Claude."""
    
    # Ensure we have enough content for analysis
    if len(technical_summary) < 100:
        log_warning("Technical summary too short for meaningful deployment analysis")
        return {
            'error': 'Insufficient data for detailed technical deployment analysis',
            'deployment_summary': {},
            'reasoning': 'Insufficient data for analysis'
        }
    
    deployment_analysis_prompt = f"""You are an expert technical architect analyzing deployment details from sales call transcripts. Based on the following technical engagement data, provide a comprehensive technical deployment analysis.

TECHNICAL ENGAGEMENT DATA:
{technical_summary}

Please provide a detailed technical deployment analysis in the following JSON format. IMPORTANT: Respond with ONLY the JSON object, no additional text, explanations, or markdown formatting:

{{
    "scm_platform": {{
        "platform": "<GitHub/GitLab/Azure DevOps/etc>",
        "deployment_type": "<Cloud/On-prem/Hybrid>",
        "details": "<specific details about their SCM setup>",
        "evidence": "<quotes or evidence from transcripts>"
    }},
    "ci_pipelines": {{
        "primary_ci": "<Jenkins/GitHub Actions/GitLab CI/Azure DevOps/etc>",
        "additional_ci": ["<other CI tools mentioned>"],
        "details": "<specific details about their CI setup>",
        "evidence": "<quotes or evidence from transcripts>"
    }},
    "programming_languages": {{
        "primary_languages": ["<main languages used>"],
        "poc_focus_languages": ["<languages they're testing Semgrep on>"],
        "details": "<specific details about language usage>",
        "evidence": "<quotes or evidence from transcripts>"
    }},
    "integrations": {{
        "interested_integrations": ["<JIRA/Slack/Teams/etc>"],
        "current_integrations": ["<existing integrations>"],
        "details": "<specific details about integration requirements>",
        "evidence": "<quotes or evidence from transcripts>"
    }},
    "supply_chain_security": {{
        "languages_tested": ["<languages for SCA testing>"],
        "package_managers": ["<npm/maven/pip/etc>"],
        "details": "<specific details about supply chain security>",
        "evidence": "<quotes or evidence from transcripts>"
    }},
    "current_security_tools": {{
        "sast": "<current SAST tool>",
        "dast": "<current DAST tool>",
        "sca": "<current SCA tool>",
        "secrets_detection": "<current secrets detection tool>",
        "aspm": "<current ASPM tool>",
        "details": "<specific details about current security tools>",
        "evidence": "<quotes or evidence from transcripts>"
    }},
    "ide_environment": {{
        "primary_ide": "<VS Code/IntelliJ/Eclipse/etc>",
        "additional_tools": ["<other development tools>"],
        "details": "<specific details about IDE setup>",
        "evidence": "<quotes or evidence from transcripts>"
    }},
    "additional_technical_details": [
        "<any other important technical details>"
    ],
    "deployment_complexity": "<Low/Medium/High>",
    "migration_considerations": [
        "<specific migration considerations>"
    ],
    "technical_risks": [
        "<potential technical risks>"
    ],
    "recommendations": [
        "<technical recommendations for deployment>"
    ]
}}

Focus on:
1. Concrete evidence from the transcripts
2. Specific technical requirements and constraints
3. Current tooling and infrastructure
4. Integration requirements
5. Migration considerations
6. Technical risks and recommendations

CRITICAL: Respond with ONLY the JSON object above, no markdown formatting, no code blocks, no additional text."""
    
    try:
        response = claude_client.analyze_pov_win_probability(technical_summary, deployment_analysis_prompt)
        
        if response.get('success'):
            analysis_text = response.get('analysis', '')
            log_debug(f"Raw Claude response for technical deployment analysis: {analysis_text[:500]}...")
            
            # Try to extract JSON from the response
            try:
                # First, try to find JSON wrapped in markdown code blocks
                import re
                
                # Look for JSON in markdown code blocks
                json_code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', analysis_text, re.DOTALL)
                if json_code_block_match:
                    json_str = json_code_block_match.group(1)
                    log_debug("Found JSON in markdown code block")
                else:
                    # Look for JSON without markdown wrapping - improved pattern
                    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', analysis_text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        log_debug("Found JSON without markdown wrapping")
                    else:
                        # Try to find the largest JSON-like structure with better pattern
                        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', analysis_text, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(0)
                            log_debug("Found JSON using improved pattern")
                        else:
                            # Last resort: find any JSON-like structure
                            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
                            if json_match:
                                json_str = json_match.group(0)
                                log_debug("Found JSON using fallback pattern")
                            else:
                                raise ValueError("No JSON structure found in response")
                
                # Clean up the JSON string
                json_str = json_str.strip()
                
                # Remove any leading/trailing text that might be before/after the JSON
                if json_str.startswith('```'):
                    json_str = json_str[3:]
                if json_str.endswith('```'):
                    json_str = json_str[:-3]
                
                # Additional cleanup for common issues
                json_str = json_str.replace('\n    ', '\n')  # Fix indentation issues
                json_str = json_str.replace('\n  ', '\n')    # Fix double spaces
                json_str = json_str.replace('\n    "', '\n"')  # Fix specific indentation issue
                json_str = json_str.replace('\n  "', '\n"')    # Fix double space before quotes
                
                log_debug(f"Cleaned JSON string (first 200 chars): {json_str[:200]}...")
                log_debug(f"JSON string length: {len(json_str)}")
                
                # Parse the JSON
                import json
                deployment_analysis = json.loads(json_str)
                
                log_info("Successfully generated technical deployment analysis")
                return deployment_analysis
                
            except json.JSONDecodeError as e:
                log_warning(f"Failed to parse JSON from Claude response: {e}")
                log_debug(f"JSON parsing error details: {e}")
                log_debug(f"Attempted to parse: {json_str[:200]}...")
                log_debug(f"Full JSON string: {json_str}")
                return _parse_technical_deployment_text(analysis_text)
            except Exception as e:
                log_warning(f"Error extracting JSON from Claude response: {e}")
                log_debug(f"Full analysis text: {analysis_text}")
                return _parse_technical_deployment_text(analysis_text)
        else:
            log_error("Failed to generate technical deployment analysis with Claude")
            return _create_fallback_technical_deployment_analysis(technical_summary)
            
    except Exception as e:
        log_error(f"Error generating technical deployment analysis: {e}")
        return _create_fallback_technical_deployment_analysis(technical_summary)

def _parse_technical_deployment_text(analysis_text: str) -> Dict[str, Any]:
    """Parse technical deployment analysis from text response when JSON parsing fails."""
    
    log_debug("Attempting to parse technical deployment analysis from text response")
    
    # Extract key technical information using regex patterns
    import re
    
    # Extract SCM platform
    scm_patterns = [
        r'scm_platform["\s]*:["\s]*\{[^}]*"platform["\s]*:["\s]*([^"]+)',
        r'platform["\s]*:["\s]*([^"]+)',
        r'github|gitlab|azure|bitbucket'
    ]
    
    scm_platform = "Unknown"
    for pattern in scm_patterns:
        scm_match = re.search(pattern, analysis_text, re.IGNORECASE)
        if scm_match:
            scm_platform = scm_match.group(1) if scm_match.groups() else scm_match.group(0)
            break
    
    # Extract CI pipelines
    ci_patterns = [
        r'ci_pipelines["\s]*:["\s]*\{[^}]*"primary_ci["\s]*:["\s]*([^"]+)',
        r'primary_ci["\s]*:["\s]*([^"]+)',
        r'jenkins|github actions|gitlab ci|azure devops|circleci'
    ]
    
    ci_pipeline = "Unknown"
    for pattern in ci_patterns:
        ci_match = re.search(pattern, analysis_text, re.IGNORECASE)
        if ci_match:
            ci_pipeline = ci_match.group(1) if ci_match.groups() else ci_match.group(0)
            break
    
    # Extract programming languages
    language_patterns = [
        r'programming_languages["\s]*:["\s]*\{[^}]*"primary_languages["\s]*:["\s]*\[([^\]]+)\]',
        r'primary_languages["\s]*:["\s]*\[([^\]]+)\]',
        r'java|python|javascript|typescript|go|rust|c#|php|ruby'
    ]
    
    languages = []
    for pattern in language_patterns:
        lang_match = re.search(pattern, analysis_text, re.IGNORECASE)
        if lang_match:
            if lang_match.groups():
                # Parse array format
                lang_str = lang_match.group(1)
                languages = [lang.strip().strip('"') for lang in lang_str.split(',')]
            else:
                # Extract individual languages
                languages = re.findall(r'java|python|javascript|typescript|go|rust|c#|php|ruby', analysis_text, re.IGNORECASE)
            break
    
    return {
        'scm_platform': {
            'platform': scm_platform,
            'deployment_type': 'Unknown',
            'details': 'Parsed from text analysis',
            'evidence': 'Text parsing fallback'
        },
        'ci_pipelines': {
            'primary_ci': ci_pipeline,
            'additional_ci': [],
            'details': 'Parsed from text analysis',
            'evidence': 'Text parsing fallback'
        },
        'programming_languages': {
            'primary_languages': languages,
            'poc_focus_languages': languages,
            'details': 'Parsed from text analysis',
            'evidence': 'Text parsing fallback'
        },
        'integrations': {
            'interested_integrations': [],
            'current_integrations': [],
            'details': 'Parsed from text analysis',
            'evidence': 'Text parsing fallback'
        },
        'supply_chain_security': {
            'languages_tested': languages,
            'package_managers': [],
            'details': 'Parsed from text analysis',
            'evidence': 'Text parsing fallback'
        },
        'current_security_tools': {
            'sast': 'Unknown',
            'dast': 'Unknown',
            'sca': 'Unknown',
            'secrets_detection': 'Unknown',
            'aspm': 'Unknown',
            'details': 'Parsed from text analysis',
            'evidence': 'Text parsing fallback'
        },
        'ide_environment': {
            'primary_ide': 'Unknown',
            'additional_tools': [],
            'details': 'Parsed from text analysis',
            'evidence': 'Text parsing fallback'
        },
        'additional_technical_details': [],
        'deployment_complexity': 'Unknown',
        'migration_considerations': [],
        'technical_risks': [],
        'recommendations': [],
        'parsing_method': 'text_fallback'
    }

def _create_fallback_technical_deployment_analysis(technical_summary: str) -> Dict[str, Any]:
    """Create a fallback technical deployment analysis when Claude analysis fails."""
    
    log_debug("Creating fallback technical deployment analysis")
    
    # Analyze the technical summary to provide basic insights
    summary_lower = technical_summary.lower()
    
    # Extract basic technical information
    scm_platform = "Unknown"
    if 'github' in summary_lower:
        scm_platform = "GitHub"
    elif 'gitlab' in summary_lower:
        scm_platform = "GitLab"
    elif 'azure' in summary_lower:
        scm_platform = "Azure DevOps"
    
    ci_pipeline = "Unknown"
    if 'jenkins' in summary_lower:
        ci_pipeline = "Jenkins"
    elif 'github actions' in summary_lower:
        ci_pipeline = "GitHub Actions"
    elif 'gitlab ci' in summary_lower:
        ci_pipeline = "GitLab CI"
    
    languages = []
    if 'java' in summary_lower:
        languages.append("Java")
    if 'python' in summary_lower:
        languages.append("Python")
    if 'javascript' in summary_lower or 'js' in summary_lower:
        languages.append("JavaScript")
    if 'typescript' in summary_lower:
        languages.append("TypeScript")
    
    return {
        'scm_platform': {
            'platform': scm_platform,
            'deployment_type': 'Unknown',
            'details': 'Fallback analysis based on technical summary',
            'evidence': 'Basic pattern matching'
        },
        'ci_pipelines': {
            'primary_ci': ci_pipeline,
            'additional_ci': [],
            'details': 'Fallback analysis based on technical summary',
            'evidence': 'Basic pattern matching'
        },
        'programming_languages': {
            'primary_languages': languages,
            'poc_focus_languages': languages,
            'details': 'Fallback analysis based on technical summary',
            'evidence': 'Basic pattern matching'
        },
        'integrations': {
            'interested_integrations': [],
            'current_integrations': [],
            'details': 'Fallback analysis based on technical summary',
            'evidence': 'Basic pattern matching'
        },
        'supply_chain_security': {
            'languages_tested': languages,
            'package_managers': [],
            'details': 'Fallback analysis based on technical summary',
            'evidence': 'Basic pattern matching'
        },
        'current_security_tools': {
            'sast': 'Unknown',
            'dast': 'Unknown',
            'sca': 'Unknown',
            'secrets_detection': 'Unknown',
            'aspm': 'Unknown',
            'details': 'Fallback analysis based on technical summary',
            'evidence': 'Basic pattern matching'
        },
        'ide_environment': {
            'primary_ide': 'Unknown',
            'additional_tools': [],
            'details': 'Fallback analysis based on technical summary',
            'evidence': 'Basic pattern matching'
        },
        'additional_technical_details': [],
        'deployment_complexity': 'Unknown',
        'migration_considerations': [],
        'technical_risks': [],
        'recommendations': [],
        'fallback_analysis': True,
        'analysis_method': 'fallback'
    }

def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description='Semgrep POV Assistant')
    parser.add_argument('--no-google-docs', action='store_true', 
                       help='Skip file creation (process transcripts only)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    parser.add_argument('--transcripts-dir', type=str,
                       help='Custom directory containing transcript files')
    parser.add_argument('--output-dir', type=str,
                       help='Custom directory for output files')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Override transcripts directory if specified
    if args.transcripts_dir:
        # Handle tilde expansion for home directory
        transcripts_path = Path(args.transcripts_dir)
        if str(transcripts_path).startswith('~'):
            transcripts_path = transcripts_path.expanduser()
            log_debug(f"Expanded tilde path for transcripts: {transcripts_path}")
        config.setdefault('paths', {})['transcripts_dir'] = str(transcripts_path)
        log_info(f"Using custom transcripts directory: {transcripts_path}")
    
    # Override output directory if specified
    if args.output_dir:
        # Handle tilde expansion for home directory
        output_path = Path(args.output_dir)
        if str(output_path).startswith('~'):
            output_path = output_path.expanduser()
            log_debug(f"Expanded tilde path for output: {output_path}")
        config.setdefault('paths', {})['output_dir'] = str(output_path)
        log_info(f"Using custom output directory: {output_path}")
    else:
        # Default to 'output' folder inside transcripts directory
        transcripts_dir = config.get('paths', {}).get('transcripts_dir', 'data/transcripts')
        transcripts_path = Path(transcripts_dir)
        if str(transcripts_path).startswith('~'):
            transcripts_path = transcripts_path.expanduser()
        output_dir = transcripts_path / 'output'
        config.setdefault('paths', {})['output_dir'] = str(output_dir)
        log_debug(f"Using default output directory: {output_dir}")
    
    # Setup logging
    log_level = "DEBUG" if args.debug else config.get('logging', {}).get('level', 'INFO')
    setup_logger(level=log_level, config=config)
    
    # Log startup information
    log_startup_info(config)
    
    try:
        # Check environment
        if not check_environment():
            return 1
        
        # Setup directories
        setup_directories(config)
        
        # Find transcript files
        transcript_files = find_transcript_files(config)
        
        if not transcript_files:
            print("❌ No transcript files found.")
            print("Please add transcript files to the data/transcripts/ directory.")
            return 1
        
        # Process transcripts
        results = process_transcripts(transcript_files, config, use_google_docs=not args.no_google_docs)
        
        # Print summary
        print_summary(results, use_google_docs=not args.no_google_docs)
        
        # Log shutdown information
        log_shutdown_info()
        
        return 0
        
    except KeyboardInterrupt:
        log_info("Application interrupted by user")
        return 1
    except Exception as e:
        log_error(f"Application error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 