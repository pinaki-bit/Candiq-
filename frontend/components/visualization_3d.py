"""
frontend/components/visualization_3d.py

Phase 13: 3D AI Visualization Component.
Embeds an interactive Three.js 3D WebGL Talent Core Visualizer connected to the /ws/pipeline WebSocket stream.
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components


def get_3d_visualization_html(ws_url: str = "ws://localhost:8000/ws/pipeline") -> str:
    """Generates the full HTML/CSS/JavaScript bundle for the 3D WebGL visualizer."""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D AI Candidate Talent Core</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            user-select: none;
        }}
        body {{
            background-color: #0b0f19;
            color: #e2e8f0;
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            overflow: hidden;
            height: 100vh;
            width: 100vw;
        }}
        #canvas-container {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
        }}
        .ui-overlay {{
            position: absolute;
            top: 15px;
            left: 15px;
            z-index: 10;
            pointer-events: none;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .title-badge {{
            background: rgba(15, 23, 42, 0.75);
            border: 1px solid rgba(99, 102, 241, 0.4);
            backdrop-filter: blur(12px);
            padding: 10px 16px;
            border-radius: 12px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }}
        .title-badge h2 {{
            font-size: 16px;
            font-weight: 700;
            background: linear-gradient(135deg, #818cf8 0%, #c084fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .title-badge p {{
            font-size: 11px;
            color: #94a3b8;
            margin-top: 2px;
        }}
        .status-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 20px;
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(52, 211, 153, 0.3);
            width: fit-content;
        }}
        .status-dot {{
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background-color: #34d399;
            box-shadow: 0 0 8px #34d399;
            animation: pulse 1.5s infinite;
        }}
        @keyframes pulse {{
            0% {{ transform: scale(0.95); opacity: 0.8; }}
            50% {{ transform: scale(1.2); opacity: 1; }}
            100% {{ transform: scale(0.95); opacity: 0.8; }}
        }}
        .controls-overlay {{
            position: absolute;
            bottom: 15px;
            right: 15px;
            z-index: 10;
            display: flex;
            gap: 8px;
        }}
        .btn {{
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(148, 163, 184, 0.2);
            color: #f1f5f9;
            padding: 8px 14px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            backdrop-filter: blur(8px);
            transition: all 0.2s ease;
        }}
        .btn:hover {{
            background: rgba(99, 102, 241, 0.3);
            border-color: #6366f1;
            transform: translateY(-2px);
        }}
        .telemetry-box {{
            position: absolute;
            bottom: 15px;
            left: 15px;
            z-index: 10;
            width: 320px;
            max-height: 160px;
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid rgba(51, 65, 85, 0.6);
            border-radius: 12px;
            padding: 10px;
            backdrop-filter: blur(12px);
            overflow-y: auto;
            font-family: monospace;
            font-size: 11px;
        }}
        .telemetry-box h4 {{
            color: #cbd5e1;
            font-size: 11px;
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .log-entry {{
            margin-bottom: 4px;
            color: #94a3b8;
            word-break: break-all;
        }}
        .log-entry .time {{
            color: #64748b;
        }}
        .log-entry .event {{
            color: #818cf8;
            font-weight: bold;
        }}
        #fallback-notice {{
            display: none;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #1e293b;
            padding: 24px;
            border-radius: 12px;
            border: 1px solid #ef4444;
            color: #f87171;
            text-align: center;
            z-index: 100;
        }}
    </style>
</head>
<body>
    <div id="canvas-container"></div>

    <div class="ui-overlay">
        <div class="title-badge">
            <h2>🌌 AI Candidate Talent Space</h2>
            <p>Real-Time Live WebSocket Pipeline Telemetry</p>
        </div>
        <div class="status-pill" id="ws-status-pill">
            <div class="status-dot" id="ws-dot"></div>
            <span id="ws-status-text">CONNECTING WEBSOCKET...</span>
        </div>
    </div>

    <div class="telemetry-box">
        <h4>⚡ Pipeline Stream Event Log</h4>
        <div id="log-list">
            <div class="log-entry"><span class="time">[INIT]</span> Visualizer ready. Subscribed to WS pipeline.</div>
        </div>
    </div>

    <div class="controls-overlay">
        <button class="btn" onclick="triggerSimulatedEvent()">⚡ Sim Event</button>
        <button class="btn" onclick="resetCamera()">🎥 Reset View</button>
    </div>

    <div id="fallback-notice">
        <h3>⚠️ WebGL Unavailable</h3>
        <p>Your browser or environment does not support 3D WebGL rendering.</p>
    </div>

    <!-- Include Three.js and OrbitControls -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>

    <script>
        let scene, camera, renderer, controls;
        let particles, particleGeo, particleMat;
        let domainNodes = [];
        let activePipelineParticles = [];
        const WS_URL = "{ws_url}";
        let socket = null;

        // Check WebGL availability
        function webglAvailable() {{
            try {{
                const canvas = document.createElement('canvas');
                return !!(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
            }} catch (e) {{
                return false;
            }}
        }}

        if (!webglAvailable()) {{
            document.getElementById('fallback-notice').style.display = 'block';
        }} else {{
            init3D();
            initWebSocket();
        }}

        function init3D() {{
            const container = document.getElementById('canvas-container');
            scene = new THREE.Scene();
            scene.fog = new THREE.FogExp2(0x0b0f19, 0.015);

            camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.set(0, 20, 45);

            renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            container.appendChild(renderer.domElement);

            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.maxDistance = 100;
            controls.minDistance = 10;

            // Ambient & Point Lights
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
            scene.add(ambientLight);

            const pointLight = new THREE.PointLight(0x6366f1, 2, 100);
            pointLight.position.set(0, 15, 0);
            scene.add(pointLight);

            // Create Ambient Candidate Starfield (Background Talent Galaxy)
            const starCount = 600;
            particleGeo = new THREE.BufferGeometry();
            const positions = new Float32Array(starCount * 3);
            const colors = new Float32Array(starCount * 3);

            const colorOptions = [
                new THREE.Color(0x6366f1), // Indigo
                new THREE.Color(0x38bdf8), // Sky Blue
                new THREE.Color(0x34d399), // Emerald
                new THREE.Color(0xf472b6), // Pink
            ];

            for (let i = 0; i < starCount; i++) {{
                positions[i * 3] = (Math.random() - 0.5) * 80;
                positions[i * 3 + 1] = (Math.random() - 0.5) * 60;
                positions[i * 3 + 2] = (Math.random() - 0.5) * 80;

                const c = colorOptions[Math.floor(Math.random() * colorOptions.length)];
                colors[i * 3] = c.r;
                colors[i * 3 + 1] = c.g;
                colors[i * 3 + 2] = c.b;
            }}

            particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            particleGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

            particleMat = new THREE.PointsMaterial({{
                size: 0.8,
                vertexColors: true,
                transparent: true,
                opacity: 0.7,
            }});

            particles = new THREE.Points(particleGeo, particleMat);
            scene.add(particles);

            // Domain Cluster Center Nodes
            const domains = [
                {{ name: "Data Science", color: 0x38bdf8, pos: new THREE.Vector3(-18, 5, -10) }},
                {{ name: "Software Eng", color: 0x6366f1, pos: new THREE.Vector3(18, 8, -5) }},
                {{ name: "DevOps", color: 0x34d399, pos: new THREE.Vector3(-10, -10, 15) }},
                {{ name: "HR & Mgmt", color: 0xf472b6, pos: new THREE.Vector3(15, -6, 12) }},
            ];

            domains.forEach(d => {{
                const geo = new THREE.IcosahedronGeometry(2.5, 2);
                const mat = new THREE.MeshPhongMaterial({{
                    color: d.color,
                    emissive: d.color,
                    emissiveIntensity: 0.3,
                    wireframe: true,
                    transparent: true,
                    opacity: 0.8
                }});
                const mesh = new THREE.Mesh(geo, mat);
                mesh.position.copy(d.pos);
                scene.add(mesh);
                domainNodes.push({{ mesh, name: d.name, basePos: d.pos }});
            }});

            window.addEventListener('resize', onWindowResize);
            animate();
        }}

        function animate() {{
            requestAnimationFrame(animate);
            const time = Date.now() * 0.001;

            if (particles) {{
                particles.rotation.y = time * 0.03;
            }}

            domainNodes.forEach((node, i) => {{
                node.mesh.rotation.x = time * (0.2 + i * 0.05);
                node.mesh.rotation.y = time * (0.3 + i * 0.05);
                node.mesh.position.y = node.basePos.y + Math.sin(time * 1.5 + i) * 1.2;
            }});

            // Animate active pipeline particles
            activePipelineParticles.forEach((p, idx) => {{
                p.mesh.rotation.x += 0.05;
                p.mesh.rotation.y += 0.05;
                if (p.targetPos) {{
                    p.mesh.position.lerp(p.targetPos, 0.05);
                }}
            }});

            controls.update();
            renderer.render(scene, camera);
        }}

        function onWindowResize() {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }}

        function resetCamera() {{
            camera.position.set(0, 20, 45);
            controls.target.set(0, 0, 0);
        }}

        function logEvent(eventType, message) {{
            const logList = document.getElementById('log-list');
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            const now = new Date().toLocaleTimeString();
            entry.innerHTML = `<span class="time">[${{now}}]</span> <span class="event">${{eventType}}</span>: ${{message}}`;
            logList.insertBefore(entry, logList.firstChild);
        }}

        function spawnPipelineParticle(eventType, data) {{
            const geo = new THREE.SphereGeometry(1.2, 16, 16);
            let color = 0x38bdf8; // default cyan

            if (eventType === 'resume.uploaded') color = 0x38bdf8;
            else if (eventType === 'resume.extracting') color = 0xf59e0b;
            else if (eventType === 'resume.classified') color = 0x818cf8;
            else if (eventType === 'resume.matched') color = 0x34d399;

            const mat = new THREE.MeshStandardMaterial({{
                color: color,
                emissive: color,
                emissiveIntensity: 0.8,
                roughness: 0.2
            }});
            const mesh = new THREE.Mesh(geo, mat);

            // Spawn at origin (0, 0, 0)
            mesh.position.set((Math.random() - 0.5) * 2, (Math.random() - 0.5) * 2, (Math.random() - 0.5) * 2);
            scene.add(mesh);

            // Target position: target one of domain nodes randomly
            const randomDomain = domainNodes[Math.floor(Math.random() * domainNodes.length)];
            const targetPos = randomDomain.basePos.clone().add(new THREE.Vector3(
                (Math.random() - 0.5) * 6,
                (Math.random() - 0.5) * 6,
                (Math.random() - 0.5) * 6
            ));

            activePipelineParticles.push({{ mesh, targetPos }});
        }}

        function initWebSocket() {{
            const dot = document.getElementById('ws-dot');
            const text = document.getElementById('ws-status-text');

            try {{
                socket = new WebSocket(WS_URL);

                socket.onopen = function() {{
                    text.innerText = "WEBSOCKET CONNECTED";
                    dot.style.backgroundColor = "#34d399";
                    logEvent("SYSTEM", "Connected to WebSocket " + WS_URL);
                }};

                socket.onmessage = function(event) {{
                    try {{
                        const msg = JSON.parse(event.data);
                        const eventType = msg.event_type || 'event';
                        const data = msg.data || {{}};
                        logEvent(eventType, JSON.stringify(data));
                        spawnPipelineParticle(eventType, data);
                    }} catch(e) {{
                        console.error(e);
                    }}
                }};

                socket.onerror = function(err) {{
                    text.innerText = "WS DISCONNECTED";
                    dot.style.backgroundColor = "#ef4444";
                }};

                socket.onclose = function() {{
                    text.innerText = "WS OFFLINE (RETRYING...)";
                    dot.style.backgroundColor = "#f59e0b";
                    setTimeout(initWebSocket, 5000);
                }};
            }} catch(err) {{
                text.innerText = "WS UNAVAILABLE";
                dot.style.backgroundColor = "#ef4444";
            }}
        }}

        function triggerSimulatedEvent() {{
            const simEvents = [
                {{ type: 'resume.uploaded', data: {{ filename: 'simulated_candidate.pdf', resume_id: 999 }} }},
                {{ type: 'resume.extracting', data: {{ status: 'parsing text & entities' }} }},
                {{ type: 'resume.classified', data: {{ domain: 'Data Science', confidence: 0.96 }} }},
                {{ type: 'resume.matched', data: {{ match_score: 92.4, status: 'Shortlisted' }} }},
            ];
            const ev = simEvents[Math.floor(Math.random() * simEvents.length)];
            logEvent(ev.type, JSON.stringify(ev.data));
            spawnPipelineParticle(ev.type, ev.data);
        }}
    </script>
</body>
</html>
"""


def render_3d_visualization(ws_url: str = "ws://localhost:8000/ws/pipeline", height: int = 550):
    """Renders the 3D WebGL Candidate Talent Space in Streamlit."""
    html_code = get_3d_visualization_html(ws_url=ws_url)
    components.html(html_code, height=height, scrolling=False)
