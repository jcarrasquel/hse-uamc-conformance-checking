package com.pais.fix;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class Order {

	protected static Double MARKET = Double.MAX_VALUE;
	
	protected String identifier;
	
	protected String currentState;
	
	protected Integer currentSize;
	
	protected Double price; 	

	protected String side;
	
	protected LocalDateTime arrivalTime;
	
	public Order(String identifier, String state, String size, String price, String side){
		this.identifier = identifier;
		this.currentState = state;
		this.currentSize = Integer.parseInt(size);
		this.price = price.equalsIgnoreCase("market") ? Order.MARKET : Double.parseDouble(price);
		this.side = side;
	}
	
	public Order(String identifier, String initialState, String initialSize, String price, String side, String arrivalTime){
		this.identifier = identifier;
		this.currentState = initialState;
		this.currentSize = Integer.parseInt(initialSize);
		this.price = price.equalsIgnoreCase("market") ? Order.MARKET : Double.parseDouble(price);
		this.side = side;
		DateTimeFormatter myFormatter = DateTimeFormatter.ofPattern("dd-MM-yyyy'T'HH:mm:ss.SSSSSS");
		this.arrivalTime = LocalDateTime.parse(arrivalTime, myFormatter);
	}
	
	public String getIdentifier() {
		return identifier;
	}

	public void setIdentifier(String identifier) {
		this.identifier = identifier;
	}

	public String getCurrentState() {
		return currentState;
	}

	public void setCurrentState(String currentState) {
		this.currentState = currentState;
	}

	public Integer getCurrentSize() {
		return currentSize;
	}

	public void setCurrentSize(Integer currentSize) {
		this.currentSize = currentSize;
	}

	public Double getPrice() {
		return price;
	}

	public void setPrice(Double price) {
		this.price = price;
	}

	public String getSide() {
		return side;
	}

	public void setSide(String side) {
		this.side = side;
	}

	public void setArrivalTime(LocalDateTime arrivalTime) {
		this.arrivalTime = arrivalTime;
	}
	
	public LocalDateTime getArrivalTime() {
		return this.arrivalTime;
	}
	
	@Override
	public boolean equals(Object o){
		if(o instanceof Order){
	      Order o2 = (Order) o;
	      return o2.identifier.equalsIgnoreCase(this.identifier);
	    }
	    return false;
	}
}
