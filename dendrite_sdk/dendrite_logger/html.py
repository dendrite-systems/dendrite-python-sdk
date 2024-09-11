import json
from typing import List, Dict, Any


def create_dashboard(input_file: str, output_file: str):
    """Create the dashboard HTML file from the input JSON file."""
    with open(input_file, "r") as f:
        data = json.load(f)

    html_content = generate_html(data)

    with open(output_file, "w") as f:
        f.write(html_content)


def generate_html(data: List[Dict[str, Any]]) -> str:
    """Generate HTML content for the dashboard."""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DendriteLogger Dashboard</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f4f4f4;
            }}
            h1 {{
                text-align: center;
                color: #2c3e50;
            }}
            .context {{
                background-color: #fff;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 20px;
                overflow: hidden;
            }}
            .context-header {{
                background-color: #3498db;
                color: #fff;
                padding: 10px 20px;
                cursor: pointer;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .context-content {{
                padding: 20px;
                display: none;
            }}
            .event {{
                background-color: #ecf0f1;
                border-radius: 4px;
                padding: 10px;
                margin-bottom: 10px;
            }}
            .event-header {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 5px;
            }}
            .event-type {{
                font-weight: bold;
                color: #e74c3c;
            }}
            .event-time {{
                font-size: 0.8em;
                color: #95a5a6;
            }}
            .event-image {{
                max-width: 100%;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <h1>DendriteLogger Dashboard</h1>
        <div id="dashboard"></div>
        <script>
            const data = {json.dumps(data)};
            
            function formatTime(timestamp) {{
                return new Date(timestamp * 1000).toLocaleString();
            }}
            
            function toggleContext(contextId) {{
                const content = document.getElementById(contextId);
                content.style.display = content.style.display === 'none' ? 'block' : 'none';
            }}
            
            function createContextElement(context, index) {{
                const contextElement = document.createElement('div');
                contextElement.className = 'context';
                const contextId = `context-${{index}}`;
                
                contextElement.innerHTML = `
                    <div class="context-header" onclick="toggleContext('${{contextId}}')">
                        <span>${{context.name}}</span>
                        <span>Duration: ${{context.elapsed_time.toFixed(2)}}s</span>
                    </div>
                    <div id="${{contextId}}" class="context-content">
                        <p>Start: ${{formatTime(context.start_time)}}</p>
                        <p>End: ${{formatTime(context.end_time)}}</p>
                        <h3>Events:</h3>
                        ${{context.events.map(event => `
                            <div class="event">
                                <div class="event-header">
                                    <span class="event-type">${{event.type}}</span>
                                    <span class="event-time">${{formatTime(event.timestamp)}}</span>
                                </div>
                                <div>${{event.message}}</div>
                                ${{Object.entries(event.metadata).map(([key, value]) => `
                                    <div><strong>${{key}}:</strong> ${{value}}</div>
                                `).join('')}}
                                ${{event.image_base64 ? `<img src="data:image/png;base64,${{event.image_base64}}" class="event-image" alt="Event Image">` : ''}}
                            </div>
                        `).join('')}}
                    </div>
                `;
                
                return contextElement;
            }}
            
            const dashboard = document.getElementById('dashboard');
            data.forEach((context, index) => {{
                dashboard.appendChild(createContextElement(context, index));
            }});
        </script>
    </body>
    </html>
    """

    return html_content


if __name__ == "__main__":
    create_dashboard("dendrite_log.json", "dendrite_log.html")
