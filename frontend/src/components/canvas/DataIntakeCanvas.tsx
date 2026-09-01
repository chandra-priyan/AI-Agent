import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

export function DataIntakeCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const width = container.clientWidth || 800;
    const height = container.clientHeight || 160;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 500);
    camera.position.z = 80;

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

    const particleCount = 40;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const speeds = new Float32Array(particleCount);
    const targetYLines = new Float32Array(particleCount);
    const colors = new Float32Array(particleCount * 3);

    const palette = [
      new THREE.Color('#4F46E5'),
      new THREE.Color('#6B63E8'),
      new THREE.Color('#9B78F0'),
    ];

    const streamYPositions = [-20, -10, 0, 10, 20];

    for (let i = 0; i < particleCount; i++) {
      const x = -90 + Math.random() * 50;
      const y = (Math.random() - 0.5) * 50;
      const z = (Math.random() - 0.5) * 10;

      positions[i * 3] = x;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = z;

      speeds[i] = 0.2 + Math.random() * 0.3;
      targetYLines[i] = streamYPositions[i % streamYPositions.length];

      const c = palette[i % palette.length];
      colors[i * 3] = c.r;
      colors[i * 3 + 1] = c.g;
      colors[i * 3 + 2] = c.b;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: 2.8,
      vertexColors: true,
      transparent: true,
      opacity: 0.5,
      sizeAttenuation: true,
    });

    const particleSystem = new THREE.Points(geometry, material);
    scene.add(particleSystem);

    // Stream lines
    const lineGeo = new THREE.BufferGeometry();
    const linePositions = new Float32Array(streamYPositions.length * 6);
    streamYPositions.forEach((y, idx) => {
      linePositions[idx * 6] = -30;
      linePositions[idx * 6 + 1] = y;
      linePositions[idx * 6 + 2] = 0;

      linePositions[idx * 6 + 3] = 80;
      linePositions[idx * 6 + 4] = y;
      linePositions[idx * 6 + 5] = 0;
    });

    lineGeo.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
    const lineMat = new THREE.LineBasicMaterial({
      color: new THREE.Color('#4F46E5'),
      transparent: true,
      opacity: 0.15,
    });

    const streamLines = new THREE.LineSegments(lineGeo, lineMat);
    scene.add(streamLines);

    let animationFrameId: number;

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      const posArray = geometry.attributes.position.array as Float32Array;

      for (let i = 0; i < particleCount; i++) {
        posArray[i * 3] += speeds[i];

        const progressX = (posArray[i * 3] + 40) / 90;
        if (progressX > 0) {
          const clamped = Math.min(Math.max(progressX, 0), 1);
          const currentY = posArray[i * 3 + 1];
          const targetY = targetYLines[i];
          posArray[i * 3 + 1] += (targetY - currentY) * 0.05 * clamped;
        }

        if (posArray[i * 3] > 80) {
          posArray[i * 3] = -90 - Math.random() * 20;
          posArray[i * 3 + 1] = (Math.random() - 0.5) * 50;
        }
      }

      geometry.attributes.position.needsUpdate = true;
      renderer.render(scene, camera);
    };

    animate();

    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      geometry.dispose();
      material.dispose();
      lineGeo.dispose();
      lineMat.dispose();
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return <div ref={containerRef} className="absolute inset-0 w-full h-full pointer-events-none overflow-hidden rounded-2xl" />;
}

export default DataIntakeCanvas;
