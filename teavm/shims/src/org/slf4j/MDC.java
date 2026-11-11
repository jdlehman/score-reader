package org.slf4j;
import java.util.HashMap;
import java.util.Map;
/** Minimal MDC: per-thread map, no logging backend. */
public final class MDC {
    private static final ThreadLocal<Map<String, String>> CTX = ThreadLocal.withInitial(HashMap::new);
    private MDC() {}
    public static void put(String key, String val) { CTX.get().put(key, val); }
    public static String get(String key) { return CTX.get().get(key); }
    public static void remove(String key) { CTX.get().remove(key); }
    public static void clear() { CTX.get().clear(); }
    public static Map<String, String> getCopyOfContextMap() { return new HashMap<>(CTX.get()); }
    public static void setContextMap(Map<String, String> map) { CTX.set(new HashMap<>(map)); }
}
