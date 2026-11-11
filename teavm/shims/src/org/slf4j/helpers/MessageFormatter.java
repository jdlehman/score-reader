package org.slf4j.helpers;
/** Minimal {} formatter (SLF4J-style). */
public final class MessageFormatter {
    private MessageFormatter() {}
    public static String format(String pattern, Object arg) {
        return arrayFormat(pattern, new Object[]{arg});
    }
    public static String format(String pattern, Object arg1, Object arg2) {
        return arrayFormat(pattern, new Object[]{arg1, arg2});
    }
    public static String arrayFormat(String pattern, Object[] args) {
        if (pattern == null) return "null";
        if (args == null || args.length == 0) return pattern;
        StringBuilder sb = new StringBuilder(pattern.length() + 32);
        int ai = 0, i = 0;
        while (true) {
            int j = pattern.indexOf("{}", i);
            if (j < 0) { sb.append(pattern, i, pattern.length()); break; }
            sb.append(pattern, i, j);
            if (ai < args.length) {
                Object a = args[ai++];
                if (a instanceof Throwable && ai == args.length) { /* trailing throwable: skip here */ }
                sb.append(a);
            } else sb.append("{}");
            i = j + 2;
        }
        return sb.toString();
    }
}
