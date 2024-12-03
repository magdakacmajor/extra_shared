package extra;

import java.io.File;

public class Custam {

	public static void main(String[] args) {
		String dir = "/home/magda/a-tud/data/spring/ftrace_reports/gen_75k/logs0";
		File f = new File(dir);
		String[] flist = f.list();
		System.out.println("akuku");
	}

}
