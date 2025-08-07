"""
Transcript processor for semgrep_pov_assistant.

This module handles the processing of call transcript files, including
reading, cleaning, analyzing, and extracting information from transcripts.
"""

import os
import json
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from pathlib import Path
import logging

from .utils.logger import get_logger, log_error, log_warning, log_info, log_debug
from .utils.file_utils import FileUtils
from .utils.text_utils import TextUtils
from .claude_client import ClaudeClient

logger = get_logger()

class TranscriptProcessor:
    """
    Processor for call transcript files.
    
    This class handles reading transcript files, cleaning the content,
    analyzing the text using Claude, and extracting actionable insights.
    """
    
    def __init__(self, claude_client: ClaudeClient, config: Optional[Dict] = None):
        """
        Initialize the transcript processor.
        
        Args:
            claude_client: Claude client instance
            config: Configuration dictionary
        """
        self.claude_client = claude_client
        self.config = config or {}
        
        # Load prompt templates
        self.prompts = self._load_prompts()
        
        # Processing settings
        self.save_intermediate_results = self.config.get('processing', {}).get('save_intermediate_results', True)
        self.output_dir = self.config.get('paths', {}).get('output_dir', 'data/output')
        
        log_info("Transcript processor initialized")
    
    def _load_prompts(self) -> Dict[str, str]:
        """
        Load prompt templates from configuration.
        
        Returns:
            Dictionary of prompt templates
        """
        try:
            import yaml
            prompts_file = Path('config/prompts.yaml')
            
            if prompts_file.exists():
                with open(prompts_file, 'r', encoding='utf-8') as f:
                    prompts = yaml.safe_load(f)
                log_debug("Loaded prompt templates from config/prompts.yaml")
                return prompts
            else:
                log_warning("Prompts file not found, using default prompts")
                return self._get_default_prompts()
                
        except Exception as e:
            log_error(f"Failed to load prompts: {e}")
            return self._get_default_prompts()
    
    def _get_default_prompts(self) -> Dict[str, str]:
        """
        Get default prompt templates.
        
        Returns:
            Dictionary of default prompt templates
        """
        return {
            'call_summary': """
            You are an expert business analyst reviewing a call transcript. Please provide a comprehensive summary of this call with the following structure:
            
            ## Call Overview
            - Date and Time: [extract from transcript]
            - Participants: [list all participants]
            - Duration: [if available]
            - Call Type: [discovery, demo, follow-up, etc.]
            
            ## Key Discussion Points
            [List 3-5 main topics discussed, with brief context]
            
            ## Business Context
            - Current Status: [where the engagement stands]
            - Pain Points Identified: [list specific pain points mentioned]
            - Requirements Discussed: [technical and business requirements]
            
            ## Action Items
            [Extract all action items with the following format:
            - Action: [description]
            - Owner: [person responsible]
            - Due Date: [if mentioned]
            - Priority: [High/Medium/Low based on context]]
            
            ## Sentiment Analysis
            - Overall Sentiment: [Positive/Neutral/Negative]
            - Key Sentiment Indicators: [specific phrases or moments]
            - Engagement Level: [High/Medium/Low]
            
            ## Next Steps
            [List immediate next steps and recommendations]
            
            Please analyze the following transcript:
            {transcript_text}
            """,
            
            'action_items': """
            Extract all action items from this call transcript. For each action item, identify:
            
            1. The specific action or task
            2. Who is responsible (owner)
            3. Due date or timeline (if mentioned)
            4. Priority level (High/Medium/Low)
            5. Context or background
            
            Format the response as a structured list:
            
            ## Action Items
            
            ### Action Item 1
            - **Action**: [description]
            - **Owner**: [person name]
            - **Due Date**: [date if mentioned]
            - **Priority**: [High/Medium/Low]
            - **Context**: [background information]
            
            [Continue for all action items found]
            
            Transcript:
            {transcript_text}
            """,
            
            'sentiment': """
            Analyze the sentiment and engagement level throughout this call transcript. Focus on:
            
            1. Overall sentiment (Positive/Neutral/Negative)
            2. Sentiment changes throughout the call
            3. Key moments that influenced sentiment
            4. Engagement level of participants
            5. Specific phrases or statements that indicate sentiment
            
            Provide your analysis in this format:
            
            ## Sentiment Analysis
            
            ### Overall Assessment
            - **Primary Sentiment**: [Positive/Neutral/Negative]
            - **Confidence Level**: [High/Medium/Low]
            - **Engagement Level**: [High/Medium/Low]
            
            ### Key Sentiment Indicators
            [List specific phrases, moments, or statements that influenced sentiment]
            
            ### Sentiment Progression
            [Describe how sentiment changed throughout the call]
            
            ### Recommendations
            [Based on sentiment analysis, provide recommendations for follow-up]
            
            Transcript:
            {transcript_text}
            """
        }
    
    def process_transcript_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Process a single transcript file.
        
        Args:
            file_path: Path to the transcript file
            
        Returns:
            Dictionary containing analysis results
        """
        file_path = Path(file_path)
        
        log_info(f"Processing transcript file: {file_path.name}")
        
        try:
            # Validate file
            if not FileUtils.validate_file_format(file_path):
                raise ValueError(f"Invalid file format: {file_path}")
            
            # Read and clean the transcript
            raw_content = FileUtils.read_text_file(file_path)
            cleaned_content = TextUtils.clean_transcript_text(raw_content)
            
            if not cleaned_content.strip():
                raise ValueError(f"Empty or invalid transcript content: {file_path}")
            
            # Extract metadata
            metadata = FileUtils.extract_metadata_from_filename(file_path)
            metadata.update(FileUtils.get_file_info(file_path))
            
            # Calculate text statistics
            text_stats = TextUtils.calculate_text_statistics(cleaned_content)
            
            log_debug(f"Transcript statistics: {text_stats}")
            
            # Analyze the transcript
            analysis_results = self._analyze_transcript(cleaned_content)
            
            # Extract action items
            action_items = self._extract_action_items(cleaned_content)
            
            # Analyze sentiment
            sentiment_analysis = self._analyze_sentiment(cleaned_content)
            
            # Compile results
            results = {
                'metadata': metadata,
                'text_statistics': text_stats,
                'analysis': analysis_results,
                'action_items': action_items,
                'sentiment_analysis': sentiment_analysis,
                'processing_timestamp': datetime.now().isoformat(),
                'file_path': str(file_path)
            }
            
            # Save intermediate results if enabled
            if self.save_intermediate_results:
                self._save_intermediate_results(results, file_path.stem)
            
            log_info(f"Successfully processed transcript: {file_path.name}")
            return results
            
        except Exception as e:
            log_error(f"Failed to process transcript {file_path}: {e}")
            return {
                'error': str(e),
                'file_path': str(file_path),
                'processing_timestamp': datetime.now().isoformat()
            }
    
    def _analyze_transcript(self, transcript_text: str) -> Dict[str, Any]:
        """
        Analyze transcript using Claude.
        
        Args:
            transcript_text: Cleaned transcript text
            
        Returns:
            Analysis results dictionary
        """
        try:
            log_debug(f"Available prompt keys: {list(self.prompts.keys())}")
            
            # Get the call summary prompt - check for the correct structure
            if 'call_analysis' in self.prompts and 'summary' in self.prompts['call_analysis']:
                prompt_template = self.prompts['call_analysis']['summary']
                log_debug("Using call_analysis.summary prompt")
            elif 'call_summary' in self.prompts:
                prompt_template = self.prompts['call_summary']
                log_debug("Using call_summary prompt")
            else:
                log_error(f"call_summary prompt not found. Available prompts: {list(self.prompts.keys())}")
                # Use a default prompt
                prompt_template = self._get_default_prompts()['call_summary']
                log_debug("Using default call_summary prompt")
            
            log_debug(f"Using prompt template: {prompt_template[:100]}...")
            
            # Analyze with Claude
            analysis_result = self.claude_client.analyze_call_transcript(transcript_text, prompt_template)
            
            log_debug(f"Claude analysis result: {analysis_result}")
            
            if analysis_result.get('success'):
                # Parse the analysis to extract structured information
                parsed_analysis = self._parse_analysis_text(analysis_result['analysis'])
                parsed_analysis['raw_analysis'] = analysis_result['analysis']
                parsed_analysis['usage'] = analysis_result.get('usage')
                parsed_analysis['model_used'] = analysis_result.get('model')
                
                log_debug(f"Parsed analysis keys: {list(parsed_analysis.keys())}")
                return parsed_analysis
            else:
                log_warning(f"Claude analysis failed: {analysis_result.get('error')}")
                return {
                    'error': analysis_result.get('error'),
                    'raw_analysis': analysis_result.get('analysis', 'Analysis failed')
                }
                
        except Exception as e:
            log_error(f"Failed to analyze transcript: {e}")
            return {
                'error': str(e),
                'raw_analysis': 'Analysis failed due to error'
            }
    
    def _parse_analysis_text(self, analysis_text: str) -> Dict[str, Any]:
        """
        Parse the analysis text to extract structured information.
        
        Args:
            analysis_text: Raw analysis text from Claude
            
        Returns:
            Parsed analysis dictionary
        """
        parsed = {
            'executive_summary': '',
            'call_overview': {},
            'key_discussion_points': [],
            'business_context': {},
            'action_items': [],
            'sentiment_analysis': {},
            'next_steps': []
        }
        
        if not analysis_text:
            return parsed
        
        # Simple parsing logic - can be enhanced
        lines = analysis_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # Detect sections
            if line.startswith('## Call Overview'):
                current_section = 'call_overview'
            elif line.startswith('## Key Discussion Points'):
                current_section = 'key_discussion_points'
            elif line.startswith('## Business Context'):
                current_section = 'business_context'
            elif line.startswith('## Action Items'):
                current_section = 'action_items'
            elif line.startswith('## Sentiment Analysis'):
                current_section = 'sentiment_analysis'
            elif line.startswith('## Next Steps'):
                current_section = 'next_steps'
            elif line.startswith('##'):
                # Other sections
                current_section = None
            else:
                # Process content based on current section
                if current_section == 'call_overview':
                    if ':' in line:
                        key, value = line.split(':', 1)
                        parsed['call_overview'][key.strip()] = value.strip()
                elif current_section == 'key_discussion_points':
                    if line.startswith('-') or line.startswith('*'):
                        parsed['key_discussion_points'].append(line.lstrip('- *').strip())
                elif current_section == 'business_context':
                    if ':' in line:
                        key, value = line.split(':', 1)
                        parsed['business_context'][key.strip()] = value.strip()
                elif current_section == 'next_steps':
                    if line.startswith('-') or line.startswith('*'):
                        parsed['next_steps'].append(line.lstrip('- *').strip())
        
        return parsed
    
    def _extract_action_items(self, transcript_text: str) -> List[Dict[str, str]]:
        """
        Extract action items from transcript.
        
        Args:
            transcript_text: Transcript text
            
        Returns:
            List of action item dictionaries
        """
        try:
            log_debug("Starting action items extraction")
            
            # Use Claude to extract action items
            action_items_result = self.claude_client.extract_action_items(transcript_text)
            
            log_debug(f"Action items result: {action_items_result}")
            
            if action_items_result.get('success'):
                action_items = action_items_result.get('action_items', [])
                
                # Ensure action_items is a list
                if not isinstance(action_items, list):
                    log_warning(f"Action items is not a list: {type(action_items)}")
                    action_items = []
                
                # Add source information to each item
                for item in action_items:
                    if isinstance(item, dict):
                        item['source'] = 'ai_extraction'
                        item['extraction_timestamp'] = datetime.now().isoformat()
                    else:
                        log_warning(f"Action item is not a dict: {type(item)}")
                
                log_debug(f"Extracted {len(action_items)} action items")
                return action_items
            else:
                log_warning(f"Action items extraction failed: {action_items_result.get('error')}")
                # Fallback to rule-based extraction
                return TextUtils.extract_action_items(transcript_text)
            
        except Exception as e:
            log_error(f"Failed to extract action items: {e}")
            # Fallback to rule-based extraction
            return TextUtils.extract_action_items(transcript_text)
    
    def _analyze_sentiment(self, transcript_text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of the transcript.
        
        Args:
            transcript_text: Transcript text
            
        Returns:
            Sentiment analysis results
        """
        try:
            log_debug("Starting sentiment analysis")
            
            sentiment_result = self.claude_client.analyze_sentiment(transcript_text)
            
            log_debug(f"Sentiment result: {sentiment_result}")
            
            if sentiment_result.get('success'):
                # The sentiment data is in the 'sentiment' key, not 'sentiment_analysis'
                sentiment_data = sentiment_result.get('sentiment', {})
                
                return {
                    'sentiment_analysis': sentiment_data,
                    'usage': sentiment_result.get('usage'),
                    'success': True
                }
            else:
                log_warning(f"Sentiment analysis failed: {sentiment_result.get('error')}")
                return {
                    'error': sentiment_result.get('error'),
                    'sentiment_analysis': 'Sentiment analysis failed',
                    'success': False
                }
                
        except Exception as e:
            log_error(f"Failed to analyze sentiment: {e}")
            return {
                'error': str(e),
                'sentiment_analysis': 'Sentiment analysis failed due to error',
                'success': False
            }
    
    def _save_intermediate_results(self, results: Dict[str, Any], filename: str):
        """
        Save intermediate processing results.
        
        Args:
            results: Processing results to save
            filename: Base filename for the saved file
        """
        try:
            FileUtils.save_intermediate_result(results, filename, self.output_dir)
            log_debug(f"Saved intermediate results for {filename}")
        except Exception as e:
            log_warning(f"Failed to save intermediate results: {e}")
    
    def process_multiple_transcripts(self, file_paths: List[Union[str, Path]]) -> Dict[str, Any]:
        """
        Process multiple transcript files.
        
        Args:
            file_paths: List of transcript file paths
            
        Returns:
            Dictionary containing results for all transcripts
        """
        log_info(f"Processing {len(file_paths)} transcript files")
        
        results = {
            'total_files': len(file_paths),
            'successful_files': 0,
            'failed_files': 0,
            'transcripts': [],
            'summary': {},
            'processing_timestamp': datetime.now().isoformat()
        }
        
        for file_path in file_paths:
            try:
                transcript_result = self.process_transcript_file(file_path)
                
                if 'error' not in transcript_result:
                    results['successful_files'] += 1
                    results['transcripts'].append(transcript_result)
                else:
                    results['failed_files'] += 1
                    results['transcripts'].append(transcript_result)
                    
            except Exception as e:
                log_error(f"Failed to process {file_path}: {e}")
                results['failed_files'] += 1
                results['transcripts'].append({
                    'error': str(e),
                    'file_path': str(file_path)
                })
        
        # Generate summary statistics
        results['summary'] = self._generate_summary_statistics(results['transcripts'])
        
        log_info(f"Completed processing: {results['successful_files']} successful, {results['failed_files']} failed")
        
        return results
    
    def _generate_summary_statistics(self, transcripts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics from multiple transcripts.
        
        Args:
            transcripts: List of transcript results
            
        Returns:
            Summary statistics dictionary
        """
        successful_transcripts = [t for t in transcripts if 'error' not in t]
        
        if not successful_transcripts:
            return {'error': 'No successful transcript processing'}
        
        # Collect all action items
        all_action_items = []
        all_participants = set()
        total_words = 0
        total_duration = 0
        
        for transcript in successful_transcripts:
            # Action items
            action_items = transcript.get('action_items', [])
            all_action_items.extend(action_items)
            
            # Participants
            participants = transcript.get('analysis', {}).get('call_overview', {}).get('Participants', '')
            if participants:
                all_participants.update([p.strip() for p in participants.split(',')])
            
            # Text statistics
            stats = transcript.get('text_statistics', {})
            total_words += stats.get('words', 0)
        
        # Analyze action items
        action_item_summary = self._analyze_action_items(all_action_items)
        
        return {
            'total_transcripts': len(successful_transcripts),
            'total_action_items': len(all_action_items),
            'unique_participants': list(all_participants),
            'total_words': total_words,
            'average_words_per_transcript': total_words / len(successful_transcripts) if successful_transcripts else 0,
            'action_item_summary': action_item_summary
        }
    
    def _analyze_action_items(self, action_items: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Analyze action items for summary statistics.
        
        Args:
            action_items: List of action item dictionaries
            
        Returns:
            Action item analysis dictionary
        """
        if not action_items:
            return {'total': 0}
        
        # Count by priority
        priority_counts = {}
        owner_counts = {}
        
        for item in action_items:
            priority = item.get('priority', 'Unknown')
            owner = item.get('owner', 'Unassigned')
            
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            owner_counts[owner] = owner_counts.get(owner, 0) + 1
        
        return {
            'total': len(action_items),
            'by_priority': priority_counts,
            'by_owner': owner_counts,
            'high_priority_count': priority_counts.get('High', 0),
            'medium_priority_count': priority_counts.get('Medium', 0),
            'low_priority_count': priority_counts.get('Low', 0)
        } 