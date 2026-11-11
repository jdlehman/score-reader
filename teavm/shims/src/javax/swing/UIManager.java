package javax.swing;
/** Minimal javax.swing.UIManager. */
public class UIManager implements java.io.Serializable {
    public static class LookAndFeelInfo implements java.io.Serializable {
        private String name, className;
        public LookAndFeelInfo(String name, String className) { this.name = name; this.className = className; }
        public String getName() { return name; }
        public String getClassName() { return className; }
        public String toString() { return name; }
    }
    private static final java.util.Map<Object, Object> DEFAULTS = new java.util.HashMap<>();
    public static LookAndFeelInfo[] getInstalledLookAndFeels() { return new LookAndFeelInfo[0]; }
    public static void setInstalledLookAndFeels(LookAndFeelInfo[] infos) {}
    public static void installLookAndFeel(LookAndFeelInfo info) {}
    public static void installLookAndFeel(String name, String className) {}
    public static String getSystemLookAndFeelClassName() { return ""; }
    public static String getCrossPlatformLookAndFeelClassName() { return ""; }
    public static Object get(Object key) { return DEFAULTS.get(key); }
    public static Object get(Object key, java.util.Locale l) { return DEFAULTS.get(key); }
    public static void put(Object key, Object value) { DEFAULTS.put(key, value); }
    public static String getString(Object key) { Object v = get(key); return v == null ? null : v.toString(); }
    public static java.awt.Color getColor(Object key) { Object v = get(key); return (v instanceof java.awt.Color) ? (java.awt.Color) v : null; }
    public static java.awt.Font getFont(Object key) { Object v = get(key); return (v instanceof java.awt.Font) ? (java.awt.Font) v : null; }
    public static Icon getIcon(Object key) { Object v = get(key); return (v instanceof Icon) ? (Icon) v : null; }
    public static boolean getBoolean(Object key) { Object v = get(key); return (v instanceof Boolean) && (Boolean) v; }
    public static int getInt(Object key) { Object v = get(key); return (v instanceof Number) ? ((Number) v).intValue() : 0; }
    public static javax.swing.UIDefaults getDefaults() { return null; }
    public static void setLookAndFeel(String className) throws Exception {}
    public static void setLookAndFeel(LookAndFeel newLookAndFeel) {}
    public static LookAndFeel getLookAndFeel() { return null; }
    public static void addPropertyChangeListener(java.beans.PropertyChangeListener listener) {}
    public static void removePropertyChangeListener(java.beans.PropertyChangeListener listener) {}
}
