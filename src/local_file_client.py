"""
Local File Output Client for semgrep_pov_assistant.

This module provides functionality to create and save analysis results
as local files instead of using Google Drive APIs.
"""

import os
import json
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from pathlib import Path
import logging

from .utils.logger import get_logger, log_error, log_warning, log_info, log_debug

logger = get_logger()

class LocalFileClient:
    """
    Local file output client for creating and saving analysis results.
    
    This class provides methods for creating local files with the analysis
    results from call transcripts, avoiding Google Drive API issues.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the local file client.
        
        Args:
            config: Configuration dictionary with output settings
        """
        self.config = config or {}
        
        # Output settings
        self.output_dir = self.config.get('paths', {}).get('output_dir', 'data/output')
        self.create_subdirectories = True  # Always create subdirectories for local file output
        
        # Ensure output directory exists
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        log_info("Local file client initialized successfully")
    
    def create_call_summary_file(self, call_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Create a call summary file locally.
        
        Args:
            call_data: Call analysis data
            filename: Optional filename (if None, auto-generates)
            
        Returns:
            Path to the created file
        """
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"call_summary_{timestamp}.txt"
            
            # Create subdirectory for this analysis if enabled
            if self.create_subdirectories:
                analysis_dir = Path(self.output_dir) / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                analysis_dir.mkdir(parents=True, exist_ok=True)
                file_path = analysis_dir / filename
            else:
                file_path = Path(self.output_dir) / filename
            
            # Build content
            content = self._build_call_summary_content(call_data)
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            log_info(f"Created call summary file: {file_path}")
            return str(file_path)
            
        except Exception as e:
            log_error(f"Failed to create call summary file: {e}")
            raise
    
    def create_json_analysis_file(self, call_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Create a JSON analysis file locally.
        
        Args:
            call_data: Call analysis data
            filename: Optional filename (if None, auto-generates)
            
        Returns:
            Path to the created file
        """
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"call_analysis_{timestamp}.json"
            
            # Create subdirectory for this analysis if enabled
            if self.create_subdirectories:
                analysis_dir = Path(self.output_dir) / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                analysis_dir.mkdir(parents=True, exist_ok=True)
                file_path = analysis_dir / filename
            else:
                file_path = Path(self.output_dir) / filename
            
            # Write JSON file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(call_data, f, indent=2, ensure_ascii=False)
            
            log_info(f"Created JSON analysis file: {file_path}")
            return str(file_path)
            
        except Exception as e:
            log_error(f"Failed to create JSON analysis file: {e}")
            raise
    
    def create_action_items_file(self, action_items: List[Dict[str, str]], filename: Optional[str] = None) -> str:
        """
        Create an action items file locally.
        
        Args:
            action_items: List of action item dictionaries
            filename: Optional filename (if None, auto-generates)
            
        Returns:
            Path to the created file
        """
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"action_items_{timestamp}.txt"
            
            # Create subdirectory for this analysis if enabled
            if self.create_subdirectories:
                analysis_dir = Path(self.output_dir) / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                analysis_dir.mkdir(parents=True, exist_ok=True)
                file_path = analysis_dir / filename
            else:
                file_path = Path(self.output_dir) / filename
            
            # Build content
            content = self._build_action_items_content(action_items)
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            log_info(f"Created action items file: {file_path}")
            return str(file_path)
            
        except Exception as e:
            log_error(f"Failed to create action items file: {e}")
            raise
    
    def create_sentiment_analysis_file(self, sentiment_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Create a sentiment analysis file locally.
        
        Args:
            sentiment_data: Sentiment analysis data
            filename: Optional filename (if None, auto-generates)
            
        Returns:
            Path to the created file
        """
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"sentiment_analysis_{timestamp}.txt"
            
            # Create subdirectory for this analysis if enabled
            if self.create_subdirectories:
                analysis_dir = Path(self.output_dir) / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                analysis_dir.mkdir(parents=True, exist_ok=True)
                file_path = analysis_dir / filename
            else:
                file_path = Path(self.output_dir) / filename
            
            # Build content
            content = self._build_sentiment_analysis_content(sentiment_data)
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            log_info(f"Created sentiment analysis file: {file_path}")
            return str(file_path)
            
        except Exception as e:
            log_error(f"Failed to create sentiment analysis file: {e}")
            raise
    
    def create_technical_deployment_analysis_file(self, deployment_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Create a technical deployment analysis file locally.
        
        Args:
            deployment_data: Technical deployment analysis data
            filename: Optional custom filename
            
        Returns:
            Path to the created file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"technical_deployment_details_{timestamp}.txt"
        
        # Ensure the output directory exists
        output_dir = Path(self.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create timestamped subdirectory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        subdir = output_dir / f"analysis_{timestamp}"
        subdir.mkdir(parents=True, exist_ok=True)
        
        # Create the file path
        file_path = subdir / filename
        
        # Build the content
        content = self._build_technical_deployment_analysis_content(deployment_data)
        
        # Write the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(file_path)

    def create_pov_analysis_file(self, pov_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Create a POV Win/Loss analysis file locally.
        
        Args:
            pov_data: POV analysis data
            filename: Optional filename (if None, auto-generates)
            
        Returns:
            Path to the created file
        """
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"pov_analysis_{timestamp}.txt"
            
            # Create subdirectory for this analysis if enabled
            if self.create_subdirectories:
                analysis_dir = Path(self.output_dir) / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                analysis_dir.mkdir(parents=True, exist_ok=True)
                file_path = analysis_dir / filename
            else:
                file_path = Path(self.output_dir) / filename
            
            # Build content
            content = self._build_pov_analysis_content(pov_data)
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            log_info(f"Created POV analysis file: {file_path}")
            return str(file_path)
            
        except Exception as e:
            log_error(f"Failed to create POV analysis file: {e}")
            raise
    
    def _build_call_summary_content(self, call_data: Dict[str, Any]) -> str:
        """
        Build content for a call summary file.
        
        Args:
            call_data: Call analysis data
            
        Returns:
            Formatted content string
        """
        metadata = call_data.get('metadata', {})
        analysis = call_data.get('analysis', {})
        action_items = call_data.get('action_items', [])
        sentiment_analysis = call_data.get('sentiment_analysis', {})
        
        content = f"""# Call Summary - Semgrep POV Assistant

## Call Details
- Date: {metadata.get('extracted_date', 'Unknown')}
- File: {metadata.get('filename', 'Unknown')}
- Duration: {metadata.get('duration', 'Unknown')}
- Participants: {', '.join(analysis.get('call_overview', {}).get('Participants', []))}

## Executive Summary
{analysis.get('executive_summary', 'No summary available')}

## Key Discussion Points
{self._format_list(analysis.get('key_discussion_points', []))}

## Business Context
{self._format_dict(analysis.get('business_context', {}))}

## Action Items
{self._format_action_items(action_items)}

## Sentiment Analysis
{self._format_sentiment_analysis(sentiment_analysis)}

## Next Steps
{self._format_list(analysis.get('next_steps', []))}

Generated by Semgrep POV Assistant
Timestamp: {datetime.now().isoformat()}
"""
        
        return content
    
    def _build_action_items_content(self, action_items: List[Dict[str, str]]) -> str:
        """
        Build content for action items file.
        
        Args:
            action_items: List of action item dictionaries
            
        Returns:
            Formatted content string
        """
        if not action_items:
            return "No action items identified."
        
        content = f"""# Action Items - Semgrep POV Assistant

## Summary
Total Action Items: {len(action_items)}

## Action Items List
{self._format_action_items(action_items)}

Generated by Semgrep POV Assistant
Timestamp: {datetime.now().isoformat()}
"""
        
        return content
    
    def _build_sentiment_analysis_content(self, sentiment_data: Dict[str, Any]) -> str:
        """
        Build content for sentiment analysis file.
        
        Args:
            sentiment_data: Sentiment analysis data
            
        Returns:
            Formatted content string
        """
        content = []
        content.append("# Sentiment Analysis - Semgrep POV Assistant")
        content.append("")
        
        # Overall sentiment
        overall_sentiment = sentiment_data.get('overall_sentiment', 'Unknown')
        confidence = sentiment_data.get('confidence', 0)
        content.append(f"## Overall Sentiment: {overall_sentiment}")
        content.append(f"**Confidence**: {confidence}%")
        content.append("")
        
        # Key indicators
        key_indicators = sentiment_data.get('key_indicators', [])
        if key_indicators:
            content.append("## Key Sentiment Indicators")
            for indicator in key_indicators:
                content.append(f"- {indicator}")
            content.append("")
        
        # Engagement level
        engagement_level = sentiment_data.get('engagement_level', 'Unknown')
        content.append(f"## Engagement Level: {engagement_level}")
        content.append("")
        
        # Sentiment changes
        sentiment_changes = sentiment_data.get('sentiment_changes', '')
        if sentiment_changes:
            content.append("## Sentiment Changes Throughout Call")
            content.append(sentiment_changes)
            content.append("")
        
        # Recommendations
        recommendations = sentiment_data.get('recommendations', [])
        if recommendations:
            content.append("## Recommendations")
            for recommendation in recommendations:
                content.append(f"- {recommendation}")
            content.append("")
        
        return "\n".join(content)
    
    def _build_pov_analysis_content(self, pov_data: Dict[str, Any]) -> str:
        """
        Build content for POV analysis file.
        
        Args:
            pov_data: POV analysis data
            
        Returns:
            Formatted content string
        """
        content = []
        content.append("# POV Win/Loss Analysis - Semgrep POV Assistant")
        content.append("")
        
        # Win probability
        win_probability = pov_data.get('win_probability', 0)
        reasoning = pov_data.get('probability_reasoning', 'No reasoning provided')
        content.append(f"## Win Probability: {win_probability}%")
        content.append(f"**Reasoning**: {reasoning}")
        content.append("")
        
        # Key positive factors
        positive_factors = pov_data.get('key_positive_factors', [])
        if positive_factors:
            content.append("## Key Positive Factors")
            for factor in positive_factors:
                content.append(f"✅ {factor}")
            content.append("")
        
        # Key risks
        risks = pov_data.get('key_risks', [])
        if risks:
            content.append("## Key Risks")
            for risk in risks:
                content.append(f"⚠️  **{risk.get('risk', 'Unknown risk')}**")
                content.append(f"   - **Severity**: {risk.get('severity', 'Unknown')}")
                content.append(f"   - **Time Open**: {risk.get('time_open', 'Unknown')}")
                content.append(f"   - **Mitigation**: {risk.get('mitigation', 'No mitigation provided')}")
                content.append("")
        
        # Technical win strategy
        tech_strategy = pov_data.get('technical_win_strategy', {})
        if tech_strategy:
            content.append("## Technical Win Strategy")
            
            # Unresolved technical questions
            unresolved_questions = tech_strategy.get('unresolved_technical_questions', [])
            if unresolved_questions:
                content.append("### 📝 Unresolved Technical Questions")
                for question in unresolved_questions:
                    content.append(f"- {question}")
                content.append("")
            
            # Recommended demonstrations
            recommended_demos = tech_strategy.get('recommended_demonstrations', [])
            if recommended_demos:
                content.append("### 🎯 Recommended Demonstrations")
                for demo in recommended_demos:
                    content.append(f"- {demo}")
                content.append("")
            
            # Competitive advantages
            competitive_advantages = tech_strategy.get('competitive_advantages', [])
            if competitive_advantages:
                content.append("### 🏆 Competitive Advantages")
                for advantage in competitive_advantages:
                    content.append(f"- {advantage}")
                content.append("")
        
        # Next steps
        next_steps = pov_data.get('next_steps', [])
        if next_steps:
            content.append("## Recommended Next Steps")
            for step in next_steps:
                content.append(f"📋 {step}")
            content.append("")
        
        # Key transcript snippets
        snippets = pov_data.get('key_transcript_snippets', [])
        if snippets:
            content.append("## Key Transcript Snippets")
            for snippet in snippets:
                content.append(f"### 📄 {snippet.get('call', 'Unknown call')}")
                content.append(f"**Context**: {snippet.get('context', 'No context')}")
                content.append(f"**Quote**: \"{snippet.get('quote', 'No quote')}\"")
                content.append(f"**Significance**: {snippet.get('significance', 'No significance provided')}")
                content.append("")
        
        # Analysis metadata
        if pov_data.get('fallback_analysis'):
            content.append("---")
            content.append("*Note: This analysis was generated using fallback methods due to insufficient data or analysis errors.*")
        
        return "\n".join(content)
    
    def _build_technical_deployment_analysis_content(self, deployment_data: Dict[str, Any]) -> str:
        """
        Build content for technical deployment analysis file.
        
        Args:
            deployment_data: Technical deployment analysis data
            
        Returns:
            Formatted content string
        """
        content = []
        content.append("# Technical Deployment Details - Semgrep POV Assistant")
        content.append("")
        
        # SCM Platform
        scm = deployment_data.get('scm_platform', {})
        if scm:
            content.append("## 📁 Source Code Management (SCM)")
            content.append(f"**Platform**: {scm.get('platform', 'Unknown')}")
            content.append(f"**Deployment Type**: {scm.get('deployment_type', 'Unknown')}")
            content.append(f"**Details**: {scm.get('details', 'No details provided')}")
            if scm.get('evidence'):
                content.append(f"**Evidence**: {scm.get('evidence')}")
            content.append("")
        
        # CI Pipelines
        ci = deployment_data.get('ci_pipelines', {})
        if ci:
            content.append("## 🔄 Continuous Integration (CI) Pipelines")
            content.append(f"**Primary CI**: {ci.get('primary_ci', 'Unknown')}")
            additional_ci = ci.get('additional_ci', [])
            if additional_ci:
                content.append(f"**Additional CI**: {', '.join(additional_ci)}")
            content.append(f"**Details**: {ci.get('details', 'No details provided')}")
            if ci.get('evidence'):
                content.append(f"**Evidence**: {ci.get('evidence')}")
            content.append("")
        
        # Programming Languages
        languages = deployment_data.get('programming_languages', {})
        if languages:
            content.append("## 💻 Programming Languages")
            primary_langs = languages.get('primary_languages', [])
            if primary_langs:
                content.append(f"**Primary Languages**: {', '.join(primary_langs)}")
            poc_langs = languages.get('poc_focus_languages', [])
            if poc_langs:
                content.append(f"**POC Focus Languages**: {', '.join(poc_langs)}")
            content.append(f"**Details**: {languages.get('details', 'No details provided')}")
            if languages.get('evidence'):
                content.append(f"**Evidence**: {languages.get('evidence')}")
            content.append("")
        
        # Integrations
        integrations = deployment_data.get('integrations', {})
        if integrations:
            content.append("## 🔗 Integrations")
            interested = integrations.get('interested_integrations', [])
            if interested:
                content.append(f"**Interested In**: {', '.join(interested)}")
            current = integrations.get('current_integrations', [])
            if current:
                content.append(f"**Current Integrations**: {', '.join(current)}")
            content.append(f"**Details**: {integrations.get('details', 'No details provided')}")
            if integrations.get('evidence'):
                content.append(f"**Evidence**: {integrations.get('evidence')}")
            content.append("")
        
        # Supply Chain Security
        sca = deployment_data.get('supply_chain_security', {})
        if sca:
            content.append("## 📦 Supply Chain Security")
            sca_langs = sca.get('languages_tested', [])
            if sca_langs:
                content.append(f"**Languages Tested**: {', '.join(sca_langs)}")
            package_mgrs = sca.get('package_managers', [])
            if package_mgrs:
                content.append(f"**Package Managers**: {', '.join(package_mgrs)}")
            content.append(f"**Details**: {sca.get('details', 'No details provided')}")
            if sca.get('evidence'):
                content.append(f"**Evidence**: {sca.get('evidence')}")
            content.append("")
        
        # Current Security Tools
        security_tools = deployment_data.get('current_security_tools', {})
        if security_tools:
            content.append("## 🛡️ Current Security Tools")
            content.append(f"**SAST**: {security_tools.get('sast', 'Unknown')}")
            content.append(f"**DAST**: {security_tools.get('dast', 'Unknown')}")
            content.append(f"**SCA**: {security_tools.get('sca', 'Unknown')}")
            content.append(f"**Secrets Detection**: {security_tools.get('secrets_detection', 'Unknown')}")
            content.append(f"**ASPM**: {security_tools.get('aspm', 'Unknown')}")
            content.append(f"**Details**: {security_tools.get('details', 'No details provided')}")
            if security_tools.get('evidence'):
                content.append(f"**Evidence**: {security_tools.get('evidence')}")
            content.append("")
        
        # IDE Environment
        ide = deployment_data.get('ide_environment', {})
        if ide:
            content.append("## 💻 IDE Environment")
            content.append(f"**Primary IDE**: {ide.get('primary_ide', 'Unknown')}")
            additional_tools = ide.get('additional_tools', [])
            if additional_tools:
                content.append(f"**Additional Tools**: {', '.join(additional_tools)}")
            content.append(f"**Details**: {ide.get('details', 'No details provided')}")
            if ide.get('evidence'):
                content.append(f"**Evidence**: {ide.get('evidence')}")
            content.append("")
        
        # Additional Technical Details
        additional_details = deployment_data.get('additional_technical_details', [])
        if additional_details:
            content.append("## 📋 Additional Technical Details")
            for detail in additional_details:
                content.append(f"• {detail}")
            content.append("")
        
        # Deployment Complexity
        complexity = deployment_data.get('deployment_complexity', 'Unknown')
        content.append(f"## 📊 Deployment Complexity")
        content.append(f"**Level**: {complexity}")
        content.append("")
        
        # Migration Considerations
        migration = deployment_data.get('migration_considerations', [])
        if migration:
            content.append("## 🔄 Migration Considerations")
            for consideration in migration:
                content.append(f"• {consideration}")
            content.append("")
        
        # Technical Risks
        risks = deployment_data.get('technical_risks', [])
        if risks:
            content.append("## ⚠️ Technical Risks")
            for risk in risks:
                content.append(f"• {risk}")
            content.append("")
        
        # Recommendations
        recommendations = deployment_data.get('recommendations', [])
        if recommendations:
            content.append("## 💡 Technical Recommendations")
            for rec in recommendations:
                content.append(f"• {rec}")
            content.append("")
        
        # Add note if this was a fallback analysis
        if deployment_data.get('fallback_analysis'):
            content.append("---")
            content.append("*Note: This analysis was generated using fallback methods due to insufficient data or analysis errors.*")
        
        return "\n".join(content)
    
    def _format_action_items(self, action_items: List[Dict[str, str]]) -> str:
        """Format action items for display."""
        if not action_items:
            return "No action items identified."
        
        formatted_items = []
        for i, item in enumerate(action_items, 1):
            formatted_item = f"""
### Action Item {i}
- **Action**: {item.get('action', 'No action specified')}
- **Owner**: {item.get('owner', 'Not assigned')}
- **Due Date**: {item.get('due_date', 'Not specified')}
- **Priority**: {item.get('priority', 'Medium')}
- **Context**: {item.get('context', 'No context provided')}
"""
            formatted_items.append(formatted_item)
        
        return '\n'.join(formatted_items)
    
    def _format_sentiment_analysis(self, sentiment_data: Dict[str, Any]) -> str:
        """Format sentiment analysis for display."""
        if not sentiment_data:
            return "No sentiment analysis available."
        
        return f"""
- Overall Sentiment: {sentiment_data.get('overall_sentiment', 'Unknown')}
- Confidence: {sentiment_data.get('confidence', 'Unknown')}%
- Engagement Level: {sentiment_data.get('engagement_level', 'Unknown')}
- Key Indicators: {', '.join(sentiment_data.get('key_indicators', []))}
"""
    
    def _format_list(self, items: List[str]) -> str:
        """Format a list of items."""
        if not items:
            return "None identified."
        
        return '\n'.join([f"- {item}" for item in items])
    
    def _format_dict(self, data: Dict[str, str]) -> str:
        """Format a dictionary of key-value pairs."""
        if not data:
            return "None identified."
        
        return '\n'.join([f"- {key}: {value}" for key, value in data.items()]) 