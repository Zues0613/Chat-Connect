// Test script for URL encryption functionality
import { 
  encryptChatId, 
  decryptChatId, 
  generateSecureChatUrl, 
  parseSecureChatUrl,
  testEncryption 
} from './urlEncryption';

// Run tests
export const runEncryptionTests = () => {
  console.log('🔐 Testing URL Encryption System...\n');
  
  // Test 1: Basic encryption/decryption
  console.log('Test 1: Basic encryption/decryption');
  const testIds = [1, 2, 100, 1000, 9999];
  let allPassed = true;
  
  testIds.forEach(id => {
    const encrypted = encryptChatId(id);
    const decrypted = decryptChatId(encrypted);
    const passed = id === decrypted;
    allPassed = allPassed && passed;
    
    console.log(`  ID: ${id} -> Encrypted: ${encrypted} -> Decrypted: ${decrypted} ${passed ? '✅' : '❌'}`);
  });
  
  console.log(`\nTest 1 Result: ${allPassed ? '✅ PASSED' : '❌ FAILED'}\n`);
  
  // Test 2: URL generation and parsing
  console.log('Test 2: URL generation and parsing');
  const testUrlIds = [1, 50, 500];
  let urlTestsPassed = true;
  
  testUrlIds.forEach(id => {
    const url = generateSecureChatUrl(id);
    const parsedId = parseSecureChatUrl(url);
    const passed = id === parsedId;
    urlTestsPassed = urlTestsPassed && passed;
    
    console.log(`  ID: ${id} -> URL: ${url} -> Parsed: ${parsedId} ${passed ? '✅' : '❌'}`);
  });
  
  console.log(`\nTest 2 Result: ${urlTestsPassed ? '✅ PASSED' : '❌ FAILED'}\n`);
  
  // Test 3: Edge cases
  console.log('Test 3: Edge cases');
  const edgeCases = [
    { input: 'invalid', expected: null },
    { input: 'abc123def456', expected: null },
    { input: '0', expected: null },
    { input: '-1', expected: null }
  ];
  
  let edgeTestsPassed = true;
  edgeCases.forEach(({ input, expected }) => {
    const result = decryptChatId(input);
    const passed = result === expected;
    edgeTestsPassed = edgeTestsPassed && passed;
    
    console.log(`  Input: "${input}" -> Result: ${result} (Expected: ${expected}) ${passed ? '✅' : '❌'}`);
  });
  
  console.log(`\nTest 3 Result: ${edgeTestsPassed ? '✅ PASSED' : '❌ FAILED'}\n`);
  
  // Test 4: Consistency (same input should always produce same output)
  console.log('Test 4: Consistency test');
  const consistencyId = 123;
  const firstEncryption = encryptChatId(consistencyId);
  const secondEncryption = encryptChatId(consistencyId);
  const consistencyPassed = firstEncryption === secondEncryption;
  
  console.log(`  ID: ${consistencyId}`);
  console.log(`  First encryption: ${firstEncryption}`);
  console.log(`  Second encryption: ${secondEncryption}`);
  console.log(`  Consistency: ${consistencyPassed ? '✅ PASSED' : '❌ FAILED'}\n`);
  
  // Final result
  const overallResult = allPassed && urlTestsPassed && edgeTestsPassed && consistencyPassed;
  console.log(`🎯 OVERALL RESULT: ${overallResult ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED'}`);
  
  return overallResult;
};

// Example usage in browser console:
// import { runEncryptionTests } from './utils/testEncryption';
// runEncryptionTests(); 