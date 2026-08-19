import os
import json
import random
import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

VERSION = "1.1.0"

# Model-specific pricing per 1M tokens (from Anthropic API pricing)
# Note: cache writes are priced at the standard 5-minute cache write rate
MODEL_PRICING = {
    'claude-fable-5': {
        'name': 'Claude Fable 5',
        'input_per_1M': 10.00,
        'output_per_1M': 50.00,
        'cache_write_per_1M': 12.50,
        'cache_read_per_1M': 1.00
    },
    'claude-mythos-5': {
        'name': 'Claude Mythos 5',
        'input_per_1M': 10.00,
        'output_per_1M': 50.00,
        'cache_write_per_1M': 12.50,
        'cache_read_per_1M': 1.00
    },
    'claude-opus-5': {
        'name': 'Claude Opus 5',
        'input_per_1M': 5.00,
        'output_per_1M': 25.00,
        'cache_write_per_1M': 6.25,
        'cache_read_per_1M': 0.50
    },
    'claude-opus-4-8': {
        'name': 'Claude Opus 4.8',
        'input_per_1M': 5.00,
        'output_per_1M': 25.00,
        'cache_write_per_1M': 6.25,
        'cache_read_per_1M': 0.50
    },
    'claude-opus-4-7': {
        'name': 'Claude Opus 4.7',
        'input_per_1M': 5.00,
        'output_per_1M': 25.00,
        'cache_write_per_1M': 6.25,
        'cache_read_per_1M': 0.50
    },
    'claude-opus-4-6': {
        'name': 'Claude Opus 4.6',
        'input_per_1M': 5.00,
        'output_per_1M': 25.00,
        'cache_write_per_1M': 6.25,
        'cache_read_per_1M': 0.50
    },
    'claude-opus-4-5': {
        'name': 'Claude Opus 4.5',
        'input_per_1M': 5.00,
        'output_per_1M': 25.00,
        'cache_write_per_1M': 6.25,
        'cache_read_per_1M': 0.50
    },
    'claude-opus-4-1': {
        'name': 'Claude Opus 4.1',
        'input_per_1M': 15.00,
        'output_per_1M': 75.00,
        'cache_write_per_1M': 18.75,
        'cache_read_per_1M': 1.50
    },
    'claude-opus-4': {
        'name': 'Claude Opus 4',
        'input_per_1M': 15.00,
        'output_per_1M': 75.00,
        'cache_write_per_1M': 18.75,
        'cache_read_per_1M': 1.50
    },
    'claude-sonnet-5': {
        'name': 'Claude Sonnet 5',
        'input_per_1M': 2.00,
        'output_per_1M': 10.00,
        'cache_write_per_1M': 2.50,
        'cache_read_per_1M': 0.20
    },
    'claude-sonnet-4-6': {
        'name': 'Claude Sonnet 4.6',
        'input_per_1M': 3.00,
        'output_per_1M': 15.00,
        'cache_write_per_1M': 3.75,
        'cache_read_per_1M': 0.30
    },
    'claude-sonnet-4-5': {
        'name': 'Claude Sonnet 4.5',
        'input_per_1M': 3.00,
        'output_per_1M': 15.00,
        'cache_write_per_1M': 3.75,
        'cache_read_per_1M': 0.30
    },
    'claude-sonnet-4': {
        'name': 'Claude Sonnet 4',
        'input_per_1M': 3.00,
        'output_per_1M': 15.00,
        'cache_write_per_1M': 3.75,
        'cache_read_per_1M': 0.30
    },
    'claude-haiku-4-5': {
        'name': 'Claude Haiku 4.5',
        'input_per_1M': 1.00,
        'output_per_1M': 5.00,
        'cache_write_per_1M': 1.25,
        'cache_read_per_1M': 0.10
    },
    'claude-3-7-sonnet': {
        'name': 'Claude 3.7 Sonnet',
        'input_per_1M': 3.00,
        'output_per_1M': 15.00,
        'cache_write_per_1M': 3.75,
        'cache_read_per_1M': 0.30
    },
    'claude-3-5-sonnet': {
        'name': 'Claude 3.5 Sonnet',
        'input_per_1M': 3.00,
        'output_per_1M': 15.00,
        'cache_write_per_1M': 3.75,
        'cache_read_per_1M': 0.30
    },
    'claude-3-5-haiku': {
        'name': 'Claude 3.5 Haiku',
        'input_per_1M': 0.80,
        'output_per_1M': 4.00,
        'cache_write_per_1M': 1.00,
        'cache_read_per_1M': 0.08
    },
    'other': {
        'name': 'Other Claude Models',
        'input_per_1M': 3.00,  # Default to Sonnet pricing
        'output_per_1M': 15.00,
        'cache_write_per_1M': 3.75,
        'cache_read_per_1M': 0.30
    }
}

