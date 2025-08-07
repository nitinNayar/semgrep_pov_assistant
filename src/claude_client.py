"""
Claude API client for semgrep_pov_assistant.

This module provides a comprehensive interface to Anthropic's Claude API for
analyzing call transcripts, generating summaries, and extracting
action items. It includes context window management, retry logic,
and fallback mechanisms.
"""

import os
import time
import json
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import logging

import anthropic
from anthropic import Anthropic

from .utils.logger import get_logger, log_error, log_warning, log_info, log_debug
from .utils.text_utils import TextUtils

logger = get_logger()

class ClaudeClient:
    """
    Claude API client with comprehensive error handling and context management.
    
    This class provides methods for interacting with Anthropic's Claude API to analyze
    call transcripts, generate summaries, and extract actionable insights.
    """
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        """
        Initialize the Claude client.
        
        Args:
            api_key: Anthropic API key (if None, will try to get from environment)
            config: Configuration dictionary with Claude settings
        """
        # Get API key
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter.")
        
        # Initialize Anthropic client
        self.client = Anthropic(api_key=self.api_key)
        
        # Load configuration
        self.config = config or {}
        self.model = self.config.get('claude', {}).get('model', 'claude-sonnet-4-20250514')
        self.fallback_model = self.config.get('claude', {}).get('fallback_model', 'claude-3-7-sonnet-20250219')
        self.max_tokens = self.config.get('claude', {}).get('max_tokens', 4000)
        self.temperature = self.config.get('claude', {}).get('temperature', 0.3)
        self.max_context_length = self.config.get('claude', {}).get('max_context_length', 200000)
        
        # Context management settings
        self.chunk_size = self.config.get('context', {}).get('chunk_size', 8000)
        self.overlap_size = self.config.get('context', {}).get('overlap_size', 500)
        self.max_chunks_per_request = self.config.get('context', {}).get('max_chunks_per_request', 4)
        
        # Rate limiting settings
        self.requests_per_minute = self.config.get('rate_limiting', {}).get('requests_per_minute', 60)
        self.delay_between_requests = self.config.get('rate_limiting', {}).get('delay_between_requests', 1)
        
        # Error handling settings
        self.max_retries = self.config.get('error_handling', {}).get('max_retry_attempts', 3)
        self.retry_delay = self.config.get('app', {}).get('retry_delay', 5)
        
        # Track API usage
        self.total_requests = 0
        self.total_tokens_used = 0
        self.last_request_time = 0
        
        log_info(f"Claude client initialized with model: {self.model}")
    
    def _rate_limit_check(self):
        """Check and enforce rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < (60 / self.requests_per_minute):
            sleep_time = (60 / self.requests_per_minute) - time_since_last
            log_debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, prompt: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Make a request to Claude API with retry logic.
        
        Args:
            prompt: The prompt to send to the model
            model: Model to use (if None, uses default model)
            **kwargs: Additional parameters for the API call
            
        Returns:
            API response dictionary
            
        Raises:
            Exception: If all retry attempts fail
        """
        model = model or self.model
        max_retries = kwargs.pop('max_retries', self.max_retries)
        
        for attempt in range(max_retries + 1):
            try:
                # Rate limiting
                self._rate_limit_check()
                
                # Prepare request parameters
                request_params = {
                    'model': model,
                    'max_tokens': kwargs.get('max_tokens', self.max_tokens),
                    'temperature': kwargs.get('temperature', self.temperature),
                    'messages': [{'role': 'user', 'content': prompt}],
                    **kwargs
                }
                
                log_debug(f"Making Claude request (attempt {attempt + 1}/{max_retries + 1})")
                
                # Make the request
                response = self.client.messages.create(**request_params)
                
                # Update usage statistics
                self.total_requests += 1
                if hasattr(response, 'usage'):
                    self.total_tokens_used += response.usage.input_tokens + response.usage.output_tokens
                
                log_debug(f"Claude request successful. Tokens used: {response.usage.input_tokens + response.usage.output_tokens if hasattr(response, 'usage') else 'unknown'}")
                
                return {
                    'content': response.content[0].text,
                    'usage': {
                        'input_tokens': response.usage.input_tokens,
                        'output_tokens': response.usage.output_tokens,
                        'total_tokens': response.usage.input_tokens + response.usage.output_tokens
                    } if hasattr(response, 'usage') else None,
                    'model': response.model,
                    'finish_reason': response.stop_reason
                }
                
            except anthropic.RateLimitError as e:
                log_warning(f"Rate limit exceeded (attempt {attempt + 1}): {e}")
                if attempt < max_retries:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    raise
                    
            except anthropic.APIError as e:
                log_error(f"Claude API error (attempt {attempt + 1}): {e}")
                if attempt < max_retries:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    raise
                    
            except Exception as e:
                log_error(f"Unexpected error (attempt {attempt + 1}): {e}")
                if attempt < max_retries:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    raise
        
        raise Exception(f"All {max_retries + 1} attempts to call Claude API failed")
    
    def analyze_call_transcript(self, transcript_text: str, prompt_template: str) -> Dict[str, Any]:
        """
        Analyze a call transcript using Claude.
        
        Args:
            transcript_text: The transcript text to analyze
            prompt_template: The prompt template to use
            
        Returns:
            Analysis results dictionary
        """
        log_info("Starting call transcript analysis")
        
        # Clean the transcript text
        cleaned_text = TextUtils.clean_transcript_text(transcript_text)
        
        # Check if text needs to be chunked
        estimated_tokens = TextUtils.estimate_tokens(cleaned_text)
        log_debug(f"Estimated tokens in transcript: {estimated_tokens}")
        
        if estimated_tokens <= self.chunk_size:
            # Process as single chunk
            return self._analyze_single_chunk(cleaned_text, prompt_template)
        else:
            # Process as multiple chunks
            return self._analyze_multiple_chunks(cleaned_text, prompt_template)
    
    def _analyze_single_chunk(self, transcript_text: str, prompt_template: str) -> Dict[str, Any]:
        """
        Analyze a single chunk of transcript text.
        
        Args:
            transcript_text: The transcript text to analyze
            prompt_template: The prompt template to use
            
        Returns:
            Analysis results dictionary
        """
        try:
            # Format the prompt with the transcript
            prompt = prompt_template.format(transcript_text=transcript_text)
            
            # Make the request
            response = self._make_request(prompt)
            
            return {
                'success': True,
                'analysis': response['content'],
                'usage': response['usage'],
                'model': response['model']
            }
            
        except Exception as e:
            log_error(f"Error analyzing single chunk: {e}")
            return {
                'success': False,
                'error': str(e),
                'analysis': None
            }
    
    def _analyze_multiple_chunks(self, transcript_text: str, prompt_template: str) -> Dict[str, Any]:
        """
        Analyze transcript text that needs to be split into multiple chunks.
        
        Args:
            transcript_text: The transcript text to analyze
            prompt_template: The prompt template to use
            
        Returns:
            Analysis results dictionary
        """
        try:
            # Split text into chunks
            chunks = TextUtils.split_text_into_chunks(
                transcript_text, 
                self.chunk_size, 
                self.overlap_size
            )
            
            log_info(f"Split transcript into {len(chunks)} chunks")
            
            # Process chunks
            chunk_results = []
            total_usage = {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
            
            for i, chunk in enumerate(chunks[:self.max_chunks_per_request]):
                log_debug(f"Processing chunk {i + 1}/{len(chunks)}")
                
                # Add chunk context to prompt
                chunk_prompt = prompt_template.format(transcript_text=chunk)
                chunk_prompt += f"\n\nNote: This is chunk {i + 1} of {len(chunks)}. Focus on the content in this specific chunk."
                
                # Analyze chunk
                chunk_response = self._make_request(chunk_prompt)
                
                if chunk_response.get('usage'):
                    total_usage['input_tokens'] += chunk_response['usage']['input_tokens']
                    total_usage['output_tokens'] += chunk_response['usage']['output_tokens']
                    total_usage['total_tokens'] += chunk_response['usage']['total_tokens']
                
                chunk_results.append(chunk_response['content'])
            
            # Combine results
            combined_analysis = "\n\n".join(chunk_results)
            
            return {
                'success': True,
                'analysis': combined_analysis,
                'usage': total_usage,
                'model': self.model,
                'chunks_processed': len(chunk_results)
            }
            
        except Exception as e:
            log_error(f"Error analyzing multiple chunks: {e}")
            return {
                'success': False,
                'error': str(e),
                'analysis': None
            }
    
    def analyze_pov_win_probability(self, engagement_summary: str, pov_prompt: str) -> Dict[str, Any]:
        """
        Analyze POV win probability using Claude.
        
        Args:
            engagement_summary: The engagement summary to analyze
            pov_prompt: The POV analysis prompt
            
        Returns:
            POV analysis results dictionary
        """
        try:
            # Make the request directly without transcript processing
            response = self._make_request(pov_prompt)
            
            return {
                'success': True,
                'analysis': response['content'],
                'usage': response['usage'],
                'model': response['model']
            }
            
        except Exception as e:
            log_error(f"Error analyzing POV win probability: {e}")
            return {
                'success': False,
                'error': str(e),
                'analysis': None
            }

    def extract_action_items(self, transcript_text: str) -> Dict[str, Any]:
        """
        Extract action items from transcript text.
        
        Args:
            transcript_text: The transcript text to analyze
            
        Returns:
            Action items dictionary
        """
        try:
            prompt = f"""
            Provide a comprehensive list of all action items.   
            For each action item, identify:
            - The action description
            - Who is responsible (owner)
            - Due date (if mentioned)
            - Also provide guidance on urgency / Priority level (High/Medium/Low)
            - on which date were they assigned (based on the date of the call in the transcript)
            -  can you share with me the more details and context and relevant snippets from the transcript

            Important notes: 
            - Only use the call transcripts provided. 
            - List the actions in reverse chronological order.
            - Do NOT Hallunicate any information. 
            - Do NOT make up any action items. 
            - Do NOT make up any information. 
            - Do NOT make up any details. 
            - Do NOT make up any context. 
            - Do NOT make up any snippets from the transcript. 
            - Do NOT make up any information. 
            
            Format the response as a JSON object with the following structure:
            {{
                "action_items": [
                    {{
                        "action": "description of the action",
                        "owner": "person responsible",
                        "due_date": "due date if mentioned",
                        "priority": "High/Medium/Low",
                        "assigned_date": "date of assignment",
                        "snippets": "snippets from the transcript"
                    }}
                ]
            }}
            
            Transcript:
            {transcript_text}
            """
            
            response = self._make_request(prompt)
            
            # Try to parse JSON response
            try:
                # Extract JSON from the response (it might be wrapped in markdown)
                content = response['content']
                
                # Remove markdown code blocks if present
                if content.startswith('```json'):
                    content = content.replace('```json', '').replace('```', '').strip()
                elif content.startswith('```'):
                    content = content.replace('```', '').strip()
                
                log_debug(f"Parsing action items JSON: {content[:200]}...")
                
                action_items_data = json.loads(content)
                action_items = action_items_data.get('action_items', [])
                
                log_debug(f"Successfully parsed {len(action_items)} action items")
                
                return {
                    'success': True,
                    'action_items': action_items,
                    'usage': response['usage']
                }
            except json.JSONDecodeError as e:
                log_warning(f"Failed to parse JSON response: {e}")
                log_debug(f"Raw response content: {response['content']}")
                # If JSON parsing fails, return the raw text
                return {
                    'success': True,
                    'action_items': [],
                    'raw_response': response['content'],
                    'usage': response['usage']
                }
                
        except Exception as e:
            log_error(f"Error extracting action items: {e}")
            return {
                'success': False,
                'error': str(e),
                'action_items': []
            }
    
    def analyze_sentiment(self, transcript_text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of the transcript.
        
        Args:
            transcript_text: The transcript text to analyze
            
        Returns:
            Sentiment analysis dictionary
        """
        try:
            prompt = f"""
            Please analyze the sentiment of the following call transcript.
            Provide a comprehensive sentiment analysis including:
            
            1. Overall sentiment (Positive/Neutral/Negative)
            2. Confidence level (0-100%)
            3. Key sentiment indicators (specific phrases or moments)
            4. Engagement level (High/Medium/Low)
            5. Sentiment changes throughout the call
            6. Recommendations based on sentiment
            
            Format the response as a JSON object:
            {{
                "overall_sentiment": "Positive/Neutral/Negative",
                "confidence": 85,
                "key_indicators": ["phrase1", "phrase2"],
                "engagement_level": "High/Medium/Low",
                "sentiment_changes": "description of changes",
                "recommendations": ["rec1", "rec2"]
            }}
            
            Transcript:
            {transcript_text}
            """
            
            response = self._make_request(prompt)
            
            # Try to parse JSON response
            try:
                # Extract JSON from the response (it might be wrapped in markdown)
                content = response['content']
                
                # Remove markdown code blocks if present
                if content.startswith('```json'):
                    content = content.replace('```json', '').replace('```', '').strip()
                elif content.startswith('```'):
                    content = content.replace('```', '').strip()
                
                log_debug(f"Parsing sentiment JSON: {content[:200]}...")
                
                sentiment_data = json.loads(content)
                
                log_debug(f"Successfully parsed sentiment data: {list(sentiment_data.keys())}")
                
                return {
                    'success': True,
                    'sentiment': sentiment_data,
                    'usage': response['usage']
                }
            except json.JSONDecodeError as e:
                log_warning(f"Failed to parse sentiment JSON response: {e}")
                log_debug(f"Raw sentiment response content: {response['content']}")
                # If JSON parsing fails, return the raw text
                return {
                    'success': True,
                    'sentiment': {},
                    'raw_response': response['content'],
                    'usage': response['usage']
                }
                
        except Exception as e:
            log_error(f"Error analyzing sentiment: {e}")
            return {
                'success': False,
                'error': str(e),
                'sentiment': {}
            }
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """
        Get usage statistics for the client.
        
        Returns:
            Usage statistics dictionary
        """
        return {
            'total_requests': self.total_requests,
            'total_tokens_used': self.total_tokens_used,
            'model': self.model,
            'fallback_model': self.fallback_model
        } 