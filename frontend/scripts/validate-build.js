#!/usr/bin/env node

/**
 * Build Validation Script
 * Validates the frontend build for common issues that cause initialization errors
 */

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const distDir = path.resolve(__dirname, '../dist')
const assetsDir = path.join(distDir, 'assets')

console.log('🔍 Validating frontend build...')

// Validation results
let hasErrors = false
let hasWarnings = false
const errors = []
const warnings = []

function addError(message) {
  errors.push(message)
  hasErrors = true
}

function addWarning(message) {
  warnings.push(message)
  hasWarnings = true
}

// Check if dist directory exists
if (!fs.existsSync(distDir)) {
  addError('❌ dist directory does not exist. Run npm run build first.')
  process.exit(1)
}

// Check if assets directory exists
if (!fs.existsSync(assetsDir)) {
  addError('❌ assets directory does not exist in dist folder.')
  process.exit(1)
}

// Get all JavaScript files
const jsFiles = fs.readdirSync(assetsDir)
  .filter(file => file.endsWith('.js'))
  .map(file => path.join(assetsDir, file))

console.log(`📦 Found ${jsFiles.length} JavaScript files:`)
jsFiles.forEach(file => {
  const filename = path.basename(file)
  const size = (fs.statSync(file).size / 1024).toFixed(1)
  console.log(`   • ${filename} (${size}KB)`)
})

// Validate each JavaScript file
for (const file of jsFiles) {
  const filename = path.basename(file)
  const content = fs.readFileSync(file, 'utf8')
  
  // Check for common initialization error patterns
  const initErrorPatterns = [
    /Cannot access '.*' before initialization/,
    /ReferenceError.*before initialization/,
    /Uncaught ReferenceError/,
    /undefined is not a function/,
    /Cannot read propert.*of undefined/,
  ]
  
  for (const pattern of initErrorPatterns) {
    if (pattern.test(content)) {
      addError(`❌ ${filename}: Contains potential initialization error pattern: ${pattern}`)
    }
  }
  
  // Check for circular dependency indicators
  const circularPatterns = [
    /import.*from.*import/,  // Suspicious circular import pattern
    /export.*import.*export/, // Suspicious re-export pattern
  ]
  
  for (const pattern of circularPatterns) {
    if (pattern.test(content)) {
      addWarning(`⚠️  ${filename}: Contains potential circular dependency pattern`)
    }
  }
  
  // Check for problematic minification patterns
  const minificationIssues = [
    /var [a-zA-Z]{1,2}=.*\1/, // Variable referencing itself
    /function [a-zA-Z]{1,2}\([^)]*\)\{.*\1/, // Function referencing itself in problematic way
  ]
  
  for (const pattern of minificationIssues) {
    if (pattern.test(content)) {
      addWarning(`⚠️  ${filename}: Contains potentially problematic minification pattern`)
    }
  }
  
  // Check file size
  const sizeKB = fs.statSync(file).size / 1024
  if (sizeKB > 2000) {
    addWarning(`⚠️  ${filename}: Large bundle size (${sizeKB.toFixed(1)}KB). Consider code splitting.`)
  }
  
  // Check for proper ES module structure
  if (!content.includes('import') && !content.includes('export') && !content.includes('__vite__')) {
    addWarning(`⚠️  ${filename}: No ES module imports/exports detected. May indicate bundling issue.`)
  }
}

// Check index.html exists and has correct script references
const indexPath = path.join(distDir, 'index.html')
if (!fs.existsSync(indexPath)) {
  addError('❌ index.html not found in dist directory')
} else {
  const indexContent = fs.readFileSync(indexPath, 'utf8')
  
  // Check that all JS files are referenced
  const jsFilenames = jsFiles.map(file => path.basename(file))
  const missingRefs = jsFilenames.filter(filename => !indexContent.includes(filename))
  
  if (missingRefs.length > 0) {
    addError(`❌ index.html missing references to: ${missingRefs.join(', ')}`)
  }
  
  // Check for proper module type
  if (!indexContent.includes('type="module"')) {
    addWarning('⚠️  index.html scripts should have type="module" for proper ES module loading')
  }
}

// Check for expected chunks based on vite.config.js
const expectedChunks = ['react-vendor', 'ui-vendor', 'utils-vendor']
const foundChunks = jsFiles
  .map(file => path.basename(file))
  .map(filename => filename.replace(/-[a-f0-9]+\.js$/, '')) // Remove hash
  .filter(name => expectedChunks.includes(name))

const missingChunks = expectedChunks.filter(chunk => !foundChunks.includes(chunk))
if (missingChunks.length > 0) {
  addWarning(`⚠️  Expected chunks not found: ${missingChunks.join(', ')}`)
}

// Report results
console.log('\n📊 Validation Results:')

if (errors.length > 0) {
  console.log('\n❌ ERRORS:')
  errors.forEach(error => console.log(`   ${error}`))
}

if (warnings.length > 0) {
  console.log('\n⚠️  WARNINGS:')
  warnings.forEach(warning => console.log(`   ${warning}`))
}

if (!hasErrors && !hasWarnings) {
  console.log('✅ All validations passed! Build appears to be healthy.')
} else if (!hasErrors) {
  console.log('✅ No critical errors found, but there are warnings to review.')
} else {
  console.log('❌ Critical errors found that may cause runtime issues.')
}

console.log('\n📋 Summary:')
console.log(`   • JavaScript files: ${jsFiles.length}`)
console.log(`   • Total bundle size: ${(jsFiles.reduce((total, file) => total + fs.statSync(file).size, 0) / 1024).toFixed(1)}KB`)
console.log(`   • Errors: ${errors.length}`)
console.log(`   • Warnings: ${warnings.length}`)

// Exit with appropriate code
process.exit(hasErrors ? 1 : 0)