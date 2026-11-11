package java.security;
/** Minimal java.security.MessageDigest (concrete stub; the JDK class is abstract). */
public class MessageDigest {
    private final String algorithm;
    public MessageDigest() { this.algorithm = ""; }
    protected MessageDigest(String algorithm) { this.algorithm = algorithm; }
    public static MessageDigest getInstance(String algorithm) { return new MessageDigest(algorithm); }
    public static MessageDigest getInstance(String algorithm, String provider) { return new MessageDigest(algorithm); }
    public static boolean isEqual(byte[] digesta, byte[] digestb) { return java.util.Arrays.equals(digesta, digestb); }
    public String getAlgorithm() { return algorithm; }
    public int getDigestLength() { return 0; }
    public void reset() {}
    public void update(byte input) {}
    public void update(byte[] input) {}
    public void update(byte[] input, int offset, int len) {}
    public void update(java.nio.ByteBuffer input) {}
    public byte[] digest() { return new byte[0]; }
    public byte[] digest(byte[] input) { return new byte[0]; }
    public int digest(byte[] buf, int offset, int len) { return 0; }
    public String toString() { return "MessageDigest." + algorithm; }
}
