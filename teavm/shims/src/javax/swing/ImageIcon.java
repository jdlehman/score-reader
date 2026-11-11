package javax.swing;
import java.awt.*;
import java.net.URL;
/** Minimal javax.swing.ImageIcon. */
public class ImageIcon implements Icon, java.io.Serializable {
    protected String filename;
    protected Image image;
    protected String description;
    public ImageIcon() {}
    public ImageIcon(String filename) { this.filename = filename; }
    public ImageIcon(String filename, String description) { this.filename = filename; this.description = description; }
    public ImageIcon(URL location) {}
    public ImageIcon(URL location, String description) {}
    public ImageIcon(Image image) { this.image = image; }
    public ImageIcon(Image image, String description) { this.image = image; this.description = description; }
    public ImageIcon(byte[] imageData) {}
    public ImageIcon(byte[] imageData, String description) {}
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public Image getImage() { return image; }
    public void setImage(Image image) { this.image = image; }
    public int getIconWidth() { return image == null ? 0 : image.getWidth(null); }
    public int getIconHeight() { return image == null ? 0 : image.getHeight(null); }
    public void paintIcon(Component c, Graphics g, int x, int y) {}
    public void setImageObserver(java.awt.image.ImageObserver observer) {}
    public java.awt.image.ImageObserver getImageObserver() { return null; }
    public int getImageLoadStatus() { return 0; }
}
