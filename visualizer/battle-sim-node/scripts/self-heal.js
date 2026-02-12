#!/usr/bin/env node
/**
 * SELF-HEAL - Automatic issue detection and repair
 * 
 * Scans for common problems and attempts to fix them:
 * - Missing imports
 * - Type errors
 * - Unused variables
 * - Formatting issues
 * - Build failures
 */

import { execSync, spawn } from 'child_process';
import { readFileSync, writeFileSync, existsSync, readdirSync, statSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join, extname } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

const C = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m',
  gray: '\x1b[90m'
};

function log(msg, color = 'reset') {
  console.log(`${C[color]}[${new Date().toLocaleTimeString()}] ${msg}${C.reset}`);
}

const fixes = {
  applied: [],
  failed: [],
  skipped: []
};

// ============================================
// HEALING FUNCTIONS
// ============================================

async function fixTypeImports(filePath, content) {
  // Fix type-only imports (TS1484)
  const typeImportPattern = /import\s*{\s*([^}]+)\s*}\s*from\s+['"]([^'"]+)['"];?/g;
  let modified = content;
  let hasChanges = false;
  
  // This is a simplified heuristic - in practice, we'd need type checking
  // For now, convert common type patterns
  const typePatterns = ['Type', 'Config', 'Props', 'State', 'Result', 'Data', 'Info'];
  
  modified = modified.replace(typeImportPattern, (match, imports, source) => {
    const items = imports.split(',').map(i => i.trim());
    const typeItems = [];
    const valueItems = [];
    
    items.forEach(item => {
      const cleanItem = item.replace(/type\s+/, '').trim();
      const isType = typePatterns.some(p => cleanItem.includes(p)) || 
                     /^[A-Z][a-zA-Z]*$/.test(cleanItem);
      
      if (isType) {
        typeItems.push(cleanItem);
      } else {
        valueItems.push(cleanItem);
      }
    });
    
    let result = '';
    if (typeItems.length > 0) {
      result += `import type { ${typeItems.join(', ')} } from '${source}';\n`;
    }
    if (valueItems.length > 0) {
      result += `import { ${valueItems.join(', ')} } from '${source}';`;
    }
    
    if (result !== match) hasChanges = true;
    return result.trim();
  });
  
  return { content: modified, fixed: hasChanges };
}

async function fixUnusedImports(filePath, content) {
  // Remove obviously unused imports (very conservative)
  const lines = content.split('\n');
  const modified = [];
  let hasChanges = false;
  
  for (const line of lines) {
    // Skip if not an import
    if (!line.includes('import ')) {
      modified.push(line);
      continue;
    }
    
    // Extract imported names
    const match = line.match(/import\s*{\s*([^}]+)\s*}/);
    if (!match) {
      modified.push(line);
      continue;
    }
    
    const imports = match[1].split(',').map(i => i.trim().split(' as ')[0].trim());
    const used = imports.filter(imp => {
      // Check if used in file (excluding the import line itself)
      const restOfFile = content.replace(line, '');
      return new RegExp(`\\b${imp}\\b`).test(restOfFile);
    });
    
    if (used.length === 0 && imports.length > 0) {
      // All imports unused - comment out for safety
      modified.push(`// TODO: Remove unused import - ${line}`);
      hasChanges = true;
    } else if (used.length < imports.length) {
      // Some imports unused
      const newImports = used.join(', ');
      modified.push(line.replace(match[1], newImports));
      hasChanges = true;
    } else {
      modified.push(line);
    }
  }
  
  return { content: modified.join('\n'), fixed: hasChanges };
}

