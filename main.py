#!/usr/bin/env python3
"""
Main CLI entry point for the CFO Forecast tool.
Provides documentation management commands and project utilities.
"""

import argparse
import sys
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from utils.progress_tracker import (
    get_tracker,
    update_progress,
    add_todo,
    update_context,
    log_decision,
    save_snapshot,
    get_status_summary
)
from config.client_context import (
    get_client_context,
    get_current_client,
    set_current_client
)
from importers.factory import (
    preview_csv_file,
    import_csv_file,
    list_supported_formats,
    detect_csv_format
)
from weekly_cash_flow import display_weekly_cash_flow
from services import get_transaction_service
from services.forecast_service import ForecastService
from services.forecast_service_v2 import forecast_service_v2


def cmd_status(args):
    """Show current progress summary."""
    summary = get_status_summary()
    current_client = get_current_client()
    
    print("\n🚀 CFO Forecast Tool - Project Status")
    print("=" * 50)
    print(f"🏢 Current Client: {current_client}")
    
    if summary["last_updated"]:
        print(f"📅 Last Updated: {summary['last_updated']}")
    
    print(f"\n📋 TODOs:")
    print(f"   • Open: {summary['todos']['open']}")
    print(f"   • Completed: {summary['todos']['completed']}")
    
    print(f"\n🐛 Open Issues: {summary['open_issues']}")
    print(f"📐 Decisions Made: {summary['decisions_made']}")
    
    if summary["recent_progress"]:
        print(f"\n📈 Recent Progress:")
        for timestamp, task in summary["recent_progress"]:
            print(f"   • {timestamp}: {task}")
    
    print("\n" + "=" * 50)
    print("💡 Tip: Use --context to see current project state")
    print("         Use --add-todo to quickly add tasks")
    print("         Use --set-client to switch clients")
    print()


def cmd_context(args):
    """Display current project context."""
    context_file = Path("docs/CONTEXT.md")
    
    if not context_file.exists():
        print("❌ Error: CONTEXT.md not found. Run --init to set up documentation.")
        return
    
    print("\n📖 Project Context")
    print("=" * 50)
    
    content = context_file.read_text()
    # Extract key sections
    sections = ["Overview", "Current State", "Architecture", "Current Limitations"]
    
    for section in sections:
        start = content.find(f"## {section}")
        if start != -1:
            end = content.find("\n## ", start + 1)
            if end == -1:
                end = len(content)
            
            section_content = content[start:end].strip()
            print(f"\n{section_content}")
            print("-" * 40)
    
    print("\n💡 Full context available in docs/CONTEXT.md")
    print()


def cmd_add_todo(args):
    """Quick todo addition."""
    task = args.task
    priority = args.priority
    
    if add_todo(task, priority):
        print(f"✅ Added TODO: {task} (Priority: {priority})")
        
        # Show current todo count
        summary = get_status_summary()
        print(f"📋 Total open TODOs: {summary['todos']['open']}")
    else:
        print(f"❌ Failed to add TODO")


def cmd_snapshot(args):
    """Save complete context snapshot."""
    print("📸 Creating project snapshot...")
    
    snapshot_path = save_snapshot()
    
    if snapshot_path:
        print(f"✅ Snapshot saved to: {snapshot_path}")
        
        # Also update progress log
        update_progress(
            phase="Documentation",
            task="Created project snapshot",
            status="completed",
            notes=f"Snapshot saved to {snapshot_path}"
        )
    else:
        print("❌ Failed to create snapshot")


def cmd_log_progress(args):
    """Log progress update."""
    if update_progress(args.phase, args.task, args.status, args.notes):
        print(f"✅ Progress logged: {args.task}")
    else:
        print("❌ Failed to log progress")


def cmd_log_decision(args):
    """Log technical decision."""
    # Parse alternatives if provided
    alternatives = []
    if args.alternatives:
        for alt in args.alternatives:
            parts = alt.split(":", 1)
            if len(parts) == 2:
                alternatives.append({
                    "option": parts[0].strip(),
                    "reason": parts[1].strip()
                })
    
    if log_decision(args.decision, args.reasoning, alternatives):
        print(f"✅ Decision logged: {args.decision}")
    else:
        print("❌ Failed to log decision")


