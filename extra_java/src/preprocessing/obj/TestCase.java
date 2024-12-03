package preprocessing.obj;

import java.util.ArrayList;
import java.util.List;

import com.github.javaparser.ast.expr.MethodCallExpr;

public class TestCase {
	
	private String id;
	
	private String className;
	
	private String classNameNL;
	
	private String ancestorClassName;
	
	private String ancestorClassNameNL;
	
	private String methodName;
	
	private String title;
	
	private String comment;
	
	private String javadocComment;
	
	private String allContainedComments;
	
	private String annotations;
	
	private String testAnnotation;
	
	private String modifiers;
	
	private String parameters;
	
	private String thrownExceptions;
	
	private String body;
	
	private boolean containsStrings;
	
	private String[] containedStrings;
	
	private String packageName;
	
	private String testcaseFullname;
	
	private String classImports;
	
	private String filePath;
	
	private String bodyTokens;
	
	private String fullMethod;
	
	private String[] fullMethodTokens;


	public String getId() {
		return id;
	}

	public void setId(String id) {
		this.id = id;
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

	public String getMethodName() {
		return methodName;
	}

	public void setMethodName(String methodName) {
		this.methodName = methodName;
	}
	
	public String getAncestorClassName() {
		return ancestorClassName;
	}

	public void setAncestorClassName(String ancestorClassName) {
		this.ancestorClassName = ancestorClassName;
	}
	public String getAncestorClassNameNL() {
		return ancestorClassNameNL;
	}

	public void setAncestorClassNameNL(String ancestorClassNameNL) {
		this.ancestorClassNameNL = ancestorClassNameNL;
	}
	
	public String getTitle() {
		return title;
	}

	public void setTitle(String title) {
		this.title = title;
	}

	public String getComment() {
		return comment;
	}

	public void setComment(String comment) {
		this.comment = comment;
	}

	public String getJavadocComment() {
		return javadocComment;
	}

	public void setJavadocComment(String javadocComment) {
		this.javadocComment = javadocComment;
	}

	public String getAllContainedComments() {
		return allContainedComments;
	}

	public void setAllContainedComments(String allContainedComments) {
		this.allContainedComments = allContainedComments;
	}

	public String getAnnotations() {
		return annotations;
	}

	public String getTestAnnotation() {
		return testAnnotation;
	}

	public void setTestAnnotation(String testAnnotation) {
		this.testAnnotation = testAnnotation;
	}

	public void setAnnotations(String annotations) {
		this.annotations = annotations;
	}

	public String getModifiers() {
		return modifiers;
	}

	public void setModifiers(String modifiers) {
		this.modifiers = modifiers;
	}

	public String getParameters() {
		return parameters;
	}

	public void setParameters(String parameters) {
		this.parameters = parameters;
	}

	public String getThrownExceptions() {
		return thrownExceptions;
	}

	public void setThrownExceptions(String thrownExceptions) {
		this.thrownExceptions = thrownExceptions;
	}

	public String getBody() {
		return body;
	}

	public void setBody(String body) {
		this.body = body;
	}

	public boolean isContainsStrings() {
		return containsStrings;
	}

	public void setContainsStrings(boolean containsStrings) {
		this.containsStrings = containsStrings;
	}

	public String[] getContainedStrings() {
		return containedStrings;
	}

	public void setContainedStrings(String[] containedStrings) {
		this.containedStrings = containedStrings;
	}

	public String getPackageName() {
		return packageName;
	}

	public void setPackageName(String packageName) {
		this.packageName = packageName;
	}

	public String getTestcaseFullname() {
		return testcaseFullname;
	}

	public void setTestcaseFullname(String testcaseFullname) {
		this.testcaseFullname = testcaseFullname;
	}

	public String getClassImports() {
		return classImports;
	}

	public void setClassImports(String classImports) {
		this.classImports = classImports;
	}

	public String getFilePath() {
		return filePath;
	}

	public void setFilePath(String filePath) {
		this.filePath = filePath;
	}

	public String getFullMethod() {
		return fullMethod;
	}

	public void setFullMethod(String fullMethod) {
		this.fullMethod = fullMethod;
	}

	public String[] getFullMethodTokens() {
		return fullMethodTokens;
	}

	public void setFullMethodTokens(String[] fullMethodTokens) {
		this.fullMethodTokens = fullMethodTokens;
	}

}