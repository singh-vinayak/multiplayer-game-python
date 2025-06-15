# gRPC Multiplayer Quiz Game 🧠

This is a full-stack, real-time multiplayer quiz game built with Python, React, and gRPC. It demonstrates a low-latency, stateful application using bidirectional streaming.

## Project Structure

```
grpc-quiz-game/
├── backend/
│   ├── __init__.py
│   ├── game_logic.py     # Core game state and rules
│   ├── quiz_service.py   # gRPC service implementation
│   ├── server.py         # Starts the gRPC server
│   ├── quiz_pb2.py       # Generated Python code
│   └── quiz_pb2_grpc.py  # Generated Python code
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/     # React UI components
│   │   │   ├── Game.tsx
│   │   │   ├── Lobby.tsx
│   │   │   └── ...
│   │   ├── proto/          # Generated JS/TS code
│   │   │   ├── quiz_pb.js
│   │   │   └── Quiz_grpc_web_pb.js
│   │   ├── App.tsx
│   │   └── index.tsx
│   ├── package.json
│   └── tsconfig.json
├── proto/
│   └── quiz.proto        # Single source of truth for the API
├── .gitignore
├── envoy.yaml            # Envoy proxy configuration
└── README.md             # This file
```

## Prerequisites

- **Python** 3.8+
- **Node.js** 16+ and npm
- **Docker** and Docker Compose

## Setup and Running Instructions

Follow these steps in order from the root directory (`grpc-quiz-game/`).

### Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd grpc-quiz-game
```

### Step 2: Generate gRPC Code

This step compiles the `.proto` file into Python and JavaScript/TypeScript code.

**1. Set up Python Virtual Environment & Install Tools**
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install grpcio grpcio-tools
```

**2. Generate Python Code**
```bash
python -m grpc_tools.protoc -I./proto --python_out=./backend --grpc_python_out=./backend ./proto/quiz.proto
```

**3. Install Node.js Dependencies for Code Generation**
```bash
npm install grpc-tools grpc-web google-protobuf
```

**4. Generate JavaScript/TypeScript Code**
```bash
# For Mac/Linux
protoc -I=./proto ./proto/quiz.proto \
  --js_out=import_style=commonjs,binary:./frontend/src/proto \
  --grpc-web_out=import_style=typescript,mode=grpcwebtext:./frontend/src/proto

# For Windows
# You might need to use the full path to protoc-gen-grpc-web plugin
# located in node_modules/.bin
```

### Step 3: Set Up and Run the Backend

**1. Install Backend Dependencies**
```bash
# Make sure you are in the virtual environment (source venv/bin/activate)
pip install -r backend/requirements.txt # You will need to create this file
```
*(Create `backend/requirements.txt` with `grpcio` inside)*

**2. Run the Python gRPC Server**
Open a new terminal window.
```bash
source venv/bin/activate
python backend/server.py
```
You should see `Server starting on port 50051...`. Keep this terminal running.

### Step 4: Set Up and Run the Frontend

**1. Install Frontend Dependencies**
Open a new terminal window.
```bash
cd frontend
npm install @mui/material @emotion/react @emotion/styled
npm install
```

**2. Run the React Development Server**
```bash
npm start
```
Your browser will open to `http://localhost:3000`, but it will **not work yet**. It needs the proxy to communicate with the backend.

### Step 5: Run the Envoy Proxy

The browser cannot talk directly to a gRPC server. Envoy acts as a proxy to translate gRPC-Web requests from the browser into standard gRPC for the backend.

**1. Run Envoy with Docker**
Open a new terminal window.
```bash
docker run --rm -it -p 8080:8080 \
  --network="host" \
  envoyproxy/envoy:v1.22.0 \
  -c /etc/envoy/envoy.yaml
```
**Note:** You may need to provide the full path to your `envoy.yaml` file by mounting it as a volume, or copy its content. For simplicity with the command above, ensure your `envoy.yaml` is in the directory you are running the command from. A better approach for projects is using docker-compose.

### Step 6: Play the Game!

1.  Make sure all three terminals (Backend Server, Frontend Server, Envoy Proxy) are running.
2.  Open **two** separate browser tabs or windows and navigate to `http://localhost:3000`.
3.  Enter a different name in each tab and click "Join".
4.  Once both players have joined, the game will start automatically. Enjoy!

#### grpcwebproxy command
grpcwebproxy --backend_addr=localhost:50055 --backend_tls=false --run_tls_server=false --server_http_debug_port=8080 --allowed_origins=http://localhost:3000