def cmd_init(args):
    """Initialize documentation system."""
    print("🚀 Initializing documentation system...")
    
    tracker = get_tracker()
    tracker.ensure_docs_exist()
    
    # Log the initialization
    update_progress(
        phase="Infrastructure",
        task="Initialized documentation system",
        status="completed",
        notes="Created all documentation files and structure"
    )
    
    print("✅ Documentation system initialized!")
    print("\n📁 Created files:")
    for doc_file in Path("docs").glob("*.md"):
        print(f"   • {doc_file}")
    
    print("\n💡 Next steps:")
    print("   1. Review and update docs/CONTEXT.md with project details")
    print("   2. Use --add-todo to start tracking tasks")
    print("   3. Use --status to check project state")


def cmd_vendor_group_forecast(args):
    """Run the VENDOR GROUP forecasting pipeline (CORRECT WORKFLOW)."""
    client_id = get_current_client()
    print(f"🔮 Running vendor group forecast pipeline for client: {client_id}")
    
    try:
        forecast_service = ForecastService()
        
        print("\n🏃 Starting vendor group forecast pipeline...")
        result = forecast_service.run_vendor_group_forecast_pipeline(client_id)
        
        if result['status'] == 'success':
            print("✅ Vendor group forecast pipeline completed successfully!")
            print(f"⏱️ Duration: {result['duration_seconds']:.2f} seconds")
            
            pattern_results = result['pattern_detection']
            print(f"\n📊 Pattern Detection Results:")
            print(f"   • Processed: {pattern_results['processed']} vendor groups")
            print(f"   • Successful: {pattern_results['successful']} vendor groups")
            
            forecast_summary = result['forecast_summary']
            print(f"\n💰 Forecast Summary:")
            print(f"   • Weeks Generated: {forecast_summary['weeks_generated']}")
            print(f"   • Total Deposits: ${forecast_summary['total_deposits']:,.2f}")
            print(f"   • Total Withdrawals: ${forecast_summary['total_withdrawals']:,.2f}")
            print(f"   • Net Movement: ${forecast_summary['net_movement']:,.2f}")
            
            # Log success
            update_progress(
                phase="Operations",
                task="Completed vendor group forecast pipeline",
                status="completed",
                notes=f"Processed {pattern_results['processed']} groups, generated {forecast_summary['weeks_generated']} weeks"
            )
        else:
            print(f"❌ Vendor group forecast pipeline failed: {result.get('error', 'Unknown error')}")
            
            # Log failure
            update_progress(
                phase="Operations", 
                task="Vendor group forecast pipeline failed",
                status="error",
                notes=result.get('error', 'Unknown error')
            )
            
    except Exception as e:
        print(f"❌ Error running vendor group forecast: {e}")
        update_progress(
            phase="Operations",
            task="Vendor group forecast pipeline error",
            status="error",
            notes=str(e)
        )

