/**
 * T030 User Preferences Enhancement: Global Test Teardown
 * Global teardown for all T030 preference tests
 */

module.exports = async () => {
  // Performance report
  if (global.testErrors && global.testErrors.length > 0) {
    console.warn('⚠️  Test errors encountered:');
    global.testErrors.forEach(error => {
      console.warn('   -', error);
    });
  }
  
  // Cleanup global variables
  delete global.testErrors;
  delete global.performanceMarks;
  delete global.mockServiceDefaults;
  delete global.testAccessibility;
  delete global.mobileTestUtils;
  delete global.performanceTestUtils;
  
  // Cleanup environment variables
  delete process.env.REACT_APP_TEST_MODE;
  
  // Memory cleanup
  if (global.gc) {
    global.gc();
  }
  
  console.log('✅ T030 Global test teardown completed');
};