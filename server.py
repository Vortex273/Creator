from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
from scenario_data import SCENARIO_TEMPLATES
import random

STATIC_DIR = 'static'

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.serve_file_with_encoding(os.path.join(STATIC_DIR, 'index.html'), 'text/html; charset=utf-8')
        else:
            filepath = os.path.join(STATIC_DIR, self.path.lstrip('/'))
            if os.path.exists(filepath) and os.path.isfile(filepath):
                ext = os.path.splitext(filepath)[1]
                content_type = {
                    '.html': 'text/html',
                    '.css': 'text/css',
                    '.js': 'application/javascript',
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.gif': 'image/gif',
                }.get(ext, 'application/octet-stream')

                if ext == '.html':
                    self.serve_file_with_encoding(filepath, content_type + '; charset=utf-8')
                else:
                    self.serve_file(filepath, content_type)
            else:
                self.send_error(404, "File Not Found")

    def do_POST(self):
        if self.path == '/generate-scheme':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')

            try:
                data = json.loads(post_data)
                theme = data.get('theme')
                age_group = data.get('age_group')
                duration = data.get('duration')

                scenarios_for_theme = SCENARIO_TEMPLATES.get(theme, {})
                scenarios_for_age = scenarios_for_theme.get(age_group, {})
                available_scenarios = scenarios_for_age.get(duration, [])

                if not available_scenarios:
                    if duration == "15_минут":
                        available_scenarios.extend(scenarios_for_age.get("30_минут", []))
                        available_scenarios.extend(scenarios_for_age.get("целый_урок", []))
                    elif duration == "30_минут":
                        available_scenarios.extend(scenarios_for_age.get("целый_урок", []))

                selected_scenarios = random.sample(available_scenarios, min(len(available_scenarios), 5))

                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')

                self.end_headers()
                response_json = json.dumps(selected_scenarios, ensure_ascii=False, indent=None)
                self.wfile.write(response_json.encode('utf-8'))

            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
            except Exception as e:
                print(f"Error processing request: {e}")  # Лог в консоль сервера
                self.send_error(500, "Internal Server Error")
        else:
            self.send_error(404, "Endpoint Not Found")

    def serve_file(self, filepath, content_type):
        """Метод для отправки файлов как бинарных данных."""
        try:
            with open(filepath, 'rb') as f:
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.end_headers()
                self.wfile.write(f.read())

        except FileNotFoundError:
            self.send_error(404, "File Not Found")

    def serve_file_with_encoding(self, filepath, content_type):
        """Метод для отправки файлов с указанием кодировки."""
        print(f"[DEBUG] Serving file with encoding: {filepath}, Content-Type: {content_type}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))

        except FileNotFoundError:
            self.send_error(404, "File Not Found")


def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f'Сервер запущен на http://localhost:{port}/')
    httpd.serve_forever()


if __name__ == '__main__':
    if not os.path.exists(STATIC_DIR):
        os.makedirs(STATIC_DIR)
    run_server()