def cmd_forecast(args):
    """Run the forecasting pipeline (uses existing system until V2 database is ready)."""
    client_id = get_current_client()
    print(f"🔮 Running forecast pipeline for client: {client_id}")
    
    try:
        # Check if V2 database tables exist
        try:
            from supabase_client import supabase
            supabase.table('vendor_groups').select('*').limit(1).execute()
            v2_available = True
        except:
            v2_available = False
        
        if v2_available:
            # Use V2 system
            print("\n🚀 Using V2 forecasting system...")
            
            # Step 1: Pattern Detection
            print("\n📊 Step 1: Detecting patterns...")
            pattern_result = forecast_service_v2.detect_all_patterns(client_id)
            print(f"✅ Detected patterns for {pattern_result['successful']} vendor groups")
            
            # Step 2: Generate Forecasts
            print("\n📈 Step 2: Generating forecasts...")
            from datetime import date
            start_date = date.today()
            weeks_ahead = args.weeks if hasattr(args, 'weeks') else 13
            
            forecast_result = forecast_service_v2.generate_all_forecasts(
                client_id, start_date=start_date, weeks_ahead=weeks_ahead
            )
            print(f"✅ Generated {forecast_result['generated']} forecast records")
            
            # Step 3: Show Summary
            if forecast_result['generated'] > 0:
                print("\n📋 Forecast Summary:")
                for group in forecast_result['groups'][:5]:  # Show first 5
                    if group['status'] == 'success':
                        print(f"   • {group['group_name']}: {group['forecasts_generated']} forecasts")
                
                # Get weekly summary
                from datetime import timedelta
                summary = forecast_service_v2.get_forecast_summary(
                    client_id, start_date, start_date + timedelta(weeks=1)
                )
                
                if 'error' not in summary:
                    print(f"\n💰 Week 1 Total: ${summary['total_amount']:,.2f}")
        
        else:
            # Use existing system
            print("\n⚠️  V2 database not ready, using existing forecast system...")
            print("💡 To enable V2: create tables from database/create_forecast_tables.sql in Supabase")
            
            forecast_service = ForecastService()
            weeks_ahead = args.weeks if hasattr(args, 'weeks') else 13
            
            # Run existing forecast pipeline
            result = forecast_service.run_full_forecast_pipeline(client_id)
            
            if result['status'] == 'success':
                print("✅ Forecast pipeline completed successfully!")
                print(f"⏱️ Duration: {result['duration_seconds']:.2f} seconds")
                
                pattern_results = result['pattern_detection']
                print(f"\n📊 Pattern Detection Results:")
                print(f"   • Processed: {pattern_results['processed']} vendors")
                print(f"   • Successful: {pattern_results['successful']} vendors")
                
                forecast_summary = result['forecast_summary']
                print(f"\n💰 Forecast Summary:")
                print(f"   • Weeks Generated: {forecast_summary['weeks_generated']}")
                print(f"   • Total Deposits: ${forecast_summary['total_deposits']:,.2f}")
                print(f"   • Total Withdrawals: ${forecast_summary['total_withdrawals']:,.2f}")
                print(f"   • Net Movement: ${forecast_summary['net_movement']:,.2f}")
            else:
                print(f"❌ Forecast pipeline failed: {result.get('error', 'Unknown error')}")
        
        # Log success
        update_progress(
            phase="Operations",
            task="Forecast pipeline completed",
            status="completed",
            notes=f"Used {'V2' if v2_available else 'existing'} forecast system"
        )
        
    except Exception as e:
        print(f"❌ Error in forecast pipeline: {e}")
        update_progress(
            phase="Operations",
            task="Forecast pipeline error",
            status="error",
            notes=str(e)
        )


def cmd_detect_patterns(args):
    """Run pattern detection on vendor groups."""
    client_id = get_current_client()
    print(f"🔍 Running pattern detection for client: {client_id}")
    
    try:
        # Check if V2 is available
        try:
            from supabase_client import supabase
            supabase.table('vendor_groups').select('*').limit(1).execute()
            v2_available = True
        except:
            v2_available = False
        
        if v2_available:
            pattern_result = forecast_service_v2.detect_all_patterns(client_id)
            print(f"✅ Detected patterns for {pattern_result['successful']} vendor groups")
            
            if pattern_result.get('results'):
                print("\nPattern Detection Results:")
                for result in pattern_result['results']:
                    if result['status'] == 'success':
                        pattern = result['pattern']
                        print(f"  • {result['group_name']}: {pattern['frequency']} ({pattern['frequency_confidence']:.2f} confidence)")
        else:
            forecast_service = ForecastService()
            pattern_result = forecast_service.detect_and_update_vendor_patterns(client_id)
            print(f"✅ Detected patterns for {pattern_result['successful']} vendors")
            
            if pattern_result.get('results'):
                print("\nPattern Detection Results:")
                for result in pattern_result['results'][:10]:  # Show first 10
                    if result['status'] == 'success':
                        pattern = result['pattern']
                        confidence = pattern.get('frequency_confidence', pattern.get('confidence', 0.0))
                        print(f"  • {result['display_name']}: {pattern['frequency']} ({confidence:.2f} confidence)")
        
    except Exception as e:
        print(f"❌ Error in pattern detection: {e}")


