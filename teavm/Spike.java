// Score Reader. Copyright (C) 2026 Jonathan Lehman. SPDX-License-Identifier: AGPL-3.0-or-later
import java.io.File;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.ArrayList;
import java.util.List;
import org.teavm.diagnostics.DefaultProblemTextConsumer;
import org.teavm.diagnostics.Problem;
import org.teavm.tooling.ConsoleTeaVMToolLog;
import org.teavm.tooling.TeaVMTargetType;
import org.teavm.tooling.TeaVMTool;
import org.teavm.vm.TeaVMOptimizationLevel;

/** Compile a Java program with TeaVM and list every problem it reports, with where it was found.
 *    java Spike js|wasm-gc <out dir> <main class> <classpath entry or @file of entries>... */
public class Spike {
    public static void main(String[] a) throws Exception {
        TeaVMTool tool = new TeaVMTool();
        tool.setTargetType(a[0].equals("js") ? TeaVMTargetType.JAVASCRIPT : TeaVMTargetType.WEBASSEMBLY_GC);
        tool.setTargetDirectory(new File(a[1]));
        tool.setMainClass(a[2]);
        List<File> cp = new ArrayList<>();
        List<URL> urls = new ArrayList<>();
        List<String> entries = new ArrayList<>();
        for (int i = 3; i < a.length; i++) {
            if (a[i].startsWith("@")) entries.addAll(java.nio.file.Files.readAllLines(java.nio.file.Path.of(a[i].substring(1))));
            else entries.add(a[i]);
        }
        for (String entry : entries) {
            if (entry.isBlank()) continue;
            File f = new File(entry).getAbsoluteFile();
            cp.add(f);
            urls.add(f.toURI().toURL());
        }
        tool.setClassPath(cp);
        tool.setClassLoader(new URLClassLoader(urls.toArray(URL[]::new), Spike.class.getClassLoader()));
        tool.setLog(new ConsoleTeaVMToolLog(false));
        tool.setOptimizationLevel(TeaVMOptimizationLevel.SIMPLE);
        tool.setDebugInformationGenerated(true);
        tool.setWasmDebugInfoLevel(org.teavm.backend.wasm.WasmDebugInfoLevel.FULL);
        try {
            tool.generate();
        } catch (Exception e) {
            e.printStackTrace();
        }
        DefaultProblemTextConsumer text = new DefaultProblemTextConsumer();
        for (Problem p : tool.getProblemProvider().getProblems()) {
            text.clear();
            p.render(text);
            System.out.println("PROBLEM " + p.getSeverity() + " | " + text.getText() + " | " + (p.getLocation() == null ? "" : p.getLocation().getMethod()));
        }
        System.out.println("generated: " + tool.getGeneratedFiles());
    }
}
