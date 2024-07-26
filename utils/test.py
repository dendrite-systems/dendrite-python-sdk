from datetime import datetime
import json

# Sample input string (each line is a cookie)
# input_string = """__ssid	4cd137a8e15407802354191953e1a61	.remitly.com	/	11/07/2025, 21:37:23	37 B			
# c_policy	GDPR	www.remitly.com	/	Session	12 B	✓	✓	
# ci_csrf_input	36f6351e9f33c852c32d	www.remitly.com	/	06/06/2024, 22:05:43	33 B			
# cookie_consent	000	www.remitly.com	/	Session	17 B	✓		
# de_hash	2XxjtCoEyaHLT2x6WPFk6U	www.remitly.com	/	11/07/2025, 20:17:22	29 B	✓		
# de_id	3RoCMHPdtZa0xFnShPviI63x8DYAIJezCmrOQHO1hIo3qnEKvBT4ybEebFwocC4TpS3qJNrrUbEH2DOYMLeNY6UPtkqZDKsc7LiW69VIdRAT	www.remitly.com	/	11/07/2025, 20:17:22	113 B	✓		
# gr	3a4e59de-b950-469b-999e-c34526dcdd77	www.remitly.com	/	11/07/2025, 22:01:43	38 B	✓		
# msub_policy	show%3Dtrue%26preselect%3Dtrue	www.remitly.com	/	Session	41 B	✓	✓	
# oauth_id_token	eyJhbGciOiJSUzI1NiIsImtpZCI6IjZmZmI5ZWI2LTJkNmMtNDJiNi1hYTcxLTJiZGY3OGVjMjVjMiIsInR5cCI6IkpXVCJ9.eyJhdF9oYXNoIjoia25BWnNXdXlUdF93RnlkZW9QRUZjZyIsImF1ZCI6WyIwZDdjYzVjMS02OGFhLTQwNTEtYjI0ZC1kNTUyZmU1Nzg1ZDIiXSwiYXV0aF90aW1lIjoxNzE3NzA0MDk5LCJleHAiOjE3MTc3MDc3MDEsImlhdCI6MTcxNzcwNDEwMSwiaXNzIjoiaHR0cHM6Ly9hdXRoLnJlbWl0bHkuY29tLyIsImp0aSI6ImFhYTJlNWMxLTg3OTgtNDQwZC1iOGFmLTlmNGU1NDM2YjljNCIsInJhdCI6MTcxNzcwNDA5NCwic2lkIjoiNjdiMTZmYTQtNTM2MS00ZjFkLTlhNzUtYjhlMTllNWNmODU5Iiwic3ViIjoicmVtOnRudF9pZF9jb21tb246Y3VzdDpjdXN0X3dhOTVUbVNRdk1oZkNyc05KNE1jancifQ.TG7V2FsyxHmgLvDoncBsMWLJbVJWNst4QBF1uVUdwQVZxf3NCQAmjawDmpKjlUfsEmuKXI976ngPI-YpbE2Pg_0wLvnuWO3pJeD3MDHRkyPXrCyw081wKszDcAwCo681yPDM3N9hIKx8jUdp3xiQ3M08iRT7CCQlAF0lcLSh2cP-xTv17FMdiG7oUWmHZJqsqDTe3n3DnfTCeV2P1YAt19EY4ESpqyiZByZv_z1sLyYAQjV8cYEa-yoKMV5nHIsHml0HPX5i4bYKUa-R0hMz2cX0K54KxGvjciQyhlki2xWb9g-5yKr_x6vBcYM8B5eJhD69rOKbuM2fhaEL1Dtdqt0rQpuf8kSa4BhwKRdk4cEIyUS2hoGDyQcx38fuVGieS2ETFloyiHN0d8rg6q-7MnNyzy8e6P39GgxK3xKxza2c4S99S-HJJzwTm5kpdnBScGPVLxc1ypHkJJbDKmzyWeMaf8aeLtkDdrTzM3bUZB1Rjvjdi05WCHi_GQAwhfKrc58xHs4J5K_9ajAbfq2inFY0X7WgdV0QylLqwLqoCiKRnwBdNih36SxO2Dk3Kb1tc4N0LdCSVV8NykPO3aPB2gR8cJNEOUdXNPRCsxfyWVeJoE6ZBS0jh2INn5FzMnN56UkCuXoKWKkpJGvkr0QgeJ6qRzKXBF6Pm4AsQJAc5JA	www.remitly.com	/	Session	1.25 KB	✓	✓	
# oauth_state	eyJub25jZSI6IjkyZWQ5M2NiMGYyMzYzMWQ2NzM3NWFjN2UzYmNjNGE3IiwidSI6ImFIUjBjSE02THk5M2QzY3VjbVZ0YVhSc2VTNWpiMjB2ZFhNdlpXNHZhRzl0WlhCaFoyVT0iLCJzZW5kaW5nX2NvdW50cnlfY29kZSI6IlVTIn0%3D	www.remitly.com	/	Session	189 B	✓	✓	
# session_data	%5B%5D	www.remitly.com	/	11/07/2025, 22:01:41	18 B	✓	✓	
# token	gjflrfnaoSO88JtJMDG929JoHUX9CKAowk0PfwwJmCd	www.remitly.com	/	Session	48 B	✓		"""