def cmd_forecast_summary(args):
    """Show forecast summary for current period."""
    client_id = get_current_client()
    print(f"📊 Forecast summary for client: {client_id}")
    
    try:
        from datetime import date, timedelta
        
        # Check if V2 is available
        try:
            from supabase_client import supabase
            supabase.table('vendor_groups').select('*').limit(1).execute()
            v2_available = True
        except:
            v2_available = False
        
        if v2_available:
            start_date = date.today()
            end_date = start_date + timedelta(weeks=13)
            
            summary = forecast_service_v2.get_forecast_summary(client_id, start_date, end_date)
            
            if 'error' not in summary:
                print(f"📅 Date Range: {summary['date_range']}")
                print(f"💰 Total Forecast: ${summary['total_amount']:,.2f}")
                print(f"📝 Forecast Records: {summary['forecast_count']}")
                print(f"🏢 Vendor Groups: {len(summary['vendor_groups'])}")
            else:
                print(f"❌ Error getting forecast summary: {summary['error']}")
        else:
            forecast_service = ForecastService()
            weekly_summary = forecast_service.generate_weekly_forecast_summary(client_id, weeks_ahead=13)
            
            if weekly_summary:
                total_deposits = sum(week['deposits'] for week in weekly_summary)
                total_withdrawals = sum(week['withdrawals'] for week in weekly_summary)
                net_movement = total_deposits - total_withdrawals
                
                print(f"📅 Weeks: {len(weekly_summary)}")
                print(f"💰 Total Deposits: ${total_deposits:,.2f}")
                print(f"💰 Total Withdrawals: ${total_withdrawals:,.2f}")
                print(f"💰 Net Movement: ${net_movement:,.2f}")
            else:
                print("❌ No forecast data available")
        
    except Exception as e:
        print(f"❌ Error getting forecast summary: {e}")


def cmd_override_forecast(args):
    """Manually override a forecast amount."""
    client_id = get_current_client()
    vendor_group, date_str, amount_str = args.override_forecast
    
    try:
        from datetime import datetime
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        new_amount = float(amount_str)
        
        print(f"🔧 Overriding forecast for {vendor_group} on {target_date} to ${new_amount:,.2f}")
        
        # Check if V2 is available
        try:
            from supabase_client import supabase
            supabase.table('vendor_groups').select('*').limit(1).execute()
            v2_available = True
        except:
            v2_available = False
        
        if v2_available:
            result = forecast_service_v2.update_manual_forecast(
                client_id, vendor_group, target_date, new_amount
            )
            
            if result['success']:
                print("✅ Forecast override saved successfully!")
            else:
                print(f"❌ Failed to save override: {result.get('error')}")
        else:
            forecast_service = ForecastService()
            success = forecast_service.create_manual_override(
                client_id, vendor_group, 'amount_change', 
                datetime.combine(target_date, datetime.min.time()),
                new_amount=new_amount,
                reason="Manual override via CLI"
            )
            
            if success:
                print("✅ Forecast override saved successfully!")
            else:
                print("❌ Failed to save forecast override")
        
    except ValueError as e:
        print(f"❌ Invalid date format or amount: {e}")
        print("💡 Use format: --override-forecast 'Vendor Name' '2025-08-04' '42000.00'")
    except Exception as e:
        print(f"❌ Error creating override: {e}")


def cmd_dashboard(args):
    """Launch the Streamlit dashboard."""
    print("🖥️  Launching dashboard...")
    
    dashboard_script = Path("run_dashboard.py")
    if dashboard_script.exists():
        import subprocess
        subprocess.run([sys.executable, str(dashboard_script)])
    else:
        print("❌ Dashboard script not found")
        print("💡 Looking for mapping_review.py...")
        
        mapping_review = Path("mapping_review.py")
        if mapping_review.exists():
            import subprocess
            subprocess.run([sys.executable, "-m", "streamlit", "run", str(mapping_review)])


