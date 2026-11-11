package org.slf4j;
import org.slf4j.helpers.MessageFormatter;
import java.util.concurrent.ConcurrentHashMap;
/** Minimal SLF4J LoggerFactory for TeaVM: no ServiceLoader/classloader lookup, console loggers. */
public final class LoggerFactory {
    private static final ConcurrentHashMap<String, Logger> LOGGERS = new ConcurrentHashMap<>();
    private static final ILoggerFactory FACTORY = name -> LOGGERS.computeIfAbsent(name, ConsoleLogger::new);
    private LoggerFactory() {}
    public static Logger getLogger(String name) { return FACTORY.getLogger(name); }
    public static Logger getLogger(Class<?> clazz) { return getLogger(clazz.getName()); }
    public static ILoggerFactory getILoggerFactory() { return FACTORY; }
    static final class ConsoleLogger implements Logger {
        private final String name;
        ConsoleLogger(String name) { this.name = name; }
        @Override public String getName() { return name; }
        @Override public boolean isTraceEnabled() { return false; }
        @Override public boolean isDebugEnabled() { return false; }
        @Override public boolean isInfoEnabled() { return true; }
        @Override public boolean isWarnEnabled() { return true; }
        @Override public boolean isErrorEnabled() { return true; }
        @Override public boolean isTraceEnabled(Marker m) { return isTraceEnabled(); }
        @Override public boolean isDebugEnabled(Marker m) { return isDebugEnabled(); }
        @Override public boolean isInfoEnabled(Marker m) { return isInfoEnabled(); }
        @Override public boolean isWarnEnabled(Marker m) { return isWarnEnabled(); }
        @Override public boolean isErrorEnabled(Marker m) { return isErrorEnabled(); }
        private void out(String level, String msg) {
            System.out.println(level + " [" + name + "] " + msg);
        }
        private void log(String level, boolean enabled, String f, Object[] a, Throwable t) {
            if (!enabled) return;
            String m = (a == null) ? f : MessageFormatter.arrayFormat(f, a);
            if (t != null) m = m + " <" + t + ">";
            out(level, m);
        }
        @Override public void trace(String m) {}
        @Override public void trace(String f, Object a) {}
        @Override public void trace(String f, Object a, Object b) {}
        @Override public void trace(String f, Object... a) {}
        @Override public void trace(String m, Throwable t) {}
        @Override public void debug(String m) {}
        @Override public void debug(String f, Object a) {}
        @Override public void debug(String f, Object a, Object b) {}
        @Override public void debug(String f, Object... a) {}
        @Override public void debug(String m, Throwable t) {}
        @Override public void info(String m) { log("INFO", true, m, null, null); }
        @Override public void info(String f, Object a) { log("INFO", true, f, new Object[]{a}, null); }
        @Override public void info(String f, Object a, Object b) { log("INFO", true, f, new Object[]{a, b}, null); }
        @Override public void info(String f, Object... a) { log("INFO", true, f, a, null); }
        @Override public void info(String m, Throwable t) { log("INFO", true, m, null, t); }
        @Override public void warn(String m) { log("WARN", true, m, null, null); }
        @Override public void warn(String f, Object a) { log("WARN", true, f, new Object[]{a}, null); }
        @Override public void warn(String f, Object a, Object b) { log("WARN", true, f, new Object[]{a, b}, null); }
        @Override public void warn(String f, Object... a) { log("WARN", true, f, a, null); }
        @Override public void warn(String m, Throwable t) { log("WARN", true, m, null, t); }
        @Override public void error(String m) { log("ERROR", true, m, null, null); }
        @Override public void error(String f, Object a) { log("ERROR", true, f, new Object[]{a}, null); }
        @Override public void error(String f, Object a, Object b) { log("ERROR", true, f, new Object[]{a, b}, null); }
        @Override public void error(String f, Object... a) { log("ERROR", true, f, a, null); }
        @Override public void error(String m, Throwable t) { log("ERROR", true, m, null, t); }
        @Override public void trace(Marker m, String s) {}
        @Override public void trace(Marker m, String f, Object a) {}
        @Override public void trace(Marker m, String f, Object a, Object b) {}
        @Override public void trace(Marker m, String f, Object... a) {}
        @Override public void trace(Marker m, String s, Throwable t) {}
        @Override public void debug(Marker m, String s) {}
        @Override public void debug(Marker m, String f, Object a) {}
        @Override public void debug(Marker m, String f, Object a, Object b) {}
        @Override public void debug(Marker m, String f, Object... a) {}
        @Override public void debug(Marker m, String s, Throwable t) {}
        @Override public void info(Marker m, String s) { info(s); }
        @Override public void info(Marker m, String f, Object a) { info(f, a); }
        @Override public void info(Marker m, String f, Object a, Object b) { info(f, a, b); }
        @Override public void info(Marker m, String f, Object... a) { info(f, a); }
        @Override public void info(Marker m, String s, Throwable t) { info(s, t); }
        @Override public void warn(Marker m, String s) { warn(s); }
        @Override public void warn(Marker m, String f, Object a) { warn(f, a); }
        @Override public void warn(Marker m, String f, Object a, Object b) { warn(f, a, b); }
        @Override public void warn(Marker m, String f, Object... a) { warn(f, a); }
        @Override public void warn(Marker m, String s, Throwable t) { warn(s, t); }
        @Override public void error(Marker m, String s) { error(s); }
        @Override public void error(Marker m, String f, Object a) { error(f, a); }
        @Override public void error(Marker m, String f, Object a, Object b) { error(f, a, b); }
        @Override public void error(Marker m, String f, Object... a) { error(f, a); }
        @Override public void error(Marker m, String s, Throwable t) { error(s, t); }
    }
}