def calculate_model_cost(model_totals):
    """
    Calculate cost for each model type with their specific pricing
    """
    total_calculated_cost = 0
    model_costs = {}
    
    for model_type, totals in model_totals.items():
        if totals['count'] > 0:  # Only calculate if model was used
            rates = MODEL_PRICING[model_type]
            calculated_cost = (
                (totals['tokensIn'] / 1_000_000) * rates['input_per_1M'] +
                (totals['tokensOut'] / 1_000_000) * rates['output_per_1M'] +
                (totals['cacheWrites'] / 1_000_000) * rates['cache_write_per_1M'] +
                (totals['cacheReads'] / 1_000_000) * rates['cache_read_per_1M']
            )
            model_costs[model_type] = {
                'calculated_cost': calculated_cost,
                'rates': rates
            }
            total_calculated_cost += calculated_cost
    
    return model_costs, total_calculated_cost

def calculate_token_usage(base_path, silent=False):
    """
    Calculate total token usage from ui_messages.json files in subdirectories
    that contain Claude Code tasks (filtered by task_metadata.json and model_id)
    """
    # Track totals by model type (one bucket per priced model)
    model_totals = {
        model_type: {
            'tokensIn': 0, 'tokensOut': 0, 'cacheWrites': 0, 'cacheReads': 0, 
            'cost': 0.0, 'count': 0
        }
        for model_type in MODEL_PRICING
    }
    
    file_count = 0
    entry_count = 0
    skipped_count = 0
    timestamps = []
    request_data = []
    
    base_path = Path(base_path)
    
    if not base_path.exists():
        if not silent:
            print(f"Error: Path {base_path} does not exist")
        return model_totals, file_count, entry_count, skipped_count, timestamps, request_data
    
    # Iterate through all subdirectories
    for folder in base_path.iterdir():
        if folder.is_dir():
            json_file = folder / "ui_messages.json"
            metadata_file = folder / "task_metadata.json"
            
            if json_file.exists() and metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    is_claude_code_task = False
                    current_model_type = 'other'
                    
                    if 'model_usage' in metadata:
                        for usage in metadata['model_usage']:
                            if usage.get('model_provider_id') == 'claude-code':
                                is_claude_code_task = True
                                model_id = usage.get('model_id', '')
                                
                                # Match the longest model key first so newer models
                                # (e.g. claude-opus-4-6) are not matched by a shorter
                                # prefix (e.g. claude-opus-4) with different pricing
                                for model_key in sorted(MODEL_PRICING.keys() - {'other'}, key=len, reverse=True):
                                    if model_id.startswith(model_key):
                                        current_model_type = model_key
                                        break
                                break
                    
                    if not is_claude_code_task:
                        skipped_count += 1
                        continue
                        
                except (FileNotFoundError, json.JSONDecodeError, KeyError):
                    skipped_count += 1
                    continue
            else:
                skipped_count += 1
                continue
                
            # Process the ui_messages.json file
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                file_count += 1
                if not silent:
                    print(f"Processing: {json_file}")
                
                for entry in data:
                    if isinstance(entry, dict) and entry.get('type') == 'say' and entry.get('say') == 'api_req_started':
                        try:
                            if 'ts' in entry:
                                timestamps.append(entry['ts'])
                            
                            text_data = json.loads(entry['text'])
                            
                            tokens_in = text_data.get('tokensIn', 0)
                            tokens_out = text_data.get('tokensOut', 0)
                            cache_writes = text_data.get('cacheWrites', 0)
                            cache_reads = text_data.get('cacheReads', 0)
                            cost = text_data.get('cost', 0.0)
                            
                            # Add to model-specific totals
                            model_totals[current_model_type]['tokensIn'] += tokens_in
                            model_totals[current_model_type]['tokensOut'] += tokens_out
                            model_totals[current_model_type]['cacheWrites'] += cache_writes
                            model_totals[current_model_type]['cacheReads'] += cache_reads
                            model_totals[current_model_type]['cost'] += cost
                            model_totals[current_model_type]['count'] += 1
                            
                            entry_count += 1
                            
                            if 'ts' in entry:
                                request_data.append({
                                    'timestamp': entry['ts'],
                                    'tokensIn': tokens_in,
                                    'tokensOut': tokens_out,
                                    'cacheWrites': cache_writes,
                                    'cacheReads': cache_reads,
                                    'cost': cost,
                                    'model_type': current_model_type
                                })
                            
                        except json.JSONDecodeError:
                            continue
                        except (KeyError, TypeError):
                            continue
                            
            except FileNotFoundError:
                if not silent:
                    print(f"Warning: Could not read {json_file}")
            except json.JSONDecodeError:
                if not silent:
                    print(f"Warning: Invalid JSON in {json_file}")
            except Exception as e:
                if not silent:
                    print(f"Error processing {json_file}: {e}")
    
    return model_totals, file_count, entry_count, skipped_count, timestamps, request_data