def cmd_set_client(args):
    """Set the current client context."""
    client_id = args.client_id
    
    if set_current_client(client_id):
        print(f"✅ Client context set to: {client_id}")
        
        # Log the change
        update_progress(
            phase="Client Management",
            task=f"Changed client context to {client_id}",
            status="completed",
            notes=f"Client context updated from CLI"
        )
    else:
        print(f"❌ Failed to set client context to: {client_id}")


def cmd_list_clients(args):
    """List available clients."""
    context = get_client_context()
    clients = context.list_available_clients()
    current = get_current_client()
    
    print("\n📋 Available Clients")
    print("=" * 30)
    
    for client in clients:
        marker = "👉" if client == current else "  "
        print(f"{marker} {client}")
    
    print(f"\n💡 Current client: {current}")
    print("💡 Use --set-client <name> to switch")
    print()


def cmd_create_client(args):
    """Create a new client."""
    client_id = args.client_id
    name = args.name
    
    context = get_client_context()
    
    if context.create_client(client_id, name):
        print(f"✅ Created new client: {client_id}")
        
        # Optionally switch to new client
        if args.switch:
            set_current_client(client_id)
            print(f"✅ Switched to new client: {client_id}")
        
        # Log the creation
        update_progress(
            phase="Client Management",
            task=f"Created new client: {client_id}",
            status="completed",
            notes=f"Client created via CLI with name: {name or client_id}"
        )
    else:
        print(f"❌ Failed to create client: {client_id}")


def cmd_preview_csv(args):
    """Preview a CSV file and detect format."""
    csv_path = args.csv_file
    client_id = get_current_client()
    format_name = getattr(args, 'format', None)
    
    print(f"📄 Previewing CSV: {csv_path}")
    print(f"🏢 Client: {client_id}")
    
    try:
        preview = preview_csv_file(csv_path, client_id, format_name)
        
        if 'error' in preview:
            print(f"❌ Error: {preview['error']}")
            return
        
        print(f"✅ Format detected: {preview['format_detected']}")
        print(f"📊 Total rows: {preview['total_rows']}")
        print(f"📋 Headers: {', '.join(preview['headers'])}")
        
        print(f"\n🔍 Sample data:")
        for i, row in enumerate(preview['sample_rows'][:3], 1):
            print(f"  Row {i}: {dict(list(row.items())[:3])}...")
        
        if preview.get('default_mapping'):
            mapping = preview['default_mapping']
            print(f"\n⚙️ Default column mapping:")
            print(f"  Date: {mapping['date_column']}")
            print(f"  Vendor: {mapping['vendor_column']}")
            print(f"  Amount: {mapping['amount_column']}")
        
        print(f"\n💡 Supported formats: {', '.join(preview.get('available_formats', []))}")
        
    except Exception as e:
        print(f"❌ Error previewing CSV: {e}")


