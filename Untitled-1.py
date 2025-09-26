<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Frame Difference Visualization</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background: #000;
            color: #fff;
            font-family: 'Arial', sans-serif;
            overflow: hidden;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }

        .container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;
            padding: 20px;
        }

        .video-container {
            position: relative;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            justify-content: center;
        }

        .video-wrapper {
            position: relative;
            border: 2px solid #333;
            border-radius: 8px;
            overflow: hidden;
            background: #111;
        }

        video, canvas {
            display: block;
            width: 320px;
            height: 240px;
            object-fit: cover;
        }

        .label {
            position: absolute;
            top: 5px;
            left: 5px;
            background: rgba(0, 0, 0, 0.8);
            color: #fff;
            padding: 5px 10px;
            font-size: 12px;
            border-radius: 4px;
            font-weight: bold;
        }

        .controls {
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
            justify-content: center;
        }

        button {
            background: linear-gradient(45deg, #ff6b6b, #ff8e8e);
            border: none;
            color: white;
            padding: 12px 20px;
            font-size: 14px;
            font-weight: bold;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 107, 107, 0.5);
        }

        button:disabled {
            background: #444;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        .slider-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .slider {
            width: 120px;
            height: 6px;
            border-radius: 3px;
            background: #333;
            outline: none;
            -webkit-appearance: none;
        }

        .slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: #ff6b6b;
            cursor: pointer;
            box-shadow: 0 2px 6px rgba(255, 107, 107, 0.5);
        }

        .slider::-moz-range-thumb {
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: #ff6b6b;
            cursor: pointer;
            border: none;
            box-shadow: 0 2px 6px rgba(255, 107, 107, 0.5);
        }

        .status {
            font-size: 14px;
            color: #aaa;
            text-align: center;
        }

        .stats {
            display: flex;
            gap: 20px;
            font-size: 12px;
            color: #888;
        }

        .error {
            color: #ff6b6b;
            background: rgba(255, 107, 107, 0.1);
            padding: 10px;
            border-radius: 5px;
            border: 1px solid rgba(255, 107, 107, 0.3);
        }

        @media (max-width: 768px) {
            .video-container {
                flex-direction: column;
            }
            video, canvas {
                width: 280px;
                height: 210px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="video-container">
            <div class="video-wrapper">
                <video id="videoElement" autoplay muted></video>
                <div class="label">Live Camera</div>
            </div>
            <div class="video-wrapper">
                <canvas id="diffCanvas"></canvas>
                <div class="label">Frame Difference</div>
            </div>
        </div>

        <div class="controls">
            <button id="startBtn">Start Camera</button>
            <button id="stopBtn" disabled>Stop</button>
            
            <div class="slider-group">
                <label>Sensitivity:</label>
                <input type="range" id="thresholdSlider" class="slider" min="10" max="100" value="30">
                <span id="thresholdValue">30</span>
            </div>
            
            <div class="slider-group">
                <label>Smoothing:</label>
                <input type="range" id="smoothingSlider" class="slider" min="0.1" max="1" step="0.1" value="0.7">
                <span id="smoothingValue">0.7</span>
            </div>
        </div>

        <div class="status" id="status">Click "Start Camera" to begin</div>
        
        <div class="stats">
            <div>FPS: <span id="fps">0</span></div>
            <div>Motion Level: <span id="motionLevel">0</span>%</div>
            <div>Pixels Changed: <span id="pixelsChanged">0</span></div>
        </div>
    </div>

    <script>
        let video, canvas, ctx;
        let isRunning = false;
        let previousFrame = null;
        let animationId = null;
        
        let threshold = 30;
        let smoothing = 0.7;
        
        let frameCount = 0;
        let lastTime = performance.now();
        let fps = 0;

        // Get DOM elements
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const status = document.getElementById('status');
        const thresholdSlider = document.getElementById('thresholdSlider');
        const smoothingSlider = document.getElementById('smoothingSlider');
        const thresholdValue = document.getElementById('thresholdValue');
        const smoothingValue = document.getElementById('smoothingValue');
        const fpsDisplay = document.getElementById('fps');
        const motionLevelDisplay = document.getElementById('motionLevel');
        const pixelsChangedDisplay = document.getElementById('pixelsChanged');

        function init() {
            video = document.getElementById('videoElement');
            canvas = document.getElementById('diffCanvas');
            ctx = canvas.getContext('2d');
            
            canvas.width = 320;
            canvas.height = 240;
            
            setupEventListeners();
        }

        function setupEventListeners() {
            startBtn.addEventListener('click', startCamera);
            stopBtn.addEventListener('click', stopCamera);
            
            thresholdSlider.addEventListener('input', (e) => {
                threshold = parseInt(e.target.value);
                thresholdValue.textContent = threshold;
            });
            
            smoothingSlider.addEventListener('input', (e) => {
                smoothing = parseFloat(e.target.value);
                smoothingValue.textContent = smoothing;
            });
        }

        async function startCamera() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { 
                        width: 320, 
                        height: 240,
                        frameRate: 30
                    } 
                });
                
                video.srcObject = stream;
                video.play();
                
                video.addEventListener('loadeddata', () => {
                    isRunning = true;
                    startBtn.disabled = true;
                    stopBtn.disabled = false;
                    status.textContent = 'Camera active - analyzing frame differences';
                    processFrames();
                });
                
            } catch (err) {
                status.innerHTML = `<div class="error">Camera access denied: ${err.message}</div>`;
            }
        }

        function stopCamera() {
            isRunning = false;
            
            if (video.srcObject) {
                video.srcObject.getTracks().forEach(track => track.stop());
                video.srcObject = null;
            }
            
            if (animationId) {
                cancelAnimationFrame(animationId);
            }
            
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            previousFrame = null;
            
            startBtn.disabled = false;
            stopBtn.disabled = true;
            status.textContent = 'Camera stopped';
            
            fpsDisplay.textContent = '0';
            motionLevelDisplay.textContent = '0';
            pixelsChangedDisplay.textContent = '0';
        }

        function processFrames() {
            if (!isRunning) return;
            
            // Calculate FPS
            frameCount++;
            const currentTime = performance.now();
            if (currentTime - lastTime >= 1000) {
                fps = Math.round((frameCount * 1000) / (currentTime - lastTime));
                fpsDisplay.textContent = fps;
                frameCount = 0;
                lastTime = currentTime;
            }
            
            // Create temporary canvas for current frame
            const tempCanvas = document.createElement('canvas');
            const tempCtx = tempCanvas.getContext('2d');
            tempCanvas.width = canvas.width;
            tempCanvas.height = canvas.height;
            
            // Draw current frame
            tempCtx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const currentImageData = tempCtx.getImageData(0, 0, canvas.width, canvas.height);
            const currentPixels = currentImageData.data;
            
            if (previousFrame) {
                const diffImageData = ctx.createImageData(canvas.width, canvas.height);
                const diffPixels = diffImageData.data;
                
                let totalDifference = 0;
                let changedPixels = 0;
                
                // Calculate frame difference
                for (let i = 0; i < currentPixels.length; i += 4) {
                    const rDiff = Math.abs(currentPixels[i] - previousFrame[i]);
                    const gDiff = Math.abs(currentPixels[i + 1] - previousFrame[i + 1]);
                    const bDiff = Math.abs(currentPixels[i + 2] - previousFrame[i + 2]);
                    
                    const avgDiff = (rDiff + gDiff + bDiff) / 3;
                    totalDifference += avgDiff;
                    
                    if (avgDiff > threshold) {
                        // Highlight changed pixels
                        diffPixels[i] = Math.min(255, avgDiff * 3);     // Red
                        diffPixels[i + 1] = Math.min(255, avgDiff * 2); // Green  
                        diffPixels[i + 2] = Math.min(255, avgDiff);     // Blue
                        diffPixels[i + 3] = 255; // Alpha
                        changedPixels++;
                    } else {
                        // Keep background dark
                        diffPixels[i] = avgDiff * 0.3;
                        diffPixels[i + 1] = avgDiff * 0.3;
                        diffPixels[i + 2] = avgDiff * 0.3;
                        diffPixels[i + 3] = 255;
                    }
                }
                
                // Update display
                ctx.putImageData(diffImageData, 0, 0);
                
                // Calculate motion statistics
                const totalPixels = (canvas.width * canvas.height);
                const motionPercentage = Math.round((changedPixels / totalPixels) * 100);
                motionLevelDisplay.textContent = motionPercentage;
                pixelsChangedDisplay.textContent = changedPixels.toLocaleString();
            } else {
                // First frame - just show black
                ctx.fillStyle = '#000';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
            }
            
            // Store current frame for next comparison (with smoothing)
            if (previousFrame) {
                for (let i = 0; i < currentPixels.length; i++) {
                    previousFrame[i] = previousFrame[i] * smoothing + currentPixels[i] * (1 - smoothing);
                }
            } else {
                previousFrame = new Uint8ClampedArray(currentPixels);
            }
            
            animationId = requestAnimationFrame(processFrames);
        }

        // Initialize when page loads
        window.addEventListener('load', init);
    </script>
</body>
</html>