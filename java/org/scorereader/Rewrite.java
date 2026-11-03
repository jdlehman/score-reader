// Score reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
package org.scorereader;

import java.io.IOException;
import java.io.InputStream;
import java.lang.classfile.ClassFile;
import java.lang.classfile.ClassHierarchyResolver;
import java.lang.classfile.ClassModel;
import java.lang.classfile.ClassTransform;
import java.lang.classfile.CodeTransform;
import java.lang.classfile.constantpool.MethodRefEntry;
import java.lang.classfile.instruction.InvokeInstruction;
import java.lang.constant.ClassDesc;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.util.jar.JarOutputStream;

/**
 * Rewrites jars so their calls to java.lang.Math's slow-in-the-browser methods go to FastMath.
 *
 *   java Rewrite.java <out dir> <jar>...   (each jar is written to the out dir under its own name)
 *
 * Only classes that call those methods are changed; every other entry is copied as it is.
 * Jar signatures are dropped, since rewritten classes would no longer match them. A changed jar
 * gets META-INF/SCORE-READER-CHANGES.txt, saying what was changed and when, as the libraries'
 * licences ask (Apache 2.0 section 4(b), LGPL 2.1 section 2(b), and others).
 */
public final class Rewrite
{
    private static final ClassDesc MATH = ClassDesc.of("java.lang.Math");
    private static final ClassDesc STRICT = ClassDesc.of("java.lang.StrictMath");
    private static final ClassDesc FAST = ClassDesc.of("org.scorereader.FastMath");
    private static final Set<String> METHODS = Set.of(
            "abs(D)D", "abs(F)F", "max(DD)D", "min(DD)D", "max(FF)F", "min(FF)F",
            "rint(D)D", "floor(D)D", "ceil(D)D", "sqrt(D)D", "hypot(DD)D");

    private static boolean ours (MethodRefEntry m)
    {
        final ClassDesc owner = m.owner().asSymbol();
        return (owner.equals(MATH) || owner.equals(STRICT))
                && METHODS.contains(m.name().stringValue() + m.type().stringValue());
    }

    private static String changes (int classes)
    {
        return "Changed by Score reader (https://github.com/jdlehman/score-reader) on " + LocalDate.now() + ".\n\n"
                + "In " + classes + " classes of this jar, calls to java.lang.Math's (or StrictMath's) abs, min, max,\n"
                + "rint, floor, ceil, sqrt and hypot now go to org.scorereader.FastMath, which gives the same results\n"
                + "faster in the browser. Nothing else was changed, except that jar signatures were removed. The\n"
                + "change was made by java/org/scorereader/Rewrite.java in that repository, when the site was built.\n";
    }

    public static void main (String[] args) throws Exception
    {
        final Path out = Path.of(args[0]);
        Files.createDirectories(out);
        final List<URL> urls = new ArrayList<>();
        for (int i = 1; i < args.length; i++) urls.add(Path.of(args[i]).toUri().toURL());
        // stack maps are recomputed for changed methods, which needs the class hierarchy
        final ClassLoader loader = new URLClassLoader(urls.toArray(URL[]::new), ClassLoader.getPlatformClassLoader());
        final ClassFile cf = ClassFile.of(ClassFile.ClassHierarchyResolverOption.of(
                ClassHierarchyResolver.defaultResolver().orElse(ClassHierarchyResolver.ofClassLoading(loader))));
        final CodeTransform redirect = (code, e) -> {
            if (e instanceof InvokeInstruction inv && inv.method() instanceof MethodRefEntry m && ours(m)) {
                code.invokestatic(FAST, m.name().stringValue(), m.typeSymbol());
            } else {
                code.with(e);
            }
        };
        int total = 0;
        for (int i = 1; i < args.length; i++) {
            final Path jar = Path.of(args[i]);
            int calls = 0, classes = 0, failed = 0;
            try (JarFile in = new JarFile(jar.toFile(), false);
                 JarOutputStream o = new JarOutputStream(Files.newOutputStream(out.resolve(jar.getFileName())))) {
                for (JarEntry e : in.stream().toList()) {
                    final String name = e.getName();
                    if (name.startsWith("META-INF/") && (name.endsWith(".SF") || name.endsWith(".RSA") || name.endsWith(".DSA") || name.endsWith(".EC"))) continue;
                    byte[] bytes;
                    try (InputStream s = in.getInputStream(e)) { bytes = s.readAllBytes(); }
                    if (name.endsWith(".class") && !e.isDirectory()) {
                        final ClassModel model = cf.parse(bytes);
                        long n = 0;
                        for (var p : model.constantPool()) if (p instanceof MethodRefEntry m && ours(m)) n++;
                        if (n > 0) {
                            try {
                                final int[] count = {0};
                                bytes = cf.transformClass(model, ClassTransform.transformingMethodBodies((code, el) -> {
                                    if (el instanceof InvokeInstruction inv && inv.method() instanceof MethodRefEntry m && ours(m)) count[0]++;
                                    redirect.accept(code, el);
                                }));
                                calls += count[0];
                                classes++;
                            } catch (RuntimeException ex) {
                                failed++; // left as it was
                                if (failed <= 3) System.err.println("  kept " + name + ": " + ex.getMessage());
                            }
                        }
                    }
                    final JarEntry copy = new JarEntry(name);
                    copy.setTime(e.getTime());
                    o.putNextEntry(copy);
                    o.write(bytes);
                    o.closeEntry();
                }
                if (classes > 0) {
                    o.putNextEntry(new JarEntry("META-INF/SCORE-READER-CHANGES.txt"));
                    o.write(changes(classes).getBytes(StandardCharsets.UTF_8));
                    o.closeEntry();
                }
            }
            if (calls > 0 || failed > 0) System.out.println(jar.getFileName() + ": " + calls + " calls in " + classes + " classes" + (failed > 0 ? ", " + failed + " classes kept as they were" : ""));
            total += calls;
        }
        System.out.println("total: " + total + " calls redirected");
    }
}
