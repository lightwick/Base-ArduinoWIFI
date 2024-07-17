import socket
import threading
import queue
from http.server import SimpleHTTPRequestHandler, HTTPServer
import os
import keyboard
import database
import queue

TCP_HOST = ''  # 모든 IP 주소에서 접속 허용
TCP_PORT = 8000  # TCP 포트는 8000
HTTP_PORT = 8001  # HTTP 포트는 8001로 설정

message_queue = queue.Queue()
lock = threading.Lock()

# 데이터베이스 연결
dbFileName = "example.db"
filePath = os.path.join(os.path.dirname(__file__), dbFileName)
dbConnection = database.connection(filePath)

# 서버 중지 플래그
stop_event = threading.Event()

# 가장 최근 6개의 센서 데이터 저장
q = queue.Queue(maxsize=6)

def update_html(message):
    # Extract the latest sensor data from the queue
    recentData = list(q.queue)

    html_content = f"""
<!doctype html>
<html>
    <head>
        <title>Message Received</title>
        <meta charset="utf-8" />
        <meta http-equiv="Content-type" content="text/html; charset=utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style type="text/css">
        body {{
            background-color: #f0f0f2;
            margin: 0;
            padding: 0;
            font-family: -apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", "Open Sans", "Helvetica Neue", Helvetica, Arial, sans-serif;
        }}
        div {{
            width: 600px;
            margin: 5em auto;
            padding: 2em;
            background-color: #fdfdff;
            border-radius: 0.5em;
            box-shadow: 2px 3px 7px 2px rgba(0,0,0,0.02);
        }}
        a:link, a:visited {{
            color: #38488f;
            text-decoration: none;
        }}
        @media (max-width: 700px) {{
            div {{
                margin: 0 auto;
                width: auto;
            }}
        }}
        </style>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script>
            // 5초마다 페이지 새로고침
            setInterval(function() {{
                window.location.reload();
            }}, 5000);

            window.onload = function() {{
                var ctx = document.getElementById('myChart').getContext('2d');
                var myChart = new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: [{', '.join([str(i+1) for i in range(len(recentData))])}],
                        datasets: [{{
                            label: 'Sensor Data',
                            data: [{', '.join(map(str, recentData))}],
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            borderColor: 'rgba(75, 192, 192, 1)',
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        scales: {{
                            y: {{
                                beginAtZero: true
                            }}
                        }}
                    }}
                }});
            }};
        </script>
    </head>
    <body>
        <div>
            <h1>Message Received</h1>
            <p>Most Recent Data: {message}</p>
            <canvas id="myChart" width="400" height="400"></canvas>
        </div>
        <script type="module">
            // import * as THREE from './node_modules/three/build/three.module.js';

            // 텍스처 로더 생성
            const textureLoader = new THREE.TextureLoader();

            // 나무 벽지 텍스처 로드
            const woodTexture = textureLoader.load('wood_texture.jpg');

            // 장면 생성
            const scene = new THREE.Scene();

            // 카메라 생성
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.set(0, 15, 40);
            camera.lookAt(0, 5, 0); // 카메라가 바닥과 박스를 향하게 조정

            // 렌더러 생성
            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.body.appendChild(renderer.domElement);

            // 창고 바닥 생성
            const floorGeometry = new THREE.PlaneGeometry(50, 50);
            const floorMaterial = new THREE.MeshStandardMaterial({{ color: 0x808080 }});
            const floor = new THREE.Mesh(floorGeometry, floorMaterial);
            floor.rotation.x = - Math.PI / 2;
            scene.add(floor);

            // 나무 벽지 배경 생성
            const wallGeometry = new THREE.PlaneGeometry(50, 30); // 벽 높이를 더 크게 조정
            const wallMaterial = new THREE.MeshBasicMaterial({{ map: woodTexture }});

            const backWall = new THREE.Mesh(wallGeometry, wallMaterial);
            backWall.position.set(0, 15, -25); // 벽 위치를 위로 조정
            scene.add(backWall);

            const leftWall = new THREE.Mesh(wallGeometry, wallMaterial);
            leftWall.position.set(-25, 15, 0);
            leftWall.rotation.y = Math.PI / 2;
            scene.add(leftWall);

            const rightWall = new THREE.Mesh(wallGeometry, wallMaterial);
            rightWall.position.set(25, 15, 0);
            rightWall.rotation.y = -Math.PI / 2;
            scene.add(rightWall);

            // 조명 추가
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
            scene.add(ambientLight);

            const pointLight = new THREE.PointLight(0xffffff, 1, 100);
            pointLight.position.set(0, 20, 0);
            scene.add(pointLight);

            // 선반 생성 함수
            function createShelf(x, y, z) {{
                const shelfGroup = new THREE.Group();

                // 선반 프레임
                const frameMaterial = new THREE.MeshStandardMaterial({{ color: 0x000000 }}); // 검정색
                const frameGeometry = new THREE.BoxGeometry(0.1, 10, 0.1);

                for (let i = 0; i < 4; i++) {{
                    const frame = new THREE.Mesh(frameGeometry, frameMaterial);
                    frame.position.set(i % 2 === 0 ? -2.5 : 2.5, 5, i < 2 ? -2 : 2);
                    shelfGroup.add(frame);
                }}

                const shelfMaterial = new THREE.MeshStandardMaterial({{ color: 0x000000 }}); // 검정색
                const shelfGeometry = new THREE.BoxGeometry(5, 0.1, 4);

                for (let i = 0; i < 5; i++) {{
                    const shelf = new THREE.Mesh(shelfGeometry, shelfMaterial);
                    shelf.position.set(0, i * 2, 0);
                    shelfGroup.add(shelf);
                }}

                shelfGroup.position.set(x, y, z);
                return shelfGroup;
            }}

            // 창고 선반 배치
            const shelf1 = createShelf(-10, 0, 0);
            const shelf2 = createShelf(10, 0, 0);
            scene.add(shelf1);
            scene.add(shelf2);

            // 박스 생성 함수
            function createBox(x, y, z, width, height, depth, color) {{
                const boxGeometry = new THREE.BoxGeometry(width, height, depth);
                const boxMaterial = new THREE.MeshStandardMaterial({{ color }});
                const box = new THREE.Mesh(boxGeometry, boxMaterial);
                box.position.set(x, y, z);
                return box;
            }}

            // 박스 배치
            const boxColors = [0xF5F5DC, 0xFFD700, 0xFF8C00, 0xFF4500]; // 베이지색, 금색, 주황색, 빨간색
            
            // numBoxes의 크기에 따라 상자 그리기
            let numBoxes = {message};
            const maxBoxNum = 6;
            numBoxes = Math.min(numBoxes, maxBoxNum);

            for (let i = 0; i < numBoxes; i++) {{
                const x = i % 2 === 0 ? -10 : 10;
                const y = 1 + 2 * Math.floor(i / 2);
                const z = 0;
                const width = 2;
                const height = 1 + 0.5 * (i % 3);
                const depth = 1;
                const color = boxColors[i % boxColors.length];
                const box = createBox(x, y, z, width, height, depth, color);
                scene.add(box);
            }}

            // 애니메이션 루프
            function animate() {{
                requestAnimationFrame(animate);
                renderer.render(scene, camera);
            }}


            animate();
        </script>
    </body>
</html>"""

    with open("index.html", "w") as f:
        f.write(html_content)

