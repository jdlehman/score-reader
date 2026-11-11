package org.slf4j;
/** Minimal SLF4J Logger for TeaVM: console output, {} formatting, no binding lookup. */
public interface Logger {
    String getName();
    boolean isTraceEnabled(); boolean isDebugEnabled(); boolean isInfoEnabled();
    boolean isWarnEnabled(); boolean isErrorEnabled();
    void trace(String msg); void trace(String f, Object a); void trace(String f, Object a, Object b);
    void trace(String f, Object... a); void trace(String msg, Throwable t);
    void debug(String msg); void debug(String f, Object a); void debug(String f, Object a, Object b);
    void debug(String f, Object... a); void debug(String msg, Throwable t);
    void info(String msg); void info(String f, Object a); void info(String f, Object a, Object b);
    void info(String f, Object... a); void info(String msg, Throwable t);
    void warn(String msg); void warn(String f, Object a); void warn(String f, Object a, Object b);
    void warn(String f, Object... a); void warn(String msg, Throwable t);
    void error(String msg); void error(String f, Object a); void error(String f, Object a, Object b);
    void error(String f, Object... a); void error(String msg, Throwable t);
    void trace(Marker m, String msg); void trace(Marker m, String f, Object a);
    void trace(Marker m, String f, Object a, Object b); void trace(Marker m, String f, Object... a);
    void trace(Marker m, String msg, Throwable t);
    void debug(Marker m, String msg); void debug(Marker m, String f, Object a);
    void debug(Marker m, String f, Object a, Object b); void debug(Marker m, String f, Object... a);
    void debug(Marker m, String msg, Throwable t);
    void info(Marker m, String msg); void info(Marker m, String f, Object a);
    void info(Marker m, String f, Object a, Object b); void info(Marker m, String f, Object... a);
    void info(Marker m, String msg, Throwable t);
    void warn(Marker m, String msg); void warn(Marker m, String f, Object a);
    void warn(Marker m, String f, Object a, Object b); void warn(Marker m, String f, Object... a);
    void warn(Marker m, String msg, Throwable t);
    void error(Marker m, String msg); void error(Marker m, String f, Object a);
    void error(Marker m, String f, Object a, Object b); void error(Marker m, String f, Object... a);
    void error(Marker m, String msg, Throwable t);
    boolean isTraceEnabled(Marker m); boolean isDebugEnabled(Marker m); boolean isInfoEnabled(Marker m);
    boolean isWarnEnabled(Marker m); boolean isErrorEnabled(Marker m);
}
