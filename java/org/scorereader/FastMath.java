package org.scorereader;

/**
 * Stand-ins for java.lang.Math, for running Audiveris in the browser (CheerpJ).
 *
 * Java 25 computes abs, min, max, rint, floor, ceil and sqrt with raw-bit conversions
 * (Double.doubleToRawLongBits and friends) or bit-by-bit algorithms. CheerpJ runs those 40 to
 * 300 times slower than the desktop, against about 10 times for ordinary arithmetic. These give
 * the same results (sqrt: within one unit in the last place) using comparisons and arithmetic.
 * Audiveris's compiled classes are rewritten to call them (see Rewrite.java).
 */
public final class FastMath
{
    private FastMath () {}

    private static final double TWO52 = 4503599627370496.0; // 2^52: doubles at least this big are whole

    public static double abs (double a) { return (a <= 0.0) ? 0.0 - a : a; } // 0.0 - (-0.0) is 0.0
    public static float abs (float a) { return (a <= 0.0f) ? 0.0f - a : a; }

    public static double max (double a, double b)
    {
        if (a != a) return a; // NaN
        if (a == 0.0 && b == 0.0) return (1 / a < 0) ? b : a; // max(-0, 0) is 0
        return (a >= b) ? a : b;
    }

    public static double min (double a, double b)
    {
        if (a != a) return a;
        if (a == 0.0 && b == 0.0) return (1 / b < 0) ? b : a; // min(0, -0) is -0
        return (a <= b) ? a : b;
    }

    public static float max (float a, float b)
    {
        if (a != a) return a;
        if (a == 0.0f && b == 0.0f) return (1 / a < 0) ? b : a;
        return (a >= b) ? a : b;
    }

    public static float min (float a, float b)
    {
        if (a != a) return a;
        if (a == 0.0f && b == 0.0f) return (1 / b < 0) ? b : a;
        return (a <= b) ? a : b;
    }

    /** Round to the nearest whole number, halves to even: adding 2^52 makes the hardware round. */
    public static double rint (double a)
    {
        if (a > 0) return (a < TWO52) ? (TWO52 + a) - TWO52 : a;
        if (a < 0) return (a > -TWO52) ? -((TWO52 - a) - TWO52) : a;
        return a; // 0, -0, NaN
    }

    public static double floor (double a)
    {
        if (!(a < TWO52 && a > -TWO52)) return a; // whole already, or NaN or infinite
        final double r = rint(a);
        return (r > a) ? r - 1 : r;
    }

    public static double ceil (double a)
    {
        if (!(a < TWO52 && a > -TWO52)) return a;
        double r = rint(a);
        if (r < a) r += 1;
        return (r == 0 && a < 0) ? -0.0 : r; // ceil(-0.7) is -0
    }

    /** Newton's method from a guess made by halving the exponent. */
    public static double sqrt (double x)
    {
        if (!(x > 0) || x == Double.POSITIVE_INFINITY) {
            return (x == 0 || x == Double.POSITIVE_INFINITY) ? x : Double.NaN; // keeps -0
        }
        if (x < 1e-300) return Math.sqrt(x); // the exponent guess fails for the tiniest numbers
        double y = Double.longBitsToDouble((Double.doubleToRawLongBits(x) >> 1) + 0x1FF8000000000000L);
        y = 0.5 * (y + x / y);
        y = 0.5 * (y + x / y);
        y = 0.5 * (y + x / y);
        y = 0.5 * (y + x / y);
        return 0.5 * (y + x / y);
    }

    /** No care for overflow: Audiveris measures pixels. */
    public static double hypot (double x, double y)
    {
        if (x != x || y != y) {
            return (x == Double.POSITIVE_INFINITY || x == Double.NEGATIVE_INFINITY
                    || y == Double.POSITIVE_INFINITY || y == Double.NEGATIVE_INFINITY)
                    ? Double.POSITIVE_INFINITY : Double.NaN;
        }
        return sqrt(x * x + y * y);
    }
}
