package preprocessing.obj;

import java.io.File;
import java.io.FileNotFoundException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedList;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;
import java.util.stream.StreamSupport;

import com.github.javaparser.JavaParser;
import com.github.javaparser.JavaToken;
import com.github.javaparser.TokenRange;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.Node;
import com.github.javaparser.ast.NodeList;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.FieldDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.TypeDeclaration;
import com.github.javaparser.ast.comments.Comment;
import com.github.javaparser.ast.comments.JavadocComment;
import com.github.javaparser.ast.expr.AnnotationExpr;
import com.github.javaparser.ast.expr.MemberValuePair;
import com.github.javaparser.ast.expr.MethodCallExpr;
import com.github.javaparser.ast.expr.NormalAnnotationExpr;
import com.github.javaparser.ast.visitor.VoidVisitorAdapter;
import preprocessing.utils.StringUtils;

public class JavaTestClass {
		
		
		private String packageName;
		
		private String className;
		
		private String classNameNL;
		
		private String classImports;
		
		private String classModifiers;
		
		private String classComment;
		
		private String classJavadocComment;
		
		private String classOrphanComments;
		
		private String classMembers;
		
		private List<TestCase> testCases = new ArrayList<TestCase>();

		private int testCasesPerClass;
		
		private String format = "(%s)";

		public String getPackageName() {
			return packageName;
		}

		public void setPackageName(String packageName) {
			this.packageName = packageName;
		}

		public String getClassName() {
			return className;
		}

		public void setClassName(String className) {
			this.className = className;
		}

		public String getClassNameNL() {
			return classNameNL;
		}

		public void setClassNameNL(String classNameNL) {
			this.classNameNL = classNameNL;
		}

		public String getClassImports() {
			return classImports;
		}

		public void setClassImports(String classImports) {
			this.classImports = classImports;
		}

		public String getClassModifiers() {
			return classModifiers;
		}

		public void setClassModifiers(String classModifiers) {
			this.classModifiers = classModifiers;
		}

		public String getClassComment() {
			return classComment;
		}

		public void setClassComment(String classComment) {
			this.classComment = classComment;
		}

		public String getClassJavadocComment() {
			return classJavadocComment;
		}

		public void setClassJavadocComment(String classJavadocComment) {
			this.classJavadocComment = classJavadocComment;
		}

		public String getClassOrphanComments() {
			return classOrphanComments;
		}

		public void setClassOrphanComments(String classOrphantComments) {
			this.classOrphanComments = classOrphantComments;
		}

		public String getClassMembers() {
			return classMembers;
		}

		public void setClassMembers(String classMembers) {
			this.classMembers = classMembers;
		}

		public List<TestCase> getTestCases() {
			return testCases;
		}

		public void setTestCases(List<TestCase> testCases) {
			this.testCases = testCases;
		}
		
		public int getTestCasesPerClass() {
			return testCasesPerClass;
		}

		public void setTestCasesPerClass(int testCasesPerStory) {
			this.testCasesPerClass = testCasesPerStory;
		}
		
		/*  https://github.com/javaparser/javaparser/blob/457a1a819638f62541a3c94af96b1e2718a4c941/javaparser-core/src/main/java/com/github/javaparser/JavaToken.java#L258
		EOF(0),
        SPACE(1),
        WINDOWS_EOL(2),
        UNIX_EOL(3),
        OLD_MAC_EOL(4),
        SINGLE_LINE_COMMENT(5),
        ENTER_JAVADOC_COMMENT(6),
        ENTER_MULTILINE_COMMENT(7),
        JAVADOC_COMMENT(8),
        MULTI_LINE_COMMENT(9),
        COMMENT_CONTENT(10) */ 
		private Integer[] toSkip = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
		
	    private List<JavaToken> getTokenList(MethodDeclaration method, Integer[] toSkip){	    	
        	TokenRange bodyRange = method.getTokenRange().get();
        	return StreamSupport.stream(bodyRange.spliterator(), false)
        						.filter(t -> !Arrays.asList(toSkip).contains(t.getKind()))
        						.collect(Collectors.toList());
	    }
		
		public void parseTestClass(String code){
			CompilationUnit cu = JavaParser.parse(code);
			parseTestClass(cu);
		}
		
		public void parseTestClass(File file) throws FileNotFoundException{
			CompilationUnit cu = JavaParser.parse(file);
			TypeDeclaration<?> parent = cu.getType(0);
			List<ClassOrInterfaceDeclaration> nested = cu.getChildNodesByType(ClassOrInterfaceDeclaration.class);
			parseTestClass(cu);
		}
		
		public void parseTestClass(CompilationUnit cu ) {
			cu.getPackageDeclaration().ifPresent(p -> packageName = p.toString().trim());
			className = cu.getType(0).getName().asString();
			classNameNL = StringUtils.extractNLWords(className);
			classImports = parseNodes(cu.getImports());
			classModifiers = cu.getType(0).getModifiers().stream()
					 								   .map(mod -> mod.toString())
					 								   .collect(Collectors.joining(" "));
			
			cu.getComment().ifPresent(c -> classComment = c.toString().trim());
			cu.getType(0).getJavadocComment()
						 .ifPresent(jc -> classJavadocComment = jc.toString().trim());
			
			classOrphanComments = parseNodes(cu.getType(0).getOrphanComments());
			cu.getType(0).getOrphanComments().forEach(Node::remove);

			classMembers = cu.getType(0).getMembers()
										.stream()
										.filter(node -> node instanceof FieldDeclaration)
										.map(node -> node.toString().trim())
										.collect(Collectors.joining(" "));
					
			new MethodVisitor().visit(cu, null);
			int id=0;
			for (TestCase tc : testCases) {
				tc.setId(id+++"");
			}
			
			testCasesPerClass = testCases.size();
		}
		
