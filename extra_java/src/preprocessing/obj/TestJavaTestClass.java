package preprocessing.obj;

import java.io.File;
import java.io.FileNotFoundException;

public class TestJavaTestClass {

	public static void main(String[] args) throws FileNotFoundException {

		String path ="/klonhome/shared/data/git/spring-projects_spring-framework/spring-core/src/test/java/org/springframework/util/SystemPropertyUtilsTests.java";
		File file = new File(path);
		JavaTestClass tc = new JavaTestClass();
		tc.parseTestClass(file);
		System.out.println("akuku");
	}

}
