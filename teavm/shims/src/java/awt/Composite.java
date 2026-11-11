package java.awt;
public interface Composite {
    CompositeContext createContext(java.awt.image.ColorModel src, java.awt.image.ColorModel dst, RenderingHints hints);
}