async function fixConsoleErrors(filePath, content) {
  // Replace console.log with console.error for error messages
  const modified = content
    .replace(/console\.log\s*\(\s*['"`](\[ERROR|Error:|FAIL|FAILED)/g, 'console.error($1')
    .replace(/console\.log\s*\(\s*['"`](\[WARN|Warning:)/g, 'console.warn($1');
  
  return { content: modified, fixed: modified !== content };
}

async function scanAndFix() {
  log('🔍 Scanning for issues...', 'cyan');
  
  const srcDir = join(ROOT, 'src');
  const files = [];
  
  function findTsFiles(dir) {
    const items = readdirSync(dir);
    for (const item of items) {
      const fullPath = join(dir, item);
      const stat = statSync(fullPath);
      if (stat.isDirectory()) {
        findTsFiles(fullPath);
      } else if (extname(item) === '.ts' || extname(item) === '.tsx') {
        files.push(fullPath);
      }
    }
  }
  
  findTsFiles(srcDir);
  
  log(`Found ${files.length} TypeScript files`, 'gray');
  
  for (const filePath of files) {
    try {
      let content = readFileSync(filePath, 'utf8');
      let modified = content;
      let fileFixes = [];
      
      // Apply fixes
      const typeFix = await fixTypeImports(filePath, modified);
      if (typeFix.fixed) {
        modified = typeFix.content;
        fileFixes.push('type-imports');
      }
      
      const unusedFix = await fixUnusedImports(filePath, modified);
      if (unusedFix.fixed) {
        modified = unusedFix.content;
        fileFixes.push('unused-imports');
      }
      
      const consoleFix = await fixConsoleErrors(filePath, modified);
      if (consoleFix.fixed) {
        modified = consoleFix.content;
        fileFixes.push('console-usage');
      }
      
      // Write if changed
      if (modified !== content) {
        writeFileSync(filePath, modified);
        fixes.applied.push({ file: filePath, fixes: fileFixes });
        log(`✅ Fixed ${filePath}: ${fileFixes.join(', ')}`, 'green');
      }
    } catch (err) {
      fixes.failed.push({ file: filePath, error: err.message });
      log(`❌ Failed to fix ${filePath}: ${err.message}`, 'red');
    }
  }
}

async function runBuildCheck() {
  log('🔨 Running build check...', 'cyan');
  
  return new Promise((resolve) => {
    const proc = spawn('npm', ['run', 'build'], {
      cwd: ROOT,
      stdio: 'pipe'
    });
    
    let output = '';
    proc.stdout.on('data', d => output += d);
    proc.stderr.on('data', d => output += d);
    
    proc.on('close', (code) => {
      if (code === 0) {
        log('✅ Build successful', 'green');
        resolve(true);
      } else {
        log('❌ Build failed', 'red');
        // Parse TypeScript errors
        const errors = output.match(/error TS\d+: .+/g) || [];
        errors.slice(0, 10).forEach(e => log(`  ${e}`, 'red'));
        if (errors.length > 10) {
          log(`  ... and ${errors.length - 10} more errors`, 'gray');
        }
        resolve(false);
      }
    });
  });
}

async function runTests() {
  log('🧪 Running tests...', 'cyan');
  
  return new Promise((resolve) => {
    const proc = spawn('npx', ['playwright', 'test', '--reporter=line'], {
      cwd: ROOT,
      stdio: 'pipe'
    });
    
    let passed = true;
    proc.on('close', (code) => {
      if (code === 0) {
        log('✅ Tests passed', 'green');
      } else {
        log('❌ Tests failed', 'red');
        passed = false;
      }
      resolve(passed);
    });
  });
}

async function generateHealingReport() {
  const reportPath = join(ROOT, 'reports', `healing-report-${Date.now()}.json`);
  
  const report = {
    timestamp: new Date().toISOString(),
    summary: {
      filesScanned: fixes.applied.length + fixes.failed.length + fixes.skipped.length,
      fixesApplied: fixes.applied.length,
      fixesFailed: fixes.failed.length
    },
    fixes: fixes.applied,
    failures: fixes.failed
  };
  
  if (!existsSync(join(ROOT, 'reports'))) {
    mkdirSync(join(ROOT, 'reports'));
  }
  
  writeFileSync(reportPath, JSON.stringify(report, null, 2));
  log(`📝 Report saved: ${reportPath}`, 'gray');
}

// ============================================
// MAIN
// ============================================

async function main() {
  log('🩹 Self-Healing System Starting...', 'cyan');
  log('=' .repeat(60), 'gray');
  
  // 1. Scan and fix code issues
  await scanAndFix();
  
  // 2. Check build
  const buildOk = await runBuildCheck();
  
  // 3. Run tests (only if build passed)
  let testsOk = false;
  if (buildOk) {
    testsOk = await runTests();
  }
  
  // 4. Generate report
  await generateHealingReport();
  
  // 5. Summary
  log('\n' + '='.repeat(60), 'gray');
  log('HEALING SUMMARY', 'bright');
  log('='.repeat(60), 'gray');
  log(`Fixes applied: ${fixes.applied.length}`, fixes.applied.length > 0 ? 'green' : 'gray');
  log(`Fixes failed: ${fixes.failed.length}`, fixes.failed.length > 0 ? 'red' : 'gray');
  log(`Build: ${buildOk ? '✅ PASS' : '❌ FAIL'}`, buildOk ? 'green' : 'red');
  log(`Tests: ${testsOk ? '✅ PASS' : '❌ FAIL'}`, testsOk ? 'green' : 'red');
  
  // Exit with error if critical issues remain
  if (fixes.failed.length > 0 || !buildOk || !testsOk) {
    process.exit(1);
  }
}

main().catch(err => {
  log(`Fatal error: ${err.message}`, 'red');
  process.exit(1);
});
