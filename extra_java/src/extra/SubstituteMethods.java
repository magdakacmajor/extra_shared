package extra;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.List;
import java.util.function.Predicate;

import com.github.javaparser.JavaParser;
import com.github.javaparser.Range;

import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.expr.AnnotationExpr;
import com.google.gson.Gson;

public class SubstituteMethods {
	
	public static List<String> substituteBody(Path classFile, 
											  Path substitutionDir,
											  MethodDeclaration method,
											  int standardLength) throws IOException {
		
		List<String> substitution = Files.readAllLines(substitutionDir);
		substitution = substitution.subList(1, substitution.size() -1);
		
		for (AnnotationExpr ae : method.getAnnotations() ){
			if (ae.toString().contains("@Test")){
				continue;
			}
			substitution.add(0, ae.toString());
		}
		String[] filler = new String [standardLength];
		Arrays.fill(filler, "");
		for (int i=0; i<substitution.size(); i++) {
			filler[i]=substitution.get(i);
		}
		
		Range range = method.getRange().get();
		int start = range.begin.line - 1;
		List<String> allLines = Files.readAllLines(classFile);
		allLines.subList(start, start+standardLength).clear();
		allLines.addAll(start, Arrays.asList(filler));

		return allLines;		
	
	}
	
	public static List<String> standardizeMethodLength(Path classFile, MethodDeclaration method, int standardLength) throws IOException {
		Range range = method.getRange().get();
		String[] filler = new String [standardLength - (range.end.line - range.begin.line)];
		Arrays.fill(filler, "");
		if (filler.length < 10) {
			System.out.println(method.getAncestorOfType(ClassOrInterfaceDeclaration.class).get().getNameAsString() + "\t" + method.getDeclarationAsString(false, false));
			System.out.println("Filler length:" + filler.length);
		}
		
		List<String> allLines =  Files.readAllLines(classFile);
		allLines.addAll(range.end.line, Arrays.asList(filler));
		return allLines;
	}
	
	public static void substitute(String mappingsDir, String substitutionDir, int standardLength) throws IOException {
		Gson gson = new Gson();
		String input = new String(Files.readAllBytes(Paths.get(mappingsDir) ) );
		ProjectMappping[] projectMappings = gson.fromJson(input, ProjectMappping[].class);

		int modifiedCount = 0;
		
		for(int i=0; i<projectMappings.length; i++){
			ProjectMappping pm = projectMappings[i];
			if(!pm.isExecutable()) {
				continue;
			}
			Path classFile = Paths.get(pm.getFilepath());//.replace("/klonhome/shared/data", "/home/magda/a-tud/data/spring"));
			String methodName = pm.getMethodName();
			String ancestorName = pm.getAncestorClassName() == null? pm.getClassName() : pm.getAncestorClassName();
			CompilationUnit cu = JavaParser.parse(classFile);
			Predicate<MethodDeclaration> match = m -> 
												(m.getDeclarationAsString(false, false).equals(String.format("void %s()",methodName))
														&& (m.getAnnotationByName("Test").isPresent())
														&& (m.getAncestorOfType(ClassOrInterfaceDeclaration.class).get().getNameAsString().equals(ancestorName) ) );
			List<MethodDeclaration> methods = cu.findAll(MethodDeclaration.class, match);
			
			if (methods.size() != 1) {
				System.out.println(classFile + "\t" + methodName);
				System.out.println("Matches found:" + methods.size());
				pm.setExecutable(false);
				continue;
			}			
			
			MethodDeclaration method=methods.get(0);
			List<String> allLines = null;
			if(substitutionDir == null) {
				allLines = standardizeMethodLength(classFile, method, standardLength);				
			}else {
				String fname = String.format("%s/%d.java", substitutionDir, i);
				allLines = substituteBody(classFile, Paths.get(fname), method, standardLength);
			}
			Files.delete(classFile);
			Files.write(classFile, allLines);
			modifiedCount++;
		}
		System.out.println("Modified: " + modifiedCount);
		System.out.println("Skipped: " + (projectMappings.length - modifiedCount));
		Files.write(Paths.get(mappingsDir.replace(".json", "_modified.json")), gson.toJson(projectMappings).getBytes());

	}

	public static void main(String[] args) throws IOException {

		String mappingsDir = args[0];
		String substitutionDir = args.length > 1? args[1] : null;
		int standardLength=39;
		
		substitute(mappingsDir, substitutionDir, standardLength);

	}

}
