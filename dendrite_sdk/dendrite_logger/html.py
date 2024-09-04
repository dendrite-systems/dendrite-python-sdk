import json
from typing import List, Dict, Any

def create_dashboard(input_file: str, output_file: str):
    """Create the dashboard HTML file from the input JSON file."""
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    html_content = generate_html(data)
    
    with open(output_file, 'w') as f:
        f.write(html_content)

def generate_html(data: List[Dict[str, Any]]) -> str:
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
            #dashboard {
                background-color: #fff;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                padding: 20px;
            }
        </style>
    </head>
    <body>
        <h1>DendriteLogger Dashboard</h1>
        <div id="dashboard"></div>
        <script>
            const data = %s;
            
            function formatTime(timestamp) {
                return new Date(timestamp * 1000).toLocaleString();
            }
            
            function createContextElement(context) {
                const contextElement = document.createElement('div');
                contextElement.className = 'context';
                contextElement.innerHTML = `
                    <h2>${context.name}</h2>
                    <p>Start: ${formatTime(context.start_time)}</p>
                    <p>Duration: ${context.elapsed_time.toFixed(2)}s</p>
                    <h3>Events:</h3>
                `;
                
                const eventsList = document.createElement('ul');
                context.events.forEach(event => {
                    const eventItem = document.createElement('li');
                    eventItem.innerHTML = `
                        <strong>${event.type}</strong> - ${event.message}
                        <br>
                        <small>${formatTime(event.timestamp)}</small>
                    `;
                    eventsList.appendChild(eventItem);
                });
                
                contextElement.appendChild(eventsList);
                return contextElement;
            }
            
            const dashboard = document.getElementById('dashboard');
            data.forEach(context => {
                dashboard.appendChild(createContextElement(context));
            });
        </script>
    </body>
    </html>
    """ % json.dumps(data)

    return html_content

if __name__ == "__main__":
    create_dashboard("dendrite_log.json", "dendrite_log.html")
