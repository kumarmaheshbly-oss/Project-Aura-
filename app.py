# ... (aapka baaki code waisa hi rahega, jaise metrics aur terminal) ...

# --- CesiumJS 3D Earth (Fixed Version) ---
st.markdown("<p style='color:#00FFFF; font-size:14px; margin-bottom:5px;'>🌐 3D ORBITAL KINEMATICS (CESIUM ENGINE)</p>", unsafe_allow_html=True)

# Convert positions to JSON for JS
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
        .cesium-viewer-bottom {{ display: none !important; }} /* Hide Cesium logo */
    </style>
</head>
<body>
    <div id="cesiumContainer"></div>
    <script>
        // 1. IMPORTANT: No Ion token required for this basic globe setup
        Cesium.Ion.defaultAccessToken = undefined; 

        // 2. IMPORTANT: Set a base URL for Cesium assets (Workers, Assets, Widgets)
        window.CESIUM_BASE_URL = 'https://cesium.com/downloads/cesiumjs/releases/1.119/Build/Cesium/';

        const viewer = new Cesium.Viewer('cesiumContainer', {{
            // Using a simple dark imagery provider that doesn't need a token
            imageryProvider: new Cesium.GridImageryProvider({{
                color: Cesium.Color.BLACK,
                glowColor: Cesium.Color.CYAN.withAlpha(0.2),
                cells: 10
            }}),
            baseLayerPicker: false,
            geocoder: false,
            homeButton: false,
            sceneModePicker: false,
            navigationHelpButton: false,
            animation: false,
            timeline: false,
            fullscreenButton: false,
            infoBox: false,       // Fixes the sandbox script blocking error[reference:4]
            selectionIndicator: false
        }});

        // Dark mode for Earth
        viewer.scene.globe.baseColor = Cesium.Color.BLACK;
        viewer.scene.globe.enableLighting = false;
        viewer.scene.backgroundColor = Cesium.Color.BLACK;
        viewer.scene.skyBox.show = false; // Hide skybox to make orbits pop

        // --- Orbit Data ---
        const posA = {js_pos_a};
        const posB = {js_pos_b};

        function addOrbit(positions, color, name) {{
            // Convert km to meters for Cesium
            const cPositions = positions.map(p => Cesium.Cartesian3.fromElements(p[0] * 1000, p[1] * 1000, p[2] * 1000));
            
            viewer.entities.add({{
                name: name,
                polyline: {{
                    positions: cPositions,
                    width: 3,
                    material: new Cesium.PolylineGlowMaterialProperty({{ 
                        glowPower: 0.3, 
                        color: Cesium.Color.fromCssColorString(color) 
                    }})
                }}
            }});
        }}

        addOrbit(posA, '#00FFFF', 'ISS');      // Cyan
        addOrbit(posB, '#FF0055', 'STARLINK'); // Pink

        // 3. Fly camera to view the orbits from a good angle
        viewer.camera.setView({{
            destination: Cesium.Cartesian3.fromDegrees(0, 0, 20000000.0) // 20,000 km away
        }});
    </script>
</body>
</html>
"""

# Embed Cesium inside Streamlit with allow-scripts and allow-same-origin
components.html(cesium_html, height=400, scrolling=False)

# ... (aapka baaki code jaise terminal logs waisa hi rahega) ...
