package java.awt;
import java.util.HashMap;
import java.util.Map;
/** Minimal java.awt.RenderingHints. */
public class RenderingHints extends HashMap<Object, Object> implements Cloneable {
    public static class Key {
        private final int key;
        protected Key(int key) { this.key = key; }
        public int getKey() { return key; }
        public boolean isCompatibleValue(Object v) { return true; }
        @Override public int hashCode() { return key; }
        @Override public boolean equals(Object o) { return o instanceof Key k && key == k.key; }
    }
    public static final Key KEY_ANTIALIASING = new Key(1);
    public static final Key KEY_RENDERING = new Key(2);
    public static final Key KEY_DITHERING = new Key(3);
    public static final Key KEY_TEXT_ANTIALIASING = new Key(4);
    public static final Key KEY_FRACTIONALMETRICS = new Key(5);
    public static final Key KEY_INTERPOLATION = new Key(6);
    public static final Key KEY_ALPHA_INTERPOLATION = new Key(7);
    public static final Key KEY_COLOR_RENDERING = new Key(8);
    public static final Key KEY_STROKE_CONTROL = new Key(9);
    public static final Object VALUE_ANTIALIAS_DEFAULT = new Object();
    public static final Object VALUE_ANTIALIAS_ON = new Object();
    public static final Object VALUE_ANTIALIAS_OFF = new Object();
    public static final Object VALUE_RENDER_DEFAULT = new Object();
    public static final Object VALUE_RENDER_SPEED = new Object();
    public static final Object VALUE_RENDER_QUALITY = new Object();
    public static final Object VALUE_TEXT_ANTIALIAS_DEFAULT = new Object();
    public static final Object VALUE_TEXT_ANTIALIAS_ON = new Object();
    public static final Object VALUE_TEXT_ANTIALIAS_OFF = new Object();
    public static final Object VALUE_TEXT_ANTIALIAS_GASP = new Object();
    public static final Object VALUE_TEXT_ANTIALIAS_LCD_HRGB = new Object();
    public static final Object VALUE_TEXT_ANTIALIAS_LCD_HBGR = new Object();
    public static final Object VALUE_TEXT_ANTIALIAS_LCD_VRGB = new Object();
    public static final Object VALUE_TEXT_ANTIALIAS_LCD_VBGR = new Object();
    public static final Object VALUE_FRACTIONALMETRICS_DEFAULT = new Object();
    public static final Object VALUE_FRACTIONALMETRICS_ON = new Object();
    public static final Object VALUE_FRACTIONALMETRICS_OFF = new Object();
    public static final Object VALUE_INTERPOLATION_NEAREST_NEIGHBOR = new Object();
    public static final Object VALUE_INTERPOLATION_BILINEAR = new Object();
    public static final Object VALUE_INTERPOLATION_BICUBIC = new Object();
    public static final Object VALUE_STROKE_DEFAULT = new Object();
    public static final Object VALUE_STROKE_PURE = new Object();
    public static final Object VALUE_STROKE_NORMALIZE = new Object();
    public RenderingHints(Map<Key, ?> init) { if (init != null) putAll(init); }
    public RenderingHints(Key key, Object value) { put(key, value); }
    @Override public Object clone() { return super.clone(); }
}