		public void parseCut(String code){
			CompilationUnit cu = JavaParser.parse(code);
			cu.getPackageDeclaration().ifPresent(p -> packageName = p.toString().trim());
//			className = cu.getType(0).getName().asString();
//			classNameNL = StringUtils.extractNLWords(className);
			classImports = parseNodes(cu.getImports());
			
			cu.getComment().ifPresent(c -> classComment = c.toString().trim());
			cu.getType(0).getJavadocComment()
						 .ifPresent(jc -> classJavadocComment = jc.toString().trim());
			
			classOrphanComments = parseNodes(cu.getOrphanComments());
			classMembers = cu.getType(0).getMembers()
										.stream()
										.filter(node -> node instanceof FieldDeclaration)
										.map(node -> node.toString().trim())
										.collect(Collectors.joining(" "));
			
			testCasesPerClass = testCases.size();
		}

		private String parseNodes(List<?> items) {
			return items.stream()
						.map(item -> item.toString().trim())
						.collect(Collectors.joining(" "));
		}
		
		private class MethodVisitor extends VoidVisitorAdapter<Void> {
			@Override
			public void visit (MethodDeclaration method, Void args){
				
				method.getAnnotationByName("Test")
						.ifPresent(testAnnot ->  parseTestCase(method, testAnnot)) ;				
			}
			
			public void parseTestCase(MethodDeclaration method, AnnotationExpr testAnnotation){
				
				if (!method.getBody().isPresent()){
					return;
					}
				
				TestCase tc = new TestCase();
				
				if (method.toString().startsWith("/")) {
					System.out.println("akuku");
				}

				method.getComment().ifPresent(c -> tc.setComment(c.toString()));
				method.getJavadocComment().ifPresent(jc -> tc.setJavadocComment(jc.toString()));
				method.removeComment();

				List<Comment> containedComments = method.getAllContainedComments();
				tc.setAllContainedComments(parseNodes(containedComments));
				containedComments.forEach(Node::remove);
				removeAllComments(method);
				
				if (testAnnotation instanceof NormalAnnotationExpr) {
					NodeList<MemberValuePair> pairs = ((NormalAnnotationExpr)testAnnotation).getPairs();
					for (MemberValuePair p : pairs){
						if (p.getNameAsString().equals("expected")){
							tc.setTestAnnotation(String.format(format, p.toString()));
						}
					}
				} 
			
//				if (testAnnotation instanceof NormalAnnotationExpr) {
//					tc.setTestAnnotationParameters( ((NormalAnnotationExpr) testAnnotation).getPairs().toString() );
//				}
				
				List <JavaToken> tokenList = getTokenList(method, toSkip);
				List <String> stringTokenList = tokenList.stream()
															.filter(st -> st.getKind() == (JavaToken.Kind.STRING_LITERAL.ordinal()))
															.map(JavaToken::getText)
															.collect(Collectors.toList());
				
				tc.setFullMethod(method.toString());
				tc.setFullMethodTokens(tokenList.stream().map(JavaToken::getText).collect(Collectors.toList()).toArray(new String[tokenList.size()]));
				tc.setContainedStrings(stringTokenList.toArray(new String[stringTokenList.size()]));
				
				
				String ancestorName = method.getAncestorOfType(ClassOrInterfaceDeclaration.class).get().getNameAsString();
				if (!ancestorName.equals(className)){
					tc.setAncestorClassName(ancestorName);
					tc.setAncestorClassNameNL(StringUtils.extractNLWords(ancestorName));
				}
				
				tc.setClassName(className);
				tc.setClassNameNL(classNameNL);
				tc.setMethodName(method.getName().toString());
				tc.setTitle(StringUtils.extractNLWords(tc.getMethodName()));
				
				tc.setAnnotations(parseNodes(method.getAnnotations()));
	
				tc.setModifiers(method.getModifiers().stream()
									 .map(mod -> mod.toString())
									 .collect(Collectors.joining(" ")));
				
				tc.setParameters(parseNodes(method.getParameters()));
				tc.setThrownExceptions(parseNodes(method.getThrownExceptions()));
				method.getBody().ifPresent(body -> tc.setBody(body.toString())) ;
				
				String pn = packageName.split(" ")[1];
				tc.setPackageName(pn.substring(0, pn.length() - 1));
				tc.setTestcaseFullname(String.join("", 
												tc.getPackageName(), ".",
												className, ".",
												ancestorName.equals(className)? "" : ancestorName + ".", 
												tc.getMethodName()));
				tc.setClassImports(getClassImports());
				testCases.add(tc); 
			}
		}
		
		public void removeAllComments(Node node) {
	        node.removeComment();
	        for (Node child : node.getChildNodes()) {
	            removeAllComments(child);
	        }
	    }
}
