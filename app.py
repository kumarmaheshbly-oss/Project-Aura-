# ... (aapka baaki code waisa hi rahega) ...

# --- CesiumJS 3D Earth (Fixed Version with preserveDrawingBuffer) ---
st.markdown("<p style='color:#00FFFF; font-size:14px; margin-bottom:5px;'>🌐 3D ORBITAL KINEMATICS (CESIUM ENGINE)</p>", unsafe_allow_html=True)

js_pos_a = json.dumps(pos_a.T.tolist())
js_pos_b = json.dumps(pos_b.T.tolist())

cesium_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cesium.com/downloads/cesiumjs/releases/1.119/Build/Cesium/Cesium.js"></script>
    <link href="https://cesium.com/downloads/cesiumjs/releases/1.119/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
    <style>
        html, body, #cesiumContainer {{ width: 100%; height: 100%; margin: 0; padding: 0; overflow: hidden; background: #000; }}
        .cesium-viewer-bottom {{ display: none !important; }}
    </style>
</head>
<body>
    <div id="cesiumContainer"></div>
    <script>
        // 1. Set the base URL for Cesium assets (Workers, etc.)
        window.CESIUM_BASE_URL = 'https://cesium.com/downloads/cesiumjs/releases/1.119/Build/Cesium/';
        
        // 2. Initialize Cesium Viewer with preserveDrawingBuffer and a simpler setup
        const viewer = new Cesium.Viewer('cesiumContainer', {{
            // This is crucial for iframe/streamlit rendering
            contextOptions: {{
                webgl: {{
                    preserveDrawingBuffer: true
                }}
            }},
            // Use a simple grid to avoid token issues
            imageryProvider: new Cesium.GridImageryProvider({{
                color: Cesium.Color.BLACK,
                glowColor: Cesium.Color.CYAN.withAlpha(0.2),
                cells: 10
            }}),
            baseLayerPicker: false, geocoder: false, homeButton: false, sceneModePicker: false,
            navigationHelpButton: false, animation: false, timeline: false, fullscreenButton: false,
            infoBox: false, selectionIndicator: false
        }});

        // Dark mode for Earth
        viewer.scene.globe.baseColor = Cesium.Color.BLACK;
        viewer.scene.globe.enableLighting = false;
        viewer.scene.backgroundColor = Cesium.Color.BLACK;
        viewer.scene.skyBox.show = false;

        // 3. Add Orbits
        const posA = {js_pos_a};
        const posB = {js_pos_b};

        function addOrbit(positions, color, name) {{
            // Convert km to meters
            const cPositions = positions.map(p => Cesium.Cartesian3.fromElements(p[0] * 1000, p[1] * 1000, p[2] * 1000));
            viewer.entities.add({{
                name: name,
                polyline: {{
                    positions: cPositions,
                    width: 3,
                    material: new Cesium.PolylineGlowMaterialProperty({{ glowColor: Cesium.Color.fromCssColorString(color), glowPower: 0.2 }})
                }}
            }});
        }}

        addOrbit(posA, '#00FFFF', 'ISS');
        addOrbit(posB, '#FF0055', 'STARLINK');

        // 4. Set camera view
        viewer.camera.setView({{ destination: Cesium.Cartesian3.fromDegrees(0, 0, 20000000.0) }});
        
        // 5. Force a render after a short delay (helps with iframe initialization)
        setTimeout(() => {{ viewer.render(); }}, 1000);
    </script>
</body>
</html>
"""

components.html(cesium_html, height=400, scrolling=False)

# ... (aapka baaki code jaise terminal logs waisa hi rahega) ...
