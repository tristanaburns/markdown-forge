/**
 * @file index.ts
 * @description Configuration settings for the Markdown Forge application
 * @module Config
 */

import dotenv from 'dotenv';
import path from 'path';

// Load environment variables from .env file
dotenv.config();

// Environment
const env = process.env.NODE_ENV || 'development';

// Base paths
const rootDir = path.resolve(__dirname, '..');
const dataDir = path.join(rootDir, 'data');
const uploadsDir = path.join(dataDir, 'uploads');
const outputDir = path.join(dataDir, 'output');
const logsDir = path.join(dataDir, 'logs');

// Application configuration
export const config = {
  // Environment
  env,
  isDevelopment: env === 'development',
  isProduction: env === 'production',
  isTest: env === 'test',

  // Server
  port: parseInt(process.env.PORT || '5000', 10),
  host: process.env.HOST || 'localhost',

  // Security
  secretKey: process.env.SECRET_KEY || 'default-secret-key',
  corsOrigin: process.env.CORS_ORIGIN || '*',

  // File upload
  maxFileSize: parseInt(process.env.MAX_FILE_SIZE || '10485760', 10), // 10MB
  allowedExtensions: ['md', 'markdown', 'mdown', 'mkdn'],

  // Directories
  paths: {
    root: rootDir,
    data: dataDir,
    uploads: uploadsDir,
    output: outputDir,
    logs: logsDir,
    public: path.join(rootDir, 'public'),
    views: path.join(rootDir, 'views'),
  },

  // Logging
  logLevel: process.env.LOG_LEVEL || 'info',
  logFormat: process.env.LOG_FORMAT || 'json',

  // Conversion settings
  usePandoc: process.env.USE_PANDOC === 'true',
  pandocPath: process.env.PANDOC_PATH || '/usr/bin/pandoc',
  
  // Cleanup settings
  fileRetentionDays: parseInt(process.env.FILE_RETENTION_DAYS || '30', 10),
}; 