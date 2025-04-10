/**
 * @file errorHandler.ts
 * @description Error handling middleware for the Markdown Forge application
 * @module ErrorHandler
 */

import { Request, Response, NextFunction } from 'express';
import { logger } from '../utils/logger';

// Custom error class for application errors
export class AppError extends Error {
  statusCode: number;
  status: string;
  isOperational: boolean;

  constructor(message: string, statusCode: number) {
    super(message);
    this.statusCode = statusCode;
    this.status = `${statusCode}`.startsWith('4') ? 'fail' : 'error';
    this.isOperational = true;

    Error.captureStackTrace(this, this.constructor);
  }
}

// Error handler middleware
export const errorHandler = (
  err: Error | AppError,
  req: Request,
  res: Response,
  next: NextFunction
): void => {
  // Default error values
  let statusCode = 500;
  let status = 'error';
  let message = 'Internal Server Error';
  let error = {};

  // If it's our custom AppError, use its properties
  if (err instanceof AppError) {
    statusCode = err.statusCode;
    status = err.status;
    message = err.message;
  } else {
    // For unknown errors, log the full error
    logger.error('Unhandled Error:', err);
  }

  // In development, send more details
  if (process.env.NODE_ENV === 'development') {
    error = {
      status,
      statusCode,
      message,
      stack: err.stack,
      error: err,
    };
  } else {
    // In production, send minimal details
    error = {
      status,
      statusCode,
      message,
    };
  }

  // Send error response
  res.status(statusCode).json(error);
};

// Not found handler
export const notFoundHandler = (req: Request, res: Response): void => {
  const error = new AppError(`Not Found - ${req.originalUrl}`, 404);
  res.status(404).json({
    status: 'fail',
    statusCode: 404,
    message: `Route ${req.originalUrl} not found`,
  });
}; 