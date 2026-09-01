import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

export function HypothesisNetworkCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const width = container.clientWidth || 800;
    const height = container.clientHeight || 180;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 500);
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

    const count = 24;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const vels = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 110;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 60;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 20;

      vels[i * 3] = (Math.random() - 0.5) * 0.03;
      vels[i * 3 + 1] = (Math.random() - 0.5) * 0.03;
      vels[i * 3 + 2] = 0;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const material = new THREE.PointsMaterial({
      color: new THREE.Color('#9B78F0'),
      size: 3,
      transparent: true,
      opacity: 0.4,
    });

    const points = new THREE.Points(geometry, material);
    scene.add(points);

    const linesGeo = new THREE.BufferGeometry();
    const linePos = new Float32Array(count * count * 6);
    linesGeo.setAttribute('position', new THREE.BufferAttribute(linePos, 3));

    const linesMat = new THREE.LineBasicMaterial({
      color: new THREE.Color('#8B5CF6'),
      transparent: true,
      opacity: 0.25,
    });

    const lines = new THREE.LineSegments(linesGeo, linesMat);
    scene.add(lines);

    let frameId: number;

    const animate = () => {
      frameId = requestAnimationFrame(animate);

      const pos = geometry.attributes.position.array as Float32Array;
      let idx = 0;

      for (let i = 0; i < count; i++) {
        pos[i * 3] += vels[i * 3];
        pos[i * 3 + 1] += vels[i * 3 + 1];

        if (Math.abs(pos[i * 3]) > 55) vels[i * 3] *= -1;
        if (Math.abs(pos[i * 3 + 1]) > 30) vels[i * 3 + 1] *= -1;

        for (let j = i + 1; j < count; j++) {
          const dx = pos[i * 3] - pos[j * 3];
          const dy = pos[i * 3 + 1] - pos[j * 3 + 1];
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 30) {
            linePos[idx * 6] = pos[i * 3];
            linePos[idx * 6 + 1] = pos[i * 3 + 1];
            linePos[idx * 6 + 2] = pos[i * 3 + 2];

            linePos[idx * 6 + 3] = pos[j * 3];
            linePos[idx * 6 + 4] = pos[j * 3 + 1];
            linePos[idx * 6 + 5] = pos[j * 3 + 2];
            idx++;
          }
        }
      }

      geometry.attributes.position.needsUpdate = true;
      linesGeo.attributes.position.needsUpdate = true;
      linesGeo.setDrawRange(0, idx * 2);

      points.rotation.y += 0.0004;
      lines.rotation.y += 0.0004;

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

  return <div ref={containerRef} className="absolute inset-0 w-full h-full pointer-events-none overflow-hidden rounded-xl" />;
}

export default HypothesisNetworkCanvas;
