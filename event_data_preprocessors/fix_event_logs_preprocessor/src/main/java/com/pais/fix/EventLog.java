package com.pais.fix;

import java.util.LinkedHashMap;

public class EventLog {
	
	private LinkedHashMap<String, Case> cases;
	
	public EventLog(){
		cases = new LinkedHashMap<String, Case>();
	}

	public LinkedHashMap<String, Case> getCases() {
		return cases;
	}

}