input_string = """__utmt	1	.remitly.com	/	07/06/2024, 15:32:15	7 B			
cookie_consent	111	www.remitly.com	/	Session	17 B			
pm_sub	true	www.remitly.com	/	Session	10 B	✓		
msub_policy	show%3Dtrue%26preselect%3Dtrue	www.remitly.com	/	Session	41 B	✓		
receive_country_code	MEX	www.remitly.com	/	Session	23 B	✓	✓	
c_policy	GDPR	www.remitly.com	/	Session	12 B	✓	✓	
__utmc	241110656	.remitly.com	/	Session	15 B			
_ga_RE4YD46C8N	GS1.1.1717766535.3.0.1717766742.60.0.0	.remitly.com	/	12/07/2025, 15:25:42	52 B			
__utma	241110656.2041087792.1717711570.1717755817.1717766536.3	.remitly.com	/	12/07/2025, 15:22:15	61 B			
_ga	GA1.1.2041087792.1717711570	.remitly.com	/	12/07/2025, 15:22:15	30 B			
cmsContentId	74345972-aa92-48fc-bdc0-40f83d78a362	www.remitly.com	/	12/07/2025, 15:22:13	48 B	✓	✓	
lang	en	www.remitly.com	/	12/07/2025, 15:22:13	6 B	✓	✓	
de_hash	2XxjtCoEyaHLT2x6WPFk6U	www.remitly.com	/	12/07/2025, 00:06:00	29 B	✓		
de_id	3RoCNPYfDQtGnk1z9ZTXdzwm8I2PJtN3oy0G1hDQYMamt5C82ejnuevohwfffjUsW0srPaRDABfnWBV3Crp0wIgHhyLqrermJ3c8NxynE1aX	www.remitly.com	/	12/07/2025, 00:06:00	113 B	✓		
amp_04c312	JO3FHyBoQ6i-NmHw_F046J...1hvpdqebd.1hvpdqebf.7.0.7	.remitly.com	/	07/06/2025, 15:22:15	60 B			Lax
AMP_d0cf3ed24c	JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjIzUm9DTlBZZkRRdEduazF6OVpUWGR6d204STJQSnROM295MEcxaERRWU1hbXQ1QzgyZWpudWV2b2h3ZmZmalVzVzBzclBhUkRBQmZuV0JWM0NycDB3SWdIaHlMcXJlcm1KM2M4Tnh5bkUxYVglMjIlMkMlMjJzZXNzaW9uSWQlMjIlM0ExNzE3NzY2NTM0OTAyJTJDJTIyb3B0T3V0JTIyJTNBZmFsc2UlMkMlMjJsYXN0RXZlbnRUaW1lJTIyJTNBMTcxNzc2NjUzNDkzNyU3RA==	.remitly.com	/	07/06/2025, 15:22:14	326 B			Lax
AMP_MKTG_d0cf3ed24c	JTdCJTdE	.remitly.com	/	07/06/2025, 00:06:09	27 B			Lax
__utmz	241110656.1717711570.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)	.remitly.com	/	07/12/2024, 02:22:15	76 B			
_fbp	fb.1.1717711569924.510697268574662812	.remitly.com	/	05/09/2024, 15:22:16	41 B			
_gcl_au	1.1.895234587.1717711570	.remitly.com	/	05/09/2024, 00:06:10	31 B			
rbuid	rbos-21ddcc4b-c22d-4510-a375-3aa3efcc6bb3	.remitly.com	/	07/07/2024, 15:22:16	46 B			
__utmb	241110656.2.9.1717766536	.remitly.com	/	07/06/2024, 15:52:15	30 B			"""

# Function to parse a single cookie line
def parse_cookie_line(line):
    parts = line.split('\t')

    expires_str = parts[4]
    if expires_str != "Session":
        expires_datetime = datetime.strptime(expires_str, "%m/%d/%Y, %H:%M:%S")
        expires_timestamp = int(expires_datetime.timestamp())
    else:
        expires_timestamp = None
    
    cookies = {
        "name": parts[0],
        "value": parts[1],
        "domain": parts[2],
        "path": parts[3],
        "size": parts[5],
    }

    if expires_timestamp:
        cookies["expires"] = expires_timestamp

    return cookies
# Split the input string into lines and parse each line
cookies = [parse_cookie_line(line) for line in input_string.strip().split('\n')]

# Convert to JSON and save to a file
with open('cookies.json', 'w') as f:
    json.dump(cookies, f,  indent=4)

print("Cookies saved to cookies.json")