export enum EncryptionMode {
  PLAIN = 'PLAIN',
  AES = 'AES',
  HOMOMORPHIC = 'HOMOMORPHIC',
}

export interface SocketLog {
  id: string;
  timestamp: string;
  sender: 'CLIENT' | 'SERVER';
  type: 'INFO' | 'DATA' | 'Handshake' | 'Error';
  message: string;
  details?: string; // Raw ciphertext or details
}

export interface EncryptedDataPacket {
  id: string;
  originalValue?: number; // Only known to client
  ciphertext: string; // The "BigInt" string representation
}

export interface ChatMessage {
  id: string;
  sender: 'Alice' | 'Bob';
  encryptedContent: string;
  decryptedContent: string;
  iv: string;
  timestamp: number;
}
