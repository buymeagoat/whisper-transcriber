#!/usr/bin/env node

/**
 * Comprehensive Build Testing Script
 * Tests various build configurations to identify initialization error patterns
 */

import { execSync } from 'child_process'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const frontendDir = path.resolve(__dirname, '..')

console.log('🧪 Running comprehensive build tests...')

// Test configurations
const testConfigs = [
  {
    name: 'Current Configuration',
    description: 'Test current vite.config.js settings',
    skipBuild: true, // Use existing build
  },
  {
    name: 'No Minification',
    description: 'Test with minification disabled',
    viteOverrides: {
      build: {
        minify: false,
      }
    }
  },
  {
    name: 'No Code Splitting',
    description: 'Test with code splitting disabled',
    viteOverrides: {
      build: {
        rollupOptions: {
          output: {
            manualChunks: undefined,
          }
        }
      }
    }
  },
  {
    name: 'Conservative Target',
    description: 'Test with ES5 target for maximum compatibility',
    viteOverrides: {
      build: {
        target: 'es5',
      }
    }
  }
]

// Results tracking
const results = []

// Backup original config
const originalConfigPath = path.join(frontendDir, 'vite.config.js')
const backupConfigPath = path.join(frontendDir, 'vite.config.js.backup')
if (!fs.existsSync(backupConfigPath)) {
  fs.copyFileSync(originalConfigPath, backupConfigPath)
}

async function runTest(config) {
  console.log(`\n🔬 Testing: ${config.name}`)
  console.log(`   ${config.description}`)
  
  const testResult = {
    name: config.name,
    success: false,
    buildTime: 0,
    bundleSize: 0,
    errors: [],
    warnings: [],
  }
  
  try {
    if (!config.skipBuild) {
      // Modify vite config for this test
      if (config.viteOverrides) {
        console.log('   📝 Updating vite config...')
        await modifyViteConfig(config.viteOverrides)
      }
      
      // Run build
      console.log('   🔨 Building...')
      const startTime = Date.now()
      
      try {
        const buildOutput = execSync('npm run build', {
          cwd: frontendDir,
          encoding: 'utf8',
          stdio: 'pipe'
        })
        
        testResult.buildTime = Date.now() - startTime
        testResult.success = true
        
        console.log(`   ✅ Build completed in ${testResult.buildTime}ms`)
      } catch (buildError) {
        testResult.errors.push(`Build failed: ${buildError.message}`)
        console.log(`   ❌ Build failed: ${buildError.message.slice(0, 100)}...`)
      }
    } else {
      testResult.success = true
    }
    
    // Validate build output
    if (testResult.success) {
      console.log('   🔍 Validating build...')
      try {
        const validationOutput = execSync('node scripts/validate-build.js', {
          cwd: frontendDir,
          encoding: 'utf8',
          stdio: 'pipe'
        })
        
        // Parse validation output for warnings/errors
        if (validationOutput.includes('❌')) {
          const errorLines = validationOutput.split('\n').filter(line => line.includes('❌'))
          testResult.errors.push(...errorLines)
        }
        
        if (validationOutput.includes('⚠️')) {
          const warningLines = validationOutput.split('\n').filter(line => line.includes('⚠️'))
          testResult.warnings.push(...warningLines)
        }
        
        // Extract bundle size
        const sizeMatch = validationOutput.match(/Total bundle size: ([\d.]+)KB/)
        if (sizeMatch) {
          testResult.bundleSize = parseFloat(sizeMatch[1])
        }
        
        console.log(`   📊 Bundle size: ${testResult.bundleSize}KB`)
        console.log(`   📋 Errors: ${testResult.errors.length}, Warnings: ${testResult.warnings.length}`)
        
      } catch (validationError) {
        testResult.errors.push(`Validation failed: ${validationError.message}`)
        console.log(`   ❌ Validation failed`)
      }
    }
    
  } catch (error) {
    testResult.errors.push(`Test failed: ${error.message}`)
    console.log(`   ❌ Test failed: ${error.message}`)
  } finally {
    // Restore original config
    if (!config.skipBuild && config.viteOverrides) {
      fs.copyFileSync(backupConfigPath, originalConfigPath)
    }
  }
  
  results.push(testResult)
  return testResult
}

