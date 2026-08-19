# CCC (Cline Claude Cost)

Ever wonder if you're overpaying for that $200/month Claude Max subscription? CCC analyzes your actual token usage from Cline VS Code extension logs to show you how much you would have paid if you were using Claude API calls instead. Discover your potential savings!

## 🛠️ Requirements

- Python 3.7.0 and above
- VS Code with Cline extension installed
- Some coding history with Cline

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/jeremysltn/CCC.git
   cd CCC
   ```

2. **Install rich**
   ```bash
   pip install rich
   ```

3. **Run the calculator**
   ```bash
   python CCC.py
   ```

## 🎯 CLI Options

- **Check version**: `python CCC.py --version` or `python CCC.py -v`
- **Export to SVG**: `python CCC.py --export-svg` (saves report as SVG file)
- **Export to HTML**: `python CCC.py --export-html` (saves report as HTML file)

## 📊 Sample Output

![CCC Demo](https://i.imgur.com/EDU8WM8.jpeg)

## 📁 Where it looks

The script analyzes logs from:
```
~/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/tasks/
```

Each Cline project folder contains a `ui_messages.json` file with detailed usage data.

## ⚠️ Important Notes

- API pricing subject to change. Check [Anthropic's official pricing](https://www.anthropic.com/pricing) for current rates.
- **Comparisons with usage limits not included** - Claude Max subscription plans have undisclosed usage limits.

## 💰 Supported Models

| Model | Input ($/MTok) | Output ($/MTok) | Cache Write ($/MTok) | Cache Read ($/MTok) |
|-------|----------------|-----------------|---------------------|---------------------|
| claude-fable-5 | $10.00 | $50.00 | $12.50 | $1.00 |
| claude-mythos-5 | $10.00 | $50.00 | $12.50 | $1.00 |
| claude-opus-5 | $5.00 | $25.00 | $6.25 | $0.50 |
| claude-opus-4-8 | $5.00 | $25.00 | $6.25 | $0.50 |
| claude-opus-4-7 | $5.00 | $25.00 | $6.25 | $0.50 |
| claude-opus-4-6 | $5.00 | $25.00 | $6.25 | $0.50 |
| claude-opus-4-5 | $5.00 | $25.00 | $6.25 | $0.50 |
| claude-opus-4-1 | $15.00 | $75.00 | $18.75 | $1.50 |
| claude-opus-4 | $15.00 | $75.00 | $18.75 | $1.50 |
| claude-sonnet-5 | $2.00 | $10.00 | $2.50 | $0.20 |
| claude-sonnet-4-6 | $3.00 | $15.00 | $3.75 | $0.30 |
| claude-sonnet-4-5 | $3.00 | $15.00 | $3.75 | $0.30 |
| claude-sonnet-4 | $3.00 | $15.00 | $3.75 | $0.30 |
| claude-haiku-4-5 | $1.00 | $5.00 | $1.25 | $0.10 |
| claude-3-7-sonnet | $3.00 | $15.00 | $3.75 | $0.30 |
| claude-3-5-sonnet | $3.00 | $15.00 | $3.75 | $0.30 |
| claude-3-5-haiku | $0.80 | $4.00 | $1.00 | $0.08 |

Cache writes are priced at the standard 5-minute cache write rate (1-hour cache writes cost more, but Cline logs don't distinguish between the two). Unrecognized models fall back to Sonnet pricing.

## 🤝 Contributing

Found a bug or want to add a feature? Pull requests welcome!

## 📝 License

MIT License - feel free to use and modify as needed.
