package com.pais.fix;

import java.util.ArrayList;

public class Case {
	
	private ArrayList<Event> events;

	public Case(){
		events = new ArrayList<Event>();
	}
	
	public void addEvent(Event e){
		this.events.add(e);
	}
	
	public ArrayList<Event> getEvents() {
		return events;
	}
	
	//TODO include attributes of an order
}
