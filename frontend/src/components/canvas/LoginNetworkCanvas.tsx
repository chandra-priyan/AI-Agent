import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

export function LoginNetworkCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Check reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    const width = container.clientWidth || window.innerWidth / 2;
    const height = container.clientHeight || window.innerHeight;

    // 1. Scene, Camera, Renderer setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
    camera.position.z = 120;

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    renderer.domElement.style.pointerEvents = 'none';
    renderer.domElement.style.position = 'absolute';
    renderer.domElement.style.top = '0';
    renderer.domElement.style.left = '0';
    renderer.domElement.style.width = '100%';
    renderer.domElement.style.height = '100%';
    container.appendChild(renderer.domElement);

    // 2. Create Particles
    const isMobile = window.innerWidth < 768;
    const particleCount = isMobile ? 35 : 70;

    const particlesGeometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const originalPositions = new Float32Array(particleCount * 3);
    const velocities = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    const palette = [
      new THREE.Color('#4F46E5'),
      new THREE.Color('#6B63E8'),
      new THREE.Color('#9B78F0'),
    ];

    for (let i = 0; i < particleCount; i++) {
      const x = (Math.random() - 0.5) * 160;
      const y = (Math.random() - 0.5) * 120;
      const z = (Math.random() - 0.5) * 60;

      positions[i * 3] = x;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = z;

      originalPositions[i * 3] = x;
      originalPositions[i * 3 + 1] = y;
      originalPositions[i * 3 + 2] = z;

      velocities[i * 3] = (Math.random() - 0.5) * 0.08;
      velocities[i * 3 + 1] = (Math.random() - 0.5) * 0.08;
      velocities[i * 3 + 2] = (Math.random() - 0.5) * 0.04;

      const c = palette[Math.floor(Math.random() * palette.length)];
      colors[i * 3] = c.r;
      colors[i * 3 + 1] = c.g;
      colors[i * 3 + 2] = c.b;
    }

    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particlesGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const particlesMaterial = new THREE.PointsMaterial({
      size: 3.5,
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      sizeAttenuation: true,
    });

    const particleSystem = new THREE.Points(particlesGeometry, particlesMaterial);
    scene.add(particleSystem);

    // 3. Create Line Connections
    const maxConnections = particleCount * 4;
    const linesGeometry = new THREE.BufferGeometry();
    const linePositions = new Float32Array(maxConnections * 6);
    const lineColors = new Float32Array(maxConnections * 6);

    linesGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
    linesGeometry.setAttribute('color', new THREE.BufferAttribute(lineColors, 3));

    const linesMaterial = new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, opacity: 0.35 });

    const lineSegments = new THREE.LineSegments(linesGeometry, linesMaterial);
    scene.add(lineSegments);

    // 4. Mouse Tracking & Lerp
    const mouse = { x: 9999, y: 9999, targetX: 9999, targetY: 9999 };

    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const relativeX = e.clientX - rect.left;
      const relativeY = e.clientY - rect.top;

      mouse.targetX = (relativeX / rect.width) * 160 - 80;
      mouse.targetY = -(relativeY / rect.height) * 120 + 60;
    };

    const handleMouseLeave = () => {
      mouse.targetX = 9999;
      mouse.targetY = 9999;
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseleave', handleMouseLeave);

    // 5. Animation Loop
    let animationFrameId: number;

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      // Lerp mouse
      mouse.x += (mouse.targetX - mouse.x) * 0.05;
      mouse.y += (mouse.targetY - mouse.y) * 0.05;

      const posAttr = particlesGeometry.attributes.position as THREE.BufferAttribute;
      const posArray = posAttr.array as Float32Array;

      let lineVertexIdx = 0;

      for (let i = 0; i < particleCount; i++) {
        // Slow float
        posArray[i * 3] += velocities[i * 3];
        posArray[i * 3 + 1] += velocities[i * 3 + 1];

        // Boundary bounce
        if (Math.abs(posArray[i * 3]) > 85) velocities[i * 3] *= -1;
        if (Math.abs(posArray[i * 3 + 1]) > 65) velocities[i * 3 + 1] *= -1;

        // Gentle soft mouse attraction/repulsion
        if (mouse.x < 9000) {
          const dx = posArray[i * 3] - mouse.x;
          const dy = posArray[i * 3 + 1] - mouse.y;
          const distSq = dx * dx + dy * dy;

          if (distSq < 1600 && distSq > 1) {
            const dist = Math.sqrt(distSq);
            const force = (40 - dist) / 40;
            posArray[i * 3] += (dx / dist) * force * 0.4;
            posArray[i * 3 + 1] += (dy / dist) * force * 0.4;
          }
        }

        // Draw connections
        for (let j = i + 1; j < particleCount; j++) {
          const dx = posArray[i * 3] - posArray[j * 3];
          const dy = posArray[i * 3 + 1] - posArray[j * 3 + 1];
          const dz = posArray[i * 3 + 2] - posArray[j * 3 + 2];
          const distSq = dx * dx + dy * dy + dz * dz;

          if (distSq < 900) { // Distance threshold
            const alpha = 1 - Math.sqrt(distSq) / 30;

            linePositions[lineVertexIdx * 6] = posArray[i * 3];
            linePositions[lineVertexIdx * 6 + 1] = posArray[i * 3 + 1];
            linePositions[lineVertexIdx * 6 + 2] = posArray[i * 3 + 2];

            linePositions[lineVertexIdx * 6 + 3] = posArray[j * 3];
            linePositions[lineVertexIdx * 6 + 4] = posArray[j * 3 + 1];
            linePositions[lineVertexIdx * 6 + 5] = posArray[j * 3 + 2];

            // Blend line colors
            lineColors[lineVertexIdx * 6] = 0.42 * alpha;
            lineColors[lineVertexIdx * 6 + 1] = 0.38 * alpha;
            lineColors[lineVertexIdx * 6 + 2] = 0.91 * alpha;

            lineColors[lineVertexIdx * 6 + 3] = 0.60 * alpha;
            lineColors[lineVertexIdx * 6 + 4] = 0.47 * alpha;
            lineColors[lineVertexIdx * 6 + 5] = 0.94 * alpha;

            lineVertexIdx++;
          }
        }
      }

      posAttr.needsUpdate = true;

      const linePosAttr = linesGeometry.attributes.position as THREE.BufferAttribute;
      const lineColAttr = linesGeometry.attributes.color as THREE.BufferAttribute;
      linePosAttr.needsUpdate = true;
      lineColAttr.needsUpdate = true;

      linesGeometry.setDrawRange(0, lineVertexIdx * 2);

      // Parallax rotation
      particleSystem.rotation.y += 0.0006;
      lineSegments.rotation.y += 0.0006;

      renderer.render(scene, camera);
    };

    animate();

    // 6. Handle Resize
    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener('resize', handleResize);

    // 7. Clean Disposal
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseleave', handleMouseLeave);
      window.removeEventListener('resize', handleResize);

      particlesGeometry.dispose();
      particlesMaterial.dispose();
      linesGeometry.dispose();
      linesMaterial.dispose();
      renderer.dispose();

      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 w-full h-full pointer-events-none overflow-hidden"
    />
  );
}

export default LoginNetworkCanvas;
