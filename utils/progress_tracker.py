"""
Progress tracking module for maintaining project documentation.
Provides functions to update various documentation files programmatically.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import re


class ProgressTracker:
    """Manages project documentation and progress tracking."""
    
    def __init__(self, docs_dir: str = "docs"):
        """Initialize the progress tracker with documentation directory."""
        self.docs_dir = Path(docs_dir)
        self.ensure_docs_exist()
    
    def ensure_docs_exist(self):
        """Ensure all documentation files exist."""
        self.docs_dir.mkdir(exist_ok=True)
        
        files = {
            "CONTEXT.md": "# Project Context\n\n## Overview\n\n## Current State\n\n## Architecture\n\n",
            "PROGRESS.md": "# Development Progress Log\n\n## Progress Entries\n\n",
            "TODO.md": "# Project TODO List\n\n## Phase 1: Foundation & Architecture\n\n",
            "DECISIONS.md": "# Technical Decisions Log\n\n## Decisions Made\n\n",
            "ISSUES.md": "# Known Issues & Blockers\n\n## Current Issues\n\n",
            "SETUP.md": "# Development Setup Guide\n\n## Prerequisites\n\n"
        }
        
        for filename, default_content in files.items():
            filepath = self.docs_dir / filename
            if not filepath.exists():
                filepath.write_text(default_content)
    
    def update_progress(self, phase: str, task: str, status: str, notes: str = "") -> bool:
        """
        Log completed work to PROGRESS.md.
        
        Args:
            phase: Development phase (e.g., "Infrastructure", "Refactoring")
            task: Task description
            status: Status of the task (e.g., "completed", "in_progress", "blocked")
            notes: Additional notes or context
            
        Returns:
            bool: Success status
        """
        try:
            progress_file = self.docs_dir / "PROGRESS.md"
            content = progress_file.read_text()
            
            # Create new entry
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            entry = f"\n### {timestamp} - {task}\n"
            entry += f"**Phase**: {phase}  \n"
            entry += f"**Status**: {status}  \n"
            if notes:
                entry += f"**Notes**: {notes}\n"
            entry += "\n---\n"
            
            # Insert after "## Progress Entries" section
            insertion_point = content.find("## Progress Entries")
            if insertion_point != -1:
                # Find the next line after the section header
                next_line = content.find("\n", insertion_point) + 1
                content = content[:next_line] + entry + content[next_line:]
            else:
                content += entry
            
            progress_file.write_text(content)
            return True
            
        except Exception as e:
            print(f"Error updating progress: {e}")
            return False
    
    def add_todo(self, item: str, priority: str = "Medium", category: str = "General") -> bool:
        """
        Add new task to TODO.md.
        
        Args:
            item: Task description
            priority: Priority level (Critical/High/Medium/Low)
            category: Category or phase for the task
            
        Returns:
            bool: Success status
        """
        try:
            todo_file = self.docs_dir / "TODO.md"
            content = todo_file.read_text()
            
            # Map priority to emoji
            priority_emoji = {
                "Critical": "🔴",
                "High": "🟡",
                "Medium": "🟢",
                "Low": "🔵"
            }
            
            emoji = priority_emoji.get(priority, "🟢")
            
            # Create new todo entry
            entry = f"- [ ] {item} (Added: {datetime.now().strftime('%Y-%m-%d')})\n"
            
            # Find the appropriate section
            section_pattern = f"### {emoji} {priority}"
            section_start = content.find(section_pattern)
            
            if section_start != -1:
                # Find the next line after the section header
                next_line = content.find("\n", section_start) + 1
                # Find the end of this section (next ### or end of file)
                next_section = content.find("\n### ", next_line)
                if next_section == -1:
                    next_section = len(content)
                
                # Insert at the end of this priority section
                content = content[:next_section] + entry + content[next_section:]
            else:
                # Add new section if it doesn't exist
                content += f"\n### {emoji} {priority}\n{entry}\n"
            
            todo_file.write_text(content)
            return True
            
        except Exception as e:
            print(f"Error adding todo: {e}")
            return False
    
    def update_context(self, section: str, content: str) -> bool:
        """
        Update project context in CONTEXT.md.
        
        Args:
            section: Section to update (e.g., "Current State", "Architecture")
            content: New content for the section
            
        Returns:
            bool: Success status
        """
        try:
            context_file = self.docs_dir / "CONTEXT.md"
            file_content = context_file.read_text()
            
            # Update the Last Updated timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d")
            file_content = re.sub(
                r'\*\*Last Updated\*\*: \d{4}-\d{2}-\d{2}',
                f'**Last Updated**: {timestamp}',
                file_content
            )
            
            # Find and update the section
            section_pattern = f"## {section}"
            section_start = file_content.find(section_pattern)
            
            if section_start != -1:
                # Find the next section (## ) or end of file
                next_section = file_content.find("\n## ", section_start + 1)
                if next_section == -1:
                    next_section = len(file_content)
                
                # Replace section content
                section_header = file_content[section_start:file_content.find("\n", section_start)]
                new_section = f"{section_header}\n{content}\n"
                file_content = file_content[:section_start] + new_section + file_content[next_section:]
            else:
                # Add new section if it doesn't exist
                file_content += f"\n## {section}\n{content}\n"
            
            context_file.write_text(file_content)
            return True
            
        except Exception as e:
            print(f"Error updating context: {e}")
            return False
    
    def log_decision(self, decision: str, reasoning: str, alternatives: List[Dict[str, str]] = None) -> bool:
        """
        Record technical decision in DECISIONS.md.
        
        Args:
            decision: What was decided
            reasoning: Why this decision was made
            alternatives: List of alternatives considered with reasons for rejection
            
        Returns:
            bool: Success status
        """
        try:
            decisions_file = self.docs_dir / "DECISIONS.md"
            content = decisions_file.read_text()
            
            # Create new decision entry
            timestamp = datetime.now().strftime("%Y-%m-%d")
            entry = f"\n### {timestamp} - {decision}\n"
            entry += "**Status**: Approved  \n"
            entry += "**Category**: Architecture  \n"
            entry += f"**Decision**: {decision}  \n"
            entry += f"**Reasoning**: {reasoning}  \n"
            
            if alternatives:
                entry += "**Alternatives Considered**:\n"
                for i, alt in enumerate(alternatives, 1):
                    entry += f"{i}. {alt.get('option', 'Unknown')} - {alt.get('reason', 'No reason provided')}\n"
            
            entry += "\n---\n"
            
            # Insert after "## Decisions Made" section
            insertion_point = content.find("## Decisions Made")
            if insertion_point != -1:
                next_line = content.find("\n", insertion_point) + 1
                content = content[:next_line] + entry + content[next_line:]
            else:
                content += entry
            
            decisions_file.write_text(content)
            return True
            
        except Exception as e:
            print(f"Error logging decision: {e}")
            return False
    
    def save_snapshot(self) -> str:
        """
        Create comprehensive project state dump.
        
        Returns:
            str: Path to snapshot file
        """
        try:
            # Create snapshots directory
            snapshots_dir = self.docs_dir / "snapshots"
            snapshots_dir.mkdir(exist_ok=True)
            
            # Generate snapshot filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_file = snapshots_dir / f"snapshot_{timestamp}.json"
            
            # Collect all documentation content
            snapshot_data = {
                "timestamp": datetime.now().isoformat(),
                "documentation": {}
            }
            
            # Read all documentation files
            for doc_file in self.docs_dir.glob("*.md"):
                if doc_file.is_file():
                    snapshot_data["documentation"][doc_file.name] = doc_file.read_text()
            
            # Save snapshot
            with open(snapshot_file, 'w') as f:
                json.dump(snapshot_data, f, indent=2)
            
            # Also create a markdown summary
            summary_file = snapshots_dir / f"summary_{timestamp}.md"
            summary_content = f"# Project Snapshot - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # Extract key information from each doc
            if "CONTEXT.md" in snapshot_data["documentation"]:
                context = snapshot_data["documentation"]["CONTEXT.md"]
                state_match = re.search(r'## Current State\n(.*?)\n##', context, re.DOTALL)
                if state_match:
                    summary_content += "## Current State\n" + state_match.group(1).strip() + "\n\n"
            
            if "TODO.md" in snapshot_data["documentation"]:
                todo = snapshot_data["documentation"]["TODO.md"]
                # Count todos
                open_todos = len(re.findall(r'- \[ \]', todo))
                completed_todos = len(re.findall(r'- \[x\]', todo))
                summary_content += f"## TODO Summary\n- Open: {open_todos}\n- Completed: {completed_todos}\n\n"
            
            if "PROGRESS.md" in snapshot_data["documentation"]:
                progress = snapshot_data["documentation"]["PROGRESS.md"]
                # Get latest entry
                latest_match = re.search(r'### (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) - ([^\n]+)', progress)
                if latest_match:
                    summary_content += f"## Latest Progress\n- {latest_match.group(1)}: {latest_match.group(2)}\n\n"
            
            summary_file.write_text(summary_content)
            
            return str(snapshot_file)
            
        except Exception as e:
            print(f"Error creating snapshot: {e}")
            return ""
    
    def get_status_summary(self) -> Dict[str, Any]:
        """
        Get current project status summary.
        
        Returns:
            dict: Summary of project status
        """
        summary = {
            "last_updated": None,
            "todos": {"open": 0, "completed": 0},
            "recent_progress": [],
            "open_issues": 0,
            "decisions_made": 0
        }
        
        try:
            # Parse TODO.md
            todo_file = self.docs_dir / "TODO.md"
            if todo_file.exists():
                todo_content = todo_file.read_text()
                summary["todos"]["open"] = len(re.findall(r'- \[ \]', todo_content))
                summary["todos"]["completed"] = len(re.findall(r'- \[x\]', todo_content))
            
            # Parse PROGRESS.md
            progress_file = self.docs_dir / "PROGRESS.md"
            if progress_file.exists():
                progress_content = progress_file.read_text()
                progress_entries = re.findall(r'### (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) - ([^\n]+)', progress_content)
                summary["recent_progress"] = progress_entries[:5]  # Last 5 entries
            
            # Parse ISSUES.md
            issues_file = self.docs_dir / "ISSUES.md"
            if issues_file.exists():
                issues_content = issues_file.read_text()
                summary["open_issues"] = len(re.findall(r'\*\*Status\*\*: Open', issues_content))
            
            # Parse DECISIONS.md
            decisions_file = self.docs_dir / "DECISIONS.md"
            if decisions_file.exists():
                decisions_content = decisions_file.read_text()
                summary["decisions_made"] = len(re.findall(r'### \d{4}-\d{2}-\d{2} -', decisions_content))
            
            # Get last updated from CONTEXT.md
            context_file = self.docs_dir / "CONTEXT.md"
            if context_file.exists():
                context_content = context_file.read_text()
                updated_match = re.search(r'\*\*Last Updated\*\*: (\d{4}-\d{2}-\d{2})', context_content)
                if updated_match:
                    summary["last_updated"] = updated_match.group(1)
            
        except Exception as e:
            print(f"Error getting status summary: {e}")
        
        return summary


# Convenience functions for direct use
_tracker = None

def get_tracker() -> ProgressTracker:
    """Get or create the global progress tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = ProgressTracker()
    return _tracker


