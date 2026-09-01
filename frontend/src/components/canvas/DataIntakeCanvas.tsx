import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

export function DataIntakeCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const width = container.clientWidth || 800;
    const height = container.clientHeight || 200;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 500);
    camera.position.z = 90;

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

    const count = 40;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const speeds = new Float32Array(count);

    for (let i = 0; i < count; i++) {
      const radius = 30 + Math.random() * 50;
      const angle = Math.random() * Math.PI * 2;
      positions[i * 3] = Math.cos(angle) * radius;
      positions[i * 3 + 1] = Math.sin(angle) * radius;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 20;

      speeds[i] = 0.15 + Math.random() * 0.25;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const material = new THREE.PointsMaterial({
      color: new THREE.Color('#4F46E5'),
      size: 2.5,
      transparent: true,
      opacity: 0.45,
    });

    const particles = new THREE.Points(geometry, material);
    scene.add(particles);

    let frameId: number;

    const animate = () => {
      frameId = requestAnimationFrame(animate);

      const pos = geometry.attributes.position.array as Float32Array;

      for (let i = 0; i < count; i++) {
        let x = pos[i * 3];
        let y = pos[i * 3 + 1];

        const dist = Math.sqrt(x * x + y * y);
        if (dist < 4) {
          // Reset to outer boundary
          const angle = Math.random() * Math.PI * 2;
          const r = 50 + Math.random() * 20;
          pos[i * 3] = Math.cos(angle) * r;
          pos[i * 3 + 1] = Math.sin(angle) * r;
        } else {
          // Flow inwards
          pos[i * 3] -= (x / dist) * speeds[i];
          pos[i * 3 + 1] -= (y / dist) * speeds[i];
        }
      }

      geometry.attributes.position.needsUpdate = true;
      particles.rotation.z += 0.002;

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

export default DataIntakeCanvas;
