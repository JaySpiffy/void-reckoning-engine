import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import { useGalaxyStore } from '../../stores/galaxyStore';
import { GalaxyMapProps } from '../../types/components';
import { getFactionColor, UI_COLORS } from '../../utils/factionColors';
import { SystemTooltip } from './SystemTooltip';
import styles from './GalaxyMap.module.css';

export const GalaxyMap: React.FC<GalaxyMapProps> = ({ className, style, onSystemClick }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    const {
        systems,
        lanes,
        bounds,
        transform,
        updateTransform,
        animations,
        clearExpiredAnimations,
        hoveredSystem,
        setHoveredSystem,
        selectSystem
    } = useGalaxyStore();

    const [isDragging, setIsDragging] = useState(false);
    const [lastMousePos, setLastMousePos] = useState({ x: 0, y: 0 });
    const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

    // Canvas sizing
    const updateCanvasSize = useCallback(() => {
        const canvas = canvasRef.current;
        const container = containerRef.current;
        if (!canvas || !container) return;

        const { width, height } = container.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;

        canvas.width = width * dpr;
        canvas.height = height * dpr;
        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;

        const ctx = canvas.getContext('2d');
        if (ctx) {
            // Reset transformation and set DPR scaling
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        }
    }, []);

    useEffect(() => {
        updateCanvasSize();
        window.addEventListener('resize', updateCanvasSize);
        return () => window.removeEventListener('resize', updateCanvasSize);
    }, [updateCanvasSize]);

    // Auto-fit logic
    const autoFit = useCallback(() => {
        if (!bounds || !containerRef.current || systems.length === 0) return;

        const { width: containerWidth, height: containerHeight } = containerRef.current.getBoundingClientRect();
        const padding = 0.1;

        // Calculate actual bounds from backend data
        const scaleX = (containerWidth * (1 - padding * 2)) / bounds.width;
        const scaleY = (containerHeight * (1 - padding * 2)) / bounds.height;
        const scale = Math.min(scaleX, scaleY, 3.0);

        // Center the galaxy: Subtract min offset * scale, then add centering margin
        const offsetX = -bounds.min_x * scale + (containerWidth - bounds.width * scale) / 2;
        const offsetY = -bounds.min_y * scale + (containerHeight - bounds.height * scale) / 2;

        updateTransform({ scale, x: offsetX, y: offsetY });
    }, [bounds, systems, updateTransform]);

    // Apply auto-fit when data loads
    useEffect(() => {
        if (systems.length > 0 && transform.scale === 1 && transform.x === 0) {
            autoFit();
        }
    }, [systems, autoFit, transform.scale, transform.x]);

    // Mouse to world coords
    const screenToWorld = useCallback((screenX: number, screenY: number) => {
        return {
            x: (screenX - transform.x) / transform.scale,
            y: (screenY - transform.y) / transform.scale
        };
    }, [transform.scale, transform.x, transform.y]);

    // Mouse handlers
    const handleMouseDown = (e: React.MouseEvent) => {
        setIsDragging(true);
        setLastMousePos({ x: e.clientX, y: e.clientY });
    };

    const handleMouseMove = (e: React.MouseEvent) => {
        const rect = canvasRef.current?.getBoundingClientRect();
        if (rect) {
            setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
        }

        if (isDragging) {
            const dx = e.clientX - lastMousePos.x;
            const dy = e.clientY - lastMousePos.y;
            updateTransform({ x: transform.x + dx, y: transform.y + dy });
            setLastMousePos({ x: e.clientX, y: e.clientY });
        }

        // Hover detection
        if (rect) {
            const worldCoords = screenToWorld(e.clientX - rect.left, e.clientY - rect.top);
            let found: string | null = null;
            for (const system of systems) {
                const dist = Math.sqrt(Math.pow(system.x - worldCoords.x, 2) + Math.pow(system.y - worldCoords.y, 2));
                if (dist < 15 / transform.scale) {
                    found = system.name;
                    break;
                }
            }
            setHoveredSystem(found);
        }
    };

    const handleMouseUp = () => setIsDragging(false);

    const handleWheel = (e: React.WheelEvent) => {
        e.preventDefault();
        const zoomSpeed = 0.1;
        const delta = e.deltaY > 0 ? 1 - zoomSpeed : 1 + zoomSpeed;
        const newScale = Math.max(0.05, Math.min(5, transform.scale * delta));

        // Zoom towards mouse position
        const rect = canvasRef.current?.getBoundingClientRect();
        if (rect) {
            const mx = e.clientX - rect.left;
            const my = e.clientY - rect.top;
            const worldX = (mx - transform.x) / transform.scale;
            const worldY = (my - transform.y) / transform.scale;
            const newX = mx - worldX * newScale;
            const newY = my - worldY * newScale;

            updateTransform({ scale: newScale, x: newX, y: newY });
        }
    };

    const handleClick = () => {
        if (hoveredSystem) {
            selectSystem(hoveredSystem);
            onSystemClick?.(hoveredSystem);
        } else {
            selectSystem(null);
        }
    };

    // Rendering
    useEffect(() => {
        let rafId: number;
        const canvas = canvasRef.current;
        const ctx = canvas?.getContext('2d');
        if (!canvas || !ctx) return;

        const render = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            ctx.save();
            ctx.translate(transform.x, transform.y);
            ctx.scale(transform.scale, transform.scale);

            // 1. Draw Lanes
            ctx.beginPath();
            ctx.strokeStyle = UI_COLORS.lane;
            ctx.lineWidth = 1 / transform.scale;
            lanes.forEach(lane => {
                const s1 = systems.find(s => s.name === lane.source);
                const s2 = systems.find(s => s.name === lane.target);
                if (s1 && s2) {
                    ctx.moveTo(s1.x, s1.y);
                    ctx.lineTo(s2.x, s2.y);
                }
            });
            ctx.stroke();

            // 2. Draw Systems
            systems.forEach(system => {
                const isHovered = hoveredSystem === system.name;
                const size = 6 / transform.scale;

                // Draw glow for hovered
                if (isHovered) {
                    ctx.beginPath();
                    ctx.arc(system.x, system.y, size * 2.5, 0, Math.PI * 2);
                    ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
                    ctx.fill();
                }

                // Node count ring? (Optional strategic value visualization)
                if (system.node_count > 1) {
                    ctx.beginPath();
                    ctx.arc(system.x, system.y, size * 2, 0, Math.PI * 2);
                    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
                    ctx.stroke();
                }

                // Draw pie chart for control
                const controlEntries = Object.entries(system.control);
                if (system.total_planets > 0 && controlEntries.length > 0) {
                    let currentAngle = -Math.PI / 2;
                    controlEntries.forEach(([faction, count]) => {
                        const sliceAngle = (count / system.total_planets) * (Math.PI * 2);
                        ctx.beginPath();
                        ctx.moveTo(system.x, system.y);
                        ctx.arc(system.x, system.y, size, currentAngle, currentAngle + sliceAngle);
                        ctx.closePath();
                        ctx.fillStyle = getFactionColor(faction);
                        ctx.fill();
                        currentAngle += sliceAngle;
                    });
                } else {
                    ctx.beginPath();
                    ctx.arc(system.x, system.y, size, 0, Math.PI * 2);
                    ctx.fillStyle = getFactionColor(system.owner);
                    ctx.fill();
                }

                // Stroke
                ctx.beginPath();
                ctx.arc(system.x, system.y, size, 0, Math.PI * 2);
                ctx.strokeStyle = isHovered ? '#fff' : UI_COLORS.systemStroke;
                ctx.lineWidth = 2 / transform.scale;
                ctx.stroke();

                // Label
                if (transform.scale > 0.3) {
                    ctx.font = `${10 / transform.scale}px var(--font-mono)`;
                    ctx.fillStyle = isHovered ? '#fff' : 'rgba(255,255,255,0.7)';
                    ctx.textAlign = 'center';
                    ctx.shadowColor = 'black';
                    ctx.shadowBlur = 4;
                    ctx.fillText(system.name, system.x, system.y + size * 3);
                    ctx.shadowBlur = 0;
                }
            });

            // 3. Draw Animations (Battles)
            const now = Date.now();
            animations.forEach(anim => {
                const age = now - anim.startTime;
                if (age < 2000) {
                    const progress = age / 2000;
                    ctx.beginPath();
                    ctx.arc(anim.x, anim.y, 10 / transform.scale + progress * 20 / transform.scale, 0, Math.PI * 2);
                    ctx.strokeStyle = anim.color;
                    ctx.globalAlpha = 1 - progress;
                    ctx.lineWidth = 2 / transform.scale;
                    ctx.stroke();
                    ctx.globalAlpha = 1.0;
                }
            });

            ctx.restore();

            rafId = requestAnimationFrame(render);
        };

        rafId = requestAnimationFrame(render);
        return () => cancelAnimationFrame(rafId);
    }, [transform, systems, lanes, hoveredSystem, animations]);

    // Cleanup expired animations periodically
    useEffect(() => {
        const interval = setInterval(() => {
            clearExpiredAnimations();
        }, 500);
        return () => clearInterval(interval);
    }, [clearExpiredAnimations]);

    const currentHoveredData = useMemo(() =>
        systems.find(s => s.name === hoveredSystem) || null
        , [systems, hoveredSystem]);

    return (
        <div
            ref={containerRef}
            className={`${styles.mapContainer} ${className || ''}`}
            style={style}
        >
            <canvas
                ref={canvasRef}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
                onWheel={handleWheel}
                onClick={handleClick}
                style={{ cursor: isDragging ? 'grabbing' : (hoveredSystem ? 'pointer' : 'grab') }}
            />
            {currentHoveredData && (
                <SystemTooltip system={currentHoveredData} position={mousePos} />
            )}
        </div>
    );
};