def update_progress(phase: str, task: str, status: str, notes: str = "") -> bool:
    """Update progress log."""
    return get_tracker().update_progress(phase, task, status, notes)


def add_todo(item: str, priority: str = "Medium", category: str = "General") -> bool:
    """Add new todo item."""
    return get_tracker().add_todo(item, priority, category)


def update_context(section: str, content: str) -> bool:
    """Update project context."""
    return get_tracker().update_context(section, content)


def log_decision(decision: str, reasoning: str, alternatives: List[Dict[str, str]] = None) -> bool:
    """Log technical decision."""
    return get_tracker().log_decision(decision, reasoning, alternatives)


def save_snapshot() -> str:
    """Save project snapshot."""
    return get_tracker().save_snapshot()


def get_status_summary() -> Dict[str, Any]:
    """Get project status summary."""
    return get_tracker().get_status_summary()


if __name__ == "__main__":
    # Example usage
    tracker = ProgressTracker()
    
    # Test progress update
    tracker.update_progress(
        phase="Infrastructure",
        task="Created progress tracking system",
        status="completed",
        notes="Implemented all core tracking functions"
    )
    
    # Test adding todo
    tracker.add_todo(
        item="Add unit tests for progress tracker",
        priority="High",
        category="Testing"
    )
    
    # Test context update
    tracker.update_context(
        section="Current State",
        content="Progress tracking system implemented. Ready for CLI integration."
    )
    
    # Test decision logging
    tracker.log_decision(
        decision="Use JSON for snapshot storage",
        reasoning="Simple, portable, and human-readable format for state preservation",
        alternatives=[
            {"option": "SQLite database", "reason": "Overkill for simple snapshots"},
            {"option": "Pickle files", "reason": "Not human-readable, version compatibility issues"}
        ]
    )
    
    # Test snapshot
    snapshot_path = tracker.save_snapshot()
    print(f"Snapshot saved to: {snapshot_path}")
    
    # Test status summary
    summary = tracker.get_status_summary()
    print(f"Project Status: {json.dumps(summary, indent=2)}")