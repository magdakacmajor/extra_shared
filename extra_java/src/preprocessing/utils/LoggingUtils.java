package preprocessing.utils;

import org.slf4j.Logger;

public class LoggingUtils {

	/**
	 * @param logger
	 *            this is the logger to display the trace message to
	 * @param message
	 *            this is the message to display
	 */
	public static void trace(Logger logger, String message) {
		if (logger.isTraceEnabled()) {
			logger.trace(getCallingMethodName() + "; " + message);
		}
	}

	/**
	 * Display a debug message.
	 * 
	 * @param logger
	 *            this is the logger to display the debug message to
	 * @param message
	 *            this is the message to display
	 */
	public static void debug(Logger logger, String message) {
		if (logger.isDebugEnabled()) {
			logger.debug(getCallingMethodName() + "; " + message);
		}
	}

	/**
	 * Display a debug message.
	 * 
	 * @param logger
	 *            this is the logger to display the debug message to
	 * @param message
	 *            this is the message to display
	 * @param e
	 *            this is the exception to display
	 */
	public static void debug(Logger logger, String message, Throwable e) {
		if (logger.isDebugEnabled()) {
			logger.debug(getCallingMethodName() + "; " + message, e);
		}
	}

	/**
	 * For use with com.ibm.rca.tools only. Method is used to display an info message.
	 * 
	 * @param logger
	 *            this is the logger to display the info message to
	 * @param message
	 *            this is the message to display
	 */
	public static void info(Logger logger, String message) {
		if (logger.isInfoEnabled()) {
			logger.info(getCallingMethodName() + "; " + message);
		}
	}

	/**
	 * For use with com.ibm.rca.tools only. Method is used to display a warning.
	 * 
	 * @param logger
	 *            this is the logger to display the warning to
	 * @param message
	 *            this is the message to display
	 */
	public static void warn(Logger logger, String message) {
		if (logger.isWarnEnabled()) {
			logger.warn(getCallingMethodName() + "; " + message);
		}
	}

	/**
	 * For use with com.ibm.rca.tools only. Method is used to display an error.
	 * 
	 * @param logger
	 *            this is the logger to display the error
	 * @param message
	 *            this is the message to display to
	 */
	public static void error(Logger logger, String message) {
		if (logger.isErrorEnabled()) {
			logger.error(getCallingMethodName() + "; " + message);
		}
	}

	/**
	 * For use with com.ibm.rca.tools only. Method is used to display an error.
	 * 
	 * @param logger
	 *            this is the logger to display the error to
	 * @param message
	 *            this is the message to display
	 * @param e
	 *            this is the exception to display
	 */
	public static void error(Logger logger, String message, Throwable e) {
		if (logger.isErrorEnabled()) {
			logger.error(getCallingMethodName() + "; " + message, e);
		}
	}

	/**
	 * Mark the entry of the method we are tracing.
	 * 
	 * @param logger
	 *            this is the logger to enter
	 */
	public static void traceEntry(Logger logger) {
		if (logger.isTraceEnabled()) {
			logger.trace("Entering " + getCallingMethodName());
		}
	}

	/**
	 * Mark the exit of the method we are tracing.
	 * 
	 * @param logger
	 *            this is the logger to exit
	 */
	public static void traceExit(Logger logger) {
		if (logger.isTraceEnabled()) {
			logger.trace("Exiting " + getCallingMethodName());
		}
	}

	private static String getCallingMethodName() {
		return Thread.currentThread().getStackTrace()[Thread.currentThread().getStackTrace().length - 1].getMethodName() + "()";
	}
}

