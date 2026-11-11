package java.security;
/** Minimal java.security.KeyStore (analysis stub). */
public class KeyStore {
    public static final String DEFAULT_TYPE = "jks";
    protected KeyStore() {}
    public static KeyStore getInstance(String type) { return new KeyStore(); }
    public static String getDefaultType() { return DEFAULT_TYPE; }
    public void load(java.io.InputStream stream, char[] password) {}
    public void store(java.io.OutputStream stream, char[] password) {}
}