def cmd_import_csv(args):
    """Import a CSV file."""
    csv_path = args.csv_file
    client_id = get_current_client()
    format_name = getattr(args, 'format', None)
    
    print(f"📥 Importing CSV: {csv_path}")
    print(f"🏢 Client: {client_id}")
    
    if format_name:
        print(f"🎯 Using format: {format_name}")
    else:
        print("🔍 Auto-detecting format...")
    
    try:
        # Parse the CSV file
        result = import_csv_file(csv_path, client_id, format_name)
        
        summary = result.get_summary()
        
        if summary['success']:
            print(f"✅ CSV parsing successful!")
            print(f"📄 Transactions parsed: {summary['transactions_imported']}")
            
            if summary['warnings'] > 0:
                print(f"⚠️ Parsing warnings: {summary['warnings']}")
            
            # Save to database
            print(f"💾 Saving transactions to database...")
            transaction_service = get_transaction_service()
            save_result = transaction_service.save_import_result(result, client_id)
            
            if save_result['success']:
                print(f"✅ Import successful!")
                print(f"📊 Transactions imported: {save_result['saved_count']}")
                
                if save_result['duplicate_count'] > 0:
                    print(f"🔄 Duplicates skipped: {save_result['duplicate_count']}")
                
                if save_result.get('errors'):
                    print(f"⚠️ Save errors: {len(save_result['errors'])}")
                    for error in save_result['errors'][:3]:  # Show first 3 errors
                        print(f"  - {error}")
                
                # Log the successful import
                update_progress(
                    phase="Data Import",
                    task=f"Imported {save_result['saved_count']} transactions from CSV",
                    status="completed",
                    notes=f"File: {csv_path}, Format: {format_name or 'auto-detected'}"
                )
                
                print(f"\n💡 Next steps:")
                print(f"  - Review vendor mappings: python main.py --dashboard")
                print(f"  - Run forecasting: python main.py --forecast")
            else:
                print(f"❌ Database import failed!")
                if save_result.get('errors'):
                    for error in save_result['errors'][:5]:
                        print(f"  - {error}")
            
        else:
            print(f"❌ CSV parsing failed!")
            print(f"🐛 Errors: {summary['errors']}")
            
            if result.errors:
                print(f"\nError details:")
                for error in result.errors[:5]:  # Show first 5 errors
                    print(f"  - {error}")
        
    except Exception as e:
        print(f"❌ Error importing CSV: {e}")


def cmd_list_formats(args):
    """List all supported CSV formats."""
    formats = list_supported_formats()
    
    print("\n📋 Supported CSV Formats")
    print("=" * 30)
    
    for fmt in formats:
        print(f"  • {fmt}")
    
    print(f"\n💡 Use --preview-csv to detect format automatically")
    print(f"💡 Use --import-csv --format \"Format Name\" to force specific format")
    print()


