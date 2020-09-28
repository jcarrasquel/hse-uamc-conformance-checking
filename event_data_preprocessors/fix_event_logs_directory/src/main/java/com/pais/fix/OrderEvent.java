package com.pais.fix;

import java.text.ParseException;

public class OrderEvent extends Event implements Comparable<OrderEvent>{

	private String orderId;	
	
	private String price;
	
	private String side;
	
	private String qty;
	
	private String receiver;
	
	private String state;
	
	private String ciOrderId;
	
	private String orderType;
	
	private String tradeId;
	
	private Order tradeOrder;
	
	public Order getTradeOrder(){
		return tradeOrder;
	}
	
	public void setTradeOrder(Order order){
		this.tradeOrder = order;
	}
		
	public OrderEvent(String activity, String state, String timestamp, String price, String side, String qty, String receiver, String ciOrderId) throws ParseException {
		super(activity, timestamp);
		if(state != null){
			this.setState(state);
		}else{
			this.state = "-";
		}
		this.ciOrderId = ciOrderId;
		this.setPrice(price);
		this.side = side;
		if(side.equalsIgnoreCase("1")){
			this.side = "buy";
		}else if(side.equalsIgnoreCase("2")){
			this.side = "sell";
		}
		this.setQty(qty); // check cases different from 1 and 2 
		this.setReceiver(receiver);
		this.tradeId = null;
	}
	
	public OrderEvent(String activity, String state, String timestamp, String price, String side, String qty, String receiver, String ciOrderId, String orderType) throws ParseException {
		super(activity, timestamp);
		if(state != null){
			this.setState(state);
		}else{
			this.state = "-";
		}
		this.ciOrderId = ciOrderId;
		this.setPrice(price);
		this.side = side;
		if(side.equalsIgnoreCase("1")){
			this.side = "buy";
		}else if(side.equalsIgnoreCase("2")){
			this.side = "sell";
		}
		this.setQty(qty); // check cases different from 1 and 2 
		this.setReceiver(receiver);
		this.setOrderType(orderType);
		this.tradeId = null;
	}
	
	public void setOrderId(String orderId){
		this.orderId = orderId;
	}
	
	public String getOrderId(){
		return orderId;
	}
	
	public void setTradeId(String tradeId){
		this.tradeId = tradeId;
	}
	
	public String getTradeId(){
		return tradeId;
	}
	
	public String getCiOrderId(){
		return ciOrderId;
	}
	
	public void setOrderType(String orderType){
		if(orderType.equalsIgnoreCase("1")){
			this.orderType = "market";
		}
		if(orderType.equalsIgnoreCase("2")){
			this.orderType = "limit";
		}
	}
	
	public String getOrderType(){
		return orderType;
	}
	
	public void setState(String state){
		this.state = state;
		if(state.equalsIgnoreCase("0")){
			this.state = "new";
		}
		if(state.equalsIgnoreCase("1")){
			this.state = "partially filled";
		}
		if(state.equalsIgnoreCase("2")){
			this.state = "filled";
		}
		if(state.equalsIgnoreCase("3")){
			this.state = "done by day";
		}
		if(state.equalsIgnoreCase("4")){
			this.state = "canceled";
		}
		if(state.equalsIgnoreCase("5")){
			this.state = "replaced";
		}
		if(state.equalsIgnoreCase("6")){
			this.state = "pending cancel";
		}
		if(state.equalsIgnoreCase("7")){
			this.state = "stopped";
		}
		if(state.equalsIgnoreCase("8")){
			this.state = "rejected";
		}
		if(state.equalsIgnoreCase("9")){
			this.state = "suspended";
		}
		if(state.equalsIgnoreCase("A")){
			this.state = "pending new";
		}
		if(state.equalsIgnoreCase("B")){
			this.state = "calculated";
		}
		if(state.equalsIgnoreCase("C")){
			this.state = "expired";
		}
		if(state.equalsIgnoreCase("D")){
			this.state = "accepted for bidding";
		}
		if(state.equalsIgnoreCase("E")){
			this.state = "pending replace";
		}
	}

	public String getState(){
		return state;
	}
	
	public String getPrice() {
		return price;
	}

	public void setPrice(String price) {
		this.price = price;
	}

	public String getSide() {
		return side;
	}

	public void setSide(String side) {
		this.side = side;
	}

	public String getQty() {
		return qty;
	}

	public void setQty(String qty) {
		this.qty = qty;
	}

	public String getReceiver() {
		return receiver;
	}

	public void setReceiver(String receiver) {
		this.receiver = receiver;
	}
	
	@Override
	public int compareTo(OrderEvent o) {
		if(timestamp.equals(o.timestamp)){
			if(activity.equals("trade") || activity.equals("trade_cancel")){
				return -1;
			}
		}
		return timestamp.compareTo(o.timestamp);
	}
}
