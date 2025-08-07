"""
Text processing utilities for semgrep_pov_assistant.

This module provides functions for processing transcript text, including
chunking for context window management, text cleaning, and basic
text analysis features.
"""

import re
import math
from typing import List, Dict, Tuple, Optional, Union
from datetime import datetime, timedelta
import logging

from .logger import get_logger

logger = get_logger()

class TextUtils:
    """Utility class for text processing operations."""
    
    # Common words to ignore in analysis
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
        'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
        'mine', 'yours', 'his', 'hers', 'ours', 'theirs'
    }
    
    # Common transcript artifacts to remove
    TRANSCRIPT_ARTIFACTS = [
        r'\[.*?\]',  # Square brackets content
        r'\(.*?\)',  # Parentheses content (sometimes speaker labels)
        r'Speaker \d+:',  # Speaker labels
        r'Participant \d+:',  # Participant labels
        r'\d{1,2}:\d{2}:\d{2}',  # Timestamps
        r'\d{1,2}:\d{2}',  # Time stamps
    ]
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate the number of tokens in a text string.
        This is a rough estimation based on word count and character count.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        if not text:
            return 0
        
        # Rough estimation: 1 token ≈ 4 characters or 0.75 words
        char_count = len(text)
        word_count = len(text.split())
        
        # Use the more conservative estimate
        estimated_tokens = max(char_count / 4, word_count * 1.3)
        
        return int(estimated_tokens)
    
    @staticmethod
    def chunk_text(text: str, max_tokens: int = 8000, overlap_tokens: int = 500) -> List[str]:
        """
        Split text into chunks that fit within token limits.
        
        Args:
            text: Text to chunk
            max_tokens: Maximum tokens per chunk
            overlap_tokens: Number of tokens to overlap between chunks
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        # If text is small enough, return as single chunk
        estimated_tokens = TextUtils.estimate_tokens(text)
        if estimated_tokens <= max_tokens:
            return [text]
        
        # Split text into sentences first
        sentences = TextUtils.split_into_sentences(text)
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = TextUtils.estimate_tokens(sentence)
            
            # If adding this sentence would exceed the limit
            if current_tokens + sentence_tokens > max_tokens and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text)
                
                # Start new chunk with overlap
                overlap_sentences = []
                overlap_tokens_used = 0
                
                # Add sentences from the end of previous chunk for overlap
                for prev_sentence in reversed(current_chunk):
                    prev_tokens = TextUtils.estimate_tokens(prev_sentence)
                    if overlap_tokens_used + prev_tokens <= overlap_tokens:
                        overlap_sentences.insert(0, prev_sentence)
                        overlap_tokens_used += prev_tokens
                    else:
                        break
                
                current_chunk = overlap_sentences + [sentence]
                current_tokens = sum(TextUtils.estimate_tokens(s) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        # Add the last chunk if it has content
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(chunk_text)
        
        logger.debug(f"Split text into {len(chunks)} chunks")
        return chunks
    
    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """
        Split text into sentences using regex patterns.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        if not text:
            return []
        
        # Pattern to match sentence endings
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
        sentences = re.split(sentence_pattern, text)
        
        # Clean up sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # Minimum sentence length
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    @staticmethod
    def clean_transcript_text(text: str) -> str:
        """
        Clean transcript text by removing artifacts and normalizing.
        
        Args:
            text: Raw transcript text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove common transcript artifacts
        for pattern in TextUtils.TRANSCRIPT_ARTIFACTS:
            text = re.sub(pattern, '', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove lines that are just punctuation or very short
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 3 and not line.isupper():
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    @staticmethod
    def extract_participants(text: str) -> List[str]:
        """
        Extract participant names from transcript text.
        
        Args:
            text: Transcript text
            
        Returns:
            List of participant names
        """
        participants = set()
        
        # Common patterns for speaker identification
        patterns = [
            r'([A-Z][a-z]+ [A-Z][a-z]+):',  # "John Smith:"
            r'([A-Z][a-z]+):',  # "John:"
            r'Speaker ([A-Z][a-z]+):',  # "Speaker John:"
            r'([A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+):',  # "John Michael Smith:"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            participants.update(matches)
        
        return list(participants)
    
    @staticmethod
    def extract_dates(text: str) -> List[str]:
        """
        Extract dates from transcript text.
        
        Args:
            text: Transcript text
            
        Returns:
            List of date strings
        """
        dates = []
        
        # Common date patterns
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{1,2}-\d{1,2}-\d{4}',  # MM-DD-YYYY
            r'\d{1,2}/\d{1,2}/\d{2}',  # MM/DD/YY
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        
        return list(set(dates))  # Remove duplicates
    
    @staticmethod
    def extract_action_items(text: str) -> List[Dict[str, str]]:
        """
        Extract action items from transcript text using keyword patterns.
        
        Args:
            text: Transcript text
            
        Returns:
            List of action item dictionaries
        """
        action_items = []
        
        # Keywords that indicate action items
        action_keywords = [
            'action item', 'todo', 'task', 'follow up', 'next steps',
            'need to', 'will do', 'going to', 'plan to', 'should',
            'must', 'have to', 'responsible for', 'assign'
        ]
        
        # Priority keywords
        priority_keywords = {
            'high': ['urgent', 'critical', 'immediate', 'asap', 'high priority'],
            'medium': ['medium', 'normal', 'standard'],
            'low': ['low', 'when possible', 'non-urgent']
        }
        
        # Split into sentences and check for action items
        sentences = TextUtils.split_into_sentences(text)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Check if sentence contains action keywords
            if any(keyword in sentence_lower for keyword in action_keywords):
                action_item = {
                    'action': sentence.strip(),
                    'priority': 'medium',  # Default priority
                    'owner': '',
                    'due_date': '',
                    'context': ''
                }
                
                # Determine priority
                for priority, keywords in priority_keywords.items():
                    if any(keyword in sentence_lower for keyword in keywords):
                        action_item['priority'] = priority
                        break
                
                # Try to extract owner (person mentioned before the action)
                owner_patterns = [
                    r'([A-Z][a-z]+ [A-Z][a-z]+) (?:will|going to|should|need to)',
                    r'([A-Z][a-z]+) (?:will|going to|should|need to)',
                ]
                
                for pattern in owner_patterns:
                    match = re.search(pattern, sentence)
                    if match:
                        action_item['owner'] = match.group(1)
                        break
                
                # Try to extract due date
                date_patterns = [
                    r'by (\d{1,2}/\d{1,2}/\d{4})',
                    r'by (\d{4}-\d{2}-\d{2})',
                    r'due (\d{1,2}/\d{1,2}/\d{4})',
                    r'(\d{1,2}/\d{1,2}/\d{4})',
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, sentence)
                    if match:
                        action_item['due_date'] = match.group(1)
                        break
                
                action_items.append(action_item)
        
        return action_items
    
    @staticmethod
    def calculate_text_statistics(text: str) -> Dict[str, Union[int, float]]:
        """
        Calculate various text statistics.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with text statistics
        """
        if not text:
            return {
                'characters': 0,
                'words': 0,
                'sentences': 0,
                'paragraphs': 0,
                'estimated_tokens': 0,
                'average_sentence_length': 0,
                'average_word_length': 0
            }
        
        # Basic counts
        char_count = len(text)
        word_count = len(text.split())
        sentence_count = len(TextUtils.split_into_sentences(text))
        paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
        estimated_tokens = TextUtils.estimate_tokens(text)
        
        # Averages
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        avg_word_length = char_count / word_count if word_count > 0 else 0
        
        return {
            'characters': char_count,
            'words': word_count,
            'sentences': sentence_count,
            'paragraphs': paragraph_count,
            'estimated_tokens': estimated_tokens,
            'average_sentence_length': round(avg_sentence_length, 2),
            'average_word_length': round(avg_word_length, 2)
        }
    
    @staticmethod
    def extract_key_phrases(text: str, max_phrases: int = 10) -> List[str]:
        """
        Extract key phrases from text using simple frequency analysis.
        
        Args:
            text: Text to analyze
            max_phrases: Maximum number of phrases to return
            
        Returns:
            List of key phrases
        """
        if not text:
            return []
        
        # Clean and normalize text
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Remove stop words
        words = [word for word in words if word not in TextUtils.STOP_WORDS and len(word) > 2]
        
        # Count word frequencies
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get most frequent words
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        # Return top phrases
        return [word for word, freq in sorted_words[:max_phrases]]
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text for consistent processing.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove punctuation (keep some for context)
        text = re.sub(r'[^\w\s\.\!\?]', '', text)
        
        return text.strip()
    
    @staticmethod
    def merge_chunk_analyses(chunk_analyses: List[Dict]) -> Dict:
        """
        Merge analyses from multiple text chunks into a single analysis.
        
        Args:
            chunk_analyses: List of analysis dictionaries from chunks
            
        Returns:
            Merged analysis dictionary
        """
        if not chunk_analyses:
            return {}
        
        merged = {
            'total_chunks': len(chunk_analyses),
            'combined_text_length': sum(analysis.get('text_length', 0) for analysis in chunk_analyses),
            'all_participants': set(),
            'all_action_items': [],
            'all_dates': set(),
            'key_phrases': {},
            'sentiment_scores': []
        }
        
        # Merge participants
        for analysis in chunk_analyses:
            participants = analysis.get('participants', [])
            merged['all_participants'].update(participants)
        
        # Merge action items
        for analysis in chunk_analyses:
            action_items = analysis.get('action_items', [])
            merged['all_action_items'].extend(action_items)
        
        # Merge dates
        for analysis in chunk_analyses:
            dates = analysis.get('dates', [])
            merged['all_dates'].update(dates)
        
        # Merge key phrases (count frequencies)
        for analysis in chunk_analyses:
            phrases = analysis.get('key_phrases', [])
            for phrase in phrases:
                merged['key_phrases'][phrase] = merged['key_phrases'].get(phrase, 0) + 1
        
        # Convert sets to lists for JSON serialization
        merged['all_participants'] = list(merged['all_participants'])
        merged['all_dates'] = list(merged['all_dates'])
        
        # Sort key phrases by frequency
        merged['key_phrases'] = dict(sorted(
            merged['key_phrases'].items(), 
            key=lambda x: x[1], 
            reverse=True
        ))
        
        return merged 