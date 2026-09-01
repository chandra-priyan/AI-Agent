import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

export function DatasetGridCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const width = container.clientWidth || 800;
    const height = container.clientHeight || 120;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 500);
    camera.position.z = 70;

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

    const rows = 4;
    const cols = 8;
    const count = rows * cols;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);

    let idx = 0;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        positions[idx * 3] = (c - cols / 2) * 12;
        positions[idx * 3 + 1] = (r - rows / 2) * 10;
        positions[idx * 3 + 2] = 0;
        idx++;
      }
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const material = new THREE.PointsMaterial({
      color: new THREE.Color('#4F46E5'),
      size: 2.5,
      transparent: true,
      opacity: 0.3,
    });

    const points = new THREE.Points(geometry, material);
    scene.add(points);

    let frameId: number;

    const animate = () => {
      frameId = requestAnimationFrame(animate);
      points.position.y = Math.sin(Date.now() * 0.001) * 1.5;
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
      cancelAnimationFrame(frameId);
      window.removeEventListener('resize', handleResize);
      geometry.dispose();
      material.dispose();
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return <div ref={containerRef} className="absolute inset-0 w-full h-full pointer-events-none overflow-hidden rounded-xl" />;
}

export default DatasetGridCanvas;
