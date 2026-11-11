package javax.imageio.spi;
/** Minimal javax.imageio.spi.IIORegistry (analysis stub). */
public class IIORegistry {
    private static final IIORegistry INSTANCE = new IIORegistry();
    protected IIORegistry() {}
    public static IIORegistry getDefaultInstance() { return INSTANCE; }
}