async function modifyViteConfig(overrides) {
  // Simple config modification (in a real implementation, you'd want proper AST manipulation)
  const originalConfig = fs.readFileSync(originalConfigPath, 'utf8')
  
  // This is a simplified approach - for production use, consider using a proper AST parser
  let modifiedConfig = originalConfig
  
  if (overrides.build?.minify === false) {
    modifiedConfig = modifiedConfig.replace(
      /minify: isProduction \? 'esbuild' : false,/,
      'minify: false,'
    )
  }
  
  if (overrides.build?.target) {
    modifiedConfig = modifiedConfig.replace(
      /target: 'es2018',/,
      `target: '${overrides.build.target}',`
    )
  }
  
  if (overrides.build?.rollupOptions?.output?.manualChunks === undefined) {
    // Remove manual chunks
    modifiedConfig = modifiedConfig.replace(
      /manualChunks: \{[\s\S]*?\},/,
      ''
    )
  }
  
  fs.writeFileSync(originalConfigPath, modifiedConfig)
}

// Run all tests
async function runAllTests() {
  console.log('🚀 Starting comprehensive build testing...')
  
  for (const config of testConfigs) {
    await runTest(config)
  }
  
  // Generate report
  console.log('\n📊 COMPREHENSIVE TEST REPORT')
  console.log('=' .repeat(50))
  
  const successfulTests = results.filter(r => r.success && r.errors.length === 0)
  const testsWithWarnings = results.filter(r => r.success && r.warnings.length > 0)
  const failedTests = results.filter(r => !r.success || r.errors.length > 0)
  
  console.log(`\n✅ Successful tests: ${successfulTests.length}`)
  console.log(`⚠️  Tests with warnings: ${testsWithWarnings.length}`)
  console.log(`❌ Failed tests: ${failedTests.length}`)
  
  if (successfulTests.length > 0) {
    console.log('\n✅ SUCCESSFUL CONFIGURATIONS:')
    successfulTests.forEach(test => {
      console.log(`   • ${test.name} (${test.bundleSize}KB, ${test.buildTime}ms)`)
    })
  }
  
  if (testsWithWarnings.length > 0) {
    console.log('\n⚠️  CONFIGURATIONS WITH WARNINGS:')
    testsWithWarnings.forEach(test => {
      console.log(`   • ${test.name} (${test.warnings.length} warnings)`)
      test.warnings.slice(0, 3).forEach(warning => {
        console.log(`     - ${warning.slice(0, 80)}...`)
      })
    })
  }
  
  if (failedTests.length > 0) {
    console.log('\n❌ FAILED CONFIGURATIONS:')
    failedTests.forEach(test => {
      console.log(`   • ${test.name}`)
      test.errors.slice(0, 3).forEach(error => {
        console.log(`     - ${error.slice(0, 80)}...`)
      })
    })
  }
  
  // Recommendations
  console.log('\n💡 RECOMMENDATIONS:')
  
  if (successfulTests.length > 0) {
    const bestTest = successfulTests.reduce((best, current) => 
      current.bundleSize < best.bundleSize ? current : best
    )
    console.log(`   • Best configuration: ${bestTest.name} (smallest bundle: ${bestTest.bundleSize}KB)`)
  }
  
  if (failedTests.length > 0) {
    console.log('   • Review failed configurations to understand stability issues')
  }
  
  if (testsWithWarnings.length > 0) {
    console.log('   • Address warnings in configurations with minor issues')
  }
  
  console.log('\n🏁 Testing complete!')
  
  // Exit with error code if current config failed
  const currentConfigResult = results.find(r => r.name === 'Current Configuration')
  if (currentConfigResult && (!currentConfigResult.success || currentConfigResult.errors.length > 0)) {
    console.log('❌ Current configuration has issues!')
    process.exit(1)
  } else {
    console.log('✅ Current configuration appears stable!')
    process.exit(0)
  }
}

// Run the tests
runAllTests().catch(error => {
  console.error('❌ Test runner failed:', error)
  process.exit(1)
})