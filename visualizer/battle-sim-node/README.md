# Darwin's Island ReHelixed

A high-performance top-down survival RPG with a deep evolution system. Evolve your genetic makeup, build fortifications, and survive against increasingly dangerous waves of enemies.

## 🎮 Play Now!

**🌐 Live Demo: https://djmsqrvve.com/DarwinsIslandReHelixedWeb**

---

## 🧬 Core Features

- **21 DNA Types**: Fire, Ice, Water, Earth, Wind, Lightning, Poison, Void, Light, Arcane, Grass, Fungus, Insect, Beast, Reptile, Aquatic, Physical, Crystal, Slime, Mech, and Chaos!
- **50+ Evolution Paths**: 3-tier Pokemon-style evolution system with branching choices
- **15 Enemy Types**: Each drops different DNA - from Goblins (Grass) to Chimeras (Chaos)
- **Dynamic DNA System**: Absorb genetic material from defeated enemies. Your character's stats transform permanently based on your genome
- **Genetic Mutation Shop**: Earn mutation points to stabilize your DNA or gain permanent resistances
- **Building & Fortification**: Place Walls and automated Sentry Towers
- **Autoplay System**: AI-controlled player for testing (Toggle with F9)

## 🚀 Getting Started

### Launching the Game
```bash
./run.sh
```

### Manual Startup
```bash
npm install
npm run dev
```

## 🎮 Controls

| Key | Action |
|-----|--------|
| **WASD** | Move Character |
| **Mouse** | Aim/Shoot |
| **1-5** | Use Ability Slots |
| **B** | Toggle Build Mode |
| **T** | Open Element Evolution |
| **Y** | Open DNA Evolution |
| **M** | Open Mutation Shop |
| **F9** | Toggle Autoplay AI |
| **F10** | Debug Panel (Unlock All!) |
| **ESC / P** | Pause |

## 🧪 Testing Features

Press **F10** in-game to open the Debug Panel:

- **🚀 UNLOCK ALL CONTENT** - Max stats, all abilities, Wave 10, extreme loot
- **Give All DNA** - Instantly get 80 of every DNA type
- **Spawn Enemies** - Spawn any enemy type instantly
- **Testing Mode** - 10x drop rates, better rarity

Perfect for testing late-game evolutions!

## 📁 Project Architecture

- `src/game/systems/`: Core logic (DNA, NPC, Combat, Building, Loot)
- `src/game/entities/`: Physical objects (Player, Enemy, Projectile)
- `src/game/ui/`: React UI components (Evolution panels, HUD)
- `src/game/systems/EvolutionTree.ts`: 1000+ lines of evolution paths!

## 🛠️ Tech Stack

- **Framework**: React 19 + TypeScript
- **Bundler**: Vite 7
- **Styling**: Tailwind CSS
- **Testing**: Playwright

## 🌐 Deployment

```bash
./deploy.sh
```

**Live Site:** https://djmsqrvve.com/DarwinsIslandReHelixedWeb/

---

## 🔖 Version History

### v0.02 - Major Content Expansion (Current)
- **10 New Enemy Types** - Full DNA variety (Spider, Wolf, Manticore, Serpent, Golem, Crystal Walker, Storm Bird, Slime Boss, Light Warden, Chimera)
- **Evolution Spam Fixed** - Each path only offered once
- **Fast Forward Mode** - Instantly unlock all content
- **Loot Notifications** - Real-time drop notifications
- **Enhanced UI** - Animations, shimmer effects, better UX

### v0.01 - Initial Release
- Core DNA system with 21 types
- Basic evolution paths
- Building system
- Autoplay AI
- Wave-based combat

---

*Darwin's Island ReHelixed - Evolve. Build. Survive.*
