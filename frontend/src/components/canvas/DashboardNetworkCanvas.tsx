import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

export function DashboardNetworkCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const width = container.clientWidth || 800;
    const height = container.clientHeight || 240;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 500);
    camera.position.z = 100;

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

    const count = 30;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const velocities = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 140;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 80;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 30;

      velocities[i * 3] = (Math.random() - 0.5) * 0.04;
      velocities[i * 3 + 1] = (Math.random() - 0.5) * 0.04;
      velocities[i * 3 + 2] = 0;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const material = new THREE.PointsMaterial({
      color: new THREE.Color('#8B5CF6'),
      size: 3,
      transparent: true,
      opacity: 0.5,
    });

    const points = new THREE.Points(geometry, material);
    scene.add(points);

    // Line segments
    const linesGeo = new THREE.BufferGeometry();
    const linePos = new Float32Array(count * count * 6);
    linesGeo.setAttribute('position', new THREE.BufferAttribute(linePos, 3));

    const linesMat = new THREE.LineBasicMaterial({
      color: new THREE.Color('#6D28D9'),
      transparent: true,
      opacity: 0.2,
    });

    const lines = new THREE.LineSegments(linesGeo, linesMat);
    scene.add(lines);

    let frameId: number;

    const animate = () => {
      frameId = requestAnimationFrame(animate);

      const pos = geometry.attributes.position.array as Float32Array;
      let lineIdx = 0;

      for (let i = 0; i < count; i++) {
        pos[i * 3] += velocities[i * 3];
        pos[i * 3 + 1] += velocities[i * 3 + 1];

        if (Math.abs(pos[i * 3]) > 70) velocities[i * 3] *= -1;
        if (Math.abs(pos[i * 3 + 1]) > 40) velocities[i * 3 + 1] *= -1;

        for (let j = i + 1; j < count; j++) {
          const dx = pos[i * 3] - pos[j * 3];
          const dy = pos[i * 3 + 1] - pos[j * 3 + 1];
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 35) {
            linePos[lineIdx * 6] = pos[i * 3];
            linePos[lineIdx * 6 + 1] = pos[i * 3 + 1];
            linePos[lineIdx * 6 + 2] = pos[i * 3 + 2];

            linePos[lineIdx * 6 + 3] = pos[j * 3];
            linePos[lineIdx * 6 + 4] = pos[j * 3 + 1];
            linePos[lineIdx * 6 + 5] = pos[j * 3 + 2];
            lineIdx++;
          }
        }
      }

      geometry.attributes.position.needsUpdate = true;
      linesGeo.attributes.position.needsUpdate = true;
      linesGeo.setDrawRange(0, lineIdx * 2);

      points.rotation.z += 0.0003;
      lines.rotation.z += 0.0003;

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
      linesGeo.dispose();
      linesMat.dispose();
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return <div ref={containerRef} className="absolute inset-0 w-full h-full pointer-events-none overflow-hidden rounded-2xl" />;
}

export default DashboardNetworkCanvas;
