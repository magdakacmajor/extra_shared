package preprocessing.obj;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.stream.Collectors;

public class SizeBounds {
	int srcLower;
	int srcUpper;
	int tgtLower;
	int tgtUpper;
		
	public SizeBounds (int srcLower, int srcUpper, int tgtLower, int tgtUpper){
		this.srcLower = srcLower;
		this.srcUpper = srcUpper;
		this.tgtLower = tgtLower;
		this.tgtUpper = tgtUpper;
	}
	
	public SizeBounds (String... args){
		ArrayList<Integer> intArgs = (ArrayList<Integer>) Arrays.stream(args)
										   .map(a -> Integer.parseInt(a))
										   .collect(Collectors.toList());
		this.srcLower = intArgs.get(0);
		this.srcUpper = intArgs.get(1);
		this.tgtLower = intArgs.get(2);
		this.tgtUpper = intArgs.get(3);
	}
	
	public int getSrcLower() {
		return srcLower;
	}
	public void setSrcLower(int srcLower) {
		this.srcLower = srcLower;
	}
	public int getSrcUpper() {
		return srcUpper;
	}
	public void setSrcUpper(int srcUpper) {
		this.srcUpper = srcUpper;
	}
	public int getTgtLower() {
		return tgtLower;
	}
	public void setTgtLower(int tgtLower) {
		this.tgtLower = tgtLower;
	}
	public int getTgtUpper() {
		return tgtUpper;
	}
	public void setTgtUpper(int tgtUpper) {
		this.tgtUpper = tgtUpper;
	}

}
