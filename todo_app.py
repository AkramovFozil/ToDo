import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import sqlite3
import urllib.parse
import requests

conn = sqlite3.connect('todo.db')
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS todo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task TEXT NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT 0
)
''')
conn.commit()


class TodoHandler(BaseHTTPRequestHandler):

    def _send_response(self, code, message):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(message).encode())

    def do_GET(self):
        if self.path == '/todos':
            c.execute('SELECT * FROM todo')
            rows = c.fetchall()
            tasks = [{'id': row[0], 'task': row[1], 'completed': bool(row[2])} for row in rows]
            self._send_response(200, tasks)
        else:
            self._send_response(404, {'error': 'Not Found'})

    def do_POST(self):
        if self.path == '/todos':
            length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(length)
            data = json.loads(post_data.decode('utf-8'))
            task = data.get('task')
            if task:
                c.execute('INSERT INTO todo (task) VALUES (?)', (task,))
                conn.commit()
                self._send_response(201, {'message': 'Task created'})
            else:
                self._send_response(400, {'error': 'Bad Request'})
        else:
            self._send_response(404, {'error': 'Not Found'})

    def do_PUT(self):
        parsed_path = urllib.parse.urlparse(self.path)
        if parsed_path.path.startswith('/todos/'):
            task_id = parsed_path.path.split('/')[-1]
            try:
                length = int(self.headers['Content-Length'])
                put_data = self.rfile.read(length)
                data = json.loads(put_data.decode('utf-8'))
                task = data.get('task')
                completed = data.get('completed')
                if task is not None and completed is not None:
                    c.execute('UPDATE todo SET task = ?, completed = ? WHERE id = ?', (task, completed, task_id))
                    conn.commit()
                    if c.rowcount == 0:
                        self._send_response(404, {'error': 'Task not found'})
                    else:
                        self._send_response(200, {'message': 'Task updated'})
                else:
                    self._send_response(400, {'error': 'Bad Request'})
            except ValueError:
                self._send_response(400, {'error': 'Bad Request'})
        else:
            self._send_response(404, {'error': 'Not Found'})

    def do_DELETE(self):
        parsed_path = urllib.parse.urlparse(self.path)
        if parsed_path.path.startswith('/todos/'):
            task_id = parsed_path.path.split('/')[-1]
            c.execute('DELETE FROM todo WHERE id = ?', (task_id,))
            conn.commit()
            if c.rowcount == 0:
                self._send_response(404, {'error': 'Task not found'})
            else:
                self._send_response(200, {'message': 'Task deleted'})
        else:
            self._send_response(404, {'error': 'Not Found'})

    def log_message(self, format, *args):
        print(f"{self.client_address[0]} - {self.log_date_time_string()} - {format % args}")


def run(server_class=HTTPServer, handler_class=TodoHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting httpd server on port {port}")
    httpd.serve_forever()


# Define the URL for the POST request
url = 'http://localhost:8000/todos'

# Define the task data to be added
data = {
    'task': 'Buy groceries'
}

# Send the POST request
response = requests.post(url, json=data)

# Print the response from the server
print(response.json())

if __name__ == '__main__':
    run()
