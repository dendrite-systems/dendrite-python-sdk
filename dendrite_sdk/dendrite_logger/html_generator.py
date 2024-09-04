import json
from typing import List, Dict, Any
from datetime import datetime

def generate_html(contexts: List[Dict[str, Any]]) -> str:
    """Generate HTML content for the dashboard."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DendriteLogger Dashboard</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f4f4f4;
            }
            h1 {
                text-align: center;
                color: #2c3e50;
            }
            .context {
                background-color: #fff;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 20px;
                padding: 20px;
            }
            .context-header {
                cursor: pointer;
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            .context-name {
                font-size: 1.2em;
                font-weight: bold;
                color: #3498db;
            }
            .context-time {
                font-size: 0.9em;
                color: #7f8c8d;
            }
            .event {
                background-color: #ecf0f1;
                border-radius: 4px;
                padding: 10px;
                margin-bottom: 10px;
            }
            .event-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 5px;
            }
            .event-type {
                font-weight: bold;
                color: #e74c3c;
            }
            .event-time {
                font-size: 0.8em;
                color: #95a5a6;
            }
            .hidden {
                display: none;
            }
        </style>
        <script>
            function toggleContext(contextId) {
                const content = document.getElementById(contextId);
                content.classList.toggle('hidden');
            }
        </script>
    </head>
    <body>
        <h1>DendriteLogger Dashboard</h1>
    """

    for i, context in enumerate(contexts):
        context_id = f"context-{i}"
        html_content += f"""
        <div class="context">
            <div class="context-header" onclick="toggleContext('{context_id}')">
                <span class="context-name">{context['name']}</span>
                <span class="context-time">
                    Start: {datetime.fromtimestamp(context['start_time']).strftime('%Y-%m-%d %H:%M:%S')}
                    | Duration: {context['elapsed_time']}
                </span>
            </div>
            <div id="{context_id}" class="hidden">
        """

        for event in context['events']:
            html_content += f"""
            <div class="event">
                <div class="event-header">
                    <span class="event-type">{event['type']}</span>
                    <span class="event-time">{datetime.fromtimestamp(float(event['timestamp'])).strftime('%Y-%m-%d %H:%M:%S')}</span>
                </div>
                <div>{event['message']}</div>
            </div>
            """

        html_content += "</div></div>"

    html_content += """
    </body>
    </html>
    """

    return html_content

def create_html_dashboard(input_file: str, output_file: str):
    """Create the dashboard HTML file from the input JSON file."""
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    contexts = [parse_context(context_str) for context_str in data]
    html_content = generate_html(contexts)
    
    with open(output_file, 'w') as f:
        f.write(html_content)

def parse_context(context_str: str) -> Dict[str, Any]:
    """Parse the context string into a dictionary."""
    lines = context_str.split('\n')
    context = {}
    context['name'] = lines[0].split('name=')[1].split(',')[0]
    context['start_time'] = float(lines[0].split('start_time=')[1].split(',')[0])
    context['elapsed_time'] = lines[0].split('elapsed_time=')[1].split(',')[0]
    
    events = []
    for line in lines[2:-1]:  # Skip the first two lines and the last line
        event = {}
        parts = line.strip().split(', ')
        for part in parts:
            key, value = part.split('=')
            event[key] = value.strip("'")
        events.append(event)
    
    context['events'] = events
    return context
