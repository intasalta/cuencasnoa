import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        # Concise logging
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")

def main():
    os.chdir(DIRECTORY)
    port = PORT
    server = None
    for attempt in range(10):
        try:
            server = socketserver.TCPServer(("", port), Handler)
            break
        except OSError:
            port += 1

    if not server:
        print("No se pudo iniciar el servidor en los puertos 8080-8090.")
        sys.exit(1)

    url = f"http://localhost:{port}/index.html"
    print("=" * 60)
    print("  DASHBOARD DE CUENCAS HÍDRICAS DEL NOA - INTA EEA SALTA")
    print("=" * 60)
    print(f"\n  Servidor web activo en: {url}")
    print("  Abriendo el navegador automáticamente...\n")
    print("  (Presiona Ctrl + C en esta ventana para cerrar el servidor)")
    print("=" * 60)

    webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor cerrado correctamente.")
        server.server_close()

if __name__ == '__main__':
    main()
