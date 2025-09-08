"use client";

import { useState } from 'react';
import { 
  encryptChatId, 
  decryptChatId, 
  generateSecureChatUrl, 
  parseSecureChatUrl
} from '../../utils/urlEncryption';
import { runEncryptionTests } from '../../utils/testEncryption';

export default function TestEncryptionPage() {
  const [testInput, setTestInput] = useState('123');
  const [testResults, setTestResults] = useState<string[]>([]);

  const runSingleTest = () => {
    const results: string[] = [];
    
    try {
      const inputId = parseInt(testInput);
      if (isNaN(inputId) || inputId <= 0) {
        results.push('❌ Please enter a valid positive number');
        setTestResults(results);
        return;
      }

      results.push(`🔍 Testing with Chat ID: ${inputId}`);
      
      // Test encryption
      const encrypted = encryptChatId(inputId);
      results.push(`🔒 Encrypted: ${encrypted}`);
      
      // Test URL generation
      const url = generateSecureChatUrl(inputId);
      results.push(`🌐 URL: ${url}`);
      
      // Test decryption
      const decrypted = decryptChatId(encrypted);
      results.push(`🔓 Decrypted: ${decrypted}`);
      
      // Test URL parsing
      const parsed = parseSecureChatUrl(url);
      results.push(`🔍 Parsed from URL: ${parsed}`);
      
      // Verify results
      const encryptionValid = decrypted === inputId;
      const urlValid = parsed === inputId;
      
      results.push(`✅ Encryption Test: ${encryptionValid ? 'PASSED' : 'FAILED'}`);
      results.push(`✅ URL Test: ${urlValid ? 'PASSED' : 'FAILED'}`);
      
      if (encryptionValid && urlValid) {
        results.push('🎉 All tests passed!');
      } else {
        results.push('❌ Some tests failed!');
      }
      
    } catch (error) {
      results.push(`❌ Error: ${error}`);
    }
    
    setTestResults(results);
  };

  const runFullTestSuite = () => {
    const results: string[] = [];
    results.push('🧪 Running Full Test Suite...\n');
    
    // Capture console.log output
    const originalLog = console.log;
    const logs: string[] = [];
    console.log = (...args) => {
      logs.push(args.join(' '));
      originalLog(...args);
    };
    
    try {
      const success = runEncryptionTests();
      results.push(...logs);
      results.push(`\n🎯 Full Test Suite Result: ${success ? '✅ ALL PASSED' : '❌ SOME FAILED'}`);
    } catch (error) {
      results.push(`❌ Test Suite Error: ${error}`);
    } finally {
      console.log = originalLog;
    }
    
    setTestResults(results);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-8">
          🔐 URL Encryption Test Page
        </h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Single Test Section */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Single Test
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Chat ID to Test:
                </label>
                <input
                  type="number"
                  value={testInput}
                  onChange={(e) => setTestInput(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter a chat ID"
                />
              </div>
              
              <button
                onClick={runSingleTest}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Run Single Test
              </button>
            </div>
          </div>
          
          {/* Full Test Suite Section */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Full Test Suite
            </h2>
            
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Run comprehensive tests on the URL encryption system.
            </p>
            
            <button
              onClick={runFullTestSuite}
              className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              Run Full Test Suite
            </button>
          </div>
        </div>
        
        {/* Results Section */}
        {testResults.length > 0 && (
          <div className="mt-8 bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Test Results
            </h2>
            
            <div className="bg-gray-100 dark:bg-gray-900 rounded-lg p-4 max-h-96 overflow-y-auto">
              {testResults.map((result, index) => (
                <div key={index} className="text-sm font-mono text-gray-800 dark:text-gray-200 mb-1">
                  {result}
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Instructions */}
        <div className="mt-8 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-3">
            📋 How to Use
          </h3>
          
          <div className="space-y-2 text-blue-800 dark:text-blue-200">
            <p>• <strong>Single Test:</strong> Test encryption/decryption with a specific chat ID</p>
            <p>• <strong>Full Test Suite:</strong> Run comprehensive tests on the entire system</p>
            <p>• <strong>Expected URLs:</strong> Should look like <code>/chat/abc123def4567890</code></p>
            <p>• <strong>Security:</strong> Chat IDs are encrypted to prevent enumeration attacks</p>
          </div>
        </div>
      </div>
    </div>
  );
} 