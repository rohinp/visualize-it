import axios from 'axios';

class LoggingService {
    static instance;
    logQueue = [];
    isProcessingQueue = false;
    maxRetries = 3;

    constructor() {
        if (LoggingService.instance) {
            return LoggingService.instance;
        }

        this.originalConsoleLog = console.log;
        this.originalConsoleError = console.error;
        this.originalConsoleWarn = console.warn;
        this.originalConsoleInfo = console.info;

        LoggingService.instance = this;
        this.setupConsoleOverrides();
    }

    setupConsoleOverrides() {
        console.log = (...args) => {
            this.originalConsoleLog.apply(console, args);
            this.queueLog('INFO', args.join(' '));
        };

        console.error = (...args) => {
            this.originalConsoleError.apply(console, args);
            this.queueLog('ERROR', args.join(' '));
        };

        console.warn = (...args) => {
            this.originalConsoleWarn.apply(console, args);
            this.queueLog('WARN', args.join(' '));
        };

        console.info = (...args) => {
            this.originalConsoleInfo.apply(console, args);
            this.queueLog('INFO', args.join(' '));
        };
    }

    queueLog(level, message) {
        // Don't log messages about failing to send logs to avoid infinite loops
        if (message.includes('Error sending log to server')) {
            return;
        }

        this.logQueue.push({ level, message, retries: 0 });
        this.processQueue();
    }

    async processQueue() {
        if (this.isProcessingQueue || this.logQueue.length === 0) {
            return;
        }

        this.isProcessingQueue = true;

        try {
            const logEntry = this.logQueue[0];
            await this.sendLogToServer(logEntry.level, logEntry.message);
            // If successful, remove from queue
            this.logQueue.shift();
        } catch (error) {
            const logEntry = this.logQueue[0];

            // Increment retry count
            logEntry.retries++;

            // If max retries reached, remove from queue
            if (logEntry.retries >= this.maxRetries) {
                this.logQueue.shift();
                this.originalConsoleWarn(`Failed to send log after ${this.maxRetries} attempts: ${logEntry.message}`);
            }
        } finally {
            this.isProcessingQueue = false;

            // If there are more items in the queue, process the next one
            if (this.logQueue.length > 0) {
                setTimeout(() => this.processQueue(), 1000); // Wait 1 second before next attempt
            }
        }
    }

    async sendLogToServer(level, message) {
        try {
            const formData = new FormData();
            formData.append('level', level);
            formData.append('message', message);

            await axios.post('http://localhost:8000/api/logs/client/add', formData);
        } catch (error) {
            // Use original console to avoid infinite loop
            this.originalConsoleError('Error sending log to server:', error.message);
            throw error; // Re-throw to handle in processQueue
        }
    }

    restoreConsole() {
        console.log = this.originalConsoleLog;
        console.error = this.originalConsoleError;
        console.warn = this.originalConsoleWarn;
        console.info = this.originalConsoleInfo;
    }
}

export default new LoggingService();