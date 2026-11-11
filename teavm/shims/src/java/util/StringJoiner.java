package java.util;
/** Minimal java.util.StringJoiner (real implementation). */
public final class StringJoiner {
    private final String prefix;
    private final String delimiter;
    private final String suffix;
    private StringBuilder value;
    private String emptyValue;
    public StringJoiner(CharSequence delimiter) { this(delimiter, "", ""); }
    public StringJoiner(CharSequence delimiter, CharSequence prefix, CharSequence suffix) {
        this.prefix = prefix.toString();
        this.delimiter = delimiter.toString();
        this.suffix = suffix.toString();
        this.emptyValue = this.prefix + this.suffix;
    }
    public StringJoiner setEmptyValue(CharSequence emptyValue) {
        this.emptyValue = emptyValue.toString();
        return this;
    }
    public StringJoiner add(CharSequence newElement) {
        if (value == null) {
            value = new StringBuilder(prefix);
        } else {
            value.append(delimiter);
        }
        value.append(newElement);
        return this;
    }
    public StringJoiner merge(StringJoiner other) {
        if (other.value != null) {
            if (value == null) {
                value = new StringBuilder(prefix);
            } else {
                value.append(delimiter);
            }
            value.append(other.value, prefix.length(), other.value.length());
        }
        return this;
    }
    @Override public String toString() {
        if (value == null) return emptyValue;
        return value.toString() + suffix;
    }
    public int length() { return toString().length(); }
}