def cmd_weekly_view(args):
    """Display weekly cash flow table."""
    client_id = get_current_client()
    weeks = getattr(args, 'weeks', 13)
    
    print(f"💰 Generating {weeks}-week cash flow projection for {client_id}...")
    
    try:
        display_weekly_cash_flow(client_id, weeks)
        
        # Log the generation
        update_progress(
            phase="Reporting",
            task=f"Generated {weeks}-week cash flow table",
            status="completed",
            notes=f"Client: {client_id}"
        )
        
    except Exception as e:
        print(f"❌ Error generating weekly cash flow: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CFO Forecast Tool - Financial forecasting automation with AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --status              # Show project status
  %(prog)s --context             # Display current state
  %(prog)s --add-todo "Fix API rate limiting" --priority High
  %(prog)s --snapshot            # Save project state
  %(prog)s --forecast            # Run forecasting pipeline
  %(prog)s --dashboard           # Launch web dashboard
        """
    )
    
    # Documentation commands
    doc_group = parser.add_argument_group('Documentation Management')
    doc_group.add_argument('--status', action='store_true',
                          help='Show current progress summary')
    doc_group.add_argument('--context', action='store_true',
                          help='Display current project state')
    doc_group.add_argument('--add-todo', dest='task', type=str,
                          help='Quick todo addition')
    doc_group.add_argument('--priority', type=str, default='Medium',
                          choices=['Critical', 'High', 'Medium', 'Low'],
                          help='Priority for new todo (default: Medium)')
    doc_group.add_argument('--snapshot', action='store_true',
                          help='Save complete context snapshot')
    
    # Progress tracking
    progress_group = parser.add_argument_group('Progress Tracking')
    progress_group.add_argument('--log-progress', nargs=4,
                               metavar=('PHASE', 'TASK', 'STATUS', 'NOTES'),
                               help='Log progress update')
    progress_group.add_argument('--log-decision', nargs=2,
                               metavar=('DECISION', 'REASONING'),
                               help='Log technical decision')
    progress_group.add_argument('--alternatives', nargs='*',
                               help='Alternative options (format: "option:reason")')
    
    # Application commands
    app_group = parser.add_argument_group('Application Commands')
    app_group.add_argument('--vendor-group-forecast', action='store_true',
                          help='Run the vendor group forecasting pipeline (RECOMMENDED)')
    app_group.add_argument('--forecast', action='store_true',
                          help='Run the V2 forecasting pipeline')
    app_group.add_argument('--detect-patterns', action='store_true',
                          help='Run pattern detection on vendor groups')
    app_group.add_argument('--dashboard', action='store_true',
                          help='Launch the Streamlit dashboard')
    app_group.add_argument('--weekly-view', action='store_true',
                          help='Display weekly cash flow table')
    app_group.add_argument('--weeks', type=int, default=13,
                          help='Number of weeks to project (default: 13)')
    app_group.add_argument('--forecast-summary', action='store_true',
                          help='Show forecast summary for current period')
    app_group.add_argument('--override-forecast', nargs=3,
                          metavar=('VENDOR_GROUP', 'DATE', 'AMOUNT'),
                          help='Manually override a forecast amount')
    
    # Client management commands
    client_group = parser.add_argument_group('Client Management')
    client_group.add_argument('--set-client', dest='client_id', type=str,
                             help='Set the current client context')
    client_group.add_argument('--list-clients', action='store_true',
                             help='List available clients')
    client_group.add_argument('--create-client', nargs=2,
                             metavar=('CLIENT_ID', 'NAME'),
                             help='Create a new client')
    client_group.add_argument('--switch', action='store_true',
                             help='Switch to newly created client')
    
    # CSV Import commands
    import_group = parser.add_argument_group('CSV Import')
    import_group.add_argument('--preview-csv', dest='csv_file', type=str,
                             help='Preview a CSV file and detect format')
    import_group.add_argument('--import-csv', dest='csv_file_import', type=str,
                             help='Import transactions from CSV file')
    import_group.add_argument('--format', type=str,
                             help='Force specific CSV format (use with --preview-csv or --import-csv)')
    import_group.add_argument('--list-formats', action='store_true',
                             help='List all supported CSV formats')
    
    # Setup commands
    setup_group = parser.add_argument_group('Setup & Maintenance')
    setup_group.add_argument('--init', action='store_true',
                            help='Initialize documentation system')
    
    args = parser.parse_args()
    
    # Execute commands
    if args.status:
        cmd_status(args)
    elif args.context:
        cmd_context(args)
    elif args.task:  # --add-todo
        cmd_add_todo(args)
    elif args.snapshot:
        cmd_snapshot(args)
    elif args.log_progress:
        args.phase, args.task, args.status, args.notes = args.log_progress
        cmd_log_progress(args)
    elif args.log_decision:
        args.decision, args.reasoning = args.log_decision
        cmd_log_decision(args)
    elif args.client_id:  # --set-client
        cmd_set_client(args)
    elif args.list_clients:
        cmd_list_clients(args)
    elif args.create_client:
        args.client_id, args.name = args.create_client
        cmd_create_client(args)
    elif args.csv_file:  # --preview-csv
        cmd_preview_csv(args)
    elif args.csv_file_import:  # --import-csv
        args.csv_file = args.csv_file_import
        cmd_import_csv(args)
    elif args.list_formats:
        cmd_list_formats(args)
    elif args.init:
        cmd_init(args)
    elif getattr(args, 'vendor_group_forecast', False):
        cmd_vendor_group_forecast(args)
    elif args.forecast:
        cmd_forecast(args)
    elif getattr(args, 'detect_patterns', False):
        cmd_detect_patterns(args)
    elif getattr(args, 'forecast_summary', False):
        cmd_forecast_summary(args)
    elif getattr(args, 'override_forecast', False):
        cmd_override_forecast(args)
    elif args.dashboard:
        cmd_dashboard(args)
    elif args.weekly_view:
        cmd_weekly_view(args)
    else:
        # No arguments provided, show help
        parser.print_help()
        print("\n💡 Quick start: python main.py --status")


if __name__ == "__main__":
    main()