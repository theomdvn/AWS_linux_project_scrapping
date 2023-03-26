import os
import time
import subprocess
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objs as go




def get_solana_price():
	cmd = 'curl -s https://blockworks.co/price/sol | grep -oP \'<p class="w-64 text-4xl text-left text-dark">\\K[^<]*\''
	price = subprocess.check_output(cmd,shell=True,text=True).strip()
	return price

def price_to_csv(price, filename='solana_prices.csv'):
	ts = pd.to_datetime('now')
	data = pd.DataFrame({'timestamp': [ts], 'price': [price]})
	
	if not os.path.exists(filename):
		data.to_csv(filename, index=False)
	else:
		data.to_csv(filename, mode = "a", header=False,index=False)
def read_price(filename='solana_prices.csv'):
	if os.path.exists(filename):
		return pd.read_csv(filename)
	else:
		return pd.DataFrame()


def generate_daily_report(df):
	if df.empty:
		return "No data available for daily report"
	daily_df = df.set_index('timestamp').resample('D').agg({
		'price':['open', 'close', 'high', 'low']
	})
        
	daily_df.columns = ['open', 'close', 'high', 'low']
	daily_df['change'] = daily_df['close'] - daily_df['open']
	daily_df['volatility'] = daily_df['high'] - daily_df['low']
	daily_df.reset_index(inplace=True)
	today = pd.to_datetime('today').normalize()
	report = daily_df[daily_df['timestamp'] == today]

	if report.empty:
		return "No data available for today's report."

	return f"""Daily Report (updated at 8 PM):
		Open: {report['open'].values[0]:.2f}
		Close: {report['close'].values[0]:.2f}
		High: {report['high'].values[0]:.2f}
		Low: {report['low'].values[0]:.2f}
		Change: {report['change'].values[0]:.2f}
		Volatility: {report['volatility'].values[0]:.2f}"""


app = dash.Dash(__name__)

app.layout = html.Div([
	html.H1("Solana Price Dashboard by Theo Midavaine IF3"),
	html.Div(id="solana-price"),
	html.Div(id="daily-report"),
	dcc.Graph(id="price-time-series"),
	dcc.Interval(
		id='interval-component',
		interval=5*60*1000,
		n_intervals=0
	)
])

@app.callback(Output("solana-price","children"),
		Output("price-time-series","figure"),
		Output("daily-report", "children"),
		Input("interval-component","n_intervals"))

def update_price_and_graph(n):
	price = get_solana_price()
	price_to_csv(price)
	df = read_price()

	fig = go.Figure()

	if not df.empty:
		fig.add_trace(go.Scatter(x=df['timestamp'],y=df['price'],mode='lines+markers', name='Solana price'))
	fig.update_layout(title = 'Solana price history', xaxis_title='Timestamp', yaxis_title='Price (USD)')

	current_time = pd.to_datetime('now').tz_localize(None)
	if current_time.hour == 20 and current_time.minute == 0:
    		daily_report = generate_daily_report(df)
	else:
    		daily_report = ""
	return f"Current Solana Price {price}",fig

if __name__ == "__main__":
	app.run_server(debug=True,host='0.0.0.0', port=8050 )

