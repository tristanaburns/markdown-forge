/**
 * @file logger.ts
 * @description Logger utility for the Markdown Forge application
 * @module Logger
 */

import winston from 'winston';
import path from 'path';
import { config } from '../config';

// Define log levels
const levels = {
  error: 0,
  warn: 1,
  info: 2,
  http: 3,
  debug: 4,
};

// Define log level based on environment
const level = (): string => {
  const env = config.env || 'development';
  const isDevelopment = env === 'development';
  return isDevelopment ? 'debug' : 'warn';
};

// Define log colors
const colors = {
  error: 'red',
  warn: 'yellow',
  info: 'green',
  http: 'magenta',
  debug: 'white',
};

// Add colors to Winston
winston.addColors(colors);

// Define log format
const format = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss:ms' }),
  winston.format.colorize({ all: true }),
  winston.format.printf(
    (info) => `${info.timestamp} ${info.level}: ${info.message}`,
  ),
);

// Define log file paths
const logDir = config.paths.logs;
const errorLogPath = path.join(logDir, 'error.log');
const combinedLogPath = path.join(logDir, 'combined.log');

// Create the logger
export const logger = winston.createLogger({
  level: level(),
  levels,
  format,
  transports: [
    // Write all logs with level 'error' and below to error.log
    new winston.transports.File({
      filename: errorLogPath,
      level: 'error',
    }),
    // Write all logs with level 'info' and below to combined.log
    new winston.transports.File({
      filename: combinedLogPath,
    }),
  ],
});

// If we're not in production, log to the console as well
if (config.env !== 'production') {
  logger.add(
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple(),
      ),
    }),
  );
}

// Create a stream object for Morgan
export const stream = {
  write: (message: string): void => {
    logger.http(message.trim());
  },
}; 