import { useEffect, useRef, useCallback, useState } from 'react';
import { BattleGameManager } from '../game/managers/BattleGameManager';
import { SIMULATION_CONFIG } from '../game/data/SimulationConfig';

interface CameraState {
    x: number;
    y: number;
    zoom: number;
}

interface BattleCanvasProps {
    game: BattleGameManager;
    camera: CameraState;
    onCameraMove: (deltaX: number, deltaY: number) => void;
    onUnitSelect?: (unitId: string | null) => void;
    selectedUnit?: string | null;
}

export function BattleCanvas({ game, camera, onCameraMove, onUnitSelect, selectedUnit }: BattleCanvasProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const animationRef = useRef<number | undefined>(undefined);
    const lastTimeRef = useRef<number>(0);
    const [hoveredUnit, setHoveredUnit] = useState<string | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const lastMousePos = useRef<{ x: number; y: number } | null>(null);

    const render = useCallback((ctx: CanvasRenderingContext2D, gameRef: BattleGameManager, cam: CameraState) => {
        const canvas = ctx.canvas;
        const width = canvas.width;
        const height = canvas.height;

        // Clear
        ctx.fillStyle = '#020617';
        ctx.fillRect(0, 0, width, height);

        // Camera transform
        ctx.save();
        ctx.translate(width / 2, height / 2);
        ctx.scale(cam.zoom, cam.zoom);
        ctx.translate(-width / 2 + cam.x, -height / 2 + cam.y);

        drawWorldBounds(ctx);
        drawGrid(ctx, cam);

        // Draw projectiles (behind units)
        for (const projectile of gameRef.battle.projectiles) {
            projectile.render(ctx);
        }

        // Draw hit effects (behind units)
        for (const effect of gameRef.battle.hitEffects) {
            effect.render(ctx);
        }

        // Draw interceptors
        for (const interceptor of gameRef.battle.interceptors) {
            interceptor.render(ctx);
        }

        // Draw all units
        for (const unit of gameRef.battle.units.values()) {
            const isHovered = hoveredUnit === unit.id;
            const isSelected = selectedUnit === unit.id;
            unit.render(ctx, isHovered, isSelected);
        }

        ctx.restore();
    }, [hoveredUnit, selectedUnit]);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const resizeCanvas = () => {
            canvas.width = canvas.parentElement?.clientWidth || 1200;
            canvas.height = canvas.parentElement?.clientHeight || 800;
        };
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        const gameLoop = (timestamp: number) => {
            const deltaTime = lastTimeRef.current 
                ? (timestamp - lastTimeRef.current) / 1000 
                : 0;
            lastTimeRef.current = timestamp;

            game.update(Math.min(deltaTime, 0.1));
            render(ctx, game, camera);

            animationRef.current = requestAnimationFrame(gameLoop);
        };

        animationRef.current = requestAnimationFrame(gameLoop);

        return () => {
            window.removeEventListener('resize', resizeCanvas);
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
        };
    }, [game, camera, render]);

    const handleMouseDown = useCallback((e: React.MouseEvent) => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        
        const rect = canvas.getBoundingClientRect();
        const worldX = (e.clientX - rect.left - canvas.width / 2) / camera.zoom + canvas.width / 2 - camera.x;
        const worldY = (e.clientY - rect.top - canvas.height / 2) / camera.zoom + canvas.height / 2 - camera.y;
        
        let clickedUnit: string | null = null;
        for (const unit of game.battle.units.values()) {
            const dist = Math.sqrt(
                Math.pow(unit.position.x - worldX, 2) + 
                Math.pow(unit.position.y - worldY, 2)
            );
            if (dist <= unit.radius * 2) {
                clickedUnit = unit.id;
                break;
            }
        }
        
        if (clickedUnit) {
            onUnitSelect?.(clickedUnit);
        } else {
            setIsDragging(true);
            lastMousePos.current = { x: e.clientX, y: e.clientY };
        }
        e.preventDefault();
    }, [camera, game, onUnitSelect]);

    const handleMouseMove = useCallback((e: React.MouseEvent) => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        
        const rect = canvas.getBoundingClientRect();
        const worldX = (e.clientX - rect.left - canvas.width / 2) / camera.zoom + canvas.width / 2 - camera.x;
        const worldY = (e.clientY - rect.top - canvas.height / 2) / camera.zoom + canvas.height / 2 - camera.y;
        
        let foundHover: string | null = null;
        for (const unit of game.battle.units.values()) {
            if (!unit.isActive) continue;
            const dist = Math.sqrt(
                Math.pow(unit.position.x - worldX, 2) + 
                Math.pow(unit.position.y - worldY, 2)
            );
            if (dist <= unit.radius * 2) {
                foundHover = unit.id;
                break;
            }
        }
        setHoveredUnit(foundHover);

        if (isDragging && lastMousePos.current) {
            const deltaX = e.clientX - lastMousePos.current.x;
            const deltaY = e.clientY - lastMousePos.current.y;
            onCameraMove(deltaX / camera.zoom, deltaY / camera.zoom);
            lastMousePos.current = { x: e.clientX, y: e.clientY };
        }
    }, [isDragging, camera, game, onCameraMove]);

    const handleMouseUp = useCallback(() => {
        setIsDragging(false);
        lastMousePos.current = null;
    }, []);

    return (
        <canvas
            ref={canvasRef}
            className={`w-full h-full ${isDragging ? 'cursor-grabbing' : hoveredUnit ? 'cursor-pointer' : 'cursor-grab'}`}
            style={{ background: '#020617', imageRendering: 'pixelated' }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
        />
    );
}

function drawWorldBounds(ctx: CanvasRenderingContext2D) {
    const w = SIMULATION_CONFIG.worldWidth;
    const h = SIMULATION_CONFIG.worldHeight;
    
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 3;
    ctx.strokeRect(0, 0, w, h);
    
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, w, h);
}

function drawGrid(ctx: CanvasRenderingContext2D, cam: CameraState) {
    const w = SIMULATION_CONFIG.worldWidth;
    const h = SIMULATION_CONFIG.worldHeight;
    const gridSize = 100;

    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1 / cam.zoom;

    for (let x = 0; x <= w; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
    }

    for (let y = 0; y <= h; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
    }

    // Team zones
    const zoneWidth = SIMULATION_CONFIG.spawnMargin + 200;
    ctx.fillStyle = 'rgba(59, 130, 246, 0.03)';
    ctx.fillRect(0, 0, zoneWidth, h);
    ctx.fillStyle = 'rgba(239, 68, 68, 0.03)';
    ctx.fillRect(w - zoneWidth, 0, zoneWidth, h);
}