class TCPHandler(threading.Thread):
    def __init__(self, conn, addr):
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr

    def run(self):
        try:
            with self.conn:
                print('Connected by', self.addr)
                while not stop_event.is_set():
                    data = self.conn.recv(1024)
                    if not data:
                        break
                    message = data.decode().strip()
                    print("Received:", message)
                    with lock:
                        message_queue.put(message)

                    if message.startswith("mipmip"):
                        number = message[len("mipmip"):]
                        if number.isdigit():
                            response = f"lablab{number}"
                            self.conn.sendall(response.encode())
                            print("Sent:", response)
                    else:
                        try:
                            receivedSensorData = int(message)
                            if q.full():
                                q.get()
                            with lock:
                                q.put(receivedSensorData)
                                dbConnection.insertData(receivedSensorData)
                        except Exception as e:
                            print(f"Exception storing data into database: {e}")

        except Exception as e:
            print(f"Exception handling client {self.addr}: {e}")

class MyHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path == '/':
                self.path = '/index.html'
            return SimpleHTTPRequestHandler.do_GET(self)
        except ConnectionAbortedError:
            print("Connection aborted by client")
        except Exception as e:
            print(f"Exception during GET request: {e}")

def tcp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((TCP_HOST, TCP_PORT))
        s.listen()
        s.settimeout(15.0)  # Set timeout to allow periodic checking of stop_event
        
        print(f"TCP Server listening on port {TCP_PORT}")

        while not stop_event.is_set():
            try:
                conn, addr = s.accept()
                print(f"Accepted connection from {addr}")
                handler = TCPHandler(conn, addr)
                handler.start()
            except socket.timeout:
                continue

def http_server():
    os.chdir('.')  # Ensure the server is serving from the current directory
    httpd = HTTPServer((TCP_HOST, HTTP_PORT), MyHTTPRequestHandler)
    print(f"HTTP server running on port {HTTP_PORT}")
    try:
        while not stop_event.is_set():
            httpd.handle_request()
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Exception in HTTP server: {e}")

def html_updater():
    while not stop_event.is_set():
        try:
            message = message_queue.get()
            with lock:
                update_html(message)
        except Exception as e:
            print(f"Exception in HTML updater: {e}")

def stop_server():
    print("Stopping server...")
    stop_event.set()

if __name__ == "__main__":
    tcp_thread = threading.Thread(target=tcp_server)
    tcp_thread.start()

    http_thread = threading.Thread(target=http_server)
    http_thread.start()

    updater_thread = threading.Thread(target=html_updater)
    updater_thread.start()

    print("Press 'q' to stop the server")
    keyboard.wait('q')
    stop_server()

    tcp_thread.join()
    http_thread.join()
    updater_thread.join()