def calculate_monthly_average(calculated_cost, timestamps):
    if not timestamps:
        return 0, 0, "No usage data found"
    
    from datetime import datetime
    
    dates = [datetime.fromtimestamp(ts / 1000) for ts in timestamps]
    dates.sort()
    
    earliest_date = dates[0]
    latest_date = dates[-1]
    time_span = (latest_date - earliest_date).days
    
    if time_span == 0:
        return calculated_cost * 30, time_span, f"All usage on {earliest_date.strftime('%Y-%m-%d')}"
    
    months_span = time_span / 30.44
    monthly_average = calculated_cost / months_span if months_span > 0 else calculated_cost
    date_range = f"{earliest_date.strftime('%Y-%m-%d')} to {latest_date.strftime('%Y-%m-%d')}"
    
    return monthly_average, time_span, date_range

def calculate_daily_usage_stats(request_data, model_costs):
    """
    Calculate daily usage statistics based on actual request data with model-specific pricing
    """
    if not request_data:
        return {}
    
    from datetime import datetime
    from collections import defaultdict
    
    # Group actual data by date
    daily_tokens_in = defaultdict(int)
    daily_tokens_out = defaultdict(int)
    daily_cache_writes = defaultdict(int)
    daily_cache_reads = defaultdict(int)
    daily_costs = defaultdict(float)
    daily_requests = defaultdict(int)
    
    # Process each request with model-specific pricing
    for request in request_data:
        date = datetime.fromtimestamp(request['timestamp'] / 1000).date()
        model_type = request.get('model_type', 'other')
        
        # Calculate accurate cost using model-specific rates
        if model_type in model_costs:
            rates = model_costs[model_type]['rates']
            accurate_cost = (
                (request['tokensIn'] / 1_000_000) * rates['input_per_1M'] +
                (request['tokensOut'] / 1_000_000) * rates['output_per_1M'] +
                (request['cacheWrites'] / 1_000_000) * rates['cache_write_per_1M'] +
                (request['cacheReads'] / 1_000_000) * rates['cache_read_per_1M']
            )
        else:
            accurate_cost = request['cost']  # Fallback to reported cost
        
        daily_tokens_in[date] += request['tokensIn']
        daily_tokens_out[date] += request['tokensOut']
        daily_cache_writes[date] += request['cacheWrites']
        daily_cache_reads[date] += request['cacheReads']
        daily_costs[date] += accurate_cost
        daily_requests[date] += 1
    
    if not daily_costs:
        return {}
    
    # Calculate total tokens per day (in + out)
    daily_total_tokens = {}
    for date in daily_tokens_in.keys():
        daily_total_tokens[date] = daily_tokens_in[date] + daily_tokens_out[date]
    
    # Calculate statistics based on actual data
    costs = list(daily_costs.values())
    tokens = list(daily_total_tokens.values())
    requests = list(daily_requests.values())
    
    stats = {
        'total_active_days': len(costs),
        'avg_daily_cost': sum(costs) / len(costs),
        'max_daily_cost': max(costs),
        'min_daily_cost': min(costs),
        'avg_daily_tokens': sum(tokens) / len(tokens),
        'max_daily_tokens': max(tokens),
        'avg_daily_requests': sum(requests) / len(requests),
        'max_daily_requests': max(requests),
        'dates': list(daily_costs.keys())
    }
    
    return stats

