package javax.swing.event;
/** Minimal javax.swing.event.HyperlinkEvent. */
public class HyperlinkEvent extends java.util.EventObject {
    public enum EventType { ACTIVATED, ENTERED, EXITED }
    protected EventType type;
    protected java.net.URL url;
    protected String desc;
    public HyperlinkEvent(Object source, EventType type, java.net.URL url) { super(source); this.type = type; this.url = url; }
    public HyperlinkEvent(Object source, EventType type, java.net.URL url, String desc) {
        super(source); this.type = type; this.url = url; this.desc = desc;
    }
    public EventType getEventType() { return type; }
    public String getDescription() { return desc; }
    public java.net.URL getURL() { return url; }
}
