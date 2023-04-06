from datetime import datetime

def generate_html_content(last_5_signals, logo_urls, fetch_interval):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="{fetch_interval}">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{current_time}</title>
<style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #222831;
            color: #ffffff;
        }}

        h1 {{
            background-color: #393e46;
            color: #ffffff;
            padding: 20px;
            margin: 0;
            animation: fadeIn 1s ease-in-out both;
        }}

        h2 {{
            padding: 10px;
            background-color: #393e46;
            margin: 0;
            animation: fadeIn 1s ease-in-out both;
            animation-delay: 0.5s;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            opacity: 0;
            animation: fadeIn 1s ease-in-out forwards;
            animation-delay: 1s;
        }}
        
        th, td {{
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #444;
        }}
        
        th {{
            background-color: #2d3436;
            font-weight: bold;
        }}

        tbody tr:nth-child(even) {{
            background-color: #393e46;
        }}

        tbody tr:hover {{
            background-color: #4e525a;
            transition: background-color 0.3s ease-in-out;
        }}

        a {{
            text-decoration: none;
            color: #00adb5;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}

        .up {{
            color: #5eba7d;
        }}

        .down {{
            color: #e17055;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}

        .coin-logo {{
            vertical-align: middle;
            margin-right: 5px;
            transition: transform 0.3s ease-in-out;
        }}

        .coin-logo:hover {{
            transform: scale(1.2);
        }}

        @media (max-width: 767px) {{
            table, thead, tbody, th, td, tr {{
                display: block;
            }}

            thead tr {{
                position: absolute;
                top: -9999px;
                left: -9999px;
            }}

            tr {{
                border: 1px solid #ccc;
                margin-bottom: 10px;
            }}

            td {{
                border: none;
                border-bottom: 1px solid #eee;
                position: relative;
                padding-left: 50%;
            }}

            td:before {{
                content: attr(data-label);
                position: absolute;
                top: 6px;
                left: 6px;
                font-weight: bold;
                width: 45%;
                padding-right: 10px;
                white-space: nowrap;
            }}
            td:last-child {{
               padding-bottom: 20px;
            }}
    }}

    @keyframes fadeIn {{
        0% {{
            opacity: 0;
        }}
        100% {{
            opacity: 1;
        }}
    }}
</style>
</head>
<body>
    <header>
        <div style="display: flex; align-items: center; justify-content: space-between; background-color: #393e46; padding: 10px;">
            <img src="logo.png" alt="Logo" style="width: 100px; height: auto;">
            <h1>Navigate Market Trends - {current_time}</h1>
        </div>
    </header>
    <div class="container">
"""


    for idx, potential_symbols in enumerate(reversed(last_5_signals), 1):
        html_content += f"<h2>Signal {idx}</h2>"
        html_content += """
        <table>
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Volume Change</th>
                    <th>Price Change</th>
                    <th>Direction</th>
                    <th>Moving Average</th>
                    <th>Current Price</th>
                    <th>Exchange Link</th>
                </tr>
            </thead>
            <tbody>
    """

        for symbol in potential_symbols:
            formatted_current_price = f"{symbol['current_price']:.8f}"
            formatted_moving_average = f"{symbol['moving_average']:.8f}"
            direction_class = "up" if symbol['price_direction'] == "Up" else "down"
            base_coin_symbol = symbol['symbol'][:-3]  
            coin_logo_url = "logo.png"  # Use the same logo for all coins

            html_content += f"""
            <tr class="{direction_class}">
                <td data-label="Symbol">
                    <img class="coin-logo" src="{coin_logo_url}" alt="{base_coin_symbol} logo" width="24" height="24">
                    {symbol['symbol']}
                </td>
                <td data-label="Volume Change">{symbol['volume_change_pct']:.2f}%</td>
                <td data-label="Price Change">{symbol['price_change_pct']}%</td>
                <td data-label="Direction">{symbol['price_direction']}</td>
                <td data-label="Moving Average">{formatted_moving_average}</td>
                <td data-label="Current Price">{formatted_current_price}</td>
                <td data-label="Exchange Link">
                    <a href="{symbol['exchange_link']}">Trade on Binance</a>
                </td>
            </tr>
    """
        html_content += """
            </tbody>
        </table>
    """
    html_content += """
    </div>
</body>
</html>
"""
    return html_content