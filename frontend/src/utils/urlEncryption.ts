// URL Encryption utility for secure chat URLs
// Uses a stable encryption to generate consistent 16-character IDs

const ENCRYPTION_KEY = 'chatconnect_2024_secure_v2';

// Simple but stable hash function
const simpleHash = (str: string): string => {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash).toString(36);
};

// Generate a stable encrypted ID from chat ID
const generateStableId = (chatId: string): string => {
  const seed = `${chatId}_${ENCRYPTION_KEY}`;
  const hash = simpleHash(seed);
  
  // Convert to base36 and ensure it's 16 characters
  let encrypted = hash;
  while (encrypted.length < 16) {
    encrypted = simpleHash(encrypted + seed);
  }
  
  // Take first 16 characters and ensure alphanumeric
  return encrypted.substring(0, 16).replace(/[^a-zA-Z0-9]/g, 'a');
};

// Encrypt chat ID for URL (stable, always same output for same input)
export const encryptChatId = (chatId: number | string): string => {
  const chatIdStr = chatId.toString();
  return generateStableId(chatIdStr);
};

// Decrypt chat ID from URL using brute force (since we need to find the original ID)
export const decryptChatId = (encryptedId: string): number | null => {
  // Try to decode as base36 first (in case it's a simple number)
  try {
    const decoded = parseInt(encryptedId, 36);
    if (!isNaN(decoded) && decoded > 0 && decoded < 1000000) { // Reasonable range
      // Verify this ID would generate the same encrypted ID
      const testEncrypted = encryptChatId(decoded);
      if (testEncrypted === encryptedId) {
        return decoded;
      }
    }
  } catch (error) {
    // Continue to brute force method
  }
  
  // Brute force search for the original ID (only for reasonable ranges)
  // In production, you might want to store a mapping in localStorage or database
  for (let i = 1; i <= 10000; i++) {
    const testEncrypted = encryptChatId(i);
    if (testEncrypted === encryptedId) {
      return i;
    }
  }
  
  console.warn('Cannot decrypt encrypted ID:', encryptedId);
  return null;
};

// Generate secure chat URL
export const generateSecureChatUrl = (chatId: number | string): string => {
  const encryptedId = encryptChatId(chatId);
  return `/chat/${encryptedId}`;
};

// Parse secure chat URL
export const parseSecureChatUrl = (url: string): number | null => {
  try {
    // Extract the encrypted ID from the URL
    const match = url.match(/\/chat\/([^/?]+)/);
    if (!match) return null;
    
    const encryptedId = match[1];
    return decryptChatId(encryptedId);
  } catch (error) {
    console.error('URL parsing error:', error);
    return null;
  }
};

// Check if URL is encrypted
export const isEncryptedUrl = (url: string): boolean => {
  const match = url.match(/\/chat\/([^/?]+)/);
  if (!match) return false;
  
  const encryptedId = match[1];
  // Check if it looks like our 16-character format
  return /^[a-zA-Z0-9]{16}$/.test(encryptedId);
};

// Convert old format URLs to new encrypted format
export const convertToEncryptedUrl = (oldUrl: string): string => {
  const match = oldUrl.match(/chatId=(\d+)/);
  if (!match) return oldUrl;
  
  const chatId = parseInt(match[1], 10);
  return generateSecureChatUrl(chatId);
};

// Test function to verify encryption/decryption works
export const testEncryption = (): void => {
  const testIds = [1, 2, 100, 1000, 9999];
  console.log('Testing URL encryption...');
  
  testIds.forEach(id => {
    const encrypted = encryptChatId(id);
    const decrypted = decryptChatId(encrypted);
    console.log(`ID: ${id} -> Encrypted: ${encrypted} -> Decrypted: ${decrypted} (${id === decrypted ? '✅' : '❌'})`);
  });
}; 