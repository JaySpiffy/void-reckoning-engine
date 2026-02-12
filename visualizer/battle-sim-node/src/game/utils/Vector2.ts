import type { Vector2 } from '../types';

export const Vec2 = {
  create(x: number = 0, y: number = 0): Vector2 {
    return { x, y };
  },

  clone(v: Vector2): Vector2 {
    return { x: v.x, y: v.y };
  },

  add(a: Vector2, b: Vector2): Vector2 {
    return { x: a.x + b.x, y: a.y + b.y };
  },

  sub(a: Vector2, b: Vector2): Vector2 {
    return { x: a.x - b.x, y: a.y - b.y };
  },

  mul(v: Vector2, scalar: number): Vector2 {
    return { x: v.x * scalar, y: v.y * scalar };
  },

  div(v: Vector2, scalar: number): Vector2 {
    return { x: v.x / scalar, y: v.y / scalar };
  },

  magnitude(v: Vector2): number {
    return Math.sqrt(v.x * v.x + v.y * v.y);
  },

  magnitudeSquared(v: Vector2): number {
    return v.x * v.x + v.y * v.y;
  },

  normalize(v: Vector2): Vector2 {
    const mag = this.magnitude(v);
    if (mag === 0) return { x: 0, y: 0 };
    return this.div(v, mag);
  },

  distance(a: Vector2, b: Vector2): number {
    return this.magnitude(this.sub(a, b));
  },

  distanceSquared(a: Vector2, b: Vector2): number {
    return this.magnitudeSquared(this.sub(a, b));
  },

  dot(a: Vector2, b: Vector2): number {
    return a.x * b.x + a.y * b.y;
  },

  lerp(a: Vector2, b: Vector2, t: number): Vector2 {
    return {
      x: a.x + (b.x - a.x) * t,
      y: a.y + (b.y - a.y) * t,
    };
  },

  angle(v: Vector2): number {
    return Math.atan2(v.y, v.x);
  },

  fromAngle(angle: number, magnitude: number = 1): Vector2 {
    return {
      x: Math.cos(angle) * magnitude,
      y: Math.sin(angle) * magnitude,
    };
  },

  zero(): Vector2 {
    return { x: 0, y: 0 };
  },

  equals(a: Vector2, b: Vector2, epsilon: number = 0.0001): boolean {
    return Math.abs(a.x - b.x) < epsilon && Math.abs(a.y - b.y) < epsilon;
  },
};