def get_combined_totals(model_totals):
    """Combine all model totals for display"""
    combined = {
        'tokensIn': sum(m['tokensIn'] for m in model_totals.values()),
        'tokensOut': sum(m['tokensOut'] for m in model_totals.values()),
        'cacheWrites': sum(m['cacheWrites'] for m in model_totals.values()),
        'cacheReads': sum(m['cacheReads'] for m in model_totals.values()),
        'cost': sum(m['cost'] for m in model_totals.values())
    }
    return combined

def calculate_monthly_costs(request_data, model_costs):
    """Calculate monthly cost breakdown from request data"""
    if not request_data:
        return {}
    
    from datetime import datetime
    from collections import defaultdict
    
    monthly_data = defaultdict(lambda: {
        'api_calls': 0,
        'total_tokens': 0,
        'total_cost': 0.0
    })
    
    for request in request_data:
        date = datetime.fromtimestamp(request['timestamp'] / 1000)
        month_key = date.strftime('%Y-%m')  # e.g., "2025-01"
        
        # Calculate accurate cost using model-specific rates
        model_type = request.get('model_type', 'other')
        if model_type in model_costs:
            rates = model_costs[model_type]['rates']
            accurate_cost = (
                (request['tokensIn'] / 1_000_000) * rates['input_per_1M'] +
                (request['tokensOut'] / 1_000_000) * rates['output_per_1M'] +
                (request['cacheWrites'] / 1_000_000) * rates['cache_write_per_1M'] +
                (request['cacheReads'] / 1_000_000) * rates['cache_read_per_1M']
            )
        else:
            accurate_cost = request['cost']  # Fallback to reported cost
        
        monthly_data[month_key]['api_calls'] += 1
        monthly_data[month_key]['total_tokens'] += request['tokensIn'] + request['tokensOut']
        monthly_data[month_key]['total_cost'] += accurate_cost
    
    return dict(monthly_data)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Cline Claude Cost Calculator - Analyze your Claude Code usage with Cline')
    parser.add_argument('-v', '--version', action='version', version=f'CCC {VERSION}')
    parser.add_argument('--export-svg', action='store_true', help='Export output to SVG file')
    parser.add_argument('--export-html', action='store_true', help='Export output to HTML file')
    args = parser.parse_args()
    
    # Enable recording if export is requested
    console = Console(record=True if (args.export_svg or args.export_html) else False)
    
    base_path = os.path.expanduser("~/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/tasks")
    
    # Header
    console.print()
    console.print(Panel.fit("💰 [bold blue]Cline Claude Cost[/bold blue] 💰", 
                          title="[bold green]CCC[/bold green]", 
                          border_style="bright_blue"))
    console.print()
    
    console.print(f"[dim]Base path: {base_path}[/dim]")
    console.print()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Processing files...", total=None)
        model_totals, file_count, entry_count, skipped_count, timestamps, request_data = calculate_token_usage(base_path, silent=True)
        progress.update(task, completed=100)
    
    # Calculate costs for each model
    model_costs, total_calculated_cost = calculate_model_cost(model_totals)
    combined_totals = get_combined_totals(model_totals)
    
    # Calculate monthly average
    monthly_average, time_span, date_range = calculate_monthly_average(total_calculated_cost, timestamps)
    
    # Calculate daily usage statistics based on actual request data
    daily_stats = calculate_daily_usage_stats(request_data, model_costs)
    
    # Model Distribution Table
    if any(m['count'] > 0 for m in model_totals.values()):
        model_table = Table(title="🤖 Model Distribution", box=box.ROUNDED, show_header=True, header_style="bold magenta", width=80)
        model_table.add_column("Model", style="cyan", no_wrap=True)
        model_table.add_column("API Calls", style="bright_white", justify="right")
        model_table.add_column("Tokens", style="bright_white", justify="right")
        model_table.add_column("Cost", style="bright_green", justify="right")
        
        for model_type, totals in model_totals.items():
            if totals['count'] > 0:
                # Generate appropriate model names
                model_name = MODEL_PRICING[model_type]['name']
                    
                total_tokens = totals['tokensIn'] + totals['tokensOut']
                cost = model_costs[model_type]['calculated_cost']
                model_table.add_row(model_name, f"{totals['count']:,}", f"{total_tokens:,}", f"${cost:.4f}")
        
        console.print(model_table)
        console.print()
    
    # Usage Summary Table
    summary_table = Table(title="📊 Usage Summary", box=box.ROUNDED, show_header=True, header_style="bold magenta", width=80)
    summary_table.add_column("Metric", style="cyan", no_wrap=True)
    summary_table.add_column("Value", style="bright_white", justify="right")
    
    summary_table.add_row("Files processed", f"{file_count:,}")
    summary_table.add_row("Files skipped (not Claude Code task)", f"[dim]{skipped_count:,}[/dim]")
    summary_table.add_row("API calls processed", f"{entry_count:,}")
    summary_table.add_row("Input tokens", f"{combined_totals['tokensIn']:,}")
    summary_table.add_row("Output tokens", f"{combined_totals['tokensOut']:,}")
    summary_table.add_row("Cache writes", f"{combined_totals['cacheWrites']:,}")
    summary_table.add_row("Cache reads", f"{combined_totals['cacheReads']:,}")
    
    console.print(summary_table)
    console.print()
    
    # Cost Breakdown by Model
    for model_type, totals in model_totals.items():
        if totals['count'] > 0:
            # Generate appropriate model names
            model_name = MODEL_PRICING[model_type]['name']
                
            rates = model_costs[model_type]['rates']
            
            cost_table = Table(title=f"💸 {model_name} Cost Breakdown", box=box.ROUNDED, show_header=True, header_style="bold green", width=80)
            cost_table.add_column("Token Type", style="cyan", no_wrap=True)
            cost_table.add_column("Count", style="bright_white", justify="right")
            cost_table.add_column("Rate per 1M", style="yellow", justify="right")
            cost_table.add_column("Cost", style="bright_green", justify="right")
            
            input_cost = (totals['tokensIn'] / 1_000_000) * rates['input_per_1M']
            output_cost = (totals['tokensOut'] / 1_000_000) * rates['output_per_1M']
            cache_write_cost = (totals['cacheWrites'] / 1_000_000) * rates['cache_write_per_1M']
            cache_read_cost = (totals['cacheReads'] / 1_000_000) * rates['cache_read_per_1M']
            
            cost_table.add_row("Input tokens", f"{totals['tokensIn']:,}", f"${rates['input_per_1M']:.2f}", f"${input_cost:.4f}")
            cost_table.add_row("Output tokens", f"{totals['tokensOut']:,}", f"${rates['output_per_1M']:.2f}", f"${output_cost:.4f}")
            cost_table.add_row("Cache writes", f"{totals['cacheWrites']:,}", f"${rates['cache_write_per_1M']:.2f}", f"${cache_write_cost:.4f}")
            cost_table.add_row("Cache reads", f"{totals['cacheReads']:,}", f"${rates['cache_read_per_1M']:.2f}", f"${cache_read_cost:.4f}", end_section=True)
            cost_table.add_row(f"[bold]{model_name} TOTAL", "", "", f"[bold bright_green]${model_costs[model_type]['calculated_cost']:.4f}[/bold bright_green]")
            
            console.print(cost_table)
            console.print()
    
    # Combined Total
    if len([m for m in model_totals.values() if m['count'] > 0]) > 1:
        total_table = Table(title="💰 Combined Total", box=box.ROUNDED, show_header=True, header_style="bold red", width=80)
        total_table.add_column("Metric", style="cyan", no_wrap=True)
        total_table.add_column("Value", style="bright_white", justify="right")
        
        total_table.add_row("[bold]TOTAL CALCULATED COST", f"[bold bright_green]${total_calculated_cost:.4f}[/bold bright_green]")
        
        console.print(total_table)
        console.print()

    # Monthly Cost Breakdown
    monthly_costs = calculate_monthly_costs(request_data, model_costs)
    if monthly_costs:
        monthly_table = Table(title="📅 Monthly Cost Breakdown", box=box.ROUNDED, show_header=True, header_style="bold green", width=80)
        monthly_table.add_column("Month", style="cyan", no_wrap=True)
        monthly_table.add_column("API Calls", style="bright_white", justify="right")
        monthly_table.add_column("Total Tokens", style="bright_white", justify="right")
        monthly_table.add_column("Total Cost", style="bright_green", justify="right")
        
        # Sort months chronologically (oldest to newest)
        sorted_months = sorted(monthly_costs.items())
        
        for month, data in sorted_months:
            monthly_table.add_row(
                month,
                f"{data['api_calls']:,}",
                f"{data['total_tokens']:,}",
                f"${data['total_cost']:.4f}"
            )
        
        console.print(monthly_table)
        console.print()

    # Usage Period Panel
    period_content = f"""[bold]Date range:[/bold] {date_range}
[bold]Time span:[/bold] {time_span} days
[bold]📊 Monthly average:[/bold] [bright_green]${monthly_average:.2f}[/bright_green]"""
    
    console.print(Panel(period_content, title="📅 Usage Period", border_style="blue", width=80))
    console.print()
    
    # Daily Usage Analysis
    if daily_stats:
        daily_table = Table(title="📈 Daily Usage Analysis", box=box.ROUNDED, show_header=True, header_style="bold cyan", width=80)
        daily_table.add_column("Metric", style="cyan", no_wrap=True)
        daily_table.add_column("Value", style="bright_white", justify="right")
        
        daily_table.add_row("Active coding days", f"{daily_stats['total_active_days']}")
        daily_table.add_row("Average cost per active day", f"${daily_stats['avg_daily_cost']:.4f}")
        daily_table.add_row("Peak daily cost", f"[bright_red]${daily_stats['max_daily_cost']:.4f}[/bright_red]")
        daily_table.add_row("Average daily tokens", f"{daily_stats['avg_daily_tokens']:,.0f}")
        daily_table.add_row("Peak daily tokens", f"[bright_red]{daily_stats['max_daily_tokens']:,.0f}[/bright_red]")
        daily_table.add_row("Average daily API calls", f"{daily_stats['avg_daily_requests']:.1f}")
        daily_table.add_row("Peak daily API calls", f"[bright_red]{daily_stats['max_daily_requests']}[/bright_red]")
        
        if daily_stats['avg_daily_cost'] > 0:
            peak_vs_avg = ((daily_stats['max_daily_cost'] - daily_stats['avg_daily_cost']) / daily_stats['avg_daily_cost']) * 100
            variation_color = "bright_red" if peak_vs_avg > 100 else "yellow" if peak_vs_avg > 50 else "green"
            daily_table.add_row("Peak day variation", f"[{variation_color}]{peak_vs_avg:.1f}% above average[/{variation_color}]")
        
        console.print(daily_table)
        console.print()
    
    # Additional Statistics
    total_tokens = combined_totals['tokensIn'] + combined_totals['tokensOut']
    total_cache_ops = combined_totals['cacheWrites'] + combined_totals['cacheReads']
    
    additional_table = Table(title="Additional Statistics", box=box.ROUNDED, show_header=True, header_style="bold white", width=80)
    additional_table.add_column("Metric", style="cyan", no_wrap=True)
    additional_table.add_column("Value", style="bright_white", justify="right")
    
    additional_table.add_row("Total tokens (in + out)", f"{total_tokens:,}")
    additional_table.add_row("Total cache operations", f"{total_cache_ops:,}")
    additional_table.add_row("Calendar day average (monthly/30)", f"${monthly_average / 30:.4f}" if monthly_average > 0 else "$0.0000")
    
    if entry_count > 0:
        avg_tokens_per_entry = total_tokens / entry_count
        avg_cost_per_entry = total_calculated_cost / entry_count
        additional_table.add_row("Average tokens per API call", f"{avg_tokens_per_entry:.1f}")
        additional_table.add_row("Average cost per API call", f"${avg_cost_per_entry:.4f}")
    
    console.print(additional_table)
    console.print()

    # Random tip selection
    tips = [
        "💡 Tip: Monitor your daily usage patterns to identify your most productive coding sessions and peak activity periods",
        "💡 Tip: Different Claude models excel at different tasks - track which models you use most for various coding activities",
        "💡 Tip: Use the API call frequency and token patterns above to understand your coding workflow and productivity trends"
    ]
    
    random_tip = random.choice(tips)
    console.print(f"[dim]{random_tip}[/dim]")
    
    # Handle export functionality
    if args.export_svg or args.export_html:
        from datetime import datetime
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        if args.export_svg:
            filename = f"CCC-{current_date}.svg"
            console.save_svg(filename, title="CCC Report")
            console.print(f"\n[green]✅ Report exported to {filename}[/green]")
        
        if args.export_html:
            filename = f"CCC-{current_date}.html"
            console.save_html(filename)
            console.print(f"\n[green]✅ Report exported to {filename}[/green]")

if __name__ == "__main__":
    main()
